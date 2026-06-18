"""
Adaptateur STT pour les modèles Whisper locaux (via faster-whisper).
"""

import logging
import time
from pathlib import Path

from stt_models.base import STTModel, TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperLocalSTT(STTModel):
    """Adaptateur STT pour Whisper local via faster-whisper."""

    tier = "local"

    def __init__(self, model_size: str = "base") -> None:
        """Initialise le modèle avec sa taille.

        Args:
            model_size: Taille du modèle Whisper (ex. 'base', 'large-turbo', 'large').
        """
        # Mapper les noms conviviaux aux identifiants exacts de faster-whisper
        mapped_size = model_size
        if model_size == "large-turbo":
            mapped_size = "large-v3-turbo"
        elif model_size == "large":
            mapped_size = "large-v3"

        self.model_size = mapped_size
        self.name = f"whisper-local-{model_size}"
        self.description = f"Whisper local via faster-whisper ({mapped_size})"
        self.model = None

    def is_available(self) -> bool:
        """Vérifie que faster-whisper est importable."""
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            logger.warning("faster-whisper n'est pas installé — modèle indisponible")
            return False

    def setup(self) -> None:
        """Charge le modèle Whisper en mémoire."""
        from faster_whisper import WhisperModel
        from config import DEVICE

        compute_type = "int8" if DEVICE == "cpu" else "float16"
        logger.info(
            "Chargement de Whisper local model=%s sur device=%s compute_type=%s",
            self.model_size, DEVICE, compute_type
        )
        self.model = WhisperModel(
            self.model_size,
            device=DEVICE,
            compute_type=compute_type
        )
        logger.info("Modèle Whisper local %s prêt", self.model_size)

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcrit le fichier audio en local."""
        if self.model is None:
            raise RuntimeError("Appeler setup() avant transcribe()")

        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        t_start = time.perf_counter()
        try:
            # Transcrire en forçant la langue à français
            segments, _info = self.model.transcribe(
                audio_path,
                language="fr",
                beam_size=5,
                vad_filter=True
            )
            # Rassembler les segments
            text = " ".join(segment.text.strip() for segment in segments)
            latency = time.perf_counter() - t_start
            return TranscriptionResult(text=text, latency=latency)
        except Exception as e:
            logger.exception("Erreur pendant la transcription Whisper local")
            latency = time.perf_counter() - t_start
            return TranscriptionResult(text="", latency=latency, error=str(e))
