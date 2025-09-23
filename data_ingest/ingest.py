"""Argo data ingestion pipeline.

Fetches monthly Argo float profiles for the Indian Ocean (year 2022),
persists structured profiles in PostgreSQL (`argo_data`), and indexes
short textual descriptions with embeddings into a Chroma collection.
"""

import numpy as np
import json
import psycopg2
import torch
from argopy import DataFetcher as ArgoDataFetcher
from sentence_transformers import SentenceTransformer
import chromadb
from datetime import datetime
from itertools import product

# -----------------------------
# CONFIG
# -----------------------------
PG_CONN = {
    "host": "localhost",
    "port": "5432",
    "dbname": "argodb",
    "user": "argo",
    "password": "Ratna@1234"
}

CHROMA_COLLECTION = "argo_data"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Device for embeddings
device = 'cuda' if torch.cuda.is_available() else 'cpu'
embedder = SentenceTransformer(EMBED_MODEL, device=device)

# Chroma client
client = chromadb.Client()
collection = client.get_or_create_collection(CHROMA_COLLECTION)


def fetch_and_store_indian_ocean():
    """Fetch and store Indian Ocean Argo data for 2022.

    Iterates month-by-month and across regional latitude/longitude chunks
    to: (1) fetch profiles via Argopy, (2) normalize and persist them to
    PostgreSQL, and (3) generate embeddings for Chroma indexing.
    """
    lat_bounds = [-40, 40]
    lon_bounds = [20, 120]

    months = [f"2022-{str(m).zfill(2)}" for m in range(1, 13)]

    for i in range(len(months)-1):
        print(f"\nProcessing month: {months[i]} to {months[i+1]}")

        lat_chunks = [(lat_bounds[0] + j*20, min(lat_bounds[0] + (j+1)*20, lat_bounds[1])) for j in range(4)]
        lon_chunks = [(lon_bounds[0] + j*25, min(lon_bounds[0] + (j+1)*25, lon_bounds[1])) for j in range(4)]

        for lat_min, lat_max in lat_chunks:
            for lon_min, lon_max in lon_chunks:
                try:
                    print(f"Fetching region: lat {lat_min}-{lat_max}, lon {lon_min}-{lon_max}")
                    ds = ArgoDataFetcher(rc="erddap", mode="standard").region(
                        [lat_min, lat_max, lon_min, lon_max, 0, 1000, months[i], months[i+1]]
                    ).to_xarray()
                except Exception as e:
                    print(f"Failed to fetch data: {e}")
                    continue

                if ds.sizes["N_POINTS"] == 0:
                    print("No profiles found in this region/month.")
                    continue

                profiles = []
                for k in range(ds.sizes["N_POINTS"]):
                    try:
                        lat = float(ds["LATITUDE"].values[k])
                        lon = float(ds["LONGITUDE"].values[k])
                        time = str(np.datetime_as_string(ds["TIME"].values[k], unit="D"))

                        platform_val = ds["PLATFORM_NUMBER"].values[k]
                        platform = str(platform_val.item() if hasattr(platform_val, "item") else platform_val)

                        pres = ds["PRES"].values[k]
                        temp = ds["TEMP"].values[k]
                        psal = ds["PSAL"].values[k]

                        pres = np.atleast_1d(pres)
                        temp = np.atleast_1d(temp)
                        psal = np.atleast_1d(psal)

                        mask = ~np.isnan(temp) & ~np.isnan(psal) & ~np.isnan(pres)
                        pres, temp, psal = pres[mask], temp[mask], psal[mask]

                        if len(pres) == 0:
                            continue

                        profiles.append({
                            "platform": platform,
                            "time": time,
                            "lat": lat,
                            "lon": lon,
                            "depths": pres.tolist(),
                            "temperature": temp.tolist(),
                            "salinity": psal.tolist(),
                        })
                    except Exception as e:
                        print(f" Skipped profile {k}: {e}")
                        continue

                if not profiles:
                    print("No valid profiles in this region.")
                    continue

                texts = [
                    f"Argo profile from float {p['platform']} at {p['time']} ({p['lat']}, {p['lon']}): "
                    f"Depths {p['depths'][:10]}... Temp {p['temperature'][:10]}... Sal {p['salinity'][:10]}..."
                    for p in profiles
                ]

                vectors = embedder.encode(texts, convert_to_numpy=True)

                conn = psycopg2.connect(**PG_CONN)
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS argo_data (
                        id SERIAL PRIMARY KEY,
                        platform VARCHAR(20),
                        profile_time TIMESTAMP,
                        lat DOUBLE PRECISION,
                        lon DOUBLE PRECISION,
                        depths JSONB,
                        temperature JSONB,
                        salinity JSONB
                    );
                """)
                for p in profiles:
                    cur.execute("""
                        INSERT INTO argo_data (platform, profile_time, lat, lon, depths, temperature, salinity)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        p["platform"], p["time"], p["lat"], p["lon"],
                        json.dumps(p["depths"]),
                        json.dumps(p["temperature"]),
                        json.dumps(p["salinity"])
                    ))
                conn.commit()
                cur.close()
                conn.close()

                for p, v, t in zip(profiles, vectors, texts):
                    collection.add(
                        documents=[t],
                        embeddings=[v.tolist()],
                        metadatas=[{
                            "platform": p["platform"],
                            "time": p["time"],
                            "lat": p["lat"],
                            "lon": p["lon"]
                        }],
                        ids=[f"{p['platform']}_{p['time']}"]
                    )

                print(f"Inserted {len(profiles)} profiles for this region/month.")

    print("Finished processing all Indian Ocean regions for 2022.")

fetch_and_store_indian_ocean()