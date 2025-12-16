"""
Pydantic models for course graph utilities.
"""

from typing import List
from pydantic import BaseModel


class PrerequisiteCycle(BaseModel):
    """Represents a detected cycle in the prerequisite graph."""
    courses: List[str]


class ShortestPathResponse(BaseModel):
    """Shortest path between two courses in the prerequisite graph."""
    from_course: str
    to_course: str
    path: List[str]
    length: int
