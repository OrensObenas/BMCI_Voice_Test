import os
from pathlib import Path

def get_dir_size(path):
    total = 0
    try:
        for p in Path(path).rglob('*'):
            if p.is_file():
                total += p.stat().st_size
    except Exception as e:
        pass
    return total

hf_cache = Path.home() / ".cache" / "huggingface"
print(f"HF cache path: {hf_cache}")
if hf_cache.exists():
    size_mb = get_dir_size(hf_cache) / (1024 * 1024)
    print(f"Total size: {size_mb:.2f} MB")

cp_cache = Path.home() / ".cache" / "cached_path"
print(f"\ncached_path cache path: {cp_cache}")
if cp_cache.exists():
    size_mb = get_dir_size(cp_cache) / (1024 * 1024)
    print(f"Total size: {size_mb:.2f} MB")
    
    print("Files in cached_path:")
    try:
        for p in cp_cache.rglob('*'):
            if p.is_file():
                print(f"  {p.relative_to(cp_cache)} - {p.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print("Error listing:", e)
else:
    print("cached_path cache does not exist.")
