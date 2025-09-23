### backend/routers/query.py

Purpose: Defines the `/api/query` endpoint that accepts a user prompt and returns an LLM-generated answer or message.

Key components:
- `QueryRequest` (Pydantic): Body model with `user_prompt: str`.
- `router = APIRouter()`: Router instance mounted under `/api` by `server.py`.
- `@router.post("/query")`: Async handler that calls `services.query.query_service`.

Error handling:
- Exceptions are caught and re-raised as `HTTPException(status_code=500, detail=str(e))`.

Contract:
- Request JSON: `{ "user_prompt": "..." }`
- Response JSON: `{ "answer": string }` or `{ "message": string }` on no data.


