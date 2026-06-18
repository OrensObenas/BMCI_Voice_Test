import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

print("Importing MeloTTS...")
from melo.api import TTS

print("Initializing MeloTTS for French...")
try:
    # Use CPU by default first
    model = TTS(language='FR', device='cpu')
    print("MeloTTS initialized successfully!")
    
    # Text to synthesize
    text = "Bonjour ! Bienvenue dans l'évaluation locale de Melo TTS. J'espère que la qualité audio et la vitesse de génération seront à la hauteur de vos attentes."
    
    # Find a French speaker ID
    spk2id = model.hps.data.spk2id
    print("Speakers found:", list(spk2id.keys()))
    french_spks = [k for k in spk2id.keys() if "FR" in k.upper()]
    speaker_id = spk2id[french_spks[0]] if french_spks else next(iter(spk2id.keys()))
    print(f"Using speaker: {french_spks[0] if french_spks else 'default'} (ID: {speaker_id})")
    
    output_path = str(project_root / "outputs" / "test_melo.wav")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("Synthesizing audio...")
    start_time = time.perf_counter()
    model.tts_to_file(text, speaker_id, output_path)
    end_time = time.perf_counter()
    
    print(f"Audio generated in {end_time - start_time:.3f} seconds!")
    print(f"File saved to: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

except Exception as e:
    print("An error occurred during MeloTTS run:")
    import traceback
    traceback.print_exc()
