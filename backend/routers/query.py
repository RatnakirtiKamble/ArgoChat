"""Query API router.

Defines the `/query` endpoint that accepts a user prompt and delegates to
the query service for LLM-driven planning and summarization.
"""
from services import query

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from typing import Optional

import time

router = APIRouter()


class QueryRequest(BaseModel):
    """Request payload for querying Argo data via natural language."""
    user_prompt: str
    location: Optional[str] = None

@router.post("/query")
async def handle_query(request: QueryRequest):
    """Handle a user query by invoking the query service.

    Returns a JSON object with either `answer` or a `message` when no data
    matches, or raises HTTP 500 on unexpected errors.
    """
    # try:
    #     prompt = request.user_prompt
    #     if request.location:
    #         prompt += f" The location provided is {request.location}."
    #     answer = await query.query_service(prompt)

    #     # Ensure answer is a string
    #     if not isinstance(answer, str):
    #         answer = str(answer)

    #     return {"answer": answer}
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

    fake_response = """
Sure! Here's a summary of Argo floats where the surface waters were warmer but gradually cooled with depth:

1. Float F12345 (2025-09-10)
   - Surface: 29.5°C
   - 50m depth: 28.1°C
   - 100m depth: 26.4°C
   - 200m depth: 24.0°C

2. Float F67890 (2025-09-12)
   - Surface: 30.2°C
   - 50m depth: 29.0°C
   - 100m depth: 27.3°C
   - 200m depth: 25.1°C

3. Float F24680 (2025-09-15)
   - Surface: 28.8°C
   - 50m depth: 27.5°C
   - 100m depth: 26.0°C
   - 200m depth: 23.8°C

These floats show a clear pattern of warmer surface waters gradually cooling with depth.
"""

    time.sleep(5)
    return {"answer": fake_response}