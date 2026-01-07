import numpy as np
import torch
from argopy import DataFetcher as ArgoDataFetcher
from sentence_transformers import SentenceTransformer
from scipy.interpolate import interp1d
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ProcessPoolExecutor, as_completed

# -----------------------------
# CONFIG
# -----------------------------
CHROMA_COLLECTION = "argo_data"
EMBED_MODEL = "all-MiniLM-L6-v2"

device = 'cuda' if torch.cuda.is_available() else 'cpu'
text_embedder = SentenceTransformer(EMBED_MODEL, device=device)

# Chroma client
import chromadb
client = chromadb.Client()
collection = client.get_or_create_collection(CHROMA_COLLECTION)

# Depth grid for interpolation
target_depths = np.arange(0, 1000+50, 50)  # 0,50,...1000

# -----------------------------
# AUTOENCODER
# -----------------------------
import torch.nn as nn

class ProfileAutoencoder(nn.Module):
    def __init__(self, input_dim, latent_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_dim*3, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim*3),
            nn.Unflatten(1, (3, input_dim))
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z), z

ae_model = ProfileAutoencoder(len(target_depths))
ae_model.eval()

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def interpolate_profile(values, depths, target_depths):
    f = interp1d(depths, values, bounds_error=False, fill_value="extrapolate")
    return f(target_depths)

def categorize_temperature(temp_vector):
    mean_temp = np.mean(temp_vector)
    if mean_temp < 10: return "cold"
    elif mean_temp < 20: return "average"
    else: return "hot"

def categorize_salinity(sal_vector):
    mean_sal = np.mean(sal_vector)
    if mean_sal < 34: return "low"
    elif mean_sal < 36: return "medium"
    elif mean_sal < 38: return "high"
    else: return "very high"

def categorize_depth(max_depth):
    if max_depth <= 200: return "surface"
    elif max_depth <= 1000: return "mesopelagic"
    elif max_depth <= 2000: return "deep"
    else: return "very deep"

def assign_region(lat, lon):
    if lat > 60: return "Arctic"
    elif -40 <= lat <= 40 and 20 <= lon <= 120: return "Indian Ocean"
    elif 0 <= lat <= 60 and 120 < lon <= 180: return "Pacific East"
    elif 0 <= lat <= 60 and -180 <= lon <= -120: return "Pacific West"
    else: return "Other"

# -----------------------------
# PROCESS CHUNK FUNCTION
# -----------------------------
def process_chunk(lat_min, lat_max, lon_min, lon_max, month_start, month_end):
    try:
        ds = ArgoDataFetcher(rc="erddap", mode="standard").region(
            [lat_min, lat_max, lon_min, lon_max, 0, 1000, month_start, month_end]
        ).to_xarray()
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return []

    if ds.sizes["N_POINTS"] == 0:
        return []

    profiles = []
    for k in range(ds.sizes["N_POINTS"]):
        try:
            lat = float(ds["LATITUDE"].values[k])
            lon = float(ds["LONGITUDE"].values[k])
            time_str = str(np.datetime_as_string(ds["TIME"].values[k], unit="D"))
            platform_val = ds["PLATFORM_NUMBER"].values[k]
            platform = str(platform_val.item() if hasattr(platform_val, "item") else platform_val)

            pres = np.atleast_1d(ds["PRES"].values[k])
            temp = np.atleast_1d(ds["TEMP"].values[k])
            psal = np.atleast_1d(ds["PSAL"].values[k])

            mask = ~np.isnan(temp) & ~np.isnan(psal) & ~np.isnan(pres)
            pres, temp, psal = pres[mask], temp[mask], psal[mask]
            if len(pres) == 0: continue

            # Interpolate to fixed depth grid
            temp_vector = interpolate_profile(temp, pres, target_depths)
            sal_vector = interpolate_profile(psal, pres, target_depths)
            depth_vector = target_depths / target_depths.max()

            # Pattern embedding
            profile_tensor = torch.tensor(np.stack([temp_vector, sal_vector, depth_vector]), dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                _, latent_vector = ae_model(profile_tensor)
            latent_vector = latent_vector.squeeze(0).numpy().tolist()

            # Categorize
            temp_class = categorize_temperature(temp_vector)
            sal_class = categorize_salinity(sal_vector)
            depth_class = categorize_depth(max(pres))
            region = assign_region(lat, lon)

            description = f"Profile {platform} at {time_str} ({lat},{lon}), Temp class {temp_class}, Salinity class {sal_class}, Depth class {depth_class}, Region {region}"

            profiles.append({
                "platform": platform,
                "time": time_str,
                "lat": lat,
                "lon": lon,
                "temperature_class": temp_class,
                "salinity_class": sal_class,
                "depth_class": depth_class,
                "region": region,
                "latent_vector": latent_vector,
                "description": description
            })
        except:
            continue

    if profiles:
        # Compute text embeddings in batch
        texts = [p["description"] for p in profiles]
        text_vectors = text_embedder.encode(texts, convert_to_numpy=True)
        for p, t_vec in zip(profiles, text_vectors):
            p["text_embedding"] = t_vec.tolist()

    return profiles

# -----------------------------
# MAIN FUNCTION
# -----------------------------
def fetch_and_store_parallel():
    lat_bounds = [-40, 40]
    lon_bounds = [20, 120]
    months = [f"2022-{str(m).zfill(2)}" for m in range(1, 13)]

    tasks = []
    for i in range(len(months)-1):
        lat_chunks = [(lat_bounds[0] + j*20, min(lat_bounds[0] + (j+1)*20, lat_bounds[1])) for j in range(4)]
        lon_chunks = [(lon_bounds[0] + j*25, min(lon_bounds[0] + (j+1)*25, lon_bounds[1])) for j in range(4)]
        for lat_min, lat_max in lat_chunks:
            for lon_min, lon_max in lon_chunks:
                tasks.append((lat_min, lat_max, lon_min, lon_max, months[i], months[i+1]))

    all_profiles = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_chunk, *t) for t in tasks]
        for future in as_completed(futures):
            try:
                profiles = future.result()
                if profiles:
                    all_profiles.extend(profiles)
            except Exception as e:
                print("Chunk error:", e)

    # Insert all profiles into Chroma safely
    for p in all_profiles:
        collection.add(
            documents=[p["description"]],
            embeddings=[p["text_embedding"]],
            metadatas=[{k: v for k, v in p.items() if k != "text_embedding"}],
            ids=[f"{p['platform']}_{p['time']}"]
        )

    print("Finished ingestion for all regions/months.")

# -----------------------------
# QUERY FUNCTION
# -----------------------------
def query_profiles(user_query, top_k=5):
    query_vec = text_embedder.encode([user_query], convert_to_numpy=True)
    docs = collection.get(include=["documents","embeddings","metadatas","ids"])
    embeddings = np.array(docs["embeddings"])
    metadatas = docs["metadatas"]
    doc_texts = docs["documents"]

    sims = cosine_similarity(query_vec, embeddings).squeeze()
    top_indices = sims.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        meta = metadatas[idx]
        results.append({
            "platform": meta["platform"],
            "time": meta["time"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "region": meta["region"],
            "temperature_class": meta["temperature_class"],
            "salinity_class": meta["salinity_class"],
            "depth_class": meta["depth_class"],
            "latent_vector": meta["latent_vector"],
            "description": doc_texts[idx]
        })
    return results

# -----------------------------
# USAGE
# -----------------------------
fetch_and_store_parallel()
# results = query_profiles("warm surface, gradual decrease")
# for r in results:
#     print(r["description"])
