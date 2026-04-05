#!/usr/bin/env python3
"""
End-to-end demo: all optional layers of analyze() in one call.

Run from repository root:
    python3 examples/full_scenario.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from magnetic_resonance import (
    analyze,
    ConfinementInput,
    ConfinementMode,
    LagrangeInput,
    LagrangePoint,
    LarmorInput,
    MagneticThermalInput,
    PlasmaTransportInput,
    RFTransferInput,
    ToroidalInput,
    preset_earth_l1_moon,
)


def main() -> int:
    report = analyze(
        larmor_input=LarmorInput(nucleus="1H", field_strength_t=3.0),
        confinement_input=ConfinementInput(
            mode=ConfinementMode.MAGNETIC_BOTTLE,
            b_max_t=6.0,
            b_min_t=1.0,
            plasma_temp_ev=100.0,
        ),
        thermal_input=MagneticThermalInput(
            heat_load_w=1000.0,
            plasma_temp_ev=100.0,
            plasma_density_m3=1e20,
        ),
        gate_nodes=preset_earth_l1_moon(field_t=3.0),
        plasma_transport_input=PlasmaTransportInput(
            electron_temp_ev=1000.0,
            electron_density_m3=1e20,
            b_field_t=5.0,
        ),
        toroidal_input=ToroidalInput(),
        rf_input=RFTransferInput(
            frequency_hz=1.28e8,
            distance_m=3.84e8,
            transmit_power_w=1e4,
            antenna_diameter_m=30.0,
        ),
        lagrange_input=LagrangeInput(point=LagrangePoint.L1),
    )

    print("Magnetic Resonance Foundation — examples/full_scenario.py")
    print(f"  omega_overall    : {report.omega_overall}")
    print(f"  athena_stage     : {report.athena_stage.value}")
    print(f"  athena_confidence: {report.athena_confidence}")
    print(f"  verdict          : {report.verdict.value}")
    print(f"  evidence_tags    : {report.evidence_tags}")
    if report.larmor:
        print(f"  larmor f₀ (MHz)  : {report.larmor.frequency_mhz}")
    if report.rf_link:
        print(f"  RF margin (dB)   : {report.rf_link.link_margin_db}")
    if report.lagrange:
        print(f"  L1 from Earth (Mm): {report.lagrange.distance_from_primary_m / 1e6:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
