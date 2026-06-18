import sys

def test():
    print("Step 1")
    sys.stdout.flush()
    import random
    print("Step 2")
    sys.stdout.flush()
    from importlib.resources import files
    print("Step 3")
    sys.stdout.flush()
    import soundfile as sf
    print("Step 4")
    sys.stdout.flush()
    import tqdm
    print("Step 5")
    sys.stdout.flush()
    from cached_path import cached_path
    print("Step 6")
    sys.stdout.flush()
    from hydra.utils import get_class
    print("Step 7")
    sys.stdout.flush()
    from omegaconf import OmegaConf
    print("Step 8")
    sys.stdout.flush()
    from f5_tts.infer.utils_infer import (
        infer_process,
        load_model,
        load_vocoder,
        preprocess_ref_audio_text,
        remove_silence_for_generated_wav,
        save_spectrogram,
        transcribe,
    )
    print("Step 9")
    sys.stdout.flush()
    from f5_tts.model.utils import seed_everything
    print("Step 10")
    sys.stdout.flush()
    
    # Let's try importing api itself
    import f5_tts.api
    print("Step 11 (api imported)")
    sys.stdout.flush()

if __name__ == "__main__":
    try:
        test()
    except BaseException as e:
        print("Caught exception:", type(e), e)
        import traceback
        traceback.print_exc()
