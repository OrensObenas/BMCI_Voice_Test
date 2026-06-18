"""
Evaluation pipeline for the French TTS benchmark.

Provides evaluators for:
- WER/CER: Word/Character Error Rate via faster-whisper + jiwer
- MOS: Mean Opinion Score via UTMOS neural predictor
- Latency: Generation time, TTFA, and RTF statistics
- Report: Markdown and JSON report generation
"""

from evaluation.wer_eval import WERAnalyzer
from evaluation.mos_eval import MOSAnalyzer
from evaluation.latency_eval import LatencyAnalyzer, LatencyStats
from evaluation.report import ReportGenerator, ModelBenchmarkResult

__all__ = [
    "WERAnalyzer",
    "MOSAnalyzer",
    "LatencyAnalyzer",
    "LatencyStats",
    "ReportGenerator",
    "ModelBenchmarkResult",
]
