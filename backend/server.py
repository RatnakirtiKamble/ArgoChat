"""FastAPI application entrypoint.

Initializes the app, applies CORS, exposes a health check, and registers
the API router under the `/api` prefix. When executed directly, runs
Uvicorn in reload mode on localhost:8000.
"""
from fastapi import FastAPI
import uvicorn
from routers import query
from middleware.cors import setup_cors


app = FastAPI()

setup_cors(app)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(query.router, prefix="/api")

if __name__ == "__main__":
    # Run development server when launched directly
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)