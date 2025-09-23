"""CORS middleware configuration.

Adds permissive CORS rules for development convenience. Consider scoping
origins in production environments.
"""
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    """Attach `CORSMiddleware` to the provided FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
