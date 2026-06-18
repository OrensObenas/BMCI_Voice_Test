import os
import sys
import winreg
import time
import shutil
from pathlib import Path

# Reload PATH
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        user_path, _ = winreg.QueryValueEx(key, "Path")
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\Environment") as key:
        system_path, _ = winreg.QueryValueEx(key, "Path")
    os.environ["PATH"] = f"{system_path};{user_path}"
    print("PATH reloaded.")
except Exception as e:
    print("Error reloading PATH:", e)

# Import F5TTS
print("Importing F5TTS...")
sys.stdout.flush()
from f5_tts.api import F5TTS

project_root = Path(__file__).resolve().parent.parent

print("\n1. Preparing reference files...")
ref_dir = project_root / "outputs" / "reference"
ref_dir.mkdir(parents=True, exist_ok=True)
kokoro_wav = project_root / "outputs" / "kokoro" / "line_01_run_0.wav"
ref_wav = ref_dir / "ref.wav"
ref_txt = ref_dir / "ref.txt"

shutil.copy(str(kokoro_wav), str(ref_wav))
ref_text = "Bonjour, bienvenue chez Atlas Bank. Comment puis-je vous aider ?"
ref_txt.write_text(ref_text, encoding="utf-8")

print("\n2. Initializing F5TTS...")
sys.stdout.flush()

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

except BaseException as e:
    print("Caught exception:", type(e), e)
    import traceback
    traceback.print_exc()
