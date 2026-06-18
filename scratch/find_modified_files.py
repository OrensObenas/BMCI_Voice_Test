import os
import time
from pathlib import Path

now = time.time()
print("Searching for files modified in the last 10 minutes...")

# We will search in C:\Users\user\.cache
cache_dir = Path.home() / ".cache"
if cache_dir.exists():
    for p in cache_dir.rglob('*'):
        try:
            if p.is_file():
                mtime = p.stat().st_mtime
                if now - mtime < 600: # 10 minutes
                    print(f"  {p} - {p.stat().st_size / (1024*1024):.2f} MB (modified {now - mtime:.0f}s ago)")
        except Exception:
            pass
else:
    print("Cache dir does not exist.")
