from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LlmQueryRequest(BaseModel):
    """Request model for an LLM query."""
    question: str


class LlmQueryResponse(BaseModel):
    """Response model for an LLM-generated Cypher query."""
    question: str
    cypher: str
    params: Dict[str, Any] = {}
    result: List[Dict[str, Any]]
    notes: Optional[str] = None
