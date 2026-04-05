#!/usr/bin/env python3
"""
Layered demo: space gate as an enclosed data center.

Run from repository root:
    python3 examples/space_gate_datacenter_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from magnetic_resonance import SpaceGateDataCenterInput, screen_space_gate_datacenter


def main() -> int:
    report = screen_space_gate_datacenter(
        SpaceGateDataCenterInput(
            gate_name="orbital_gate_dc_alpha",
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

    print("Magnetic Resonance Foundation — examples/space_gate_datacenter_demo.py")
    print(f"  gate_name                 : {report.gate_name}")
    print(f"  internal_air_omega        : {report.internal_air_omega}")
    print(f"  internal_air_verdict      : {report.internal_air_verdict}")
    print(f"  external_radiator_omega   : {report.external_radiator_omega}")
    print(f"  external_radiator_verdict : {report.external_radiator_verdict}")
    print(f"  magnetic_assist_omega     : {report.magnetic_assist_omega}")
    print(f"  transport_efficiency      : {report.heat_transport_efficiency_0_1}")
    print(f"  overall_omega             : {report.overall_omega}")
    print(f"  athena_stage              : {report.athena_stage.value}")
    print(f"  verdict                   : {report.verdict.value}")
    print(f"  bottleneck_layer          : {report.bottleneck_layer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
