"""
Configuration globale du benchmark TTS.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# ── Rechargement du PATH Windows pour détecter FFmpeg (Gyan.FFmpeg.Shared) ──────
if sys.platform.startswith("win"):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            user_path, _ = winreg.QueryValueEx(key, "Path")
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\Environment") as key:
            system_path, _ = winreg.QueryValueEx(key, "Path")
        os.environ["PATH"] = f"{system_path};{user_path}"
    except Exception:
        pass

# ── espeak-ng (requis par Kokoro pour le phonemizer français) ──────────────────
ESPEAK_NG_DIR = r"C:\Program Files\eSpeak NG"
if os.path.isdir(ESPEAK_NG_DIR) and ESPEAK_NG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ESPEAK_NG_DIR + ";" + os.environ.get("PATH", "")


# ── Chemins ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Device ─────────────────────────────────────────────────────────────────────
def get_device() -> str:
    """Détecte le meilleur device disponible (cuda > cpu)."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        # Intel XPU support (Intel Extension for PyTorch)
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            return "xpu"
    except ImportError:
        pass
    return "cpu"

DEVICE = get_device()

# ── Clés API ───────────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
HUME_API_KEY = os.getenv("HUME_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# ── Paramètres ASR (pour WER) ─────────────────────────────────────────────────
ASR_MODEL = "base"  # Whisper model pour la transcription du benchmark TTS
ASR_LANGUAGE = "fr"

# ── Paramètres benchmark ──────────────────────────────────────────────────────
DEFAULT_SAMPLE_RATE = 24000  # Hz
NUM_RUNS = 3                 # Nombre de runs pour moyenner les mesures
NUM_WARMUP = 1               # Runs d'échauffement (non comptés)

# ── Modèles disponibles ───────────────────────────────────────────────────────
AVAILABLE_MODELS = [
    "kokoro",
    "melo",
    "xtts",
    "f5tts",
    "elevenlabs",
    "gtts",
    "edgetts",
    "openai",
    "hume",
    "mistral",
]

# Sous-ensemble par défaut (modèles légers CPU / API gratuites)
DEFAULT_MODELS = ["kokoro", "melo", "gtts", "edgetts"]

# ── Modèles STT disponibles ───────────────────────────────────────────────────
AVAILABLE_STT_MODELS = [
    "elevenlabs",
    "mistral",
    "cohere",
    "openai",
    "whisper-local-base",
    "whisper-local-large-turbo",
    "whisper-local-large",
]

DEFAULT_STT_MODELS = [
    "elevenlabs",
    "mistral",
    "cohere",
    "whisper-local-large-turbo",
]

if __name__ == "__main__":
    print(f"[config] Device détecté : {DEVICE}")
    print(f"[config] Outputs -> {OUTPUTS_DIR}")
    print(f"[config] Results -> {RESULTS_DIR}")
