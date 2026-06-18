#!/usr/bin/env python3
"""
Script de génération d'audios de discussion complets.
Pour chaque modèle TTS, synthétise les 21 répliques du dialogue bancaire en alternant
les voix/styles entre l'Agent (conseillère) et le Client (mécontent), puis fusionne
les fichiers avec un silence de 0.8 seconde pour créer l'audio final.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa

# Force UTF-8 encoding on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ajouter le chemin du projet
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import OUTPUTS_DIR, DEVICE
from dialogue import DIALOGUE, DialogueLine
from models import get_model, list_available_models

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("discussion_generator")


def load_audio_mono_24k(path: str) -> np.ndarray:
    """Charge un fichier audio, le convertit en mono et le rééchantillonne à 24kHz si nécessaire."""
    data, sr = sf.read(path)
    # Convertir en mono si stéréo
    if len(data.shape) > 1:
        if data.shape[1] > 1:
            data = np.mean(data, axis=1)
        else:
            data = data.flatten()
    # Rééchantillonner à 24000 Hz
    if sr != 24000:
        data = librosa.resample(data, orig_sr=sr, target_sr=24000)
    return data


def generate_f5tts_references():
    """Génère des fichiers de référence de voix masculines et féminines via EdgeTTS pour F5-TTS."""
    ref_dir = OUTPUTS_DIR / "reference_discussion"
    ref_dir.mkdir(parents=True, exist_ok=True)
    
    ref_female_wav = ref_dir / "ref_female.wav"
    ref_male_wav = ref_dir / "ref_male.wav"
    
    # Textes de référence
    txt_female = "Bonjour, bienvenue chez Atlas Bank. Comment puis-je vous aider ?"
    txt_male = "Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant."
    
    import edge_tts
    import asyncio
    
    async def _synth(text, voice, output_wav):
        mp3_path = output_wav.with_suffix(".mp3")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(mp3_path))
        # Convertir en WAV 24kHz mono
        data, sr = librosa.load(str(mp3_path), sr=24000, mono=True)
        sf.write(str(output_wav), data, sr)
        mp3_path.unlink()
        
    if not ref_female_wav.exists():
        logger.info("Génération de la référence F5-TTS féminine via Edge-TTS...")
        asyncio.run(_synth(txt_female, "fr-FR-DeniseNeural", ref_female_wav))
        
    if not ref_male_wav.exists():
        logger.info("Génération de la référence F5-TTS masculine via Edge-TTS...")
        asyncio.run(_synth(txt_male, "fr-FR-HenriNeural", ref_male_wav))
        
    return str(ref_female_wav), txt_female, str(ref_male_wav), txt_male


def prepare_user_voice_reference():
    """Prépare le fichier audio de l'utilisateur (my_voice.ogg) pour le clonage F5-TTS."""
    user_audio_ogg = PROJECT_ROOT / "my_voice.ogg"
    if not user_audio_ogg.exists():
        return None, None
        
    ref_dir = OUTPUTS_DIR / "reference_discussion"
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref_user_wav = ref_dir / "my_voice_ref.wav"
    
    # Transcription obtenue via Whisper local
    txt_user = "Bon, bon, dis, j'espère que vous allez bien, on vous permet de vous appeler parce que j'en ai besoin d'avoir d'aide, que j'ai des problèmes assez compliqués cette pensée, et j'espère que vous voir avoir votre aide, merci."
    
    # Convertir en WAV 24kHz mono
    logger.info("Traitement de la voix de l'utilisateur (my_voice.ogg) pour le clonage F5-TTS...")
    data, sr = librosa.load(str(user_audio_ogg), sr=24000, mono=True)
    sf.write(str(ref_user_wav), data, sr)
    
    return str(ref_user_wav), txt_user



def configure_model_for_role(model_name: str, model_instance, role: str, emotion: str, f5_refs: tuple = None):
    """Configure dynamiquement les paramètres de voix du modèle selon le rôle (agent / client)."""
    
    # 1. KOKORO
    if model_name == "kokoro":
        if role == "agent":
            model_instance.voice = "ff_siwis"
            model_instance.speed = 1.05
        else:
            model_instance.voice = "ff_siwis"
            model_instance.speed = 0.90

    # 2. MELOTTS
    elif model_name == "melo":
        if role == "agent":
            model_instance.speed = 1.05
        else:
            model_instance.speed = 0.90

    # 3. EDGE-TTS
    elif model_name == "edgetts":
        if role == "agent":
            model_instance.voice = "fr-FR-DeniseNeural"
        else:
            model_instance.voice = "fr-FR-HenriNeural"

    # 4. GTTS
    elif model_name == "gtts":
        if role == "agent":
            model_instance.tld = "fr"
        else:
            model_instance.tld = "ca"  # Accent québécois pour le client

    # 5. OPENAI
    elif model_name == "openai":
        if role == "agent":
            model_instance.voice = "nova"  # Féminin fluide
        else:
            model_instance.voice = "onyx"  # Masculin grave

    # 6. MISTRAL
    elif model_name == "mistral":
        # Mistral possède une seule voix française (Marie) mais avec des émotions
        if role == "agent":
            model_instance.voice = "fr_marie_neutral"
        else:
            # Le client s'énerve au fil de la discussion
            if emotion in ["colère", "furieux", "irrité"]:
                model_instance.voice = "fr_marie_angry"
            elif emotion in ["déterminé", "insistant"]:
                model_instance.voice = "fr_marie_excited"
            else:
                model_instance.voice = "fr_marie_sad"

    # 7. HUME
    elif model_name == "hume":
        # Hume supporte des IDs de voix précis
        if role == "agent":
            model_instance.voice_id = "9e1f9e4f-691a-4bb0-b87c-e306a4c838ef"  # Claire (Female)
        else:
            model_instance.voice_id = "f98af01b-9e56-4b90-884e-0644a250391c"  # Benjamin (Male)

    # 8. ELEVENLABS
    elif model_name == "elevenlabs":
        voices = getattr(model_instance, "available_voices", [])
        
        # Trouver la voix de la conseillère (Agent) : priorité Bella, Matilda, Sarah, sinon n'importe quelle voix féminine
        agent_voice = None
        for name_pref in ["Bella", "Matilda", "Sarah"]:
            for v in voices:
                if name_pref in v.get("name", ""):
                    agent_voice = v
                    break
            if agent_voice:
                break
        if not agent_voice:
            female_voices = [v for v in voices if v.get("labels", {}).get("gender", "").lower() == "female"]
            if female_voices:
                agent_voice = female_voices[0]

        # Trouver la voix du client (gronchon/fâché) : priorité Adam (ferme/dominant), Harry (guerrier féroce), Callum, sinon n'importe quel homme
        client_voice = None
        for name_pref in ["Adam", "Harry", "Callum"]:
            for v in voices:
                if name_pref in v.get("name", ""):
                    client_voice = v
                    break
            if client_voice:
                break
        if not client_voice:
            male_voices = [v for v in voices if v.get("labels", {}).get("gender", "").lower() == "male"]
            if male_voices:
                client_voice = male_voices[0]

        if role == "agent":
            if agent_voice:
                model_instance.voice_id = agent_voice["voice_id"]
                logger.debug("ElevenLabs Agent: choisi %s", agent_voice.get("name"))
            elif voices:
                model_instance.voice_id = voices[0]["voice_id"]
        else:
            if client_voice:
                model_instance.voice_id = client_voice["voice_id"]
                logger.debug("ElevenLabs Client: choisi %s", client_voice.get("name"))
            elif len(voices) >= 2:
                model_instance.voice_id = voices[1]["voice_id"]
            elif voices:
                model_instance.voice_id = voices[0]["voice_id"]

    # 9. F5-TTS
    elif model_name == "f5tts" and f5_refs:
        ref_female_wav, txt_female, ref_male_wav, txt_male = f5_refs
        if role == "agent":
            model_instance._ref_file = ref_female_wav
            model_instance._ref_text = txt_female
        else:
            model_instance._ref_file = ref_male_wav
            model_instance._ref_text = txt_male


def main():
    parser = argparse.ArgumentParser(description="Générateur de discussions complètes TTS")
    parser.add_argument(
        "--models", nargs="+", default=None,
        help="Modèles TTS à lancer (ex. kokoro melo edgetts gtts hume openai mistral f5tts)"
    )
    args = parser.parse_args()

    # Détection des modèles disponibles
    available = list_available_models()
    target_models = args.models or [m for m in available if m != "xtts"]  # XTTS exclu d'office
    
    # Filtrer par rapport à la disponibilité réelle
    target_models = [m for m in target_models if m in available]
    
    if not target_models:
        logger.error("Aucun modèle cible disponible pour la synthèse.")
        return

    logger.info("Modèles sélectionnés pour générer les discussions : %s", target_models)

    # Dossier de sortie final des discussions
    discussion_out_dir = OUTPUTS_DIR / "discussions"
    discussion_out_dir.mkdir(parents=True, exist_ok=True)

    # Préparer les références de clonage pour F5-TTS si nécessaire
    f5_refs = None
    if "f5tts" in target_models:
        try:
            user_ref_wav, user_ref_txt = prepare_user_voice_reference()
            default_female_wav, txt_female, default_male_wav, txt_male = generate_f5tts_references()
            if user_ref_wav:
                logger.info("Voix de l'utilisateur (clonée) détectée pour le Client !")
                f5_refs = (default_female_wav, txt_female, user_ref_wav, user_ref_txt)
            else:
                f5_refs = (default_female_wav, txt_female, default_male_wav, txt_male)
        except Exception as e:
            logger.exception("Impossible de préparer les références de voix F5-TTS : %s", e)

    # Lancer la génération pour chaque modèle
    for model_name in target_models:
        logger.info("═══ Début de la génération de la discussion complète : %s ═══", model_name)
        
        try:
            model = get_model(model_name)
            model.setup()
        except Exception as e:
            logger.exception("Échec du chargement/setup du modèle %s : %s", model_name, e)
            continue

        temp_wavs = []
        model_temp_dir = OUTPUTS_DIR / "temp_discussion" / model_name
        model_temp_dir.mkdir(parents=True, exist_ok=True)

        success = True
        try:
            # Synthétiser chaque réplique une par une avec la voix correspondante
            for idx, line in enumerate(DIALOGUE):
                logger.info("[%s] Synthèse de la réplique %d/%d (%s) : '%s'", 
                            model_name, line.id, len(DIALOGUE), line.role, line.text[:40] + "...")
                
                # Appliquer la voix associée au rôle
                configure_model_for_role(model_name, model, line.role, line.emotion, f5_refs)
                
                temp_output_wav = model_temp_dir / f"line_{line.id:02d}.wav"
                
                t_start = time.perf_counter()
                
                # Synthétiser avec retries pour les APIs (gérer le rate limit 429)
                # Synthétiser avec retries pour les APIs (gérer le rate limit 429)
                max_attempts = 5
                for attempt in range(1, max_attempts + 1):
                    try:
                        model.synthesize(line.text, str(temp_output_wav))
                        break
                    except Exception as e:
                        if ("429" in str(e) or "limit" in str(e).lower()) and attempt < max_attempts:
                            logger.warning("[%s] Rate limit (429) détecté. Attente de 60.0 secondes pour réinitialiser la fenêtre...", model_name)
                            time.sleep(60.0)
                        else:
                            if attempt == max_attempts:
                                raise
                            time.sleep(2.0)
                            
                # Proactif : pause pour éviter les rate limits sur les APIs cloud
                if getattr(model, "tier", "cpu") == "api":
                    time.sleep(2.0)
                            
                t_duration = time.perf_counter() - t_start
                logger.info("[%s] Ligne %d générée en %.2f s", model_name, line.id, t_duration)
                
                temp_wavs.append(str(temp_output_wav))

        except Exception as e:
            logger.exception("Erreur durant la synthèse de la discussion avec %s : %s", model_name, e)
            success = False
        finally:
            model.teardown()

        # Si toutes les répliques sont générées avec succès, on les concatène
        if success and temp_wavs:
            logger.info("[%s] Concaténation des répliques audio...", model_name)
            try:
                final_samples = []
                sample_rate = 24000
                pause_samples = np.zeros(int(sample_rate * 0.8))  # Pause de 0.8 seconde
                
                for i, path in enumerate(temp_wavs):
                    # Charger l'audio de la réplique (converti en 24kHz mono)
                    data = load_audio_mono_24k(path)
                    final_samples.extend(data)
                    
                    # Ajouter une pause après chaque réplique sauf la dernière
                    if i < len(temp_wavs) - 1:
                        final_samples.extend(pause_samples)

                # Écrire l'audio de discussion final
                output_discussion_path = discussion_out_dir / f"discussion_{model_name}.wav"
                sf.write(str(output_discussion_path), np.array(final_samples, dtype=np.float32), sample_rate)
                logger.info("✅ Discussion complète sauvegardée avec succès : %s", output_discussion_path)
                logger.info("Taille du fichier : %d octets", output_discussion_path.stat().st_size)

                # Nettoyer les WAVs temporaires
                for path in temp_wavs:
                    try:
                        Path(path).unlink()
                    except OSError:
                        pass
                try:
                    model_temp_dir.rmdir()
                except OSError:
                    pass

            except Exception as e:
                logger.exception("Échec de la concaténation de la discussion %s : %s", model_name, e)


if __name__ == "__main__":
    main()
