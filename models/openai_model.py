"""
Adaptateur TTS pour l'API OpenAI (via REST / requests).

N'utilise pas le SDK officiel pour éviter les dépendances lourdes.
Supporte le streaming pour mesurer précisément le TTFA.

Variable d'environnement requise : ``OPENAI_API_KEY``
"""

import io
import logging
import time
from pathlib import Path

import requests
import soundfile as sf
import librosa

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)


class OpenAIModel(TTSModel):
    """Adaptateur pour l'API OpenAI TTS (cloud, REST direct)."""

    name = "openai"
    description = "OpenAI API — tts-1 (cloud REST)"
    tier = "api"

    def __init__(self) -> None:
        self._api_key: str = ""
        self.voice = "nova"  # Voix féminine de référence très fluide en français
        self.model = "tts-1"  # Modèle standard (tts-1-hd pour la haute définition)

    def is_available(self) -> bool:
        """Vérifie que la clé API est configurée."""
        try:
            from config import OPENAI_API_KEY
            if not OPENAI_API_KEY:
                return False
            return True
        except ImportError:
            return False

    def setup(self) -> None:
        """Charge la clé API."""
        from config import OPENAI_API_KEY
        self._api_key = OPENAI_API_KEY

    def teardown(self) -> None:
        """Pas de nettoyage nécessaire."""
        pass

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* via l'API OpenAI.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.
        """
        if not self._api_key:
            raise RuntimeError("Appeler setup() avant synthesize()")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("OpenAI: synthèse de %d caractères", len(text))

        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": "mp3",
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
                        logger.debug("OpenAI: TTFA = %.4f s", ttfa)
                    audio_chunks.append(chunk)

        except requests.RequestException as exc:
            logger.error("OpenAI: erreur pendant la requête de synthèse: %s", exc)
            raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        if not audio_chunks:
            raise RuntimeError("L'API OpenAI n'a retourné aucun audio")

        raw_audio = b"".join(audio_chunks)

        # Enregistrer le fichier MP3 temporaire
        mp3_path = output_path.replace(".wav", ".mp3") if output_path.endswith(".wav") else output_path + ".mp3"
        with open(mp3_path, "wb") as f:
            f.write(raw_audio)

        # Convertir MP3 en WAV
        try:
            data, sample_rate = librosa.load(mp3_path, sr=24000, mono=True)
            sf.write(output_path, data, sample_rate)
            audio_duration = len(data) / sample_rate
        except Exception as e:
            logger.warning("OpenAI: Impossible de convertir MP3→WAV via librosa: %s. Essai soundfile direct.", e)
            try:
                data, sample_rate = sf.read(mp3_path)
                sf.write(output_path, data, sample_rate)
                audio_duration = len(data) / sample_rate
            except Exception as e2:
                logger.error("OpenAI: Échec complet de la conversion MP3→WAV: %s", e2)
                raise RuntimeError(f"Échec de la conversion MP3→WAV: {e2}")

        # Supprimer le MP3 temporaire
        try:
            Path(mp3_path).unlink()
        except OSError:
            pass

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
            "OpenAI: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
