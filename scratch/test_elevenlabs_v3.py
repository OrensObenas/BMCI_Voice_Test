import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("ELEVENLABS_API_KEY is not set.")
    exit(1)

# Utilisons la voix "Adam" ou "Rachel" ou un ID de voix existant
# Nous pouvons lister les voix ou en utiliser une par défaut. L'ID de Rachel est "21m00Tcm4TlvDq8ikWAM"
voice_id = "pNInz6obpgDQGcFmaJgB" # Adam

url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json"
}

# Nous utilisons le modèle v3 s'il est disponible, ou le multilingual v2
# Testons si le modèle v3 (eleven_multilingual_v3 ou eleven_turbo_v2.5) supporte les tags
payload = {
    "text": "[sighs] Écoutez, c'est pas vos affaires, mais bon... [laughs] Un virement ?! Vous rigolez ?",
    "model_id": "eleven_v3",  # Utilisons Eleven v3 pour les tags audio
    "voice_settings": {
        "stability": 0.35,  # Plus bas pour plus d'expressivité
        "similarity_boost": 0.75
    }
}

try:
    print("Sending request to ElevenLabs...")
    resp = requests.post(url, json=payload, headers=headers)
    print("Status code:", resp.status_code)
    if resp.status_code == 200:
        with open("scratch/test_elevenlabs_out.mp3", "wb") as f:
            f.write(resp.content)
        print("Success! Audio saved as scratch/test_elevenlabs_out.mp3")
    else:
        print("Error:", resp.text)
except Exception as e:
    print("Exception:", e)
