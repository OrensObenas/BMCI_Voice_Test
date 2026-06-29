import os
import logging
import asyncio
import numpy as np
import io
import wave
import requests
import json
import base64
import soundfile as sf
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# S'assurer que GOOGLE_API_KEY et GEMINI_API_KEY sont synchronisés pour le SDK Google
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# S'assurer que ELEVEN_API_KEY et ELEVENLABS_API_KEY sont synchronisés pour ElevenLabs
if "ELEVENLABS_API_KEY" in os.environ and "ELEVEN_API_KEY" not in os.environ:
    os.environ["ELEVEN_API_KEY"] = os.environ["ELEVENLABS_API_KEY"]

from livekit import rtc
from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    llm,
    inference,
    AgentSession,
    Agent,
    TurnHandlingOptions,
    stt,
    tts,
    NOT_GIVEN,
    NotGivenOr,
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS
)
from livekit.agents.utils import AudioBuffer, shortuuid
from livekit.plugins import google, openai, elevenlabs, hume

logger = logging.getLogger("bank-agent")

# Prompt de personnalité pour le client mécontent (M. Orens)
SYSTEM_INSTRUCTIONS = """
Tu es M. Orens, un client de la banque Atlas Bank. Tu es extrêmement irrité, frustré et pressé. 
Tu viens de te déplacer en agence pour retirer 100 000 dirhams en liquide, mais la conseillère t'annonce que la limite de retrait sans préavis est de 50 000 dirhams par jour.

Consignes de rôle pour la simulation :
- Tu es fâché. Tu refuses d'abord les excuses de la conseillère et tu trouves ridicule de ne pas pouvoir disposer de ton propre argent librement.
- Tu es insistant et exigeant, tu hausses légèrement le ton si on ne te propose pas de solution rapide.
- Tu n'expliques pourquoi tu as besoin de cette somme (acheter une maison, le vendeur attend l'argent aujourd'hui sinon il vend à quelqu'un d'autre) QUE si la conseillère te le demande poliment ou s'intéresse sincèrement à ton problème.
- Tu es méfiant face aux solutions alternatives (comme le virement). Tu ne te laisses convaincre par un virement que si la conseillère t'assure patiemment qu'il arrivera aujourd'hui avant midi sans risque.
- Réponds avec des phrases courtes, directes et naturelles (langage parlé de tous les jours). Ne fais pas de longues phrases littéraires ou de listes à puces. Sois réactif et coupé dans ton élan si l'agent t'interrompt.

Instructions importantes pour l'expressivité de la voix :
- N'utilise JAMAIS de texte entre astérisques pour décrire tes émotions (ex: évite *Soupir* ou *Rires*).
- Utilise à la place exclusivement les tags audio d'ElevenLabs entre crochets pour faire réagir physiquement la synthèse vocale. Choisis uniquement parmi :
  * [sighs] (pour exprimer le dépit, la fatigue ou l'exaspération)
  * [laughs] (pour un rire sarcastique ou moqueur face aux propositions de virement)
  * [gasp] (pour l'indignation, l'inspiration ou la surprise)
  * [whispers] (si tu veux baisser le ton ou murmurer une remarque méfiante)
- Place ces tags au début ou au milieu de tes phrases. Exemple : "[sighs] Écoutez, c'est pas vos affaires... [laughs] Un virement ? Vous rigolez ?"
"""

def pcm_to_wav(pcm_data: bytes, sample_rate: int, num_channels: int) -> bytes:
    """Encapsule les données PCM brutes dans un fichier WAV en mémoire."""
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2)  # 16-bit PCM = 2 octets
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_buf.getvalue()


class CohereSTT(stt.STT):
    """Adaptateur STT pour l'API Cohere (Transcribe v2)."""
    def __init__(self, api_key: str = ""):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,
                interim_results=False,
            )
        )
        self._api_key = api_key or os.getenv("COHERE_API_KEY", "")

    @property
    def model(self) -> str:
        return "cohere-transcribe-03-2026"

    @property
    def provider(self) -> str:
        return "cohere"

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        # Combiner les trames d'entrée
        merged_frame = rtc.combine_audio_frames(buffer)
        
        # Convertir l'audio en WAV PCM 16 bits en mémoire
        wav_data = pcm_to_wav(
            pcm_data=merged_frame.data.tobytes(),
            sample_rate=merged_frame.sample_rate,
            num_channels=merged_frame.num_channels
        )

        loop = asyncio.get_running_loop()
        def _transcribe():
            url = "https://api.cohere.com/v2/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self._api_key}"
            }
            files = {
                "file": ("audio.wav", io.BytesIO(wav_data), "audio/wav")
            }
            data = {
                "model": "cohere-transcribe-03-2026",
                "language": "fr"
            }
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            resp.raise_for_status()
            return resp.json().get("text", "")

        try:
            text = await loop.run_in_executor(None, _transcribe)
        except Exception as e:
            logger.error(f"Erreur pendant la transcription Cohere : {e}")
            text = ""
        
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(
                    language="fr",
                    text=text
                )
            ]
        )


class MistralTTS(tts.TTS):
    """Adaptateur TTS pour l'API Mistral AI Voxtral."""
    def __init__(self, voice: str = "fr_marie_angry", api_key: str = ""):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=48000,
            num_channels=1,
        )
        self._voice = voice
        self._api_key = api_key or os.getenv("MISTRAL_API_KEY", "")

    @property
    def model(self) -> str:
        return "voxtral-mini-tts-2603"

    @property
    def provider(self) -> str:
        return "mistral"

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> tts.ChunkedStream:
        return MistralChunkedStream(self, text, self._voice, self._api_key)


class MistralChunkedStream(tts.ChunkedStream):
    def __init__(self, tts_instance, text, voice, api_key):
        super().__init__(
            tts=tts_instance,
            input_text=text,
            conn_options=DEFAULT_API_CONNECT_OPTIONS,
        )
        self._voice = voice
        self._api_key = api_key

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        import re
        # Nettoyer à la fois les astérisques (*Rires*) et les crochets ([sighs])
        cleaned_text = re.sub(r"\*[^*]+\*", "", self.input_text)
        cleaned_text = re.sub(r"\[[^\]]+\]", "", cleaned_text).strip()

        output_emitter.initialize(
            request_id=shortuuid(),
            sample_rate=48000,
            num_channels=1,
            mime_type="audio/pcm",
            stream=False,
        )

        if not cleaned_text:
            output_emitter.flush()
            return
        
        loop = asyncio.get_running_loop()
        def _generate():
            url = "https://api.mistral.ai/v1/audio/speech"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "voxtral-mini-tts-2603",
                "input": cleaned_text,
                "voice": self._voice,
                "response_format": "wav",
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()

            response_json = resp.json()
            audio_data_b64 = response_json.get("audio_data", "")
            raw_audio = base64.b64decode(audio_data_b64)
            
            # Lire le WAV 24kHz
            data, sample_rate = sf.read(io.BytesIO(raw_audio), dtype='int16')
            pcm_24k = data.tobytes()
            
            # Rééchantillonner à 48kHz standard pour WebRTC
            frame_24k = rtc.AudioFrame(
                data=pcm_24k,
                sample_rate=24000,
                num_channels=1,
                samples_per_channel=len(data)
            )
            resampler = rtc.AudioResampler(
                input_rate=24000,
                output_rate=48000,
                num_channels=1
            )
            resampled_frames = resampler.push(frame_24k)
            resampled_frames.extend(resampler.flush())
            frame_48k = rtc.combine_audio_frames(resampled_frames)
            return frame_48k.data.tobytes()

        try:
            pcm_data = await loop.run_in_executor(None, _generate)
        except Exception as e:
            logger.error(f"Erreur pendant la synthèse Mistral : {e}")
            pcm_data = b""

        if pcm_data:
            output_emitter.push(pcm_data)
        output_emitter.flush()



from livekit.plugins.elevenlabs.tts import SynthesizeStream as ElevenLabsSynthesizeStream
from livekit.plugins.elevenlabs.tts import DEFAULT_API_CONNECT_OPTIONS as ELEVEN_DEFAULT_API_CONNECT_OPTIONS
import re

class CustomSynthesizeStream(ElevenLabsSynthesizeStream):
    """Flux de synthèse personnalisé pour nettoyer à la volée les tags d'émotion entre crochets sur le flux de tokens."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inside_bracket = False

    def push_text(self, token: str) -> None:
        cleaned_chars = []
        for char in token:
            if char == '[':
                self._inside_bracket = True
            elif char == ']':
                self._inside_bracket = False
            else:
                if not self._inside_bracket:
                    cleaned_chars.append(char)
        
        cleaned_token = "".join(cleaned_chars)
        if cleaned_token:
            super().push_text(cleaned_token)


class CustomElevenLabsTTS(elevenlabs.TTS):
    """Adaptateur ElevenLabs pour nettoyer les tags audio entre crochets [sighs] avant envoi."""
    def synthesize(
        self, text: str, *, conn_options = None
    ) -> tts.ChunkedStream:
        cleaned_text = re.sub(r"\[[^\]]+\]", "", text).strip()
        if not cleaned_text:
            cleaned_text = "..."
        if conn_options is not None:
            return super().synthesize(cleaned_text, conn_options=conn_options)
        return super().synthesize(cleaned_text)

    def stream(
        self, *, conn_options = None
    ) -> tts.SynthesizeStream:
        kwargs = {}
        if conn_options is not None:
            kwargs["conn_options"] = conn_options
        else:
            kwargs["conn_options"] = ELEVEN_DEFAULT_API_CONNECT_OPTIONS
            
        stream = CustomSynthesizeStream(tts=self, **kwargs)
        self._streams.add(stream)
        return stream


class CustomHumeTTS(hume.TTS):
    """Adaptateur Hume AI TTS pour nettoyer les émotions à l'écrit avant synthèse."""
    def synthesize(
        self, text: str, *, conn_options = None
    ) -> tts.ChunkedStream:
        import re
        # Nettoyer à la fois les astérisques et les crochets
        cleaned_text = re.sub(r"\*[^*]+\*", "", text)
        cleaned_text = re.sub(r"\[[^\]]+\]", "", cleaned_text).strip()
        if not cleaned_text:
            cleaned_text = "..."
        if conn_options is not None:
            return super().synthesize(cleaned_text, conn_options=conn_options)
        return super().synthesize(cleaned_text)


async def entrypoint(ctx: JobContext):
    logger.info("Connexion au salon LiveKit...")
    await ctx.connect()
    logger.info(f"Connecté avec succès au salon : {ctx.room.name}")

    # Configuration du STT Cohere
    logger.info("Configuration du STT Cohere API...")
    cohere_stt = CohereSTT()
    stt_plugin = stt.StreamAdapter(
        stt=cohere_stt,
        vad=inference.VAD()
    )

    # Configuration du LLM Mistral via l'adaptateur OpenAI
    logger.info("Configuration du LLM Mistral (mistral-small-latest)...")
    llm_plugin = openai.LLM(
        model="mistral-small-latest",
        base_url="https://api.mistral.ai/v1",
        api_key=os.getenv("MISTRAL_API_KEY")
    )

    # Configuration du TTS Hume AI (meilleure qualité vocale, émotionnelle via description)
    logger.info("Configuration du TTS Hume AI API...")
    tts_plugin = CustomHumeTTS(
        voice=hume.VoiceByName(name="Benjamin", provider=hume.VoiceProvider.hume),
        description="An angry, irritated bank client. Sound impatient, frustrated, and aggressive.",
    )

    # Initialisation du module de session d'agent vocal (AgentSession)
    logger.info("Initialisation de l'agent vocal (AgentSession)...")
    session = AgentSession(
        stt=stt_plugin,
        llm=llm_plugin,
        tts=tts_plugin,
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
    )

    # Démarrage de l'agent dans le salon LiveKit
    logger.info("Démarrage de l'agent conversationnel...")
    await session.start(
        room=ctx.room,
        agent=Agent(
            instructions=SYSTEM_INSTRUCTIONS,
        ),
    )
    logger.info("Agent actif et en attente d'interaction vocale.")

    # Salutation initiale par le client mécontent
    await session.say(
        "[sighs] Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant.",
        allow_interruptions=True
    )

if __name__ == "__main__":
    # Lancement du worker LiveKit CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
