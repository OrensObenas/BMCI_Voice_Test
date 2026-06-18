#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           TTS Benchmark — Script Principal                   ║
║   Évaluation comparative de modèles TTS en français          ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python run_benchmark.py                          # Tous les modèles disponibles
    python run_benchmark.py --models kokoro melo     # Modèles spécifiques
    python run_benchmark.py --models kokoro --runs 5 # 5 runs pour la stabilité
    python run_benchmark.py --lines 1-5              # Seulement les lignes 1-5
    python run_benchmark.py --list                   # Lister les modèles disponibles
    python run_benchmark.py --skip-eval              # Générer audio sans évaluer
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Force UTF-8 encoding on Windows to prevent console print errors with emojis/special characters
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ── Configuration ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    OUTPUTS_DIR, RESULTS_DIR, DEVICE, NUM_RUNS, NUM_WARMUP,
    AVAILABLE_MODELS, DEFAULT_MODELS, ASR_MODEL, ASR_LANGUAGE,
)
from dialogue import DIALOGUE, DialogueLine

console = Console()

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("benchmark")


# ══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def parse_line_range(line_arg: str) -> list[int]:
    """Parse un argument de lignes : '1-5', '1,3,7', 'all'."""
    if not line_arg or line_arg == "all":
        return list(range(1, len(DIALOGUE) + 1))
    
    ids = []
    for part in line_arg.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            ids.extend(range(int(start), int(end) + 1))
        else:
            ids.append(int(part))
    return ids


def list_available_models():
    """Affiche les modèles disponibles et leur statut."""
    from models import MODEL_REGISTRY
    
    table = Table(title="🎤 Modèles TTS Disponibles", show_lines=True)
    table.add_column("Nom", style="cyan bold")
    table.add_column("Description", style="white")
    table.add_column("Tier", style="magenta")
    table.add_column("Disponible", style="green")
    
    for name, model_cls in MODEL_REGISTRY.items():
        model = model_cls()
        available = "✅" if model.is_available() else "❌"
        table.add_row(name, model.description, model.tier, available)
    
    console.print(table)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def run_generation(model_name: str, lines: list[DialogueLine], num_runs: int, 
                   num_warmup: int) -> list[dict]:
    """
    Génère l'audio pour toutes les lignes avec un modèle donné.
    Retourne une liste de résultats par ligne et par run.
    """
    from models import get_model
    
    model = get_model(model_name)
    if not model.is_available():
        logger.warning(f"Modèle '{model_name}' non disponible — skip")
        return []
    
    logger.info(f"Chargement du modèle : {model_name}")
    model.setup()
    
    model_output_dir = OUTPUTS_DIR / model_name
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    total_steps = len(lines) * (num_warmup + num_runs)
    
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[bold cyan]{model_name}[/]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Synthèse", total=total_steps)
        
        for line in lines:
            line_results = []
            
            for run_idx in range(num_warmup + num_runs):
                is_warmup = run_idx < num_warmup
                run_label = f"warmup_{run_idx}" if is_warmup else f"run_{run_idx - num_warmup}"
                
                output_path = str(
                    model_output_dir / f"line_{line.id:02d}_{run_label}.wav"
                )
                
                try:
                    result = model.synthesize(line.text, output_path)
                    
                    result_dict = {
                        "model": model_name,
                        "line_id": line.id,
                        "role": line.role,
                        "emotion": line.emotion,
                        "difficulty": line.difficulty,
                        "text": line.text,
                        "run": run_label,
                        "is_warmup": is_warmup,
                        "audio_path": result.audio_path,
                        "generation_time": result.generation_time,
                        "ttfa": result.ttfa,
                        "sample_rate": result.sample_rate,
                        "audio_duration": result.audio_duration,
                        "rtf": result.rtf,
                        "error": None,
                    }
                    
                except Exception as e:
                    logger.error(f"Erreur {model_name} ligne {line.id} {run_label}: {e}")
                    result_dict = {
                        "model": model_name,
                        "line_id": line.id,
                        "role": line.role,
                        "emotion": line.emotion,
                        "difficulty": line.difficulty,
                        "text": line.text,
                        "run": run_label,
                        "is_warmup": is_warmup,
                        "audio_path": None,
                        "generation_time": None,
                        "ttfa": None,
                        "sample_rate": None,
                        "audio_duration": None,
                        "rtf": None,
                        "error": str(e),
                    }
                
                if not is_warmup:
                    line_results.append(result_dict)
                
                progress.advance(task)
            
            all_results.extend(line_results)
    
    model.teardown()
    logger.info(f"✅ {model_name} : {len(all_results)} résultats générés")
    return all_results


def run_evaluation(generation_results: list[dict]) -> list[dict]:
    """
    Évalue les audios générés : WER, MOS, latence.
    Enrichit les résultats avec les scores d'évaluation.
    """
    if not generation_results:
        return generation_results
    
    # ── WER ────────────────────────────────────────────────────────────────
    wer_analyzer = None
    try:
        from evaluation.wer_eval import WERAnalyzer
        console.print(f"[bold yellow]📝 Chargement du modèle ASR (Whisper {ASR_MODEL})...[/]")
        wer_analyzer = WERAnalyzer(model_size=ASR_MODEL, language=ASR_LANGUAGE, device=DEVICE)
        console.print("[bold green]✅ ASR prêt[/]")
    except Exception as e:
        logger.warning(f"WER non disponible : {e}")
    
    # ── MOS ────────────────────────────────────────────────────────────────
    mos_analyzer = None
    try:
        from evaluation.mos_eval import MOSAnalyzer
        console.print("[bold yellow]⭐ Chargement du modèle UTMOS...[/]")
        mos_analyzer = MOSAnalyzer(device="cpu")
        console.print("[bold green]✅ UTMOS prêt[/]")
    except Exception as e:
        logger.warning(f"MOS non disponible : {e}")
    
    # ── Évaluation par ligne ───────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold magenta]Évaluation[/]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Évaluation", total=len(generation_results))
        
        for result in generation_results:
            if result.get("error") or not result.get("audio_path"):
                result["wer"] = None
                result["cer"] = None
                result["hypothesis"] = None
                result["mos"] = None
                progress.advance(task)
                continue
            
            audio_path = result["audio_path"]
            reference_text = result["text"]
            
            # WER
            if wer_analyzer:
                try:
                    wer_result = wer_analyzer.compute_wer(reference_text, audio_path)
                    result["wer"] = wer_result["wer"]
                    result["cer"] = wer_result["cer"]
                    result["hypothesis"] = wer_result["hypothesis"]
                except Exception as e:
                    logger.warning(f"WER échoué pour {audio_path}: {e}")
                    result["wer"] = None
                    result["cer"] = None
                    result["hypothesis"] = None
            else:
                result["wer"] = None
                result["cer"] = None
                result["hypothesis"] = None
            
            # MOS
            if mos_analyzer:
                try:
                    result["mos"] = mos_analyzer.predict_mos(audio_path)
                except Exception as e:
                    logger.warning(f"MOS échoué pour {audio_path}: {e}")
                    result["mos"] = None
            else:
                result["mos"] = None
            
            progress.advance(task)
    
    return generation_results


def aggregate_results(all_results: list[dict]) -> list[dict]:
    """
    Agrège les résultats par modèle pour le rapport final.
    """
    from evaluation.latency_eval import LatencyAnalyzer
    
    models = {}
    for r in all_results:
        model = r["model"]
        if model not in models:
            models[model] = []
        models[model].append(r)
    
    aggregated = []
    for model_name, results in models.items():
        valid = [r for r in results if not r.get("error")]
        if not valid:
            continue
        
        # WER / CER
        wers = [r["wer"] for r in valid if r.get("wer") is not None]
        cers = [r["cer"] for r in valid if r.get("cer") is not None]
        
        # MOS
        moss = [r["mos"] for r in valid if r.get("mos") is not None]
        
        # Latence
        gen_times = [r["generation_time"] for r in valid if r.get("generation_time")]
        ttfas = [r["ttfa"] for r in valid if r.get("ttfa")]
        rtfs = [r["rtf"] for r in valid if r.get("rtf")]
        
        # Par difficulté
        def avg_by_difficulty(results, metric):
            by_diff = {}
            for diff in ["easy", "medium", "hard"]:
                vals = [r[metric] for r in results 
                        if r.get("difficulty") == diff and r.get(metric) is not None]
                by_diff[diff] = sum(vals) / len(vals) if vals else None
            return by_diff
        
        agg = {
            "model": model_name,
            "num_lines": len(set(r["line_id"] for r in valid)),
            "num_results": len(valid),
            "avg_wer": sum(wers) / len(wers) if wers else None,
            "avg_cer": sum(cers) / len(cers) if cers else None,
            "avg_mos": sum(moss) / len(moss) if moss else None,
            "wer_by_difficulty": avg_by_difficulty(valid, "wer"),
            "mos_by_difficulty": avg_by_difficulty(valid, "mos"),
            "gen_time_stats": LatencyAnalyzer.compute_stats(gen_times) if gen_times else None,
            "ttfa_stats": LatencyAnalyzer.compute_stats(ttfas) if ttfas else None,
            "rtf_stats": LatencyAnalyzer.compute_stats(rtfs) if rtfs else None,
            "line_results": results,
        }
        aggregated.append(agg)
    
    return aggregated


def display_summary(aggregated: list[dict]):
    """Affiche un résumé dans la console."""
    table = Table(
        title="🏆 Résultats du Benchmark TTS",
        show_lines=True,
        title_style="bold white on blue",
    )
    table.add_column("🏷️ Modèle", style="cyan bold", min_width=12)
    table.add_column("📝 WER (%)", justify="center", style="yellow")
    table.add_column("🔤 CER (%)", justify="center", style="yellow")
    table.add_column("⭐ MOS", justify="center", style="green")
    table.add_column("⏱️ RTF", justify="center", style="magenta")
    table.add_column("🚀 Gen (s)", justify="center", style="blue")
    table.add_column("📊 TTFA (s)", justify="center", style="blue")
    
    # Trier par MOS décroissant
    sorted_results = sorted(
        aggregated, 
        key=lambda x: x.get("avg_mos") or 0, 
        reverse=True
    )
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, agg in enumerate(sorted_results):
        medal = medals[i] if i < len(medals) else "  "
        name = f"{medal} {agg['model']}"
        
        wer = f"{agg['avg_wer']*100:.1f}" if agg.get("avg_wer") is not None else "N/A"
        cer = f"{agg['avg_cer']*100:.1f}" if agg.get("avg_cer") is not None else "N/A"
        mos = f"{agg['avg_mos']:.2f}" if agg.get("avg_mos") is not None else "N/A"
        
        rtf = "N/A"
        gen_time = "N/A"
        ttfa = "N/A"
        
        if agg.get("rtf_stats"):
            rtf = f"{agg['rtf_stats'].mean:.3f}"
        if agg.get("gen_time_stats"):
            gen_time = f"{agg['gen_time_stats'].mean:.2f}"
        if agg.get("ttfa_stats"):
            ttfa = f"{agg['ttfa_stats'].mean:.3f}"
        
        table.add_row(name, wer, cer, mos, rtf, gen_time, ttfa)
    
    console.print()
    console.print(table)
    console.print()


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🎤 Benchmark TTS — Évaluation de modèles sur le français",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--models", nargs="+", default=None,
        help=f"Modèles à tester (défaut: {DEFAULT_MODELS}). Choix: {AVAILABLE_MODELS}",
    )
    parser.add_argument(
        "--runs", type=int, default=NUM_RUNS,
        help=f"Nombre de runs par ligne (défaut: {NUM_RUNS})",
    )
    parser.add_argument(
        "--warmup", type=int, default=NUM_WARMUP,
        help=f"Runs d'échauffement (défaut: {NUM_WARMUP})",
    )
    parser.add_argument(
        "--lines", type=str, default="all",
        help="Lignes à tester : 'all', '1-5', '1,3,7' (défaut: all)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Lister les modèles disponibles",
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Générer audio sans évaluer (WER/MOS)",
    )
    parser.add_argument(
        "--skip-wer", action="store_true",
        help="Passer l'évaluation WER (Whisper est lourd)",
    )
    parser.add_argument(
        "--skip-mos", action="store_true",
        help="Passer l'évaluation MOS (UTMOS)",
    )
    
    args = parser.parse_args()
    
    # ── Bannière ───────────────────────────────────────────────────────────
    console.print(Panel.fit(
        "[bold white]🎤 TTS Benchmark[/] — [dim]Évaluation comparative FR[/]\n"
        f"[dim]Device: {DEVICE} │ Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}[/]",
        border_style="blue",
    ))
    
    if args.list:
        list_available_models()
        return
    
    # ── Sélection des modèles ──────────────────────────────────────────────
    model_names = args.models or DEFAULT_MODELS
    
    # ── Sélection des lignes ───────────────────────────────────────────────
    line_ids = parse_line_range(args.lines)
    lines = [line for line in DIALOGUE if line.id in line_ids]
    
    console.print(f"[bold]Modèles :[/] {', '.join(model_names)}")
    console.print(f"[bold]Lignes  :[/] {len(lines)} répliques (IDs: {line_ids[:5]}{'...' if len(line_ids) > 5 else ''})")
    console.print(f"[bold]Runs    :[/] {args.runs} (+ {args.warmup} warmup)")
    console.print()
    
    # ── Génération ─────────────────────────────────────────────────────────
    all_results = []
    
    for model_name in model_names:
        console.print(f"\n[bold blue]{'═' * 60}[/]")
        console.print(f"[bold blue]  🔊 Modèle : {model_name}[/]")
        console.print(f"[bold blue]{'═' * 60}[/]")
        
        results = run_generation(
            model_name=model_name,
            lines=lines,
            num_runs=args.runs,
            num_warmup=args.warmup,
        )
        all_results.extend(results)
    
    if not all_results:
        console.print("[bold red]❌ Aucun résultat généré. Vérifiez l'installation des modèles.[/]")
        return
    
    # ── Évaluation ─────────────────────────────────────────────────────────
    if not args.skip_eval:
        console.print(f"\n[bold magenta]{'═' * 60}[/]")
        console.print(f"[bold magenta]  📊 Évaluation[/]")
        console.print(f"[bold magenta]{'═' * 60}[/]\n")
        
        # Temporarily disable WER/MOS if requested
        if args.skip_wer:
            for r in all_results:
                r["wer"] = None
                r["cer"] = None
                r["hypothesis"] = None
        
        if args.skip_mos:
            for r in all_results:
                r["mos"] = None
        
        if not args.skip_wer or not args.skip_mos:
            all_results = run_evaluation(all_results)
        
    else:
        for r in all_results:
            r["wer"] = None
            r["cer"] = None
            r["hypothesis"] = None
            r["mos"] = None
    
    # ── Agrégation et rapport ──────────────────────────────────────────────
    console.print(f"\n[bold green]{'═' * 60}[/]")
    console.print(f"[bold green]  📋 Rapport[/]")
    console.print(f"[bold green]{'═' * 60}[/]\n")
    
    aggregated = aggregate_results(all_results)
    display_summary(aggregated)
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON brut
    json_path = RESULTS_DIR / f"benchmark_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        from evaluation.latency_eval import LatencyStats
        
        def _serialize(obj):
            """Custom serializer for non-standard types."""
            if isinstance(obj, LatencyStats):
                return obj.to_dict()
            return str(obj)
        
        json_safe = []
        for agg in aggregated:
            safe = {}
            for k, v in agg.items():
                if k == "line_results":
                    safe[k] = [{lk: lv for lk, lv in lr.items()} for lr in v]
                elif isinstance(v, LatencyStats):
                    safe[k] = v.to_dict()
                else:
                    safe[k] = v
            json_safe.append(safe)
        json.dump(json_safe, f, ensure_ascii=False, indent=2, default=_serialize)
    
    console.print(f"[dim]📁 Résultats JSON : {json_path}[/]")
    
    # Rapport Markdown
    try:
        from evaluation.report import ReportGenerator, ModelBenchmarkResult
        from evaluation.latency_eval import LatencyStats
        report_gen = ReportGenerator(RESULTS_DIR)
        
        # Convertir les dicts agrégés en ModelBenchmarkResult
        benchmark_results = []
        for agg in aggregated:
            mbr = ModelBenchmarkResult(
                model_name=agg["model"],
                tier="local",
                num_lines=agg["num_lines"],
                num_runs=agg["num_results"],
                avg_wer=agg.get("avg_wer") or 0.0,
                avg_cer=agg.get("avg_cer") or 0.0,
                wer_by_difficulty=agg.get("wer_by_difficulty", {}),
                avg_mos=agg.get("avg_mos") or 0.0,
                mos_by_difficulty=agg.get("mos_by_difficulty", {}),
                generation_time=agg.get("gen_time_stats"),
                ttfa=agg.get("ttfa_stats"),
                rtf=agg.get("rtf_stats"),
                line_results=agg.get("line_results", []),
            )
            benchmark_results.append(mbr)
        
        md_path, _ = report_gen.save_report(benchmark_results)
        console.print(f"[dim]📄 Rapport MD    : {md_path}[/]")
    except Exception as e:
        logger.warning(f"Génération du rapport MD échouée : {e}")
    
    console.print("\n[bold green]✅ Benchmark terminé ![/]\n")


if __name__ == "__main__":
    main()
