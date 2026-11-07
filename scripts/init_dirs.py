# scripts/init_dirs.py
import os
from pathlib import Path

def init_workspace():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    uploads_dir = data_dir / "uploads"
    models_dir = data_dir / "models" / "flashrank"

    for path in [data_dir, uploads_dir, models_dir]:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Verified directory: {path}")

if __name__ == "__main__":
    init_workspace()