import os
import asyncio
import wave
from dotenv import load_dotenv
from livekit.plugins import hume

# Charger l'environnement
load_dotenv()

async def main():
    import livekit.agents
    async with livekit.agents.utils.http_context.open():
        # Initialiser le TTS de Hume AI via le plugin LiveKit
        hume_tts = hume.TTS(
            voice=hume.VoiceByName(name="Benjamin", provider=hume.VoiceProvider.hume),
            description="An angry, irritated bank client. Sound impatient, frustrated, and aggressive.",
        )
        
        text = "Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant."
        print(f"Synthesizing text: '{text}'...")
        
        # Lancer la synthèse
        stream = hume_tts.synthesize(text)
        
        audio_data = b""
        async for chunk in stream:
            # chunk est un SynthesizedAudio, l'audio pcm est dans chunk.frame
            frame = chunk.frame
            audio_data += frame.data.tobytes()
        
    print(f"Successfully synthesized audio! Total bytes: {len(audio_data)}")
    
    if len(audio_data) > 0:
        os.makedirs("scratch", exist_ok=True)
        with wave.open("scratch/hume_test.wav", "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2) # 16-bit PCM
            wav_file.setframerate(48000)
            wav_file.writeframes(audio_data)
        print("Saved to scratch/hume_test.wav")

if __name__ == "__main__":
    asyncio.run(main())
