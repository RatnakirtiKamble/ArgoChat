"""Query utilities and helpers.

Contains async SQL query functions, serialization helpers, vector search
using Chroma and SentenceTransformers, utilities for parsing/sanitizing
LLM output, and in-memory filter functions applied to result sets.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.db_connection import get_db
from sentence_transformers import SentenceTransformer
import chromadb
import json
from config import settings
import datetime

# -----------------------------
# CONFIG
# -----------------------------
EMBED_MODEL = settings.EMBED_MODEL
CHROMA_COLLECTION = settings.CHROMA_COLLECTION

chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

embedder = SentenceTransformer(EMBED_MODEL)


# -----------------------------
# SQL QUERY FUNCTIONS (SAFE)
# -----------------------------
def serialize_row(row: dict) -> dict:
    """Convert any `datetime` or `date` values in a row to ISO strings."""
    serialized = {}
    for k, v in row.items():
        if isinstance(v, (datetime.datetime, datetime.date)):
            serialized[k] = v.isoformat()
        else:
            serialized[k] = v
    return serialized

async def get_profiles_by_region(
    lat_min: float, lat_max: float, lon_min: float, lon_max: float
) -> List[Dict[str, Any]]:
    """Fetch Argo profiles within the specified lat/lon bounds."""
    async with get_db() as session:  # session is AsyncSession
        result = await session.execute(
            text("""
                SELECT *
                FROM argo_data
                WHERE lat BETWEEN :lat_min AND :lat_max
                  AND lon BETWEEN :lon_min AND :lon_max
            """),
            {"lat_min": lat_min, "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max}
        )
        return [dict(row) for row in result.mappings().all()]

async def get_profiles_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch Argo profiles within an inclusive date range (YYYY-MM-DD)."""
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    async with get_db() as session:
        result = await session.execute(
            text("""
                SELECT *
                FROM argo_data
                WHERE profile_time BETWEEN :start_date AND :end_date
            """),
            {"start_date": start_date, "end_date": end_date}
        )
        rows = result.mappings().all()
        return [serialize_row(dict(r)) for r in rows]


async def get_profile_by_id(profile_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single Argo profile by numeric primary key `id`."""
    async with get_db() as session:
        result = await session.execute(
            text("SELECT * FROM argo_data WHERE id = :profile_id"),
            {"profile_id": profile_id}
        )
        row = result.mappings().first()
        return dict(row) if row else None


# -----------------------------
# SQL QUERY FUNCTIONS
# -----------------------------

async def get_profiles_by_temperature_range(temp_min: float, temp_max: float) -> List[Dict[str, Any]]:
    """Fetch profiles where any temperature value falls within given bounds."""
    async with get_db() as session:
        result = await session.execute(
            text("""
                SELECT *
                FROM argo_data
                WHERE EXISTS (
                    SELECT 1 FROM jsonb_array_elements(temperature) AS temp(value)
                    WHERE (temp.value::float) BETWEEN :temp_min AND :temp_max
                )
            """),
            {"temp_min": temp_min, "temp_max": temp_max}
        )
        rows = [dict(row) for row in result.mappings().all()]

        for r in rows:
            for k, v in r.items():
                if isinstance(v, (datetime.datetime, datetime.date)):
                    r[k] = v.isoformat()
        return rows


# -----------------------------
# VECTOR SEARCH
# -----------------------------

def vector_search(docs: List[Dict[str, Any]], n_results: int = 5) -> List[Dict[str, Any]]:
    """Embed docs and query Chroma to retrieve the top-N most similar.

    Input docs are JSON-serialized prior to embedding to preserve fields.
    """

    doc_texts = [json.dumps(d) for d in docs]
    embeddings = embedder.encode(doc_texts).tolist()
    
    results = collection.query(
        query_embeddings=embeddings,
        n_results=n_results
    )
    
   
    top_docs = []
    for idx_list in results['ids']:  
        for idx in idx_list:
            top_docs.append(docs[int(idx)])
    
    return top_docs[:n_results]


# -----------------------------
# CUSTOM QUERY (ADVANCED)
# -----------------------------

async def custom_query(sql: str) -> List[Dict[str, Any]]:
    """Execute a read-only custom SQL query, restricted to SELECT statements."""
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")
    async with get_db() as session:
        result = await session.execute(text(sql))
        return [dict(row) for row in result.mappings().all()]

import json
import re
ALLOWED_FUNCTIONS = {
    "get_profiles_by_temperature_range",
    "get_profiles_by_region",
    "get_profiles_by_date_range",
    "get_profile_by_id",
}
import re, json
from typing import List, Dict

def extract_json_from_text(text: str) -> List[Dict]:
    """Extract the first valid JSON list/dict from a free-form LLM output.

    Handles fenced code blocks, surrounding prose, and normalizes `None`
    to `null` for JSON compatibility.
    """
    # Grab anything that starts with [ or { and ends with ] or }
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```|([\[\{][\s\S]*[\]\}])"
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        raise ValueError("No JSON list or object found in the text.")

    json_str = match.group(1) or match.group(2)
    json_str = json_str.strip().replace("None", "null")

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            return [parsed]  
        if isinstance(parsed, list):
            return parsed
        raise ValueError("Extracted JSON is neither list nor dict.")
    except json.JSONDecodeError as e:
        print(" Failed JSON:", json_str)
        raise ValueError(f"Invalid JSON format: {e}")


def sanitize_function_calls(calls: List[Dict]) -> List[Dict]:
    """Filter to allowed functions and backfill missing parameters.

    Unknown functions are skipped; reasonable defaults are applied where
    required (e.g., temperature ranges).
    """
    clean_calls = []
    for call in calls:
        fn = call.get("function")
        args = call.get("args", {})

        if fn not in ALLOWED_FUNCTIONS:
            print(f"⚠️ Skipping unsupported function: {fn}")
            continue

        # Fill in missing params safely
        if fn == "get_profiles_by_temperature_range":
            args.setdefault("temp_min", -5.0)
            args.setdefault("temp_max", 40.0)  # typical ocean temp range

        clean_calls.append({"function": fn, "args": args})

    return clean_calls

def filter_by_temperature_range(profiles: List[Dict], temp_min: float, temp_max: float) -> List[Dict]:
    """Filter an in-memory list of profiles by inclusive temperature bounds."""
    return [
        p for p in profiles
        if p.get("temperature") is not None and temp_min <= p["temperature"] <= temp_max
    ]

def filter_by_date_range(profiles: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    """Filter an in-memory list of profiles by inclusive date range."""
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    return [
        p for p in profiles
        if p.get("profile_time") is not None and start_date <= p["profile_time"] <= end_date
    ]

def filter_by_id(profiles: List[Dict], profile_id: Any) -> List[Dict]:
    """Filter an in-memory list of profiles by primary key `id`."""
    profile_id = int(profile_id) if isinstance(profile_id, str) and profile_id.isdigit() else profile_id
    return [p for p in profiles if p.get("id") == profile_id]

def filter_by_region(profiles: List[Dict], profile_id: Any) -> List[Dict]:
    """Placeholder: region filtering occurs at the database layer."""
    # This function is a placeholder as region filtering is done at DB level
    return profiles
