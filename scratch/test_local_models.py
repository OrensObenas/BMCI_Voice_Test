import sys
from pathlib import Path

print("1. Checking F5-TTS...")
try:
    from f5_tts.api import F5TTS
    print("F5-TTS is installed!")
except Exception as e:
    print("F5-TTS import failed:", e)

print("\n2. Checking Parler-TTS...")
try:
    import parler_tts
    print("Parler-TTS is installed!")
except Exception as e:
    print("Parler-TTS import failed:", e)

print("\n3. Checking OpenVINO / Optimum Intel...")
try:
    import openvino as ov
    print("OpenVINO is installed!")
except Exception as e:
    print("OpenVINO import failed:", e)

try:
    import optimum.intel as opt_intel
    print("Optimum Intel is installed!")
except Exception as e:
    print("Optimum Intel import failed:", e)
