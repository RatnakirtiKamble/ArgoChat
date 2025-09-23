### backend/db/db_connection.py

Purpose: Provide an async SQLAlchemy session factory and a context manager for DB access.

Components:
- `Settings` is instantiated locally to read `ASYNC_DATABASE_URL`.
- `engine = create_async_engine(DATABASE_URL, echo=True, future=True)`.
- `AsyncSessionLocal = sessionmaker(..., class_=AsyncSession, expire_on_commit=False, ...)`.
- `get_db()` async context manager that yields a session and ensures closure.

Usage:
```python
async with get_db() as session:
    result = await session.execute(...)
```

Notes:
- `echo=True` will log SQL statements; disable for production.


