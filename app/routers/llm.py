from fastapi import APIRouter, Depends
from app.models.llm import LlmQueryRequest, LlmQueryResponse
from app.services.llm import run_llm_query
from app.services.auth import get_api_key

router = APIRouter(
    prefix="/api/llm",
    tags=["llm"],
    dependencies=[Depends(get_api_key)],
)

@router.post("/query", response_model=LlmQueryResponse)
def llm_query(req: LlmQueryRequest):
    cypher, params, result, mode = run_llm_query(req.question)
    return LlmQueryResponse(
        question=req.question,
        cypher=cypher,
        params=params,
        result=result,
        notes=f"mode={mode}",
    )
