import requests
import time
import sys

url = "https://huggingface.co/Systran/faster-whisper-base/resolve/main/model.bin"
print(f"Downloading {url}...")
try:
    start_time = time.time()
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    downloaded = 0
    with open("test_model.bin", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                percent = (downloaded / total_size) * 100 if total_size else 0
                sys.stdout.write(f"\rDownloaded: {downloaded / (1024*1024):.2f} MB ({percent:.1f}%)")
                sys.stdout.flush()
    print(f"\nFinished in {time.time() - start_time:.2f} seconds.")
except Exception as e:
    print(f"\nError: {e}")
