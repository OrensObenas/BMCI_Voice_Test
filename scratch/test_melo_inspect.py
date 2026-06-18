import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

print("Importing MeloTTS...")
from melo.api import TTS

print("Initializing MeloTTS...")
model = TTS(language='FR', device='cpu')

spk2id = model.hps.data.spk2id
print("Type of spk2id:", type(spk2id))
print("Dir of spk2id:", dir(spk2id))
try:
    print("spk2id keys:", spk2id.keys())
except Exception as e:
    print("spk2id.keys() failed:", e)

try:
    print("spk2id items:", spk2id.items())
except Exception as e:
    print("spk2id.items() failed:", e)

try:
    print("spk2id as dict attributes:", spk2id.__dict__)
except Exception as e:
    print("spk2id.__dict__ failed:", e)
