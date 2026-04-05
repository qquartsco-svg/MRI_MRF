#!/usr/bin/env python3
"""
MRF -> Factory handoff demo.

Run from repository root:
    python3 examples/factory_handoff_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from magnetic_resonance import (
    try_mri_manufacturing_readiness,
    try_gate_manufacturing_readiness,
    try_foundry_resonance_tick,
    try_fabless_semiconductor_bridge,
)


def main() -> int:
    print("Magnetic Resonance Foundation — examples/factory_handoff_demo.py")

    mri = try_mri_manufacturing_readiness(b0_field_t=3.0)
    gate = try_gate_manufacturing_readiness(field_t=3.0, nucleus="1H")
    foundry = try_foundry_resonance_tick(3.0, "1H")
    fabless = try_fabless_semiconductor_bridge(3.0, "1H")

    print(f"  MRI->MTF      : {mri}")
    print(f"  Gate->MTF     : {gate}")
    print(f"  Gate->Foundry : {foundry}")
    print(f"  Gate->Fabless : {fabless}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
