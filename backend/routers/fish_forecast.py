# ...existing code...

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.fish_forecast import predict_fish_presence, save_fish_forecast
from db.db_connection import get_db
from datetime import datetime
import ollama

router = APIRouter()

class FishForecastRequest(BaseModel):
    region: dict  # {lat_min, lat_max, lon_min, lon_max}
    temperature: float
    salinity: float
    oxygen: float
    fish_type: str = "Red Snapper"  # Default fish type
    mode: str = "researcher"  # "researcher" or "farmer"
    language: str = "en"  # Language code for notifications
    phone: str = None  # Farmer phone number for SMS

class PromptRequest(BaseModel):
    prompt: str

@router.post("/prompt")
async def ollama_prompt(request: PromptRequest):
    """Parse user prompt with Ollama, extract region/fish type, and return fish forecast results."""
    ollama_response = ollama.generate(model="mistral:7b", prompt=request.prompt)
    prompt_lower = request.prompt.lower()
    # Region extraction
    if "east coast" in prompt_lower:
        region = {"lat_min": 8, "lat_max": 22, "lon_min": 80, "lon_max": 90}
    elif "west coast" in prompt_lower:
        region = {"lat_min": 8, "lat_max": 22, "lon_min": 68, "lon_max": 80}
    elif "bay of bengal" in prompt_lower:
        region = {"lat_min": 8, "lat_max": 22, "lon_min": 85, "lon_max": 95}
    elif "arabian sea" in prompt_lower:
        region = {"lat_min": 8, "lat_max": 22, "lon_min": 65, "lon_max": 75}
    elif "indian coast" in prompt_lower:
        region = {"lat_min": 6, "lat_max": 23, "lon_min": 68, "lon_max": 90}
    elif "indian ocean" in prompt_lower:
        region = {"lat_min": -10, "lat_max": 25, "lon_min": 60, "lon_max": 100}  # Covers Indian Ocean near India
    elif "gujarat" in prompt_lower:
        region = {"lat_min": 20, "lat_max": 24, "lon_min": 68, "lon_max": 72}
    elif "tamil nadu" in prompt_lower:
        region = {"lat_min": 8, "lat_max": 13, "lon_min": 77, "lon_max": 80}
    else:
        region = {"lat_min": 6, "lat_max": 23, "lon_min": 68, "lon_max": 90}
    # Weather extraction
    temperature = 25
    salinity = 33
    oxygen = 6
    if "hot" in prompt_lower or "summer" in prompt_lower:
        temperature = 30
    if "cold" in prompt_lower or "winter" in prompt_lower:
        temperature = 20
    if "rain" in prompt_lower:
        oxygen = 7
    # Fish type extraction
    if "mackerel" in prompt_lower:
        fish_type = "Mackerel"
    elif "sardine" in prompt_lower:
        fish_type = "Sardine"
    elif "snapper" in prompt_lower:
        fish_type = "Red Snapper"
    elif "tuna" in prompt_lower:
        fish_type = "Tuna"
    elif "pomfret" in prompt_lower:
        fish_type = "Pomfret"
    elif "anchovy" in prompt_lower:
        fish_type = "Anchovy"
    elif "hilsa" in prompt_lower:
        fish_type = "Hilsa"
    else:
        fish_type = "Common Fish"  # Use a generic type if not specified
    results = []
    lat_steps = 5
    lon_steps = 5
    lat_range = [region["lat_min"] + i * (region["lat_max"] - region["lat_min"]) / lat_steps for i in range(lat_steps + 1)]
    lon_range = [region["lon_min"] + i * (region["lon_max"] - region["lon_min"]) / lon_steps for i in range(lon_steps + 1)]
    print(f"DEBUG: region={region}, lat_range={lat_range}, lon_range={lon_range}")
    for lat in lat_range:
        for lon in lon_range:
            input_features = {
                "temperature": temperature,
                "salinity": salinity,
                "oxygen": oxygen
            }
            prediction = predict_fish_presence(input_features)
            results.append({
                "lat": lat,
                "lon": lon,
                "fish_type": fish_type,
                "presence": prediction
            })
    print(f"DEBUG: region_results={results}")
    return {"region_results": results, "llm_response": ollama_response}

@router.post("/fish_forecast")
async def fish_forecast_endpoint(request: FishForecastRequest):
	"""Predict fish presence for a region and return results for map visualization and notifications."""
	try:
		region = request.region
		lat_steps = 5
		lon_steps = 5
		lat_range = [region["lat_min"] + i * (region["lat_max"] - region["lat_min"]) / lat_steps for i in range(lat_steps + 1)]
		lon_range = [region["lon_min"] + i * (region["lon_max"] - region["lon_min"]) / lon_steps for i in range(lon_steps + 1)]
		results = []
		for lat in lat_range:
			for lon in lon_range:
				input_features = {
					"temperature": request.temperature,
					"salinity": request.salinity,
					"oxygen": request.oxygen
				}
				prediction = predict_fish_presence(input_features)
				results.append({
					"lat": lat,
					"lon": lon,
					"fish_type": request.fish_type,
					"presence": prediction
				})
		# Researcher mode: return detailed results for map
		if request.mode == "researcher":
			return {"region_results": results}
		# Farmer mode: send SMS notification if fish presence predicted
		else:
			max_presence = max(results, key=lambda x: x["presence"])
			message = f"{request.fish_type} expected near ({max_presence['lat']:.2f}, {max_presence['lon']:.2f}) with value {max_presence['presence']:.2f}."
			if request.phone:
				from services.fish_forecast import send_sms_notification
				send_sms_notification(request.phone, message)
			return {"message": message, "region_results": results}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))