#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           STT Benchmark — Script Principal                   ║
║   Évaluation comparative de modèles STT/ASR en français      ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python run_stt_benchmark.py                          # Modèles STT par défaut
    python run_stt_benchmark.py --models mistral cohere  # Modèles spécifiques
    python run_stt_benchmark.py --tts-models kokoro      # Restreindre à un moteur TTS
    python run_stt_benchmark.py --list                   # Lister les modèles STT disponibles
"""

import argparse
import json
import logging
import sys
import time
import unicodedata
import re
from datetime import datetime
from pathlib import Path

import jiwer
import soundfile as sf
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
    OUTPUTS_DIR, RESULTS_DIR, DEVICE,
    AVAILABLE_STT_MODELS, DEFAULT_STT_MODELS
)
from dialogue import DIALOGUE

console = Console()

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("stt_benchmark")

# Punctuation to strip during normalisation
_PUNCT_RE = re.compile(r"[\.,:;!\?\"\'\—\–\-\(\)\[\]\{\}«»…]+")


def normalize_text(text: str) -> str:
    """Normalise le texte pour un calcul de WER/CER équitable."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def list_available_stt_models():
    """Affiche les modèles STT disponibles et leur statut."""
    from stt_models import STT_CLASSES, get_stt_model
    
    table = Table(title="🎤 Modèles STT / ASR Disponibles", show_lines=True)
    table.add_column("Nom", style="cyan bold")
    table.add_column("Description", style="white")
    table.add_column("Tier", style="magenta")
    table.add_column("Disponible", style="green")
    
    # Lister les APIs
    for name, model_cls in STT_CLASSES.items():
        model = model_cls()
        available = "✅" if model.is_available() else "❌"
        table.add_row(name, model.description, model.tier, available)
        
    # Lister les tailles Whisper locales
    for size in ["base", "large-v3-turbo", "large-v3"]:
        name = f"whisper-local-{size}"
        model = get_stt_model(name)
        available = "✅" if model.is_available() else "❌"
        table.add_row(name, model.description, model.tier, available)
    
    console.print(table)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="STT Benchmark — Évaluation comparative FR")
    parser.add_argument(
        "--models", nargs="+", default=None,
        help=f"Modèles STT à tester (défaut: {DEFAULT_STT_MODELS}). Choix: {AVAILABLE_STT_MODELS}",
    )
    parser.add_argument(
        "--tts-models", nargs="+", default=None,
        help="Moteurs TTS dont on souhaite évaluer les audios (défaut: tous les moteurs trouvés dans outputs/)",
    )
    parser.add_argument(
        "--lines", type=str, default="all",
        help="Lignes à tester : 'all', '1-5', '1,3,7' (défaut: all)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Lister les modèles STT disponibles",
    )
    
    args = parser.parse_args()
    
    # ── Bannière ───────────────────────────────────────────────────────────
    console.print(Panel.fit(
        "[bold white]🎤 STT / ASR Benchmark[/] — [dim]Évaluation comparative FR[/]\n"
        f"[dim]Device: {DEVICE} │ Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}[/]",
        border_style="cyan",
    ))
    
    if args.list:
        list_available_stt_models()
        return
        
    # ── Sélection des modèles STT ──────────────────────────────────────────
    stt_names = args.models or DEFAULT_STT_MODELS
    
    # ── Sélection des moteurs TTS ──────────────────────────────────────────
    if args.tts_models:
        tts_names = args.tts_models
    else:
        # Scanner le répertoire outputs/ pour voir quels TTS ont des fichiers
        if not OUTPUTS_DIR.exists():
            console.print("[bold red]❌ Le répertoire d'outputs audio n'existe pas. Veuillez lancer le benchmark TTS d'abord.[/]")
            return
        tts_names = [d.name for d in OUTPUTS_DIR.iterdir() if d.is_dir() and d.name != "__pycache__"]
        
    if not tts_names:
        console.print("[bold red]❌ Aucun répertoire audio trouvé dans outputs/. Veuillez générer les audios avec le benchmark TTS d'abord.[/]")
        return
        
    # ── Sélection des lignes de dialogue ───────────────────────────────────
    line_ids = parse_line_range(args.lines)
    lines_map = {line.id: line for line in DIALOGUE if line.id in line_ids}
    
    console.print(f"[bold]Modèles STT :[/] {', '.join(stt_names)}")
    console.print(f"[bold]Moteurs TTS :[/] {', '.join(tts_names)}")
    console.print(f"[bold]Lignes      :[/] {len(lines_map)} répliques (IDs: {sorted(list(lines_map.keys()))[:5]}{'...' if len(lines_map) > 5 else ''})")
    console.print()
    
    # ── Chargement des modèles STT ─────────────────────────────────────────
    stt_models = {}
    for stt_name in stt_names:
        from stt_models import get_stt_model
        try:
            model = get_stt_model(stt_name)
            if model.is_available():
                stt_models[stt_name] = model
            else:
                console.print(f"[yellow]⚠️ Modèle STT '{stt_name}' non disponible (dépendances/clés manquantes) — Ignoré[/]")
        except Exception as e:
            console.print(f"[red]❌ Erreur lors du chargement de '{stt_name}' : {e} — Ignoré[/]")
            
    if not stt_models:
        console.print("[bold red]❌ Aucun modèle STT disponible pour l'évaluation.[/]")
        return
        
    # ── Collecte des fichiers audio existants ──────────────────────────────
    eval_tasks = []  # Liste de tuples (stt_name, tts_name, line_id, audio_path)
    for tts_name in tts_names:
        tts_dir = OUTPUTS_DIR / tts_name
        if not tts_dir.exists():
            continue
        for line_id in lines_map.keys():
            # Chercher le fichier WAV de la réplique
            audio_path = tts_dir / f"line_{line_id:02d}_run_0.wav"
            if audio_path.exists():
                for stt_name in stt_models.keys():
                    eval_tasks.append((stt_name, tts_name, line_id, audio_path))
                    
    if not eval_tasks:
        console.print("[bold red]❌ Aucun fichier audio correspondant aux critères n'a été trouvé dans outputs/.[/]")
        return
        
    console.print(f"[bold green]▶ Lancement de {len(eval_tasks)} tâches de transcription...[/]\n")
    
    # Initialiser les modèles STT (setup)
    for stt_name, model in stt_models.items():
        console.print(f"[dim]Initialisation de {stt_name}...[/]")
        model.setup()
        
    # Exécution des transcriptions
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold magenta]ASR Transcription[/]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Transcription", total=len(eval_tasks))
        
        for stt_name, tts_name, line_id, audio_path in eval_tasks:
            model = stt_models[stt_name]
            line = lines_map[line_id]
            
            # Charger les infos de l'audio
            try:
                audio_info = sf.info(str(audio_path))
                duration = audio_info.duration
                sample_rate = audio_info.samplerate
            except Exception as e:
                logger.warning(f"Impossible de lire les infos de {audio_path}: {e}")
                duration = 0.0
                sample_rate = 0
            
            # Transcrire
            t_res = model.transcribe(str(audio_path))
            
            # WER / CER
            wer = None
            cer = None
            norm_ref = normalize_text(line.text)
            norm_hyp = ""
            
            if not t_res.error and t_res.text:
                norm_hyp = normalize_text(t_res.text)
                try:
                    # Calculer le WER
                    wer = jiwer.wer(norm_ref, norm_hyp)
                    cer = jiwer.cer(norm_ref, norm_hyp)
                except Exception as e:
                    logger.warning(f"Erreur de calcul WER/CER : {e}")
            
            rtf = t_res.latency / duration if duration > 0 else 0.0
            
            result_dict = {
                "stt_model": stt_name,
                "tts_model": tts_name,
                "line_id": line_id,
                "role": line.role,
                "emotion": line.emotion,
                "difficulty": line.difficulty,
                "reference": line.text,
                "hypothesis": t_res.text,
                "normalized_reference": norm_ref,
                "normalized_hypothesis": norm_hyp,
                "wer": wer,
                "cer": cer,
                "latency": t_res.latency,
                "duration": duration,
                "rtf": rtf,
                "error": t_res.error
            }
            results.append(result_dict)
            progress.advance(task_id)
            
    # Libérer les modèles
    for stt_name, model in stt_models.items():
        model.teardown()
        
    # ── Agrégation des résultats ──────────────────────────────────────────
    # 1. Agrégation par modèle STT (Overall ASR performance)
    stt_stats = {}
    for r in results:
        stt = r["stt_model"]
        if stt not in stt_stats:
            stt_stats[stt] = {"wers": [], "cers": [], "latencies": [], "rtfs": [], "errors": 0, "total": 0}
        
        stt_stats[stt]["total"] += 1
        if r["error"]:
            stt_stats[stt]["errors"] += 1
        else:
            if r["wer"] is not None:
                stt_stats[stt]["wers"].append(r["wer"])
                stt_stats[stt]["cers"].append(r["cer"])
            stt_stats[stt]["latencies"].append(r["latency"])
            stt_stats[stt]["rtfs"].append(r["rtf"])
            
    stt_aggregated = []
    for stt, stats in stt_stats.items():
        valid_count = len(stats["wers"])
        stt_aggregated.append({
            "stt_model": stt,
            "avg_wer": sum(stats["wers"]) / valid_count if valid_count > 0 else None,
            "avg_cer": sum(stats["cers"]) / valid_count if valid_count > 0 else None,
            "avg_latency": sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else None,
            "avg_rtf": sum(stats["rtfs"]) / len(stats["rtfs"]) if stats["rtfs"] else None,
            "success_rate": (stats["total"] - stats["errors"]) / stats["total"] if stats["total"] > 0 else 0.0
        })
        
    # 2. Agrégation par moteur TTS (Intelligibilité relative)
    tts_stats = {}
    for r in results:
        if r["error"] or r["wer"] is None:
            continue
        tts = r["tts_model"]
        if tts not in tts_stats:
            tts_stats[tts] = {"wers": [], "cers": []}
        tts_stats[tts]["wers"].append(r["wer"])
        tts_stats[tts]["cers"].append(r["cer"])
        
    tts_aggregated = []
    for tts, stats in tts_stats.items():
        tts_aggregated.append({
            "tts_model": tts,
            "avg_wer": sum(stats["wers"]) / len(stats["wers"]) if stats["wers"] else None,
            "avg_cer": sum(stats["cers"]) / len(stats["cers"]) if stats["cers"] else None,
        })
        
    # Sort aggregates
    stt_aggregated.sort(key=lambda x: x["avg_wer"] if x["avg_wer"] is not None else 999.0)
    tts_aggregated.sort(key=lambda x: x["avg_wer"] if x["avg_wer"] is not None else 999.0)
    
    # ── Affichage console ──────────────────────────────────────────────────
    # Table 1: STT Rankings
    stt_table = Table(title="🏆 Classement des modèles STT / ASR", show_lines=True)
    stt_table.add_column("Rang", style="yellow bold")
    stt_table.add_column("Modèle STT", style="cyan bold")
    stt_table.add_column("WER (%) ⬇️", style="white")
    stt_table.add_column("CER (%) ⬇️", style="white")
    stt_table.add_column("Latence Moy. (s) ⬇️", style="white")
    stt_table.add_column("RTF Moy. ⬇️", style="white")
    stt_table.add_column("Succès", style="green")
    
    for idx, s in enumerate(stt_aggregated):
        wer_str = f"{s['avg_wer']*100:.2f}%" if s['avg_wer'] is not None else "N/A"
        cer_str = f"{s['avg_cer']*100:.2f}%" if s['avg_cer'] is not None else "N/A"
        lat_str = f"{s['avg_latency']:.3f} s" if s['avg_latency'] is not None else "N/A"
        rtf_str = f"{s['avg_rtf']:.3f}" if s['avg_rtf'] is not None else "N/A"
        succ_str = f"{s['success_rate']*100:.1f}%"
        stt_table.add_row(
            str(idx + 1), s["stt_model"], wer_str, cer_str, lat_str, rtf_str, succ_str
        )
    console.print(stt_table)
    console.print()
    
    # Table 2: TTS Intelligibility
    tts_table = Table(title="🔊 Intelligibilité des moteurs TTS (Mesurée par WER)", show_lines=True)
    tts_table.add_column("Rang", style="yellow bold")
    tts_table.add_column("Moteur TTS", style="cyan bold")
    tts_table.add_column("WER Moyen (%) ⬇️", style="white")
    tts_table.add_column("CER Moyen (%) ⬇️", style="white")
    
    for idx, t in enumerate(tts_aggregated):
        wer_str = f"{t['avg_wer']*100:.2f}%" if t['avg_wer'] is not None else "N/A"
        cer_str = f"{t['avg_cer']*100:.2f}%" if t['avg_cer'] is not None else "N/A"
        tts_table.add_row(
            str(idx + 1), t["tts_model"], wer_str, cer_str
        )
    console.print(tts_table)
    console.print()
    
    # ── Sauvegarde des rapports ────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # JSON brut
    json_path = RESULTS_DIR / f"stt_results_{timestamp}.json"
    raw_output = {
        "generated_at": datetime.now().isoformat(),
        "stt_performance": stt_aggregated,
        "tts_intelligibility": tts_aggregated,
        "detailed_results": results
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw_output, f, ensure_ascii=False, indent=2)
    console.print(f"[dim]📁 Résultats JSON : {json_path}[/]")
    
    # Rapport Markdown
    md_path = RESULTS_DIR / f"stt_report_{timestamp}.md"
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 🎤 STT / ASR Benchmark — Rapport d'Évaluation en Français\n\n")
        f.write(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 🏆 Classement Général des Modèles STT / ASR\n\n")
        f.write("| Rang | Modèle STT | WER (%) | CER (%) | Latence Moy. (s) | RTF Moy. | Taux de Succès |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for idx, s in enumerate(stt_aggregated):
            wer_str = f"{s['avg_wer']*100:.2f}%" if s['avg_wer'] is not None else "N/A"
            cer_str = f"{s['avg_cer']*100:.2f}%" if s['avg_cer'] is not None else "N/A"
            lat_str = f"{s['avg_latency']:.3f} s" if s['avg_latency'] is not None else "N/A"
            rtf_str = f"{s['avg_rtf']:.3f}" if s['avg_rtf'] is not None else "N/A"
            succ_str = f"{s['success_rate']*100:.1f}%"
            f.write(f"| {idx+1} | **{s['stt_model']}** | {wer_str} | {cer_str} | {lat_str} | {rtf_str} | {succ_str} |\n")
            
        f.write("\n## 🔊 Classement de l'Intelligibilité des Moteurs TTS\n\n")
        f.write("> [!NOTE]\n")
        f.write("> Cette table indique le **WER moyen** subi par les audios de chaque moteur TTS. Plus le WER est bas, plus la voix générée est nette, claire et facilement intelligible pour les modèles de reconnaissance vocale.\n\n")
        f.write("| Rang | Moteur TTS | WER Moyen (%) | CER Moyen (%) |\n")
        f.write("| :---: | :--- | :---: | :---: |\n")
        for idx, t in enumerate(tts_aggregated):
            wer_str = f"{t['avg_wer']*100:.2f}%" if t['avg_wer'] is not None else "N/A"
            cer_str = f"{t['avg_cer']*100:.2f}%" if t['avg_cer'] is not None else "N/A"
            f.write(f"| {idx+1} | **{t['tts_model']}** | {wer_str} | {cer_str} |\n")
            
        f.write("\n## 🔄 Évaluation Croisée Détaillée (Couple STT ✕ TTS)\n\n")
        
        # Construire une matrice pivot (rows = STT, cols = TTS, val = WER)
        f.write("### Matrice WER (%) par Couple\n\n")
        f.write("| Modèle STT | " + " | ".join(tts_names) + " |\n")
        f.write("| :--- | " + " | ".join([":---:"] * len(tts_names)) + " |\n")
        
        # Calculer le WER par couple
        couple_wer = {}
        for r in results:
            if r["error"] or r["wer"] is None:
                continue
            key = (r["stt_model"], r["tts_model"])
            if key not in couple_wer:
                couple_wer[key] = []
            couple_wer[key].append(r["wer"])
            
        for stt in stt_names:
            if stt not in stt_models:
                continue
            row_parts = [f"**{stt}**"]
            for tts in tts_names:
                wers = couple_wer.get((stt, tts), [])
                if wers:
                    avg_c_wer = sum(wers) / len(wers)
                    row_parts.append(f"{avg_c_wer*100:.2f}%")
                else:
                    row_parts.append("N/A")
            f.write("| " + " | ".join(row_parts) + " |\n")
            
        f.write("\n## 📄 Transcriptions Détaillées (Exemples)\n\n")
        # Donner 3 exemples de phrases avec les transcriptions de chaque modèle
        sample_line_ids = sorted(list(lines_map.keys()))[:3]
        for lid in sample_line_ids:
            line = lines_map[lid]
            f.write(f"### Réplique {lid} (Difficulté : {line.difficulty})\n")
            f.write(f"*   **Référence** : `{line.text}`\n")
            for stt in stt_names:
                # Trouver la transcription de stt pour cette réplique sur un des TTS (ex. edgetts)
                for tts in tts_names:
                    # Trouver le résultat
                    match = next((res for res in results if res["stt_model"] == stt and res["tts_model"] == tts and res["line_id"] == lid), None)
                    if match and not match["error"] and match["hypothesis"]:
                        f.write(f"*   **{stt}** (sur audio {tts}) : `{match['hypothesis']}`\n")
                        break
            f.write("\n")
            
    console.print(f"[dim]📄 Rapport MD    : {md_path}[/]")
    console.print("\n[bold green]✅ Benchmark STT terminé ![/]\n")


if __name__ == "__main__":
    main()
