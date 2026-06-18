"""
Adaptateur TTS pour Google Translate TTS (via gTTS).

Modèle d'API gratuit qui ne requiert aucune clé d'authentification.
Génère de l'audio MP3 à 24kHz (généralement).
"""

import logging
import time
from pathlib import Path

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)


class GTTSModel(TTSModel):
    """Adaptateur pour gTTS (Google Translate TTS)."""

    name = "gtts"
    description = "Google Translate TTS (API gratuite)"
    tier = "api"

    def __init__(self) -> None:
        self.lang = "fr"
        self.tld = "com"

    def is_available(self) -> bool:
        """Vérifie que la bibliothèque gtts est disponible."""
        try:
            import gtts  # noqa: F401
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
        """Synthétise *text* via gTTS.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.
        """
        from gtts import gTTS
        import soundfile as sf
        import librosa

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("gTTS: synthèse de %d caractères", len(text))

        t_start = time.perf_counter()

        tld = getattr(self, "tld", "com")
        tts = gTTS(text=text, lang=self.lang, tld=tld)
        
        # Sauvegarder en MP3 temporaire
        mp3_path = output_path.replace(".wav", ".mp3") if output_path.endswith(".wav") else output_path + ".mp3"
        tts.save(mp3_path)

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        # Convertir MP3 en WAV
        try:
            data, sample_rate = librosa.load(mp3_path, sr=24000, mono=True)
            sf.write(output_path, data, sample_rate)
            audio_duration = len(data) / sample_rate
        except Exception as e:
            logger.warning("gTTS: Impossible de convertir MP3→WAV via librosa: %s. Essai soundfile direct.", e)
            try:
                data, sample_rate = sf.read(mp3_path)
                sf.write(output_path, data, sample_rate)
                audio_duration = len(data) / sample_rate
            except Exception as e2:
                logger.error("gTTS: Échec complet de la conversion MP3→WAV: %s", e2)
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
            ttfa=generation_time,  # gTTS n'offre pas de streaming natif facilement mesurable
            sample_rate=sample_rate,
            audio_duration=audio_duration,
            rtf=rtf,
        )
        logger.info(
            "gTTS: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
