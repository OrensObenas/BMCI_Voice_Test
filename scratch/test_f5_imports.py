import sys
import traceback

print("Attempting to import f5_tts.api and catch BaseException...")
try:
    import f5_tts.api
    print("SUCCESS: f5_tts.api imported!")
except BaseException as e:
    print(f"FAILED: caught BaseException of type {type(e)}:")
    traceback.print_exc()
