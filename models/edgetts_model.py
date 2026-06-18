"""
Adaptateur TTS pour Microsoft Edge TTS (via edge-tts).

Modèle d'API gratuit qui utilise les voix de synthèse vocale Azure Neural.
Supporte le streaming pour mesurer précisément le TTFA.
"""

import asyncio
import logging
import time
from pathlib import Path

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)


class EdgeTTSModel(TTSModel):
    """Adaptateur pour Edge TTS (Microsoft Azure Neural)."""

    name = "edgetts"
    description = "Microsoft Edge TTS (Azure Neural API, gratuit)"
    tier = "api"

    def __init__(self) -> None:
        # fr-FR-DeniseNeural est une voix féminine très naturelle et expressive
        self.voice = "fr-FR-DeniseNeural"

    def is_available(self) -> bool:
        """Vérifie que la bibliothèque edge-tts est installée."""
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False

    def setup(self) -> None:
        """Pas d'initialisation nécessaire."""
        pass

    def teardown(self) -> None:
        """Pas de nettoyage nécessaire."""
        pass

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* via edge-tts en mesurant le TTFA.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.
        """
        import edge_tts
        import soundfile as sf
        import librosa

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("EdgeTTS: synthèse de %d caractères", len(text))

        mp3_path = output_path.replace(".wav", ".mp3") if output_path.endswith(".wav") else output_path + ".mp3"

        t_start = time.perf_counter()
        ttfa = None

        async def _stream_to_file():
            nonlocal ttfa
            communicate = edge_tts.Communicate(text, self.voice)
            with open(mp3_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        if ttfa is None:
                            ttfa = time.perf_counter() - t_start
                            logger.debug("EdgeTTS: TTFA = %.4f s", ttfa)
                        f.write(chunk["data"])

        try:
            asyncio.run(_stream_to_file())
        except Exception as exc:
            logger.error("EdgeTTS: Erreur pendant le streaming de la synthèse: %s", exc)
            raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        # Convertir MP3 en WAV
        try:
            data, sample_rate = librosa.load(mp3_path, sr=24000, mono=True)
            sf.write(output_path, data, sample_rate)
            audio_duration = len(data) / sample_rate
        except Exception as e:
            logger.warning("EdgeTTS: Impossible de convertir MP3→WAV via librosa: %s. Essai soundfile direct.", e)
            try:
                data, sample_rate = sf.read(mp3_path)
                sf.write(output_path, data, sample_rate)
                audio_duration = len(data) / sample_rate
            except Exception as e2:
                logger.error("EdgeTTS: Échec complet de la conversion MP3→WAV: %s", e2)
                raise RuntimeError(f"Échec de la conversion MP3→WAV: {e2}")

        # Supprimer le MP3 temporaire si converti avec succès
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
            "EdgeTTS: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
