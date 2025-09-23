### data_ingest/ingest.py

Purpose: Fetch Argo float profiles (Indian Ocean, 2022 by month), insert into PostgreSQL table `argo_data`, and index descriptive texts + embeddings into a Chroma collection.

Workflow:
1. Define bounds for latitude/longitude and iterate monthly windows across 2022.
2. For each month and regional chunk, fetch profiles via `argopy.DataFetcher(...).region([...]).to_xarray()`.
3. Extract fields: `platform`, `time`, `lat`, `lon`, `PRES`, `TEMP`, `PSAL`; mask NaNs and convert arrays to lists.
4. Build short textual descriptions; compute embeddings via `SentenceTransformer` on CPU/GPU.
5. Insert rows into PostgreSQL `argo_data` (creates table if missing).
6. Add documents and embeddings to Chroma collection (default `argo_data`).

Configuration:
- `PG_CONN`: Connection dict for PostgreSQL.
- `CHROMA_COLLECTION`: Target Chroma collection.
- `EMBED_MODEL`: Embedding model name.

Notes:
- Skips empty regions or invalid profiles; continues on fetch errors.
- Uses chunked lat/lon to reduce request size and memory.


