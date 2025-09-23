### backend/utils/queries.py

Purpose: Shared utilities for database queries, serialization, vector search, JSON extraction, sanitization, and in-memory filters.

Sections:
- Config: Initializes Chroma client/collection and SentenceTransformer embedder from settings.
- SQL query functions (async):
  - `get_profiles_by_region(lat_min, lat_max, lon_min, lon_max)`
  - `get_profiles_by_date_range(start_date, end_date)` (parses dates and serializes to ISO)
  - `get_profile_by_id(profile_id)`
  - `get_profiles_by_temperature_range(temp_min, temp_max)` (uses JSONB arrays)
- Vector search:
  - `vector_search(docs, n_results=5)`: Embeds JSONified docs, queries Chroma, maps ids back to input list.
- Custom query (read-only):
  - `custom_query(sql)`: Ensures `SELECT` only, executes and returns mappings.
- LLM output handling:
  - `extract_json_from_text(text)`: Extracts first JSON block/list from possibly fenced text.
  - `sanitize_function_calls(calls)`: Filters to allowed functions and fills defaults.
- In-memory filters:
  - `filter_by_temperature_range`, `filter_by_date_range`, `filter_by_id`, `filter_by_region` (placeholder).

Notes:
- `serialize_row` converts `datetime`/`date` values to ISO strings.
- `ALLOWED_FUNCTIONS` safeguards execution;
- Date parsing format: `%Y-%m-%d`.


