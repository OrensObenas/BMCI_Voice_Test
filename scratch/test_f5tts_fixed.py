import os
import sys
import shutil
import time
import winreg
from pathlib import Path

# 1. Dynamically reload PATH from Registry to get FFmpeg path
try:
    print("Reloading PATH from registry...")
    # User path
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        user_path, _ = winreg.QueryValueEx(key, "Path")
    # System path
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\Environment") as key:
        system_path, _ = winreg.QueryValueEx(key, "Path")
    
    # Update current process environment
    new_path = f"{system_path};{user_path}"
    os.environ["PATH"] = new_path
    print("PATH reloaded successfully!")
    
    # Look for ffmpeg in the paths
    ffmpeg_found = False
    for p in new_path.split(";"):
        if p.strip() and os.path.exists(os.path.join(p.strip(), "ffmpeg.exe")):
            print(f"Found ffmpeg.exe in: {p.strip()}")
            ffmpeg_found = True
            break
    if not ffmpeg_found:
        print("Warning: ffmpeg.exe not found in reloaded PATH!")
except Exception as e:
    print("Error reloading PATH:", e)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import F5TTS early to avoid DLL load collisions after torchaudio loads DLLs
from f5_tts.api import F5TTS

print("\n2. Preparing reference files...")
ref_dir = project_root / "outputs" / "reference"
ref_dir.mkdir(parents=True, exist_ok=True)

kokoro_wav = project_root / "outputs" / "kokoro" / "line_01_run_0.wav"
ref_wav = ref_dir / "ref.wav"
ref_txt = ref_dir / "ref.txt"

if not kokoro_wav.exists():
    print(f"Error: Kokoro wav {kokoro_wav} not found!")
    sys.exit(1)

shutil.copy(str(kokoro_wav), str(ref_wav))
ref_text = "Bonjour, bienvenue chez Atlas Bank. Comment puis-je vous aider ?"
ref_txt.write_text(ref_text, encoding="utf-8")

print("\n3. Testing torchaudio load with torchcodec backend...")
try:
    import torch
    import torchaudio
    print("Torch version:", torch.__version__)
    print("Torchaudio version:", torchaudio.__version__)
    
    # Load WAV using torchaudio
    audio, sr = torchaudio.load(str(ref_wav))
    print(f"Success! Reference audio loaded: shape={audio.shape}, samplerate={sr}")
except Exception as e:
    print("Failed to load audio with torchaudio:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Initializing F5-TTS...")
try:
    f5 = F5TTS(device="cpu")
    print("F5-TTS initialized successfully!")

    gen_text = "Ceci est un test de synthèse locale avec le modèle F5 TTS. La voix doit ressembler au fichier de référence."
    output_path = str(project_root / "outputs" / "test_f5tts.wav")
    
    print(f"Synthesizing: '{gen_text}'...")
    start_time = time.perf_counter()
    wav, sr, spect = f5.infer(
        ref_file=str(ref_wav),
        ref_text=ref_text,
        gen_text=gen_text
    )
    end_time = time.perf_counter()
    print(f"Synthesis completed in {end_time - start_time:.2f} seconds!")
    
    import soundfile as sf
    sf.write(output_path, wav, sr)
    print(f"Saved generated audio to: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

except Exception as e:
    print("An error occurred during F5-TTS execution:")
    import traceback
    traceback.print_exc()
