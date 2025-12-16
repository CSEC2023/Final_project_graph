"""
Pydantic model for high-level analytics about the course graph.
"""

from pydantic import BaseModel


class CourseAnalytics(BaseModel):
    """Aggregated statistics about courses and prerequisites."""
    total_courses: int
    total_students: int
    avg_prerequisites: float
    max_prerequisites: int
    courses_without_prerequisites: int
