"""
Adaptateur STT pour l'API Cohere Transcribe.
"""

import logging
import time
from pathlib import Path
import requests

from stt_models.base import STTModel, TranscriptionResult

logger = logging.getLogger(__name__)


class CohereSTT(STTModel):
    """Adaptateur STT pour l'API Cohere (Transcribe v2)."""

    name = "cohere"
    description = "Cohere Transcribe v2 API"
    tier = "api"

    def __init__(self) -> None:
        self._api_key = ""

    def is_available(self) -> bool:
        """Vérifie que la clé Cohere est configurée."""
        try:
            from config import COHERE_API_KEY
            return bool(COHERE_API_KEY)
        except ImportError:
            return False

    def setup(self) -> None:
        """Initialise la clé API."""
        from config import COHERE_API_KEY
        self._api_key = COHERE_API_KEY

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcrit le fichier audio via l'API Cohere."""
        if not self._api_key:
            raise RuntimeError("Appeler setup() avant transcribe()")

        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        url = "https://api.cohere.com/v2/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }

        t_start = time.perf_counter()
        try:
            with open(audio_path, "rb") as f:
                files = {
                    "file": (Path(audio_path).name, f, "audio/wav")
                }
                data = {
                    "model": "cohere-transcribe-03-2026",
                    "language": "fr"
                }
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
                resp.raise_for_status()

                res_json = resp.json()
                text = res_json.get("text", "")
                latency = time.perf_counter() - t_start
                return TranscriptionResult(text=text, latency=latency)
        except Exception as e:
            logger.exception("Erreur pendant la transcription Cohere")
            latency = time.perf_counter() - t_start
            return TranscriptionResult(text="", latency=latency, error=str(e))
