"""
WER / CER evaluator for the French TTS benchmark.

Uses **faster-whisper** (CTranslate2 backend) for ASR transcription and
**jiwer** for computing Word Error Rate (WER) and Character Error Rate (CER).

The text normaliser is French-aware: it preserves accented characters (é, è, ê,
ç, ù, …) while stripping punctuation and collapsing whitespace so that the
comparison is fair.
"""

import logging
import re
import unicodedata
from pathlib import Path

import jiwer
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Punctuation characters to strip during normalisation.
_PUNCT_RE = re.compile(r"[\.,:;!\?\"\'\—\–\-\(\)\[\]\{\}«»…]+")


class WERAnalyzer:
    """Transcribe audio with faster-whisper and compute WER/CER vs. reference."""

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        language: str = "fr",
        device: str = "cpu",
    ) -> None:
        """Load the faster-whisper model.

        Parameters
        ----------
        model_size:
            Whisper model identifier (e.g. ``"large-v3-turbo"``).
        language:
            ISO-639-1 language code for forced decoding (``"fr"``).
        device:
            ``"cpu"`` or ``"cuda"``.
        """
        self.language = language
        compute_type = "int8" if device == "cpu" else "float16"

        logger.info(
            "Loading faster-whisper model=%s device=%s compute_type=%s",
            model_size,
            device,
            compute_type,
        )
        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception:
            logger.exception("Failed to load faster-whisper model '%s'", model_size)
            raise

    # ── Transcription ─────────────────────────────────────────────────────

    def transcribe(self, audio_path: str) -> str:
        """Transcribe an audio file and return the concatenated text.

        Parameters
        ----------
        audio_path:
            Path to a WAV / FLAC / MP3 file.

        Returns
        -------
        str
            The transcribed text.
        """
        audio_path = str(audio_path)
        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.debug("Transcribing %s", audio_path)
        segments, _info = self.model.transcribe(
            audio_path,
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments)
        logger.debug("Hypothesis: %s", text)
        return text

    # ── WER / CER ─────────────────────────────────────────────────────────

    def compute_wer(self, reference: str, audio_path: str) -> dict:
        """Transcribe *audio_path* and compare against *reference*.

        Parameters
        ----------
        reference:
            Ground-truth text.
        audio_path:
            Path to the synthesised audio file.

        Returns
        -------
        dict
            Keys: ``reference``, ``hypothesis``, ``wer``, ``cer``,
            ``substitutions``, ``deletions``, ``insertions``.
        """
        hypothesis = self.transcribe(audio_path)

        ref_norm = self.normalize_text(reference)
        hyp_norm = self.normalize_text(hypothesis)

        # --- Word-level metrics ---
        wer_output = jiwer.process_words(ref_norm, hyp_norm)
        wer_score = wer_output.wer

        # --- Character-level metrics ---
        cer_output = jiwer.process_characters(ref_norm, hyp_norm)
        cer_score = cer_output.cer

        return {
            "reference": ref_norm,
            "hypothesis": hyp_norm,
            "wer": round(wer_score, 4),
            "cer": round(cer_score, 4),
            "substitutions": wer_output.substitutions,
            "deletions": wer_output.deletions,
            "insertions": wer_output.insertions,
        }

    # ── Text normalisation ────────────────────────────────────────────────

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalise text for fair WER/CER comparison.

        Steps:
        1. NFKC unicode normalisation (preserves French accents but
           normalises ligatures and compatibility chars).
        2. Lower-case.
        3. Strip punctuation (keeps letters, digits, spaces).
        4. Collapse whitespace to a single space and strip.

        Parameters
        ----------
        text:
            Raw text string.

        Returns
        -------
        str
            Normalised text ready for WER/CER comparison.
        """
        text = unicodedata.normalize("NFKC", text)
        text = text.lower()
        text = _PUNCT_RE.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
