from typing import List, Literal

from pydantic import BaseModel


class GdsScore(BaseModel):
    """Graph algorithm score for a course."""
    course: str
    score: float


class GdsTopResponse(BaseModel):
    """Top-K response for a graph algorithm."""
    graph: str
    algorithm: Literal["pagerank", "degree"]
    top_k: int
    results: List[GdsScore]
