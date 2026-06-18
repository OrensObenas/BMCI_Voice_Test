import os
import sys
import shutil
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

print("1. Preparing reference files...")
ref_dir = project_root / "outputs" / "reference"
ref_dir.mkdir(parents=True, exist_ok=True)

kokoro_wav = project_root / "outputs" / "kokoro" / "line_01_run_0.wav"
ref_wav = ref_dir / "ref.wav"
ref_txt = ref_dir / "ref.txt"

if not kokoro_wav.exists():
    print(f"Error: Kokoro wav {kokoro_wav} not found! Please run Kokoro model first.")
    any_wav = next(project_root.glob("outputs/**/*.wav"), None)
    if any_wav:
        print(f"Using fallback wav: {any_wav}")
        shutil.copy(str(any_wav), str(ref_wav))
    else:
        print("No wav found at all!")
        sys.exit(1)
else:
    shutil.copy(str(kokoro_wav), str(ref_wav))
    print("Reference wav copied successfully.")

# Write the reference text
ref_text = "Bonjour, bienvenue chez Atlas Bank. Comment puis-je vous aider ?"
ref_txt.write_text(ref_text, encoding="utf-8")
print("Reference text written successfully.")

print("\n2. Importing F5-TTS...")
from f5_tts.api import F5TTS

print("\n3. Initializing F5-TTS on CPU...")
try:
    # Initialize F5TTS using correct parameters
    f5 = F5TTS(
        device="cpu"
    )
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
    
    # Save using soundfile
    import soundfile as sf
    sf.write(output_path, wav, sr)
    print(f"Saved generated audio to: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

except Exception as e:
    print("An error occurred during F5-TTS execution:")
    import traceback
    traceback.print_exc()
