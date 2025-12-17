from fastapi import APIRouter, Query, HTTPException, Depends
from app.database.neo4j import neo4j_client
from app.models.ml import MlRecommendationsResponse, MlRecommendation, MlPredictResponse
from app.services.gds import top_courses
from app.services.auth import get_api_key
from app.services.ml_model import predict_pass_probability

router = APIRouter(
    prefix="/api/ml",
    tags=["ml"],
    dependencies=[Depends(get_api_key)],
)

@router.get("/recommendations", response_model=MlRecommendationsResponse)
def recommend_courses(
    student_id: str = Query(...),
    top_k: int = Query(10, ge=1, le=30),
):
    # student existence
    exists = neo4j_client.run(
        "MATCH (s:Student {id:$id}) RETURN s LIMIT 1",
        id=student_id,
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Student not found")

    # Graph-based recommendation: PageRank top courses (GDS baseline)

    top = top_courses("pagerank", top_k=top_k)
    recs = [
        MlRecommendation(
            course=x["course"],
            score=x["score"],
            reason="High PageRank: central prerequisite hub",
        )
        for x in top
    ]
    return MlRecommendationsResponse(student_id=student_id, top_k=top_k, recommendations=recs)

@router.get("/predict", response_model=MlPredictResponse)
def predict_pass(
    student_id: str = Query(...),
    course_id: str = Query(...),
):
    proba, feats = predict_pass_probability(student_id=student_id, course_id=course_id)
    return MlPredictResponse(
        student_id=student_id,
        course_id=course_id,
        probability=float(proba),
        prediction=bool(proba >= 0.5),
        features=feats,
    )
