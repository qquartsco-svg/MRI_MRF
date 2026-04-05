#!/usr/bin/env python3
"""
MRF space gate evolution demo.

Run from repository root:
    python3 examples/space_gate_evolution_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from magnetic_resonance import (
    SpaceGateDataCenterInput,
    SpaceGateEvolutionInput,
    evaluate_space_gate_evolution,
    screen_space_gate_datacenter,
    try_foundry_resonance_tick,
    try_gate_manufacturing_readiness,
    try_orbital_gate_bridge,
    try_satellite_gate_bridge,
    try_superconducting_field,
    try_terracore_gate_bridge,
)


def main() -> int:
    thermal = screen_space_gate_datacenter(
        SpaceGateDataCenterInput(
            gate_name="evolution_demo_node",
            compute_heat_load_w=900.0,
            radiator_area_m2=6.5,
            internal_air_supply_temp_c=20.0,
            internal_air_exhaust_limit_c=36.0,
            internal_air_volumetric_flow_m3_s=0.95,
            field_t=3.0,
            magnetic_assist_enabled=True,
            magnetic_assist_fraction_0_1=0.12,
            thermal_mass_j_per_k=22_000.0,
        )
    )
    sat = try_satellite_gate_bridge(heat_load_w=260.0)
    orb = try_orbital_gate_bridge(altitude_km=550.0)
    mfg = try_gate_manufacturing_readiness(field_t=3.0, nucleus="1H")
    foundry = try_foundry_resonance_tick(3.0, "1H")
    sc = try_superconducting_field(current_a=180.0)
    terra = try_terracore_gate_bridge(heat_load_w=260.0, crew_count=1, mission_days=10.0, closed_loop=True)

    evo = evaluate_space_gate_evolution(
        SpaceGateEvolutionInput(
            system_name="earthlike_gate_seed",
            thermal_omega=thermal.overall_omega,
            satellite_omega=sat["omega_satellite"] if sat else 0.0,
            orbital_omega=orb["omega_orb"] if orb else 0.0,
            manufacturing_omega=mfg["omega_mfg"] if mfg else 0.0,
            resonance_network_omega=0.62,
            superconducting_omega=sc["omega_total"] if sc else None,
            terracore_viability_0_1=terra["omega_terracore"] if terra else None,
            foundry_omega=foundry["omega_foundry"] if foundry else None,
            internal_air_enabled=True,
            closed_loop_life_support_enabled=True,
        )
    )

    print("Magnetic Resonance Foundation — examples/space_gate_evolution_demo.py")
    print(f"  current_phase : {evo.current_phase.value}")
    print(f"  next_phase    : {evo.next_phase.value if evo.next_phase else 'none'}")
    print(f"  overall_omega : {evo.overall_omega}")
    print(f"  bottlenecks   : {evo.bottlenecks}")
    print(f"  terracore     : {terra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
