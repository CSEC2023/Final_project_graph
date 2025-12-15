from typing import List

from pydantic import BaseModel


class MlRecommendation(BaseModel):
    """Single ML course recommendation."""
    course: str
    score: float
    reason: str


class MlRecommendationsResponse(BaseModel):
    """Response model for ML recommendations."""
    student_id: str
    top_k: int
    recommendations: List[MlRecommendation]


class MlPredictRequest(BaseModel):
    """Request model for ML prediction."""
    student_id: str
    course_id: str


class MlPredictResponse(BaseModel):
    """Response model for ML prediction result."""
    student_id: str
    course_id: str
    probability: float
    prediction: bool
    features: dict

