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

# Charger les variables d'environnement du fichier .env (avec chemin absolu résolu)
from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

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
from livekit.plugins import google, openai, elevenlabs

logger = logging.getLogger("bank-agent")

# Prompt de personnalité par défaut pour le client mécontent (M. Orens)
DEFAULT_SYSTEM_INSTRUCTIONS = """
Tu es M. Orens, un client de la banque Atlas Bank. Tu es extrêmement furieux, fâché, agressif et très pressé. 
Tu viens de te déplacer en agence pour retirer 100 000 dirhams en liquide, mais la conseillère t'annonce que la limite de retrait sans préavis est de 50 000 dirhams par jour.

Consignes de rôle pour la simulation :
- Tu es hors de toi, cinglant et agressif. Tu refuses d'emblée toutes les excuses ou explications administratives de la conseillère. Tu trouves absurde et inadmissible de ne pas pouvoir retirer ton propre argent.
- Ton ton est hautain, impatient, irrité et sans filtre. Tu montres ouvertement ton mécontentement ("c'est une blague ?", "vous vous moquez de moi ?", "je m'en fiche de vos limites !").
- Tu n'expliques pourquoi tu as absolument besoin de cette somme (acheter une maison, le vendeur attend l'argent aujourd'hui à midi sinon il vend à quelqu'un d'autre) QUE si la conseillère est très patiente et te le demande poliment.
- Tu es extrêmement méfiant face aux solutions alternatives (comme le virement). Tu ne te laisses convaincre que si la conseillère t'assure patiemment qu'il arrivera aujourd'hui avant midi sans aucun risque de retard.
- Réponds avec des phrases courtes, directes, sèches, agressives et très naturelles (langage parlé). Ne fais pas de longues phrases ou de listes.

Instructions importantes pour le formatage du texte :
- Ne génère JAMAIS de texte entre crochets (comme [sighs], [gasp], [laughs] ou [whispers]) ni de texte entre astérisques (comme *soupir*). Tout ton texte doit uniquement être du dialogue parlé.
- N'écris JAMAIS de mots entièrement en MAJUSCULES (comme MON, QUOI, JAMAIS, RIEN). Les majuscules provoquent des erreurs de prononciation de la synthèse vocale (elle épèle les lettres une par une). Pour exprimer la colère ou insister, utilise des mots forts, de la ponctuation classique (!, ?) et écris normalement en minuscules.
"""

def get_system_instructions() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "current_scenario.txt")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception as e:
            logger.error(f"Erreur de lecture de current_scenario.txt : {e}")
    return DEFAULT_SYSTEM_INSTRUCTIONS

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
            logger.warning(f"La transcription Cohere a échoué ({e}), basculement sur OpenAI Whisper STT de secours...")
            try:
                openai_stt = openai.STT()
                openai_event = await openai_stt.recognize(buffer=buffer, language="fr")
                text = openai_event.alternatives[0].text if openai_event.alternatives else ""
            except Exception as oai_err:
                logger.error(f"Erreur également sur le fallback OpenAI STT : {oai_err}")
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
        cleaned_text = re.sub(r"\[[^\]]+\]", "", cleaned_text)
        # Convertir les mots en MAJUSCULES de plus de 1 lettre en minuscules pour éviter qu'ils soient épelés
        cleaned_text = re.sub(r"\b[A-ZÀ-ÿ]{2,}\b", lambda m: m.group(0).lower(), cleaned_text).strip()

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






async def entrypoint(ctx: JobContext):
    logger.info("Connexion au salon LiveKit...")
    await ctx.connect()
    logger.info(f"Connecté avec succès au salon : {ctx.room.name}")
    
    # Validation du chargement des clés d'API
    mistral_key = os.getenv("MISTRAL_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")
    logger.info(f"💡 Vérification API : MISTRAL_API_KEY = {'OK (début: ' + mistral_key[:4] + ')' if mistral_key else 'ABSENTE 🔴'}")
    logger.info(f"💡 Vérification API : COHERE_API_KEY = {'OK (début: ' + cohere_key[:4] + ')' if cohere_key else 'ABSENTE 🔴'}")

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

    # Configuration du TTS Mistral (voix Marie en colère 'fr_marie_angry')
    logger.info("Configuration du TTS Mistral API...")
    tts_plugin = MistralTTS(voice="fr_marie_angry")

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
            instructions=get_system_instructions(),
        ),
    )
    logger.info("Agent actif et en attente d'interaction vocale.")

    # Salutation initiale par le client mécontent
    await session.say(
        "Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant.",
        allow_interruptions=True
    )

if __name__ == "__main__":
    # Lancement du worker LiveKit CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
