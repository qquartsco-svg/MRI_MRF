"""
Space Gate Data Center Thermal Stack
====================================

우주 게이트를 내부 대기 순환형 데이터센터로 가정할 때의 레이어형 열 스크리닝.

Layer 1: internal air convection (SpaceThermal terrestrial path)
Layer 2: magnetic resonance auxiliary transport (MRF proxy, optional)
Layer 3: external radiator rejection (SpaceThermal orbital radiation path)

핵심 원칙:
- 내부 대류와 외부 복사는 같은 식으로 섞지 않는다.
- 자기공명은 일반 공기를 직접 돌리는 주 냉각기가 아니라 보조 수송층으로만 취급한다.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Optional

from .athena_stage import map_athena_stage
from .contracts import (
    AthenaStage,
    MagneticThermalInput,
    ReadinessVerdict,
    SpaceGateDataCenterInput,
    SpaceGateDataCenterReport,
)
from .thermal_transport import screen_magnetic_thermal

_STAGING = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _try_import(package_dir: str, module_path: str) -> Optional[Any]:
    pkg = os.path.join(_STAGING, package_dir)
    if not os.path.isdir(pkg):
        return None
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    try:
        return importlib.import_module(module_path)
    except Exception:
        return None


def _readiness_from_omega(omega: float) -> ReadinessVerdict:
    if omega >= 0.85:
        return ReadinessVerdict.PRODUCTION_READY
    if omega >= 0.65:
        return ReadinessVerdict.PILOT_READY
    if omega >= 0.40:
        return ReadinessVerdict.PROTOTYPE_READY
    return ReadinessVerdict.NOT_READY


def _best_bottleneck(
    air_omega: float,
    radiator_omega: float,
    magnetic_omega: float | None,
) -> str:
    pairs: list[tuple[str, float]] = [
        ("internal_air", air_omega),
        ("external_radiator", radiator_omega),
    ]
    if magnetic_omega is not None:
        pairs.append(("magnetic_assist", magnetic_omega))
    pairs.sort(key=lambda x: x[1])
    return pairs[0][0]


def screen_space_gate_datacenter(inp: SpaceGateDataCenterInput) -> SpaceGateDataCenterReport:
    """Screen a space-gate-like enclosed compute node with layered thermal logic."""
    contracts_mod = _try_import("Space_Thermal_Dynamics_Foundation", "space_thermal_dynamics.contracts")
    air_mod = _try_import("Space_Thermal_Dynamics_Foundation", "space_thermal_dynamics.terrestrial_convection")
    space_mod = _try_import("Space_Thermal_Dynamics_Foundation", "space_thermal_dynamics.foundation")
    if contracts_mod is None or air_mod is None or space_mod is None:
        raise RuntimeError("Space_Thermal_Dynamics_Foundation is required for the space gate data center stack.")

    AirCoolingInput = contracts_mod.AirCoolingInput
    SpaceThermalDesignInput = contracts_mod.SpaceThermalDesignInput
    OrbitalExposureInput = contracts_mod.OrbitalExposureInput

    warnings: list[str] = []
    evidence_tags: list[str] = ["space_gate_datacenter", "layered_thermal_stack"]

    air_inp = AirCoolingInput(
        system_name=f"{inp.gate_name}_internal_air",
        heat_load_w=inp.compute_heat_load_w,
        supply_air_temp_c=inp.internal_air_supply_temp_c,
        exhaust_temp_limit_c=inp.internal_air_exhaust_limit_c,
        mass_flow_kg_s=inp.internal_air_mass_flow_kg_s,
        volumetric_flow_m3_s=inp.internal_air_volumetric_flow_m3_s,
        heat_transfer_coeff_w_m2k=inp.internal_heat_transfer_coeff_w_m2k,
        convection_area_m2=inp.internal_convection_area_m2,
        notes="internal enclosed atmosphere path",
    )
    air = air_mod.screen_air_cooling(air_inp)
    evidence_tags.extend(list(air.evidence_tags))
    if air.verdict.value != "adequate":
        warnings.append(f"Internal air path is {air.verdict.value}.")

    magnetic_omega: float | None = None
    assist_fraction = max(0.0, min(1.0, inp.magnetic_assist_fraction_0_1))
    if inp.magnetic_assist_enabled and assist_fraction > 0:
        mag = screen_magnetic_thermal(
            MagneticThermalInput(
                heat_load_w=inp.compute_heat_load_w * assist_fraction,
                plasma_temp_ev=100.0,
                plasma_density_m3=1e20,
                b_field_t=max(inp.field_t, 0.1),
                loop_length_m=25.0,
                loop_cross_section_m2=0.05,
            )
        )
        magnetic_omega = mag.omega_thermal_transport
        evidence_tags.append("magnetic_auxiliary_transport")
        warnings.append("Magnetic resonance transport is treated as an auxiliary proxy, not the primary air-cooling loop.")
    else:
        magnetic_omega = None

    base_transport_eff = 0.88
    assist_bonus = 0.0
    if magnetic_omega is not None:
        assist_bonus = 0.08 * assist_fraction * magnetic_omega
    transport_eff = max(0.50, min(0.98, base_transport_eff + assist_bonus))

    design = SpaceThermalDesignInput(
        system_name=f"{inp.gate_name}_external_radiator",
        internal_power_w=inp.compute_heat_load_w,
        radiator_area_m2=inp.radiator_area_m2,
        emissivity=inp.emissivity,
        absorptivity=inp.absorptivity,
        heat_transport_efficiency=transport_eff,
        max_operating_temp_c=inp.max_operating_temp_c,
        min_operating_temp_c=inp.min_operating_temp_c,
        thermal_mass_j_per_k=inp.thermal_mass_j_per_k,
        notes="external vacuum-side radiator path",
    )
    orbit = OrbitalExposureInput()
    space = space_mod.run_foundation(design, orbit)
    evidence_tags.extend(list(space.evidence_tags))
    if space.verdict.value != "stable":
        warnings.append(f"External radiator path is {space.verdict.value}.")

    weights: list[tuple[float, float]] = [
        (air.omega_air_0_1, 0.45),
        (space.omega_thermal, 0.45),
    ]
    if magnetic_omega is not None:
        weights.append((magnetic_omega, 0.10))

    denom = sum(w for _, w in weights)
    overall = round(sum(v * w for v, w in weights) / denom, 4) if denom else 0.0
    bottleneck = _best_bottleneck(air.omega_air_0_1, space.omega_thermal, magnetic_omega)
    athena_stage, athena_confidence = map_athena_stage(
        overall,
        conceptual_fraction=0.10 if magnetic_omega is not None else 0.0,
        warning_count=len(warnings),
    )
    verdict = _readiness_from_omega(overall)

    recommendation = (
        f"Primary bottleneck: {bottleneck}. "
        f"Internal air verdict={air.verdict.value}, external radiator verdict={space.verdict.value}."
    )
    if bottleneck == "internal_air":
        recommendation += " Increase airflow or widen allowable internal delta-T."
    elif bottleneck == "external_radiator":
        recommendation += " Increase radiator area/emissivity or reduce sustained compute load."
    else:
        recommendation += " Treat magnetic transport only as an auxiliary improvement layer."

    return SpaceGateDataCenterReport(
        gate_name=inp.gate_name,
        internal_air_omega=air.omega_air_0_1,
        internal_air_verdict=air.verdict.value,
        internal_air_outlet_temp_c=air.exhaust_air_temp_c,
        external_radiator_omega=space.omega_thermal,
        external_radiator_verdict=space.verdict.value,
        equilibrium_temp_c=space.radiation.equilibrium_temp_c,
        magnetic_assist_omega=magnetic_omega,
        magnetic_assist_fraction_0_1=assist_fraction if magnetic_omega is not None else 0.0,
        heat_transport_efficiency_0_1=round(transport_eff, 4),
        overall_omega=overall,
        athena_stage=athena_stage,
        athena_confidence=athena_confidence,
        verdict=verdict,
        bottleneck_layer=bottleneck,
        recommendation=recommendation,
        evidence_tags=evidence_tags,
        warnings=warnings,
    )
