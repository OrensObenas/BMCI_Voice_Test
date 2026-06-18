"""
Adaptateur STT pour l'API ElevenLabs Scribe.
"""

import logging
import time
from pathlib import Path
import requests

from stt_models.base import STTModel, TranscriptionResult

logger = logging.getLogger(__name__)


class ElevenLabsSTT(STTModel):
    """Adaptateur STT pour l'API ElevenLabs (Scribe v2)."""

    name = "elevenlabs"
    description = "ElevenLabs Scribe v2 API"
    tier = "api"

    def __init__(self) -> None:
        self._api_key = ""

    def is_available(self) -> bool:
        """Vérifie que la clé ElevenLabs est configurée."""
        try:
            from config import ELEVENLABS_API_KEY
            return bool(ELEVENLABS_API_KEY)
        except ImportError:
            return False

    def setup(self) -> None:
        """Initialise la clé API."""
        from config import ELEVENLABS_API_KEY
        self._api_key = ELEVENLABS_API_KEY

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcrit le fichier audio via l'API ElevenLabs Scribe."""
        if not self._api_key:
            raise RuntimeError("Appeler setup() avant transcribe()")

        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {
            "xi-api-key": self._api_key
        }

        t_start = time.perf_counter()
        try:
            with open(audio_path, "rb") as f:
                files = {
                    "file": (Path(audio_path).name, f, "audio/wav")
                }
                data = {
                    "model_id": "scribe_v2",
                    "language_code": "fr"
                }
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
                resp.raise_for_status()

                res_json = resp.json()
                text = res_json.get("text", "")
                latency = time.perf_counter() - t_start
                return TranscriptionResult(text=text, latency=latency)
        except Exception as e:
            logger.exception("Erreur pendant la transcription ElevenLabs Scribe")
            latency = time.perf_counter() - t_start
            return TranscriptionResult(text="", latency=latency, error=str(e))
