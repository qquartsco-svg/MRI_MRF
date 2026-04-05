#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def main() -> int:
    steps = [
        [sys.executable, "scripts/verify_package_identity.py"],
        [sys.executable, "scripts/verify_signature.py"],
        [sys.executable, "examples/full_scenario.py"],
        [sys.executable, "-m", "pytest", "tests", "-q"],
    ]
    for step in steps:
        code = run(step)
        if code != 0:
            return code
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
