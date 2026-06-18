import os
from pathlib import Path

f5_path = Path(r"C:\Users\user\.gemini\antigravity\scratch\tts-benchmark\.venv\Lib\site-packages\f5_tts")
print(f"Searching for exit calls in {f5_path}...")

for p in f5_path.rglob("*.py"):
    try:
        content = p.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if "sys.exit" in line or "exit(" in line:
                # ignore comments
                if not line.strip().startswith("#"):
                    print(f"{p.relative_to(f5_path)}:{i} - {line.strip()}")
    except Exception as e:
        pass
