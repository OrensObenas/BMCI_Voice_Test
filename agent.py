import os
import logging
import asyncio
import numpy as np
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# S'assurer que GOOGLE_API_KEY et GEMINI_API_KEY sont synchronisés pour le SDK Google
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# eSpeak NG requis par Kokoro pour le phonemizer
ESPEAK_NG_DIR = r"C:\Program Files\eSpeak NG"
if os.path.isdir(ESPEAK_NG_DIR) and ESPEAK_NG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ESPEAK_NG_DIR + ";" + os.environ.get("PATH", "")

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
from livekit.plugins import google
from faster_whisper import WhisperModel
from kokoro import KPipeline

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
"""

class LocalWhisperSTT(stt.STT):
    """Adaptateur STT pour Whisper en local via faster-whisper."""
    def __init__(self, model_size: str = "large-v3-turbo", device: str = "cpu", compute_type: str = "int8"):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,
                interim_results=False,
            )
        )
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    @property
    def model(self) -> str:
        return f"whisper-local-{self._model_size}"

    @property
    def provider(self) -> str:
        return "faster-whisper"

    def _get_model(self):
        if self._model is None:
            logger.info(f"Chargement de Whisper local ({self._model_size}) sur {self._device} ({self._compute_type})...")
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type
            )
            logger.info("Modèle Whisper local chargé.")
        return self._model

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        # Combiner les trames d'entrée
        merged_frame = rtc.combine_audio_frames(buffer)
        
        # Rééchantillonner en 16000Hz si nécessaire (Whisper attend du 16kHz)
        if merged_frame.sample_rate != 16000:
            resampler = rtc.AudioResampler(
                input_rate=merged_frame.sample_rate,
                output_rate=16000,
                num_channels=1,
            )
            resampled_frames = resampler.push(merged_frame)
            resampled_frames.extend(resampler.flush())
            merged_frame = rtc.combine_audio_frames(resampled_frames)

        # Convertir PCM 16 bits en float32 normalisé [-1.0, 1.0]
        audio_data = np.frombuffer(merged_frame.data, dtype=np.int16)
        audio_float32 = audio_data.astype(np.float32) / 32768.0

        loop = asyncio.get_running_loop()
        def _transcribe():
            model = self._get_model()
            segments, _info = model.transcribe(
                audio_float32,
                language="fr",
                beam_size=5,
                vad_filter=True
            )
            return " ".join(seg.text.strip() for seg in segments)

        text = await loop.run_in_executor(None, _transcribe)
        
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(
                    language="fr",
                    text=text
                )
            ]
        )


class LocalKokoroTTS(tts.TTS):
    """Adaptateur TTS pour Kokoro en local."""
    def __init__(self, voice: str = "ff_siwis", speed: float = 1.0):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self._voice = voice
        self._speed = speed
        self._pipeline = None

    @property
    def model(self) -> str:
        return "kokoro-v0.19"

    @property
    def provider(self) -> str:
        return "kokoro"

    def _get_pipeline(self):
        if self._pipeline is None:
            logger.info("Initialisation du pipeline Kokoro (lang=f)...")
            self._pipeline = KPipeline(lang_code="f")
            logger.info("Pipeline Kokoro initialisé.")
        return self._pipeline

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> tts.ChunkedStream:
        return KokoroChunkedStream(self, text, self._get_pipeline(), self._voice, self._speed)


class KokoroChunkedStream(tts.ChunkedStream):
    def __init__(self, tts_instance, text, pipeline, voice, speed):
        super().__init__(
            tts=tts_instance,
            input_text=text,
            conn_options=DEFAULT_API_CONNECT_OPTIONS,
        )
        self._pipeline = pipeline
        self._voice = voice
        self._speed = speed

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=shortuuid(),
            sample_rate=24000,
            num_channels=1,
            mime_type="audio/pcm",
            stream=False,
        )
        
        loop = asyncio.get_running_loop()
        def _generate():
            chunks = []
            for _, _, audio_chunk in self._pipeline(self.input_text, voice=self._voice, speed=self._speed):
                chunks.append(audio_chunk)
            if not chunks:
                return b""
            full_audio = np.concatenate(chunks)
            return (full_audio * 32767.0).astype(np.int16).tobytes()

        pcm_data = await loop.run_in_executor(None, _generate)
        if pcm_data:
            output_emitter.push(pcm_data)
        output_emitter.flush()


async def entrypoint(ctx: JobContext):
    logger.info("Connexion au salon LiveKit...")
    await ctx.connect()
    logger.info(f"Connecté avec succès au salon : {ctx.room.name}")

    # Configuration du STT local Whisper
    logger.info("Configuration du STT Whisper local...")
    local_stt = LocalWhisperSTT()
    stt_plugin = stt.StreamAdapter(
        stt=local_stt,
        vad=inference.VAD()
    )

    # Configuration du LLM Google Gemini
    logger.info("Configuration du LLM Google Gemini...")
    llm_plugin = google.LLM(model="gemini-2.5-flash")

    # Configuration du TTS local Kokoro
    logger.info("Configuration du TTS Kokoro local...")
    tts_plugin = LocalKokoroTTS()

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
        "Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant.",
        allow_interruptions=True
    )

if __name__ == "__main__":
    # Lancement du worker LiveKit CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
