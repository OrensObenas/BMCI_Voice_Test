try:
    print("Attempting to import TTS from TTS.api...")
    from TTS.api import TTS
    print("Success! TTS imported successfully.")
except Exception as e:
    print("Failed to import TTS:")
    import traceback
    traceback.print_exc()
