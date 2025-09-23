"""Application configuration using pydantic-settings.

Provides environment-driven settings for database URLs, embedding model,
and Chroma collection. Values can be overridden via a `.env` file.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Typed application settings loaded from environment or `.env`."""
    ASYNC_DATABASE_URL: str = "sqlite:///./test.db"
    SYNC_DATABASE_URL: str = "sqlite:///./test.db"
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_COLLECTION: str = "data"

    class Config:
        env_file = ".env"

settings = Settings()

