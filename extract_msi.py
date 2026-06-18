"""Extract espeak-ng MSI contents using msilib (stdlib)."""
import msilib
import os
import shutil
import sys

msi_path = sys.argv[1] if len(sys.argv) > 1 else "espeak-ng.msi"
out_dir = sys.argv[2] if len(sys.argv) > 2 else "espeak-ng-local"

os.makedirs(out_dir, exist_ok=True)

try:
    db = msilib.OpenDatabase(msi_path, msilib.MSIDBOPEN_READONLY)
    # List tables
    view = db.OpenView("SELECT * FROM File")
    view.Execute(None)
    print("Files in MSI:")
    while True:
        try:
            rec = view.Fetch()
            if rec is None:
                break
            filename = rec.GetString(1)
            print(f"  {filename}")
        except Exception:
            break
    view.Close()
except Exception as e:
    print(f"msilib approach failed: {e}")
    print("Trying subprocess approach...")
    import subprocess
    # Use Windows built-in expand command
    result = subprocess.run(
        ["expand", msi_path, "-F:*", out_dir],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"expand failed: {result.stderr}")
