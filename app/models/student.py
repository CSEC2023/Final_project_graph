from typing import List
from pydantic import BaseModel


class EligibilityResponse(BaseModel):
    """
    Response model indicating whether a student is eligible
    to take a given course and which prerequisites are missing.
    """
    student_id: str
    course_id: str
    eligible: bool
    missing_prerequisites: List[str]


class CourseSequenceResponse(BaseModel):
    """
    Response model representing a recommended course sequence,
    grouped into levels where courses can be taken in parallel.
    """
    student_id: str
    target_course: str
    sequence: List[List[str]]
