"""Application configuration using pydantic-settings.

Provides environment-driven settings for database URLs, embedding model,
and Chroma collection. Values can be overridden via a `.env` file.
"""
from typing import Optional

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Typed application settings loaded from environment or `.env`."""
    
    DATABASE_URL: str = "sqlite:///./test.db"

    ASYNC_DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    CHROMA_SERVER: str = "http://localhost:8001"
    OLLAMA_HOST: str = "http://localhost:11434"

    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_COLLECTION: str = "data"

    class Config:
        env_file = ".env"

    def __init__(self, **values):
        super().__init__(**values)

        if not self.SYNC_DATABASE_URL:
            self.SYNC_DATABASE_URL = self.DATABASE_URL

        if not self.ASYNC_DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                self.ASYNC_DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            else:
               
                self.ASYNC_DATABASE_URL = self.DATABASE_URL


settings = Settings()

