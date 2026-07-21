"""Convenience wrapper: run the canonical seed script from src/backend/.

The canonical seed lives at db/seed/seed.py (relative to the repo root).
This shim lets developers do `cd src/backend && python seed.py` without
having to know the full path, as documented in the README and run scripts.

Usage (from repo root, with backend venv active):
    cd src/backend
    venv\\Scripts\\python.exe seed.py          # Windows
    venv/bin/python seed.py                    # macOS / Linux
"""
from __future__ import annotations

import runpy
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[2] / "db" / "seed" / "seed.py"

if __name__ == "__main__":
    runpy.run_path(str(SEED_PATH), run_name="__main__")
