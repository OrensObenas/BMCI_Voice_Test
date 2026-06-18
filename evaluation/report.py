"""
Report generator for the French TTS benchmark.

Produces:
- A self-contained **Markdown** report with summary table, per-model details,
  difficulty breakdowns, and latency percentiles.
- A **JSON** dump of all raw results for downstream analysis.
"""

import json
import logging
import platform
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from evaluation.latency_eval import LatencyStats

logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────

_DIFFICULTY_EMOJI = {
    "easy": "🟢 Easy",
    "medium": "🟡 Medium",
    "hard": "🔴 Hard",
}

_RANK_EMOJI = ["🥇", "🥈", "🥉"]


def _fmt(value: float, decimals: int = 2) -> str:
    """Format a float to *decimals* places, returning '—' for NaN / None."""
    if value is None or value != value:  # NaN check
        return "—"
    return f"{value:.{decimals}f}"


def _pct(value: float) -> str:
    """Format a 0-1 ratio as a percentage string."""
    if value is None or value != value:
        return "—"
    return f"{value * 100:.1f}"


# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class ModelBenchmarkResult:
    """Aggregated benchmark results for a single TTS model."""

    model_name: str
    tier: str  # e.g. "local", "cloud-api"
    num_lines: int
    num_runs: int

    # WER metrics
    avg_wer: float
    avg_cer: float
    wer_by_difficulty: dict = field(default_factory=dict)  # {easy: x, …}

    # MOS metrics
    avg_mos: float = 0.0
    mos_by_difficulty: dict = field(default_factory=dict)

    # Latency metrics
    generation_time: LatencyStats | None = None
    ttfa: LatencyStats | None = None
    rtf: LatencyStats | None = None

    # Per-line details
    line_results: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a JSON-friendly dictionary."""
        d = {
            "model_name": self.model_name,
            "tier": self.tier,
            "num_lines": self.num_lines,
            "num_runs": self.num_runs,
            "avg_wer": self.avg_wer,
            "avg_cer": self.avg_cer,
            "wer_by_difficulty": self.wer_by_difficulty,
            "avg_mos": self.avg_mos,
            "mos_by_difficulty": self.mos_by_difficulty,
            "generation_time": self.generation_time.to_dict() if self.generation_time else None,
            "ttfa": self.ttfa.to_dict() if self.ttfa else None,
            "rtf": self.rtf.to_dict() if self.rtf else None,
            "line_results": self.line_results,
        }
        return d


# ── Report generator ──────────────────────────────────────────────────────────


class ReportGenerator:
    """Generate Markdown and JSON benchmark reports."""

    def __init__(self, results_dir: Path) -> None:
        """
        Parameters
        ----------
        results_dir:
            Directory where generated reports will be saved.
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    # ── Summary table ─────────────────────────────────────────────────────

    def generate_summary_table(self, results: list[ModelBenchmarkResult]) -> str:
        """Build a Markdown table comparing all models, sorted by MOS desc.

        Parameters
        ----------
        results:
            List of per-model benchmark results.

        Returns
        -------
        str
            Markdown-formatted table.
        """
        ranked = sorted(results, key=lambda r: r.avg_mos, reverse=True)

        lines: list[str] = []
        lines.append(
            "| Rank | Model | Tier | WER (%) | CER (%) | MOS | RTF | Gen Time (s) | TTFA (s) |"
        )
        lines.append(
            "|:----:|:------|:-----|--------:|--------:|----:|----:|-------------:|---------:|"
        )

        for idx, r in enumerate(ranked):
            rank = _RANK_EMOJI[idx] if idx < len(_RANK_EMOJI) else f"#{idx + 1}"
            rtf_mean = _fmt(r.rtf.mean, 3) if r.rtf else "—"
            gen_mean = _fmt(r.generation_time.mean, 3) if r.generation_time else "—"
            ttfa_mean = _fmt(r.ttfa.mean, 3) if r.ttfa else "—"
            lines.append(
                f"| {rank} | **{r.model_name}** | {r.tier} "
                f"| {_pct(r.avg_wer)} | {_pct(r.avg_cer)} "
                f"| {_fmt(r.avg_mos, 2)} | {rtf_mean} "
                f"| {gen_mean} | {ttfa_mean} |"
            )

        return "\n".join(lines)

    # ── Detailed report ───────────────────────────────────────────────────

    def generate_detailed_report(
        self, results: list[ModelBenchmarkResult]
    ) -> str:
        """Produce a full Markdown benchmark report.

        Sections:
        1. Header with timestamp and system info
        2. Summary comparison table
        3. Per-model detailed results
        4. WER breakdown by difficulty
        5. MOS breakdown by difficulty
        6. Latency percentiles

        Parameters
        ----------
        results:
            List of per-model benchmark results.

        Returns
        -------
        str
            Self-contained Markdown string.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections: list[str] = []

        # ── 1. Header ────────────────────────────────────────────────────
        sections.append("# 🎙️ French TTS Benchmark Report")
        sections.append("")
        sections.append(f"**Generated:** {now}  ")
        sections.append(f"**Platform:** {platform.platform()}  ")
        sections.append(f"**Python:** {platform.python_version()}  ")
        sections.append(f"**Processor:** {platform.processor() or 'N/A'}  ")
        if results:
            sections.append(
                f"**Lines evaluated:** {results[0].num_lines} | "
                f"**Runs per line:** {results[0].num_runs}"
            )
        sections.append("")
        sections.append("---")
        sections.append("")

        # ── 2. Summary table ─────────────────────────────────────────────
        sections.append("## 📊 Summary")
        sections.append("")
        sections.append(self.generate_summary_table(results))
        sections.append("")
        sections.append("> **RTF** (Real-Time Factor): < 1.0 = faster than real-time playback.")
        sections.append("")
        sections.append("---")
        sections.append("")

        # ── 3. Per-model details ─────────────────────────────────────────
        ranked = sorted(results, key=lambda r: r.avg_mos, reverse=True)
        for idx, r in enumerate(ranked):
            rank = _RANK_EMOJI[idx] if idx < len(_RANK_EMOJI) else f"#{idx + 1}"
            sections.append(f"## {rank} {r.model_name}")
            sections.append("")
            sections.append(f"- **Tier:** {r.tier}")
            sections.append(f"- **Avg WER:** {_pct(r.avg_wer)}%")
            sections.append(f"- **Avg CER:** {_pct(r.avg_cer)}%")
            sections.append(f"- **Avg MOS:** {_fmt(r.avg_mos)}")
            sections.append("")

            # ── WER by difficulty ────────────────────────────────────────
            sections.append("### WER by Difficulty")
            sections.append("")
            sections.append("| Difficulty | WER (%) |")
            sections.append("|:-----------|--------:|")
            for diff in ("easy", "medium", "hard"):
                label = _DIFFICULTY_EMOJI.get(diff, diff)
                val = r.wer_by_difficulty.get(diff)
                sections.append(f"| {label} | {_pct(val) if val is not None else '—'} |")
            sections.append("")

            # ── MOS by difficulty ────────────────────────────────────────
            sections.append("### MOS by Difficulty")
            sections.append("")
            sections.append("| Difficulty | MOS |")
            sections.append("|:-----------|----:|")
            for diff in ("easy", "medium", "hard"):
                label = _DIFFICULTY_EMOJI.get(diff, diff)
                val = r.mos_by_difficulty.get(diff)
                sections.append(f"| {label} | {_fmt(val) if val is not None else '—'} |")
            sections.append("")

            # ── Latency percentiles ──────────────────────────────────────
            sections.append("### ⏱️ Latency Percentiles")
            sections.append("")
            sections.append(
                "| Metric | Mean | Median | P95 | P99 | Min | Max | Std |"
            )
            sections.append(
                "|:-------|-----:|-------:|----:|----:|----:|----:|----:|"
            )
            for label, stats in [
                ("Gen Time (s)", r.generation_time),
                ("TTFA (s)", r.ttfa),
                ("RTF", r.rtf),
            ]:
                if stats:
                    sections.append(
                        f"| {label} "
                        f"| {_fmt(stats.mean, 4)} "
                        f"| {_fmt(stats.median, 4)} "
                        f"| {_fmt(stats.p95, 4)} "
                        f"| {_fmt(stats.p99, 4)} "
                        f"| {_fmt(stats.min, 4)} "
                        f"| {_fmt(stats.max, 4)} "
                        f"| {_fmt(stats.std, 4)} |"
                    )
                else:
                    sections.append(f"| {label} | — | — | — | — | — | — | — |")
            sections.append("")
            sections.append("---")
            sections.append("")

        # ── Footer ───────────────────────────────────────────────────────
        sections.append(
            "*Report generated automatically by the French TTS Benchmark pipeline.*"
        )
        sections.append("")

        return "\n".join(sections)

    # ── JSON export ───────────────────────────────────────────────────────

    def save_json(
        self, results: list[ModelBenchmarkResult], filename: str
    ) -> str:
        """Save raw results as JSON.

        Parameters
        ----------
        results:
            List of per-model benchmark results.
        filename:
            Output filename (e.g. ``"results.json"``).

        Returns
        -------
        str
            Absolute path to the written JSON file.
        """
        out_path = self.results_dir / filename
        payload = {
            "generated_at": datetime.now().isoformat(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "models": [r.to_dict() for r in results],
        }

        try:
            out_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("JSON results saved → %s", out_path)
        except Exception:
            logger.exception("Failed to write JSON report to %s", out_path)
            raise

        return str(out_path)

    # ── Save both formats ─────────────────────────────────────────────────

    def save_report(
        self, results: list[ModelBenchmarkResult]
    ) -> tuple[str, str]:
        """Generate and save both Markdown and JSON reports.

        Parameters
        ----------
        results:
            List of per-model benchmark results.

        Returns
        -------
        tuple[str, str]
            ``(markdown_path, json_path)`` as absolute path strings.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Markdown
        md_filename = f"benchmark_report_{timestamp}.md"
        md_path = self.results_dir / md_filename
        report_md = self.generate_detailed_report(results)
        try:
            md_path.write_text(report_md, encoding="utf-8")
            logger.info("Markdown report saved → %s", md_path)
        except Exception:
            logger.exception("Failed to write Markdown report to %s", md_path)
            raise

        # JSON
        json_filename = f"benchmark_results_{timestamp}.json"
        json_path = self.save_json(results, json_filename)

        return str(md_path), json_path
