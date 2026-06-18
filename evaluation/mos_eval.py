"""
MOS (Mean Opinion Score) evaluator for the French TTS benchmark.

Uses **UTMOS** (``utmos22_strong`` from ``tarepan/SpeechMOS``) — a neural MOS
predictor trained on human ratings — to produce a quality score between 1.0
(bad) and 5.0 (excellent) for each synthesised utterance.

The model runs on CPU by default and expects 16 kHz mono audio.
"""

import logging
from pathlib import Path

import librosa
import numpy as np
import torch

logger = logging.getLogger(__name__)


class MOSAnalyzer:
    """Predict perceptual quality (MOS) via the UTMOS neural model."""

    def __init__(self, device: str = "cpu") -> None:
        """Load the UTMOS predictor from ``torch.hub``.

        Parameters
        ----------
        device:
            ``"cpu"`` or ``"cuda"``.
        """
        self.device = torch.device(device)

        logger.info("Loading UTMOS model (utmos22_strong) on %s …", device)
        try:
            self.predictor = torch.hub.load(
                "tarepan/SpeechMOS:v1.2.0",
                "utmos22_strong",
                trust_repo=True,
            )
            self.predictor = self.predictor.to(self.device)
            self.predictor.eval()
        except Exception:
            logger.exception("Failed to load UTMOS model")
            raise

        logger.info("UTMOS model loaded successfully")

    # ── Single-file prediction ────────────────────────────────────────────

    def predict_mos(self, audio_path: str) -> float:
        """Predict MOS for a single audio file.

        The audio is resampled to 16 kHz mono before inference.

        Parameters
        ----------
        audio_path:
            Path to a WAV / FLAC / MP3 file.

        Returns
        -------
        float
            Predicted MOS in the range [1.0, 5.0].
        """
        audio_path = str(audio_path)
        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.debug("Predicting MOS for %s", audio_path)

        # Load and resample to 16 kHz mono (UTMOS requirement)
        waveform, _sr = librosa.load(audio_path, sr=16000, mono=True)
        waveform_tensor = torch.from_numpy(waveform).unsqueeze(0).to(self.device)

        with torch.no_grad():
            score = self.predictor(waveform_tensor, sr=16000)

        mos = float(score.item())
        # Clamp to valid MOS range
        mos = max(1.0, min(5.0, mos))

        logger.debug("MOS = %.3f for %s", mos, audio_path)
        return round(mos, 4)

    # ── Batch prediction ──────────────────────────────────────────────────

    def predict_batch(self, audio_paths: list[str]) -> list[float]:
        """Predict MOS for multiple audio files.

        Files are processed sequentially (UTMOS is lightweight; batching
        variable-length audio would require padding and offers marginal
        speed-up on CPU).

        Parameters
        ----------
        audio_paths:
            List of paths to audio files.

        Returns
        -------
        list[float]
            Predicted MOS scores in the same order as *audio_paths*.
        """
        scores: list[float] = []
        for i, path in enumerate(audio_paths, 1):
            try:
                score = self.predict_mos(path)
                scores.append(score)
            except Exception:
                logger.exception(
                    "Failed to predict MOS for %s (%d/%d)",
                    path,
                    i,
                    len(audio_paths),
                )
                scores.append(float("nan"))
        return scores
