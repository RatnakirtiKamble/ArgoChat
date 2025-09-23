## ArgoChat Documentation

This documentation describes the architecture and components of ArgoChat. Code is not modified; docs provide context, responsibilities, and usage.

### Overview
- Backend: FastAPI service exposing `/api/query`, LLM planning with Ollama, SQL + vector search with Chroma, and summarization.
- Data Ingest: Script to fetch Argo data, store in PostgreSQL, and index in Chroma.
- Frontend: React (Vite + TS) chat UI with region selection map (Leaflet) calling backend.

### Structure
- backend/
  - server.py: FastAPI app, CORS, router registration.
  - config.py: Pydantic Settings for env-configurable parameters.
  - middleware/cors.py: CORS policy.
  - routers/query.py: `/api/query` endpoint and request model.
  - services/query.py: Orchestrates LLM plan, SQL queries, filters, vector search, summarization.
  - db/db_connection.py: Async SQLAlchemy session factory and context manager.
  - utils/queries.py: Query helpers, vector search, JSON extraction, sanitization, in-memory filters.
- data_ingest/
  - ingest.py: Fetches Argo data by regions/months, loads into PostgreSQL and Chroma.
- frontend/
  - src/pages/LandingPage.tsx: Chat UI + map modal for region selection.
  - src/App.tsx, src/main.tsx: Routing and app bootstrap.
  - index.html, vite.config.ts, package.json, tailwind.config.js: Build tooling.

### Environments
Configure values via `.env` per `backend/config.py`:
- ASYNC_DATABASE_URL, SYNC_DATABASE_URL, EMBED_MODEL, CHROMA_COLLECTION

### Data Flow
1) User asks question in UI; optional region selected.
2) Frontend posts `{ user_prompt }` to `/api/query`.
3) Backend LLM returns a sequence of allowed function calls.
4) Backend executes SQL then in-memory filters in sequence.
5) Vector search ranks top results; LLM summarizes data.
6) Summary returned to UI.

### Notes
- Vector store: Chroma persistent client at `backend/chroma_store`.
- LLM: Ollama `mistral:7b` assumed available locally.
- Database: Async SQLAlchemy; ingest script targets PostgreSQL table `argo_data`.


