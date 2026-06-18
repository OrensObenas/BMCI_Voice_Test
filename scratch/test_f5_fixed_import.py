import sys
import traceback

print("Importing torch first...")
import torch
print("Now importing F5TTS...")
try:
    from f5_tts.api import F5TTS
    print("SUCCESS: F5TTS imported successfully!")
except BaseException as e:
    print("FAILED:", type(e), e)
    traceback.print_exc()
