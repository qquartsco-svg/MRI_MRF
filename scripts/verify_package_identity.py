#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED = [
    "README.md",
    "README_EN.md",
    "CONCEPT.md",
    "BLOCKCHAIN_INFO.md",
    "BLOCKCHAIN_INFO_EN.md",
    "VERSION",
    "pyproject.toml",
    "SIGNATURE.sha256",
    "magnetic_resonance/__init__.py",
    "magnetic_resonance/contracts.py",
    "magnetic_resonance/foundation.py",
    "magnetic_resonance/space_gate_datacenter.py",
    "magnetic_resonance/athena_stage.py",
    "scripts/generate_signature.py",
    "scripts/verify_signature.py",
    "scripts/verify_package_identity.py",
    "scripts/cleanup_generated.py",
    "scripts/release_check.py",
    "tests/test_magnetic_resonance.py",
]


def main() -> int:
    missing = [rel for rel in REQUIRED if not (ROOT / rel).exists()]
    if missing:
        for rel in missing:
            print(f"MISSING  {rel}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
