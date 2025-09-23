"""Query API router.

Defines the `/query` endpoint that accepts a user prompt and delegates to
the query service for LLM-driven planning and summarization.
"""
from services import query

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

router = APIRouter()


class QueryRequest(BaseModel):
    """Request payload for querying Argo data via natural language."""
    user_prompt: str

@router.post("/query")
async def handle_query(request: QueryRequest):
    """Handle a user query by invoking the query service.

    Returns a JSON object with either `answer` or a `message` when no data
    matches, or raises HTTP 500 on unexpected errors.
    """
    try:
        answer = await query.query_service(request.user_prompt)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))