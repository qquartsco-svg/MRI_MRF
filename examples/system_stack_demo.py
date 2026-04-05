#!/usr/bin/env python3
"""
MRF system stack demo.

Run from repository root:
    python3 examples/system_stack_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from magnetic_resonance import (
    SpaceGateDataCenterInput,
    screen_space_gate_datacenter,
    try_satellite_gate_bridge,
    try_orbital_gate_bridge,
    try_gate_manufacturing_readiness,
    try_foundry_resonance_tick,
    try_fabless_semiconductor_bridge,
    try_superconducting_field,
)


def main() -> int:
    thermal = screen_space_gate_datacenter(
        SpaceGateDataCenterInput(
            gate_name="orbital_gate_dc_stack",
            compute_heat_load_w=1200.0,
            radiator_area_m2=8.0,
            internal_air_supply_temp_c=20.0,
            internal_air_exhaust_limit_c=38.0,
            internal_air_volumetric_flow_m3_s=1.2,
            field_t=3.0,
            magnetic_assist_enabled=True,
            magnetic_assist_fraction_0_1=0.15,
            thermal_mass_j_per_k=25_000.0,
        )
    )
    sat = try_satellite_gate_bridge(heat_load_w=300.0)
    orb = try_orbital_gate_bridge(altitude_km=550.0)
    mfg = try_gate_manufacturing_readiness(field_t=3.0, nucleus="1H")
    foundry = try_foundry_resonance_tick(3.0, "1H")
    fabless = try_fabless_semiconductor_bridge(3.0, "1H")
    sc = try_superconducting_field(current_a=180.0)

    print("Magnetic Resonance Foundation — examples/system_stack_demo.py")
    print(f"  thermal_overall_omega : {thermal.overall_omega}")
    print(f"  thermal_bottleneck    : {thermal.bottleneck_layer}")
    print(f"  satellite_bridge      : {sat}")
    print(f"  orbital_bridge        : {orb}")
    print(f"  manufacturing_bridge  : {mfg}")
    print(f"  foundry_bridge        : {foundry}")
    print(f"  fabless_bridge        : {fabless}")
    print(f"  superconducting_bridge: {sc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
