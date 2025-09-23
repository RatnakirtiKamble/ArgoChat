### backend/server.py

Purpose: Application entrypoint creating the FastAPI app, enabling CORS, exposing a health check, and registering API routers.

Key elements:
- `app = FastAPI()`: Instantiates the web application.
- `setup_cors(app)`: Enables permissive CORS (see `middleware/cors.py`).
- `@app.get("/health")`: Simple health endpoint returning `{ "status": "ok" }`.
- `app.include_router(query.router, prefix="/api")`: Mounts the query API under `/api`.
- Uvicorn runner when executed as `__main__` binds to `127.0.0.1:8000` with reload.

Runtime notes:
- Expects router module `backend/routers/query.py` to be importable.
- CORS allows all origins, methods, and headers by default.


