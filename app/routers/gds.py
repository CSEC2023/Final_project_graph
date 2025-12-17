from fastapi import APIRouter, Query

from app.models.gds import GdsScore, GdsTopResponse
from app.services.gds import GRAPH_NAME, top_courses


router = APIRouter(prefix="/api/gds", tags=["gds"])


@router.get("/top-courses", response_model=GdsTopResponse)
def get_top_courses(
    algorithm: str = Query("pagerank", pattern="^(pagerank|degree)$"),
    top_k: int = Query(10, ge=1, le=50),
):
    """Return top-ranked courses using a GDS algorithm."""
    results = top_courses(algorithm=algorithm, top_k=top_k)

    return GdsTopResponse(
        graph=GRAPH_NAME,
        algorithm=algorithm,  # type: ignore
        top_k=top_k,
        results=[GdsScore(**r) for r in results],
    )
