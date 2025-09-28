# ...existing code...

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import FishForecast
from db.db_connection import get_db
import numpy as np


# Path to trained model
MODEL_PATH = r"d:\ArgoChat\backend\models\fish_forecast_model.joblib"

def train_fish_model(data_path: str):
	"""Train and save a Random Forest model for fish prediction."""
	df = pd.read_csv(data_path)
	features = ["temperature", "salinity", "depth", "latitude", "longitude", "time"]
	target = "fish_presence"
	X = df[features]
	y = df[target]
	model = RandomForestRegressor(n_estimators=100, random_state=42)
	model.fit(X, y)
	joblib.dump(model, MODEL_PATH)
	print("Fish prediction model trained and saved.")



def predict_fish_presence(input_features: dict):
	"""Predict fish presence using trained model."""
	model = joblib.load(MODEL_PATH)
	X = np.array([
		input_features["temperature"],
		input_features["salinity"],
		input_features["oxygen"]
	]).reshape(1, -1)
	prediction = model.predict(X)[0]
	return prediction

# Example SMS notification (Twilio)
def send_sms_notification(phone_number: str, message: str):
	try:
		from twilio.rest import Client
		# Set your Twilio credentials here
		account_sid = 'YOUR_TWILIO_ACCOUNT_SID'
		auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
		client = Client(account_sid, auth_token)
		client.messages.create(
			body=message,
			from_='+1234567890',  # Your Twilio phone number
			to=phone_number
		)
		print(f"SMS sent to {phone_number}")
	except Exception as e:
		print(f"Failed to send SMS: {e}")

async def save_fish_forecast(session: AsyncSession, forecast: dict):
	"""Save prediction result to DB."""
	fish_obj = FishForecast(**forecast)
	session.add(fish_obj)
	await session.commit()
	await session.refresh(fish_obj)
	return fish_obj