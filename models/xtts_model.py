"""
Adaptateur TTS pour Coqui XTTSv2.

XTTSv2 est un modèle multilingue de clonage vocal.  Il requiert soit un
speaker intégré (``speaker``), soit un fichier audio de référence
(``speaker_wav``).  L'adaptateur tente d'abord d'utiliser les speakers
intégrés, puis repasse sur un WAV de référence si disponible.

⚠️  Ce modèle est lourd en CPU — toutes les opérations sont enveloppées
dans des try/except robustes.

Dépendance : ``pip install TTS soundfile``
"""

import logging
import time
from pathlib import Path

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)

# ── Constantes XTTSv2 ────────────────────────────────────────────────────────
XTTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
XTTS_LANGUAGE = "fr"
XTTS_DEVICE = "cpu"  # Pas de CUDA disponible sur cette machine


class XTTSModel(TTSModel):
    """Adaptateur pour Coqui XTTSv2 (multilingue, CPU-only).

    Le modèle est initialisé avec les speakers intégrés.  Si aucun
    speaker n'est disponible, l'adaptateur tente d'utiliser un WAV
    de référence placé dans le dossier ``outputs/reference/``.
    """

    name = "xtts"
    description = "Coqui XTTSv2 — multilingual voice cloning TTS (CPU)"
    tier = "cpu"

    def __init__(self) -> None:
        self._tts = None
        self._speaker: str | None = None
        self._speaker_wav: str | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Vérifie que le package ``TTS`` (Coqui) est importable."""
        try:
            from TTS.api import TTS as _CoquiTTS  # noqa: F401
            return True
        except ImportError:
            logger.warning("TTS (Coqui) n'est pas installé — modèle indisponible")
            return False

    def setup(self) -> None:
        """Charge le modèle XTTSv2 et sélectionne un speaker.

        L'initialisation peut être longue (téléchargement du modèle ~1.8 Go
        la première fois).

        Stratégie de sélection du speaker :
        1. Utiliser le premier speaker intégré s'il y en a.
        2. Sinon, chercher un WAV de référence dans ``outputs/reference/``.
        3. Sinon, logger un warning — synthesize() lèvera une erreur.
        """
        from TTS.api import TTS as CoquiTTS

        logger.info("Initialisation de XTTSv2 (model=%s, device=%s)",
                     XTTS_MODEL_NAME, XTTS_DEVICE)

        try:
            self._tts = CoquiTTS(model_name=XTTS_MODEL_NAME).to(XTTS_DEVICE)
        except Exception:
            logger.exception("Échec du chargement de XTTSv2")
            raise

        # Stratégie 1 : speakers intégrés
        speakers = getattr(self._tts, "speakers", None) or []
        if speakers:
            self._speaker = speakers[0]
            logger.info("XTTSv2: utilisation du speaker intégré '%s'", self._speaker)
            return

        # Stratégie 2 : WAV de référence
        try:
            from config import OUTPUTS_DIR
            ref_dir = OUTPUTS_DIR / "reference"
        except ImportError:
            ref_dir = Path("outputs/reference")

        ref_dir.mkdir(parents=True, exist_ok=True)
        ref_wavs = list(ref_dir.glob("*.wav"))
        if ref_wavs:
            self._speaker_wav = str(ref_wavs[0])
            logger.info("XTTSv2: utilisation du WAV de référence '%s'",
                         self._speaker_wav)
            return

        # Aucun speaker disponible
        logger.warning(
            "XTTSv2: aucun speaker intégré ni WAV de référence trouvé. "
            "Placez un fichier .wav dans %s pour activer le clonage vocal.",
            ref_dir,
        )

    def teardown(self) -> None:
        """Libère le modèle XTTSv2."""
        self._tts = None
        self._speaker = None
        self._speaker_wav = None
        logger.debug("XTTSv2 libéré")

    # ── Synthèse ─────────────────────────────────────────────────────────

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* via XTTSv2 et sauvegarde en WAV.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.

        Raises:
            RuntimeError: Si le modèle n'a pas été initialisé via setup()
                ou si aucun speaker n'est configuré.
        """
        import soundfile as sf

        if self._tts is None:
            raise RuntimeError("Appeler setup() avant synthesize()")

        if self._speaker is None and self._speaker_wav is None:
            raise RuntimeError(
                "XTTSv2: aucun speaker configuré. Placez un fichier .wav de "
                "référence dans outputs/reference/ ou vérifiez que le modèle "
                "dispose de speakers intégrés."
            )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("XTTSv2: synthèse de %d caractères", len(text))

        t_start = time.perf_counter()

        try:
            if self._speaker:
                self._tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    language=XTTS_LANGUAGE,
                    speaker=self._speaker,
                )
            else:
                self._tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    language=XTTS_LANGUAGE,
                    speaker_wav=self._speaker_wav,
                )
        except Exception:
            logger.exception("XTTSv2: erreur pendant la synthèse")
            raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        # Lire le fichier pour obtenir la durée audio
        info = sf.info(output_path)
        audio_duration = info.duration
        sample_rate = info.samplerate

        # XTTSv2 n'est pas streaming → TTFA = temps total
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
            "XTTSv2: %.2f s audio en %.3f s (RTF=%.3f)",
            result.audio_duration, result.generation_time, result.rtf,
        )
        return result
