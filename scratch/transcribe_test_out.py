import os
from faster_whisper import WhisperModel

def main():
    audio_path = "scratch/test_elevenlabs_out.mp3"
    if not os.path.exists(audio_path):
        print(f"File {audio_path} not found.")
        return

    print("Loading Whisper model...")
    # Utilisons un modèle minuscule "tiny" pour aller très vite sur CPU
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    
    print("Transcribing...")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    print(f"Detected language: {info.language} with probability {info.language_probability}")
    print("Transcript:")
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

if __name__ == "__main__":
    main()
