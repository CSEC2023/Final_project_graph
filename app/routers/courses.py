"""
Routers for course-level graph operations such as cycle detection
and shortest prerequisite paths.
"""

from typing import List

from fastapi import APIRouter, Query

from app.database.neo4j import neo4j_client
from app.models.course import PrerequisiteCycle, ShortestPathResponse

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/prerequisites/cycles", response_model=List[PrerequisiteCycle])
def get_prerequisite_cycles(limit: int = 50):
    """
    Return cycles found in the prerequisite graph.

    A cycle occurs when a course eventually requires itself.
    """
    query = """
    MATCH p = (c:Course)-[:REQUIRES*1..10]->(c)
    WITH [n IN nodes(p) | n.code] AS codes
    RETURN DISTINCT codes AS cycle
    LIMIT $limit
    """

    records = neo4j_client.run(query, limit=limit)

    cycles: list[PrerequisiteCycle] = []
    for record in records:
        codes = record["cycle"]
        if codes and len(codes) > 1:
            cycles.append(PrerequisiteCycle(courses=codes))

    return cycles


@router.get("/path/shortest", response_model=ShortestPathResponse)
def shortest_prerequisite_path(
    from_course: str = Query(..., description="Starting course code"),
    to_course: str = Query(..., description="Target course code"),
):
    """
    Compute the shortest prerequisite path between two courses.
    """
    query = """
    MATCH (start:Course {code: $from_code}), (end:Course {code: $to_code})
    MATCH p = shortestPath( (start)-[:REQUIRES*0..10]->(end) )
    RETURN [n IN nodes(p) | n.code] AS codes
    """

    records = neo4j_client.run(
        query,
        from_code=from_course,
        to_code=to_course,
    )

    if not records:
        return ShortestPathResponse(
            from_course=from_course,
            to_course=to_course,
            path=[],
            length=0,
        )

    codes = records[0]["codes"] or []
    length = len(codes)
