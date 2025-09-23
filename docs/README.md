# ArgoChat

ArgoChat is an end-to-end system for exploring and querying **Argo oceanographic data** through a natural language chat interface.  
It combines **FastAPI**, **LLM planning with Ollama**, **SQL + vector search (Chroma)**, and a **React (Vite + TypeScript) frontend** with an interactive map.

---

## ✨ Features
- **Natural language queries** over Argo float datasets.  
- **LLM-driven query planning** (via Ollama).  
- **Hybrid search**: SQL queries + vector retrieval with Chroma.  
- **Interactive frontend** with chat and region selection (Leaflet map).  
- **Data ingestion pipeline** to fetch, store, and index Argo data.

---

## 📂 Project Structure
```
backend/
  server.py              # FastAPI app, CORS, router registration
  config.py              # Pydantic Settings for env parameters
  middleware/cors.py     # CORS policy
  routers/query.py       # /api/query endpoint + request model
  services/query.py      # Orchestrates LLM plan, SQL, filters, vector search, summarization
  db/db_connection.py    # Async SQLAlchemy session factory
  utils/queries.py       # Query helpers, vector search, sanitization

data_ingest/
  ingest.py              # Fetch + load Argo data into PostgreSQL and Chroma

frontend/
  src/pages/LandingPage.tsx   # Chat UI + region map modal
  src/App.tsx, src/main.tsx   # Routing + app bootstrap
  index.html, vite.config.ts  # Build tooling
```

# Configuration

All configuration is managed via environment variables in a .env file (read by backend/config.py):

```
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/argo
SYNC_DATABASE_URL=postgresql://user:pass@localhost:5432/argo
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_COLLECTION=argo_vectors
```

# Getting Started
## 1. Clone and install dependencies
```
git clone https://github.com/your-org/ArgoChat.git
cd ArgoChat
```
- Backend
```
cd backend
pip install -r requirements.txt
```

- Frontend
```
cd frontend
npm install
```

# 2. Setup PostgreSQL

Ensure PostgreSQL is running and create a database:
```
createdb argo
```

# 3. Run Data Ingest

This script fetches Argo data and loads it into PostgreSQL + Chroma vector store.
```
cd data_ingest
python ingest.py
```

# 4. Start Backend (FastAPI)

From the backend/ folder:
```
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

# 5. Start Frontend (React + Vite)

From the frontend/ folder:
```
npm run dev
```
Frontend will be available at: http://localhost:5173

# Data Flow

1. User asks a question in the UI (optionally selects a region).

2. Frontend posts { user_prompt } to /api/query.

3. Backend LLM (Ollama) returns a sequence of allowed function calls.

4. Backend executes SQL queries → applies in-memory filters.

5. Vector search (Chroma) ranks results.

6. LLM generates a natural language summary.

7. Summary returned to frontend chat UI.

# 📌 Notes

- Vector Store: Chroma persistent client at backend/chroma_store/.

- LLM: Assumes ollama run mistral:7b available locally.

- Database: PostgreSQL + async SQLAlchemy.

- Data Ingest: Targets PostgreSQL table argo_data.