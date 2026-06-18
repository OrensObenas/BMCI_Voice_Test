"""
Adaptateur TTS pour MeloTTS.

MeloTTS est un modèle non-streaming qui génère l'audio complet d'un
coup via ``tts_to_file()``.  Puisqu'il n'y a pas de flux progressif,
le TTFA est égal au temps total de génération.

Dépendance : ``pip install melo-tts soundfile``
"""

import logging
import time
from pathlib import Path

from models.base import SynthesisResult, TTSModel

try:
    from config import DEVICE
except ImportError:
    DEVICE = "cpu"

logger = logging.getLogger(__name__)

# ── Constantes MeloTTS ───────────────────────────────────────────────────────
MELO_LANGUAGE = "FR"


class MeloModel(TTSModel):
    """Adaptateur pour MeloTTS (non-streaming, CPU/GPU).

    Le modèle génère l'audio en un seul appel ``tts_to_file()`` — il n'y a
    pas de concept de « premier chunk », donc TTFA = generation_time.
    """

    name = "melo"
    description = "MeloTTS — fast non-streaming multilingual TTS"
    tier = "cpu"

    def __init__(self) -> None:
        self._tts = None
        self._speaker_id: int | None = None
        self.speed: float = 1.0

    # ── Lifecycle ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Vérifie que le package ``melo`` est importable."""
        try:
            from melo.api import TTS as _MeloTTS  # noqa: F401
            return True
        except ImportError:
            logger.warning("melo n'est pas installé — modèle indisponible")
            return False

    def setup(self) -> None:
        """Charge le modèle MeloTTS et sélectionne le premier speaker français."""
        from melo.api import TTS as MeloTTS

        device = DEVICE
        logger.info("Initialisation de MeloTTS (lang=%s, device=%s)",
                     MELO_LANGUAGE, device)

        self._tts = MeloTTS(language=MELO_LANGUAGE, device=device)

        # Trouver le premier speaker disponible pour le français
        spk2id: dict = self._tts.hps.data.spk2id
        logger.debug("Speakers disponibles : %s", list(spk2id.keys()))

        # Chercher un speaker français (contient 'FR') ou prendre le premier
        french_speakers = [k for k in spk2id.keys() if "FR" in k.upper()]
        if french_speakers:
            speaker_name = french_speakers[0]
        else:
            speaker_name = next(iter(spk2id.keys()))
            logger.warning(
                "Aucun speaker français trouvé, utilisation de '%s'", speaker_name
            )

        self._speaker_id = spk2id[speaker_name]
        logger.info("MeloTTS prêt — speaker='%s' (id=%d)",
                     speaker_name, self._speaker_id)

    def teardown(self) -> None:
        """Libère le modèle MeloTTS."""
        self._tts = None
        self._speaker_id = None
        logger.debug("MeloTTS libéré")

    # ── Synthèse ─────────────────────────────────────────────────────────

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* et écrit le WAV via ``tts_to_file()``.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.

        Raises:
            RuntimeError: Si le modèle n'a pas été initialisé via setup().
        """
        import soundfile as sf

        if self._tts is None or self._speaker_id is None:
            raise RuntimeError("Appeler setup() avant synthesize()")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        logger.debug("MeloTTS: synthèse de %d caractères", len(text))
        t_start = time.perf_counter()

        speed = getattr(self, "speed", 1.0)
        self._tts.tts_to_file(
            text,
            self._speaker_id,
            output_path,
            speed=speed,
        )

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        # Lire le fichier pour obtenir la durée audio
        info = sf.info(output_path)
        audio_duration = info.duration
        sample_rate = info.samplerate

        # Pas de streaming → TTFA = temps total
        rtf = generation_time / audio_duration if audio_duration > 0 else float("inf")

        result = SynthesisResult(
            audio_path=output_path,
            generation_time=generation_time,
            ttfa=generation_time,
            sample_rate=sample_rate,
            audio_duration=audio_duration,
            rtf=rtf,
        )
        logger.info(
            "MeloTTS: %.2f s audio en %.3f s (RTF=%.3f)",
            result.audio_duration, result.generation_time, result.rtf,
        )
        return result
