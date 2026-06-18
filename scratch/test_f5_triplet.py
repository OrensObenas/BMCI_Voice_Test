import sys

print("Step 1: soundfile")
sys.stdout.flush()
import soundfile as sf

print("Step 2: cached_path")
sys.stdout.flush()
from cached_path import cached_path

print("Step 3: utils_infer")
sys.stdout.flush()
from f5_tts.infer.utils_infer import infer_process

print("SUCCESS")
sys.stdout.flush()
