#!/usr/bin/env python3
"""
Générateur de rapport complet des transcriptions obtenues pour le benchmark STT.
"""

import json
from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
RESULTS_DIR = PROJECT_ROOT / "results"

def main():
    # Trouver le dernier fichier JSON stt_results_*.json
    json_files = sorted(list(RESULTS_DIR.glob("stt_results_*.json")))
    if not json_files:
        print("Aucun fichier de résultats STT JSON trouvé dans results/")
        return

    latest_json = json_files[-1]
    print(f"Chargement des résultats depuis : {latest_json.name}")

    with open(latest_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    detailed_results = data.get("detailed_results", [])
    if not detailed_results:
        print("Aucun résultat détaillé trouvé dans le JSON.")
        return

    # Organiser les données par line_id, puis par tts_model, puis par stt_model
    organized = {}
    for r in detailed_results:
        lid = r["line_id"]
        ref = r["reference"]
        tts = r["tts_model"]
        stt = r["stt_model"]
        hyp = r["hypothesis"] or "(Transcription vide / Erreur)"
        wer = r["wer"]
        cer = r["cer"]
        error = r["error"]

        if lid not in organized:
            organized[lid] = {
                "reference": ref,
                "tts_models": {}
            }

        if tts not in organized[lid]["tts_models"]:
            organized[lid]["tts_models"][tts] = {}

        organized[lid]["tts_models"][tts][stt] = {
            "hypothesis": hyp,
            "wer": wer,
            "cer": cer,
            "error": error
        }

    # Générer le rapport Markdown
    report_path = RESULTS_DIR / "all_transcriptions_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 📄 Rapport Complet des Transcriptions du Benchmark STT\n\n")
        f.write(f"Ce rapport contient **l'intégralité des transcriptions réelles** obtenues pour chaque réplique de dialogue, pour tous les moteurs de synthèse vocale (TTS) et modèles de reconnaissance (STT).\n\n")
        f.write(f"Fichier de données source : `{latest_json.name}`\n\n")
        f.write("---\n\n")

        # Trier par ID de ligne
        for lid in sorted(organized.keys()):
            line_data = organized[lid]
            ref = line_data["reference"]
            
            f.write(f"## 💬 Réplique {lid:02d}\n")
            f.write(f"> **Référence (Texte original)** : `{ref}`\n\n")

            # Trier les moteurs TTS par nom
            for tts in sorted(line_data["tts_models"].keys()):
                f.write(f"### 🔊 Voix générée par : **{tts}**\n")
                
                # Lister les transcriptions des modèles STT
                stt_data = line_data["tts_models"][tts]
                for stt in sorted(stt_data.keys()):
                    info = stt_data[stt]
                    hyp = info["hypothesis"]
                    
                    if info["error"]:
                        f.write(f"- ❌ **{stt}** : *Erreur d'API / Transcription échouée ({info['error']})*\n")
                    else:
                        wer_pct = f"{info['wer'] * 100:.1f}%" if info["wer"] is not None else "N/A"
                        cer_pct = f"{info['cer'] * 100:.1f}%" if info["cer"] is not None else "N/A"
                        f.write(f"- **{stt}** : `{hyp}` *(WER: {wer_pct} │ CER: {cer_pct})*\n")
                
                f.write("\n")
            
            f.write("---\n\n")

    print(f"Rapport Markdown généré avec succès : {report_path.name}")

if __name__ == "__main__":
    main()
