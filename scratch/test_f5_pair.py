import subprocess
import sys

def run_import_pair(pre_import):
    cmd = [
        sys.executable,
        "-c",
        f"print('Trying: {pre_import}...'); import {pre_import}; from f5_tts.infer.utils_infer import infer_process; print('  SUCCESS!')"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Result for {pre_import}:")
    print(f"  Exit code: {res.returncode}")
    print(f"  Stdout: {res.stdout.strip()}")
    if res.stderr:
        print(f"  Stderr: {res.stderr.strip()}")
    print("-" * 50)

print("Testing pre-imports with f5_tts.infer.utils_infer:")
run_import_pair("cached_path")
run_import_pair("hydra")
run_import_pair("omegaconf")
