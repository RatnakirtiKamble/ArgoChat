### backend/services/query.py

Purpose: Orchestrates the full question-answering workflow using LLM planning, database queries, in-memory filtering, vector search, and final LLM summarization.

Flow:
1. Build a constrained system prompt for the LLM listing allowed functions and output format (JSON list of function calls).
2. Call Ollama (`mistral:7b`) to generate a function plan for the user prompt.
3. Extract and sanitize JSON function calls via `utils.queries.extract_json_from_text` and `sanitize_function_calls`.
4. Execute the first function as a database query; apply subsequent filters in memory using a mapping of functions.
5. If results exist, run `vector_search` to rank top profiles; convert to textual summary context.
6. Ask LLM to summarize results given the user prompt and the selected profiles; return the summary text.

Dependencies:
- `chromadb.PersistentClient` with collection from settings.
- `SentenceTransformer` embedder set by `settings.EMBED_MODEL`.
- `torch.cuda.empty_cache()` invoked at start of query to manage GPU memory.

Inputs/Outputs:
- Input: `user_prompt: str`
- Output: Summary string or an object with `{"message": "No data found..."}` or an error dict when parsing fails.

Operational notes:
- Allowed functions: `get_profiles_by_temperature_range`, `get_profiles_by_region`, `get_profiles_by_date_range`, `get_profile_by_id`.
- Subsequent filters operate on previously fetched results; the first step must produce data.


