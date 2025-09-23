"""Query orchestration service.

Generates an LLM function plan, executes SQL queries and in-memory
filters, ranks results via vector search, and returns a natural language
summary tailored to the original prompt.
"""
import json
from ollama import Client
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.db_connection import get_db
from sentence_transformers import SentenceTransformer
import chromadb
import torch
from config import settings
from utils.queries import (
    get_profiles_by_temperature_range,
    vector_search,
    get_profile_by_id,
    get_profiles_by_region,
    get_profiles_by_date_range,
    extract_json_from_text,
    sanitize_function_calls, 
    filter_by_date_range,
    filter_by_id, 
    filter_by_temperature_range,
    filter_by_region
)

# -----------------------------
# CONFIG
# -----------------------------
EMBED_MODEL = settings.EMBED_MODEL
CHROMA_COLLECTION = settings.CHROMA_COLLECTION

# Initialize Ollama
ollama_client = Client()

# Initialize Chroma
chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

# Initialize embedder
embedder = SentenceTransformer(EMBED_MODEL)


# -----------------------------
# QUERY SERVICE
# -----------------------------
async def query_service(user_prompt: str) -> str:
    """Execute an LLM-planned data retrieval and summarization workflow.

    Steps:
    1) Ask the LLM to output a JSON list of allowed function calls.
    2) Execute the first call against the database; apply subsequent calls
       as in-memory filters.
    3) Use vector search to rank top profiles and pass them to the LLM for
       summarization.

    Returns
    -------
    str
        Summary text produced by the LLM, or a message dict when no data
        is found.
    """
    torch.cuda.empty_cache()

    system_prompt = """
    You are an assistant that answers questions about Argo ocean data by returning a SEQUENCE of function calls.

    Rules:
    - Allowed functions:
      - get_profiles_by_temperature_range(temp_min:float, temp_max:float)
      - get_profiles_by_region(lat_min:float, lat_max:float, lon_min:float, lon_max:float)
      - get_profiles_by_date_range(start_date:str, end_date:str)
      - get_profile_by_id(profile_id:int)
    - Do NOT invent new function names.
    - Do NOT add explanations or extra text.
    - ALWAYS include all required parameters. Use reasonable defaults instead of leaving parameters out.
    - Respond ONLY with a valid JSON list of function calls.
    - While passing dates make sure the day dates are valid for the month.

    Example valid output:
    [
      {"function": "get_profiles_by_date_range", "args": {"start_date": "2022-08-01", "end_date": "2022-08-31"}},
      {"function": "get_profiles_by_temperature_range", "args": {"temp_min": -5.0, "temp_max": 5.0}}
    ]
    """

    # Step 1: Ask LLM for function plan
    response = ollama_client.chat(
        model="mistral:7b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response["message"]["content"]
    print(f"LLM generated plan:\n{content}")

    try:
        function_calls = extract_json_from_text(content)
        function_calls = sanitize_function_calls(function_calls)
    except Exception as e:
        return {"error": f"Failed to parse function calls: {str(e)}"}

    # Step 2: Execute functions in sequence
    results = []
    for i, call in enumerate(function_calls):
        fn_name = call["function"]
        args = call["args"]

        fn_map = {"get_profiles_by_temperature_range": (get_profiles_by_temperature_range, filter_by_temperature_range), 
                  "get_profiles_by_region": (get_profiles_by_region, filter_by_region), 
                  "get_profiles_by_date_range": (get_profiles_by_date_range, filter_by_date_range), 
                  "get_profile_by_id": (get_profile_by_id, filter_by_id)}
        if i == 0:
            results = await fn_map[fn_name][0](**args)
        else:
            results = fn_map[fn_name][1](results, **args)

        if not results:
            return {"message": "No data found after applying filters."}

    # Step 3: Vector search to rank top 5 results
    top_profiles = vector_search(results, n_results=5)

    # Step 4: Convert to summary text
    data_str = "\n".join(
        f"Profile {p['id']}: Temp={p.get('temperature')}, "
        f"Salinity={p.get('salinity')}, Lat={p.get('lat')}, "
        f"Lon={p.get('lon')}, Time={p.get('time')}"
        for p in top_profiles
    )

    # Step 5: Summarize with LLM
    summary = ollama_client.chat(
        model="mistral:7b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that summarizes Argo ocean profiles. "
                    "Use only the data provided, do not hallucinate. "
                    "Include numeric trends, ranges, and important details."
                ),
            },
            {
                "role": "user",
                "content": f"User asked: {user_prompt}\n\nHere is the data to summarize:\n{data_str}",
            },
        ],
    )

    return summary["message"]["content"]
