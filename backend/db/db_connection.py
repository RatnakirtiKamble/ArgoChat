"""Async SQLAlchemy database session utilities.

Creates the async engine and session factory based on `ASYNC_DATABASE_URL`
from settings, and exposes `get_db()` as an async context manager to yield
and cleanup a session per request.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Settings
from contextlib import asynccontextmanager

settings = Settings()
DATABASE_URL = settings.ASYNC_DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

@asynccontextmanager
async def get_db():
    """Yield an `AsyncSession`, ensuring it is closed after use."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
