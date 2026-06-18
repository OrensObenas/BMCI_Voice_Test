"""
Latency statistics evaluator for the French TTS benchmark.

Computes descriptive statistics (mean, median, percentiles, …) over lists of
timing values and the Real-Time Factor (RTF).

RTF < 1.0 means the system generates audio faster than real-time playback.
"""

import logging
import math
import statistics
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LatencyStats:
    """Descriptive statistics for a collection of timing values (seconds)."""

    mean: float
    median: float
    p95: float
    p99: float
    min: float
    max: float
    std: float
    values: list[float] = field(default_factory=list, repr=False)

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary (for JSON export)."""
        return {
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "p95": round(self.p95, 4),
            "p99": round(self.p99, 4),
            "min": round(self.min, 4),
            "max": round(self.max, 4),
            "std": round(self.std, 4),
            "n": len(self.values),
        }


class LatencyAnalyzer:
    """Static helpers for latency / RTF analysis."""

    @staticmethod
    def compute_stats(values: list[float]) -> LatencyStats:
        """Compute descriptive statistics from a list of timing values.

        Parameters
        ----------
        values:
            Non-empty list of timing measurements (seconds).

        Returns
        -------
        LatencyStats
            Aggregated statistics including mean, median, P95, P99, min, max,
            and standard deviation.

        Raises
        ------
        ValueError
            If *values* is empty.
        """
        if not values:
            raise ValueError("Cannot compute statistics on an empty list")

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        mean = statistics.mean(sorted_vals)
        median = statistics.median(sorted_vals)
        std = statistics.stdev(sorted_vals) if n >= 2 else 0.0

        # Percentiles via nearest-rank (index clamp)
        p95_idx = min(math.ceil(0.95 * n) - 1, n - 1)
        p99_idx = min(math.ceil(0.99 * n) - 1, n - 1)

        return LatencyStats(
            mean=round(mean, 4),
            median=round(median, 4),
            p95=round(sorted_vals[p95_idx], 4),
            p99=round(sorted_vals[p99_idx], 4),
            min=round(sorted_vals[0], 4),
            max=round(sorted_vals[-1], 4),
            std=round(std, 4),
            values=values,
        )

    @staticmethod
    def compute_rtf(generation_time: float, audio_duration: float) -> float:
        """Compute the Real-Time Factor.

        RTF = generation_time / audio_duration

        An RTF < 1.0 indicates that synthesis is faster than real-time.

        Parameters
        ----------
        generation_time:
            Wall-clock time to generate the audio (seconds).
        audio_duration:
            Duration of the generated audio (seconds).

        Returns
        -------
        float
            Real-Time Factor, or ``inf`` if *audio_duration* is zero.
        """
        if audio_duration <= 0.0:
            logger.warning(
                "audio_duration=%.4f is non-positive; returning inf for RTF",
                audio_duration,
            )
            return float("inf")
        return round(generation_time / audio_duration, 4)
