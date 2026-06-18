"""
Adaptateur TTS pour F5-TTS.

F5-TTS est un modèle de synthèse vocale récent qui fonctionne par
clonage vocal à partir d'un fichier audio de référence.  Il peut être
lent sur CPU mais produit une qualité audio élevée.

⚠️  F5-TTS nécessite un fichier audio de référence et son texte
correspondant pour fonctionner.  Si aucun fichier de référence n'est
trouvé, ``is_available()`` retourne False.

Dépendance : ``pip install f5-tts soundfile``
"""

import logging
import time
from pathlib import Path

import numpy as np

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)

# Essayer d'importer F5-TTS immédiatement au niveau du module pour éviter les plantages de DLL Windows (Access Violation)
# si torchaudio est déjà chargé/utilisé.
try:
    from f5_tts.api import F5TTS
    _F5_TTS_AVAILABLE = True
except ImportError:
    F5TTS = None
    _F5_TTS_AVAILABLE = False

# ── Constantes F5-TTS ────────────────────────────────────────────────────────
F5_MODEL_TYPE = "F5-TTS"
F5_ODE_METHOD = "euler"
F5_DEFAULT_REF_TEXT = "Bonjour, bienvenue."  # Texte de référence par défaut


class F5TTSModel(TTSModel):
    """Adaptateur pour F5-TTS (voice cloning, CPU).

    Le modèle nécessite un fichier audio de référence (``ref_file``) et
    son texte (``ref_text``) pour synthétiser de nouveaux textes avec la
    voix de la référence.

    Le fichier de référence est cherché dans ``outputs/reference/``.
    """

    name = "f5tts"
    description = "F5-TTS — high-quality voice cloning TTS"
    tier = "cpu"

    def __init__(self) -> None:
        self._model = None
        self._ref_file: str | None = None
        self._ref_text: str = F5_DEFAULT_REF_TEXT
        self._sample_rate: int = 24000

    # ── Lifecycle ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Vérifie que le package ``f5_tts`` est importable."""
        return _F5_TTS_AVAILABLE

    def setup(self) -> None:
        """Initialise le modèle F5-TTS et localise le fichier de référence.

        Le fichier de référence est cherché dans ``outputs/reference/``.
        S'il n'existe pas, un warning est émis mais le setup continue
        (``synthesize()`` lèvera une erreur si la référence manque).
        """
        if not _F5_TTS_AVAILABLE:
            raise ImportError("f5-tts n'est pas installé ou n'a pas pu être importé")

        try:
            from config import DEVICE, OUTPUTS_DIR
            device = DEVICE
            ref_dir = OUTPUTS_DIR / "reference"
        except ImportError:
            device = "cpu"
            ref_dir = Path("outputs/reference")

        logger.info("Initialisation de F5-TTS (model=%s, device=%s)",
                     "F5TTS_v1_Base", device)

        try:
            self._model = F5TTS(
                model="F5TTS_v1_Base",
                ckpt_file="",
                vocab_file="",
                ode_method=F5_ODE_METHOD,
                use_ema=True,
                vocoder_local_path=None,
                device=device,
            )
        except Exception:
            logger.exception("Échec de l'initialisation de F5-TTS")
            raise

        # Chercher un fichier de référence
        ref_dir.mkdir(parents=True, exist_ok=True)
        ref_wavs = list(ref_dir.glob("*.wav"))
        if ref_wavs:
            self._ref_file = str(ref_wavs[0])
            logger.info("F5-TTS: référence audio = '%s'", self._ref_file)

            # Chercher un fichier texte de référence associé
            ref_txt = ref_wavs[0].with_suffix(".txt")
            if ref_txt.exists():
                self._ref_text = ref_txt.read_text(encoding="utf-8").strip()
                logger.info("F5-TTS: référence texte = '%s'", self._ref_text)
        else:
            logger.warning(
                "F5-TTS: aucun fichier de référence trouvé dans %s. "
                "Placez un fichier .wav (et optionnellement un .txt) pour "
                "activer la synthèse.",
                ref_dir,
            )

        logger.info("F5-TTS prêt")

    def teardown(self) -> None:
        """Libère le modèle F5-TTS."""
        self._model = None
        self._ref_file = None
        logger.debug("F5-TTS libéré")

    # ── Synthèse ─────────────────────────────────────────────────────────

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* avec F5-TTS via clonage vocal.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec métriques de performance.

        Raises:
            RuntimeError: Si le modèle ou la référence ne sont pas disponibles.
        """
        import soundfile as sf

        if self._model is None:
            raise RuntimeError("Appeler setup() avant synthesize()")

        if self._ref_file is None:
            raise RuntimeError(
                "F5-TTS: aucun fichier de référence configuré. "
                "Placez un fichier .wav dans outputs/reference/"
            )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("F5-TTS: synthèse de %d caractères", len(text))

        t_start = time.perf_counter()

        try:
            wav, sr, _ = self._model.infer(
                ref_file=self._ref_file,
                ref_text=self._ref_text,
                gen_text=text,
            )
        except Exception:
            logger.exception("F5-TTS: erreur pendant la synthèse")
            raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        # Convertir en numpy si nécessaire
        if not isinstance(wav, np.ndarray):
            try:
                wav = np.array(wav)
            except Exception:
                wav = np.frombuffer(wav, dtype=np.float32)

        self._sample_rate = sr if sr else self._sample_rate

        # Sauvegarder en WAV
        sf.write(output_path, wav, self._sample_rate)

        audio_duration = len(wav) / self._sample_rate
        # F5-TTS n'est pas streaming → TTFA = temps total
        rtf = generation_time / audio_duration if audio_duration > 0 else float("inf")

        result = SynthesisResult(
            audio_path=output_path,
            generation_time=generation_time,
            ttfa=generation_time,
            sample_rate=self._sample_rate,
            audio_duration=audio_duration,
            rtf=rtf,
        )
        logger.info(
            "F5-TTS: %.2f s audio en %.3f s (RTF=%.3f)",
            result.audio_duration, result.generation_time, result.rtf,
        )
        return result
