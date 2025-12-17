from fastapi import APIRouter, Depends

from app.database.neo4j import neo4j_client
from app.models.analytics import CourseAnalytics
from app.services.auth import get_api_key


router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_api_key)],
)


@router.get("/courses/summary", response_model=CourseAnalytics)
def courses_summary():
    """Return basic analytics about courses and prerequisites."""
    query = """
    // count prerequisites per course
    MATCH (c:Course)
    OPTIONAL MATCH (c)-[:REQUIRES]->(p:Course)
    WITH c, count(p) AS prereq_count

    WITH
      count(c) AS total_courses,
      avg(prereq_count) AS avg_prereqs,
      max(prereq_count) AS max_prereqs,
      count(CASE WHEN prereq_count = 0 THEN 1 END) AS no_prereq

    OPTIONAL MATCH (s:Student)
    WITH total_courses, avg_prereqs, max_prereqs, no_prereq, count(DISTINCT s) AS total_students

    RETURN
      total_courses AS totalCourses,
      total_students AS totalStudents,
      avg_prereqs AS avgPrereqs,
      max_prereqs AS maxPrereqs,
      no_prereq AS coursesWithoutPrereqs
    """

    records = neo4j_client.run(query)
    if not records:
        return CourseAnalytics(
            total_courses=0,
            total_students=0,
            avg_prerequisites=0.0,
            max_prerequisites=0,
            courses_without_prerequisites=0,
        )

    rec = records[0]

    return CourseAnalytics(
        total_courses=rec["totalCourses"] or 0,
        total_students=rec["totalStudents"] or 0,
        avg_prerequisites=float(rec["avgPrereqs"] or 0.0),
        max_prerequisites=rec["maxPrereqs"] or 0,
        courses_without_prerequisites=rec["coursesWithoutPrereqs"] or 0,
    )
