import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
url = "https://api.mistral.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "mistral-small-latest",
    "messages": [{"role": "user", "content": "Bonjour"}]
}

try:
    resp = requests.post(url, json=payload, headers=headers)
    print("Status:", resp.status_code)
    print("Response:", resp.json())
except Exception as e:
    print("Error:", e)
