"""
Routes handling student-related operations.

This module defines FastAPI endpoints that allow:
- Checking whether a student is eligible to take a course (prerequisite validation).
- Computing an ordered sequence of courses to reach a target course
  using the prerequisite graph stored in Neo4j.
"""

from fastapi import APIRouter, HTTPException, Query

from app.database.neo4j import neo4j_client
from app.models.student import EligibilityResponse, CourseSequenceResponse

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/{student_id}/eligibility", response_model=EligibilityResponse)
def check_student_eligibility(student_id: str, course_id: str = Query(...)):
    """
    Determine whether a student is eligible to take a target course.

    This endpoint checks:
    - All prerequisites of the target course (direct and indirect).
    - All courses the student has already passed (via HAS_PASSED).
    - The missing prerequisites, if any.

    Args:
        student_id (str): Unique ID of the student.
        course_id (str): Course code of the target course.

    Returns:
        EligibilityResponse: Structured eligibility result containing:
            - eligible (bool): True if all prerequisites are satisfied.
            - missing_prerequisites (list[str]): List of unmet prerequisite courses.
    """
    query = """
    MATCH (target:Course {code: $course_id})
    OPTIONAL MATCH (target)-[:REQUIRES*1..]->(prereq:Course)
    WITH target, collect(DISTINCT prereq) AS prereqs

    MATCH (s:Student {id: $student_id})
    OPTIONAL MATCH (s)-[:HAS_PASSED]->(c:Course)
    WITH prereqs, collect(DISTINCT c) AS passed, s, target

    WITH [p IN prereqs WHERE NOT p IN passed] AS missing, s, target
    RETURN missing
    """

    records = neo4j_client.run(
        query,
        student_id=student_id,
        course_id=course_id,
    )

    if not records:
        raise HTTPException(status_code=404, detail="Student or course not found")

    missing_nodes = records[0]["missing"] or []
    missing_codes = [node["code"] for node in missing_nodes]

    return EligibilityResponse(
        student_id=student_id,
        course_id=course_id,
        eligible=len(missing_codes) == 0,
        missing_prerequisites=missing_codes,
    )


@router.get("/{student_id}/plan/sequence", response_model=CourseSequenceResponse)
def plan_course_sequence(student_id: str, course_id: str = Query(...)):
    """
    Suggest a valid ordering of courses (grouped by levels) leading to a target course.

    This endpoint:
    - Collects all prerequisite relationships (direct or indirect) for the target course.
    - Retrieves all courses the student has already completed.
    - Builds a dependency graph and performs a level-based scheduling algorithm,
      returning groups of courses that can be taken together once prerequisites
      from previous levels are satisfied.

    Args:
        student_id (str): Unique ID of the student.
        course_id (str): Course code of the target course.

    Returns:
        CourseSequenceResponse: Contains:
            - target_course (str)
            - sequence (list[list[str]])
    """

    # -------------------------------
    # (1) Extract prerequisite edges
    # -------------------------------
    edges_query = """
MATCH (target:Course {code: $course_id})
CALL {
  WITH target
  MATCH p = (target)-[:REQUIRES*1..10]->(:Course)
  UNWIND relationships(p) AS r
  WITH DISTINCT startNode(r) AS c, endNode(r) AS pr
  RETURN c AS courseNode, pr AS prereqNode
}
RETURN
  courseNode.code AS course,
  prereqNode.code AS prereq,
  $course_id AS target_code
LIMIT 5000
"""


    edge_records = neo4j_client.run(edges_query, course_id=course_id)

    if not edge_records:
        # The target course either does not exist or has no prerequisites
        exists = neo4j_client.run(
            "MATCH (c:Course {code: $code}) RETURN c LIMIT 1",
            code=course_id,
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Target course not found")

        # Course exists but has no prerequisites → return a minimal sequence
        passed_codes = {
            r["code"]
            for r in neo4j_client.run(
                """
                MATCH (s:Student {id: $student_id})-[:HAS_PASSED]->(c:Course)
                RETURN c.code AS code
                """,
                student_id=student_id,
            )
        }

        sequence: list[list[str]] = []
        if course_id not in passed_codes:
            sequence.append([course_id])

        return CourseSequenceResponse(
            student_id=student_id,
            target_course=course_id,
            sequence=sequence,
        )

    # Build edges and nodes sets
    edges: list[tuple[str, str]] = []
    nodes: set[str] = set()
    target_code = edge_records[0]["target_code"]

    for rec in edge_records:
        course = rec["course"]
        prereq = rec["prereq"]
        edges.append((course, prereq))
        nodes.add(course)
        nodes.add(prereq)

    nodes.add(target_code)

    # -------------------------------
    # (2) Courses student has passed
    # -------------------------------
    passed_records = neo4j_client.run(
        """
        MATCH (s:Student {id: $student_id})-[:HAS_PASSED]->(c:Course)
        RETURN c.code AS code
        """,
        student_id=student_id,
    )
    passed_courses = {r["code"] for r in passed_records}

    # -------------------------------
    # (3) Build prerequisite map
    # -------------------------------
    prereqs: dict[str, set[str]] = {n: set() for n in nodes}
    for course, prereq in edges:
        prereqs.setdefault(course, set()).add(prereq)
        prereqs.setdefault(prereq, set())

    # -------------------------------
    # (4) Level-based scheduling
    # -------------------------------
    done: set[str] = set(passed_courses)
    remaining: set[str] = set(nodes) - done

    # Target already completed → nothing to plan
    if target_code in done:
        return CourseSequenceResponse(
            student_id=student_id,
            target_course=target_code,
            sequence=[],
        )

    sequence: list[list[str]] = []

    while remaining:
        level = sorted(
            [
                c
                for c in remaining
                if prereqs.get(c, set()).issubset(done)
            ]
        )

        if not level:
            # Remaining nodes cannot be unlocked → cycle or malformed graph
            sequence.append(sorted(list(remaining)))
            break

        sequence.append(level)
        done.update(level)
        remaining -= set(level)

    return CourseSequenceResponse(
        student_id=student_id,
        target_course=target_code,
        sequence=sequence,
    )
