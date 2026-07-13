import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
voice_id = "pNInz6obpgDQGcFmaJgB" # Adam

async def main():
    # Multi-stream input URL as used by the plugin
    url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_multilingual_v2&output_format=mp3_22050_32"
    headers = {
        "xi-api-key": api_key
    }
    async with aiohttp.ClientSession() as session:
        try:
            print("Connecting to WS...")
            async with session.ws_connect(url, headers=headers) as ws:
                print("Connection established!")
                
                # Send the bos/initial message as per elevenlabs docs
                init_msg = {
                    "text": " ",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8
                    },
                    "generation_config": {
                        "chunk_length_schedule": [120, 160, 250, 290]
                    },
                    "xi_api_key": api_key
                }
                await ws.send_str(json.dumps(init_msg))
                
                # Send text chunk
                text_msg = {
                    "text": "Bonjour. Je suis venu pour retirer cent mille dirhams.",
                    "try_trigger_generation": True
                }
                await ws.send_str(json.dumps(text_msg))
                
                # Send eos
                eos_msg = {
                    "text": ""
                }
                await ws.send_str(json.dumps(eos_msg))
                
                # Read responses
                print("Reading responses...")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if "audio" in data and data["audio"]:
                            print(f"Received audio chunk! Length: {len(data['audio'])}")
                        elif "message" in data:
                            print(f"Received message/error: {data['message']}")
                        else:
                            print(f"Received other data: {data}")
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("Connection closed by server.")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"WS error: {ws.exception()}")
                        break
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
