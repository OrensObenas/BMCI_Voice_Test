"""
Adaptateur TTS pour l'API Hume Octave (via REST / requests).

Utilise l'API REST directement sans SDK.
Supporte le streaming pour mesurer précisément le TTFA.

Variable d'environnement requise : ``HUME_API_KEY``
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


class HumeModel(TTSModel):
    """Adaptateur pour l'API Hume Octave TTS (cloud, REST direct)."""

    name = "hume"
    description = "Hume Octave API (cloud REST)"
    tier = "api"

    def __init__(self) -> None:
        self._api_key: str = ""
        self.voice_id: str = ""

    def is_available(self) -> bool:
        """Vérifie que la clé API est configurée."""
        try:
            from config import HUME_API_KEY
            if not HUME_API_KEY:
                return False
            return True
        except ImportError:
            return False

    def setup(self) -> None:
        """Charge la clé API."""
        from config import HUME_API_KEY
        self._api_key = HUME_API_KEY

    def teardown(self) -> None:
        """Pas de nettoyage nécessaire."""
        pass

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* via l'API Hume.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.
        """
        if not self._api_key:
            raise RuntimeError("Appeler setup() avant synthesize()")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Hume: synthèse de %d caractères", len(text))

        url = "https://api.hume.ai/v0/tts/file"
        headers = {
            "X-Hume-Api-Key": self._api_key,
            "Content-Type": "application/json",
        }
        
        utterance = {"text": text}
        if self.voice_id:
            utterance["voice"] = {"id": self.voice_id}
            
        payload = {
            "utterances": [utterance],
            "format": {
                "type": "mp3"
            }
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
                        logger.debug("Hume: TTFA = %.4f s", ttfa)
                    audio_chunks.append(chunk)

        except requests.RequestException as exc:
            logger.error("Hume: erreur pendant la requête de synthèse: %s", exc)
            raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        if not audio_chunks:
            raise RuntimeError("L'API Hume n'a retourné aucun audio")

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
            logger.warning("Hume: Impossible de convertir MP3→WAV via librosa: %s. Essai soundfile direct.", e)
            try:
                data, sample_rate = sf.read(mp3_path)
                sf.write(output_path, data, sample_rate)
                audio_duration = len(data) / sample_rate
            except Exception as e2:
                logger.error("Hume: Échec complet de la conversion MP3→WAV: %s", e2)
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
            "Hume: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
