#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / ".pytest_cache",
    ROOT / "build",
    ROOT / "dist",
]


def main() -> int:
    for target in TARGETS:
        if target.exists():
            shutil.rmtree(target)
            print(f"REMOVED  {target.relative_to(ROOT)}")
    for pyc in ROOT.rglob("*.pyc"):
        pyc.unlink()
        print(f"REMOVED  {pyc.relative_to(ROOT)}")
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache)
        print(f"REMOVED  {cache.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
