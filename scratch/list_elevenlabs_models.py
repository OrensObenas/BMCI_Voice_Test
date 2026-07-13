import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("ELEVENLABS_API_KEY is not set.")
    exit(1)

url = "https://api.elevenlabs.io/v1/models"
headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json"
}

try:
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        models = resp.json()
        print("Available Models:")
        for model in models:
            print(f"- ID: {model.get('model_id')} | Name: {model.get('name')}")
    else:
        print("Error:", resp.text)
except Exception as e:
    print("Exception:", e)
