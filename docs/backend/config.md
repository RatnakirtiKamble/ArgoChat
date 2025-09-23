### backend/config.py

Purpose: Centralized configuration via `pydantic-settings`. Loads values from environment or `.env`.

Settings:
- `ASYNC_DATABASE_URL` (str): SQLAlchemy async database URL. Defaults to SQLite test DB.
- `SYNC_DATABASE_URL` (str): Synchronous database URL for tools that require it.
- `EMBED_MODEL` (str): SentenceTransformer model name used for embeddings.
- `CHROMA_COLLECTION` (str): Chroma collection name for vector search.

Usage:
- Instantiate using `settings = Settings()` and import throughout the backend.
- `.env` file path is controlled by inner `Config.env_file = ".env"`.


