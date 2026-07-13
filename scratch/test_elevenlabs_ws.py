import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
voice_id = "pNInz6obpgDQGcFmaJgB" # Adam

async def test_ws(model_id):
    url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model_id}"
    headers = {
        "xi-api-key": api_key
    }
    async with aiohttp.ClientSession() as session:
        try:
            print(f"Connecting to WS for model {model_id}...")
            async with session.ws_connect(url, headers=headers) as ws:
                print(f"Connection SUCCESS for model {model_id}!")
                # Close connection
                await ws.close()
                return True
        except Exception as e:
            print(f"Connection FAILED for model {model_id}: {e}")
            return False

async def main():
    await test_ws("eleven_v3")
    await test_ws("eleven_multilingual_v2")

if __name__ == "__main__":
    asyncio.run(main())
