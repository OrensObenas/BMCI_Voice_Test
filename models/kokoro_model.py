"""
Adaptateur TTS pour Kokoro v1.0.

Kokoro est un modèle TTS léger et rapide qui fonctionne en streaming :
il génère l'audio par morceaux (chunks), ce qui permet de mesurer
précisément le *time to first audio* (TTFA).

Dépendance : ``pip install kokoro soundfile``
"""

import logging
import time
from pathlib import Path

import numpy as np

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)

# ── Constantes Kokoro ────────────────────────────────────────────────────────
KOKORO_LANG = "f"
KOKORO_VOICE = "ff_siwis"
KOKORO_SAMPLE_RATE = 24000


class KokoroModel(TTSModel):
    """Adaptateur pour le modèle Kokoro v1.0 (streaming, CPU-friendly).

    Le pipeline Kokoro génère un flux de tuples
    ``(graphemes, phonemes, audio_chunk)`` — l'adaptateur concatène tous
    les chunks et mesure le TTFA sur le premier.
    """

    name = "kokoro"
    description = "Kokoro v1.0 — lightweight streaming French TTS"
    tier = "cpu"

    def __init__(self) -> None:
        self._pipeline = None
        self.voice = KOKORO_VOICE
        self.speed = 1.0

    # ── Lifecycle ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Vérifie que le package ``kokoro`` est importable."""
        try:
            import kokoro  # noqa: F401
            return True
        except ImportError:
            logger.warning("kokoro n'est pas installé — modèle indisponible")
            return False

    def setup(self) -> None:
        """Crée le pipeline Kokoro pour le français."""
        from kokoro import KPipeline

        logger.info("Initialisation du pipeline Kokoro (lang=%s, voice=%s)",
                     KOKORO_LANG, KOKORO_VOICE)
        self._pipeline = KPipeline(lang_code=KOKORO_LANG)
        logger.info("Pipeline Kokoro prêt")

    def teardown(self) -> None:
        """Libère le pipeline."""
        self._pipeline = None
        logger.debug("Pipeline Kokoro libéré")

    # ── Synthèse ─────────────────────────────────────────────────────────

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* en WAV via le pipeline Kokoro.

        Le pipeline est itératif — on mesure le TTFA au premier chunk
        et on concatène tous les chunks pour l'audio final.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.

        Raises:
            RuntimeError: Si le pipeline n'a pas été initialisé via setup().
        """
        import soundfile as sf

        if self._pipeline is None:
            raise RuntimeError("Appeler setup() avant synthesize()")

        audio_chunks: list[np.ndarray] = []
        ttfa: float | None = None

        logger.debug("Kokoro: synthèse de %d caractères", len(text))
        t_start = time.perf_counter()

        voice = getattr(self, "voice", KOKORO_VOICE)
        speed = getattr(self, "speed", 1.0)
        for _graphemes, _phonemes, audio_chunk in self._pipeline(
            text, voice=voice, speed=speed
        ):
            if ttfa is None:
                ttfa = time.perf_counter() - t_start
                logger.debug("Kokoro: TTFA = %.4f s", ttfa)
            audio_chunks.append(audio_chunk)

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        # Concaténer les chunks et sauvegarder en WAV
        if not audio_chunks:
            raise RuntimeError("Le pipeline Kokoro n'a produit aucun audio")

        full_audio = np.concatenate(audio_chunks)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, full_audio, KOKORO_SAMPLE_RATE)

        audio_duration = len(full_audio) / KOKORO_SAMPLE_RATE
        rtf = generation_time / audio_duration if audio_duration > 0 else float("inf")

        result = SynthesisResult(
            audio_path=output_path,
            generation_time=generation_time,
            ttfa=ttfa if ttfa is not None else generation_time,
            sample_rate=KOKORO_SAMPLE_RATE,
            audio_duration=audio_duration,
            rtf=rtf,
        )
        logger.info(
            "Kokoro: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
