"""
Adaptateur TTS pour l'API Mistral AI Voxtral (via REST / requests).

Variable d'environnement requise : ``MISTRAL_API_KEY``
"""

import io
import logging
import time
from pathlib import Path

import requests
import soundfile as sf

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)


class MistralModel(TTSModel):
    """Adaptateur pour l'API Mistral Voxtral TTS (cloud, REST direct)."""

    name = "mistral"
    description = "Mistral AI API — voxtral-mini-tts-2603 (cloud REST)"
    tier = "api"

    def __init__(self) -> None:
        self._api_key: str = ""
        self.voice = "fr_marie_neutral"  # Voix française native par défaut
        self.model = "voxtral-mini-tts-2603"

    def is_available(self) -> bool:
        """Vérifie que la clé API est configurée."""
        try:
            from config import MISTRAL_API_KEY
            if not MISTRAL_API_KEY:
                return False
            return True
        except ImportError:
            return False

    def setup(self) -> None:
        """Charge la clé API."""
        from config import MISTRAL_API_KEY
        self._api_key = MISTRAL_API_KEY

    def teardown(self) -> None:
        """Pas de nettoyage nécessaire."""
        pass

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* via l'API Mistral.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.
        """
        if not self._api_key:
            raise RuntimeError("Appeler setup() avant synthesize()")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Mistral: synthèse de %d caractères", len(text))

        url = "https://api.mistral.ai/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": "wav",
        }

        ttfa: float | None = None
        audio_chunks: list[bytes] = []

        t_start = time.perf_counter()
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=30,
            )
            resp.raise_for_status()

            for chunk in resp.iter_content(chunk_size=4096):
                if chunk and len(chunk) > 0:
                    if ttfa is None:
                        ttfa = time.perf_counter() - t_start
                        logger.debug("Mistral: TTFA = %.4f s", ttfa)
                    audio_chunks.append(chunk)

        except requests.RequestException as exc:
            logger.error("Mistral: erreur pendant la requête de synthèse: %s", exc)
            raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        if not audio_chunks:
            raise RuntimeError("L'API Mistral n'a retourné aucun audio")

        raw_response = b"".join(audio_chunks)
        try:
            import json
            import base64
            response_json = json.loads(raw_response)
            audio_data_b64 = response_json.get("audio_data", "")
            raw_audio = base64.b64decode(audio_data_b64)
        except Exception as e:
            logger.error("Mistral: Échec du parsing JSON ou décodage base64 : %s", e)
            raise RuntimeError(f"Réponse API Mistral invalide : {e}")

        # Enregistrer le fichier WAV directement
        with open(output_path, "wb") as f:
            f.write(raw_audio)

        # Lire le fichier pour extraire la durée et le sample rate
        try:
            data, sample_rate = sf.read(output_path)
            audio_duration = len(data) / sample_rate
        except Exception as e:
            logger.error("Mistral: Impossible de lire le fichier WAV sauvegardé: %s", e)
            raise RuntimeError(f"Fichier WAV corrompu retourné par Mistral: {e}")

        rtf = generation_time / audio_duration if audio_duration > 0 else float("inf")

        result = SynthesisResult(
            audio_path=output_path,
            generation_time=generation_time,
            ttfa=ttfa if ttfa is not None else generation_time,
            sample_rate=sample_rate,
            audio_duration=audio_duration,
            rtf=rtf,
        )
        logger.info(
            "Mistral: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
