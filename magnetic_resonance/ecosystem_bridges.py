"""
Ecosystem Bridges — 형제 엔진 느슨한 결합
==========================================

FrequencyCore     → 공명 분석 재사용
Superconducting   → 코일/자기장 설계
SpaceThermal      → 복사+대류 병렬 비교
Optics            → 전자기파/파장 screening
Foundry           → 공정/테이프아웃 readiness tick
Manufacturing     → 코일/구조물 제조 readiness
TerraCore/Satellite → 폐회로 생존성 / 자가순환 해비타트 viability

형제 엔진이 없으면 None으로 조용히 degrade 된다.
"""
from __future__ import annotations

import importlib
import math
import os
import sys
from typing import Any, Dict, Optional

from .larmor import larmor_frequency
from .contracts import LarmorInput

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


def try_frequency_resonance(natural_hz: float, excitation_hz: float, damping: float = 0.05) -> Optional[Dict[str, Any]]:
    """FrequencyCore → Tesla 공명 분석."""
    mod = _try_import("FrequencyCore_Engine", "frequency_core.resonance")
    if mod is None:
        return None
    try:
        sig = [1.0, 0.9, 0.8, 0.7]
        rr = mod.analyze_resonance(sig, natural_hz, excitation_hz)
        return {
            "resonance_state": rr.resonance_state.value,
            "coupling_efficiency": rr.coupling_efficiency,
            "omega_freq": rr.omega_freq,
        }
    except Exception:
        return None


def try_superconducting_field(current_a: float = 100.0) -> Optional[Dict[str, Any]]:
    """Superconducting_Magnet_Stack → 자기장/퀀치 readiness bridge."""
    contracts_mod = _try_import("Superconducting_Magnet_Stack", "superconducting_magnet_stack.contracts")
    pipeline_mod = _try_import("Superconducting_Magnet_Stack", "superconducting_magnet_stack.pipeline")
    if contracts_mod is None or pipeline_mod is None:
        return None
    try:
        material = contracts_mod.MaterialCandidate(
            name="NbTi",
            tc_k=9.2,
            jc_a_per_mm2_77k=3000.0,
            bc2_t=14.5,
            anisotropy=1.0,
        )
        cryo = contracts_mod.CryoProfile(
            operating_temp_k=4.2,
            heat_load_w=25.0,
            cooling_capacity_w=80.0,
        )
        design = contracts_mod.MagnetDesign(
            target_field_t=3.0,
            operating_current_a=current_a,
            conductor_cross_section_mm2=120.0,
            inductance_h=8.0,
            stored_energy_j=0.5 * 8.0 * current_a * current_a,
            stress_mpa=120.0,
            coil_length_m=2.0,
            operating_temp_k=4.2,
        )
        readiness, quench = pipeline_mod.run_magnet_design_assessment(material, cryo, design)
        return {
            "bridge": "superconducting_available",
            "omega_total": readiness.omega_total,
            "verdict": readiness.verdict,
            "quench_severity": quench.severity,
            "target_field_t": design.target_field_t,
        }
    except Exception:
        return None


def try_space_thermal_screen(heat_w: float, area_m2: float = 1.0) -> Optional[Dict[str, Any]]:
    """Space_Thermal_Dynamics → 복사 스크리닝."""
    mod = _try_import("Space_Thermal_Dynamics_Foundation", "space_thermal_dynamics.foundation")
    if mod is None:
        return None
    try:
        from space_thermal_dynamics.contracts import SpaceThermalDesignInput, OrbitalExposureInput
        design = SpaceThermalDesignInput(
            system_name="mr_thermal_bridge",
            internal_power_w=heat_w,
            radiator_area_m2=area_m2,
        )
        orbit = OrbitalExposureInput()
        report = mod.run_foundation(design, orbit)
        return {
            "omega_thermal": report.omega_thermal,
            "verdict": report.verdict.value,
        }
    except Exception:
        return None


def resonance_to_em_snapshot(field_t: float, nucleus: str = "1H") -> Dict[str, Any]:
    """자기공명 조건을 전자기파 snapshot으로 투영한다."""
    lr = larmor_frequency(LarmorInput(nucleus=nucleus, field_strength_t=field_t))
    wavelength_nm = lr.wavelength_m * 1e9
    if wavelength_nm >= 1e6:
        regime = "microwave"
    elif wavelength_nm >= 25_000:
        regime = "far_ir"
    elif wavelength_nm >= 2_500:
        regime = "mid_ir"
    elif wavelength_nm >= 780:
        regime = "near_ir"
    elif wavelength_nm >= 380:
        regime = "visible"
    else:
        regime = "uv_or_xray"
    return {
        "nucleus": nucleus,
        "field_t": field_t,
        "frequency_hz": lr.frequency_hz,
        "frequency_mhz": lr.frequency_mhz,
        "wavelength_m": lr.wavelength_m,
        "wavelength_nm": round(wavelength_nm, 3),
        "regime": regime,
    }


def try_optics_resonance_bridge(
    field_t: float,
    nucleus: str = "1H",
    *,
    aperture_diameter_mm: float = 100.0,
    focal_length_mm: float = 200.0,
    coating_layers: int = 0,
    temperature_c: float = 25.0,
) -> Optional[Dict[str, Any]]:
    """Magnetic Resonance → Optics_Foundation screening bridge."""
    contracts_mod = _try_import("Optics_Foundation", "optics_foundation.contracts")
    foundation_mod = _try_import("Optics_Foundation", "optics_foundation.foundation")
    if contracts_mod is None or foundation_mod is None:
        return None
    try:
        OpticalDesignInput = contracts_mod.OpticalDesignInput
        snapshot = resonance_to_em_snapshot(field_t, nucleus=nucleus)
        design = OpticalDesignInput(
            name=f"mr_{nucleus}_{field_t:g}T",
            wavelength_nm=max(snapshot["wavelength_nm"], 1.0),
            refractive_index=1.0,
            aperture_diameter_mm=aperture_diameter_mm,
            focal_length_mm=focal_length_mm,
            num_surfaces=2,
            coating_layers=coating_layers,
            substrate_material="vacuum_window",
            temperature_c=temperature_c,
        )
        report = foundation_mod.analyze(design)
        return {
            "regime": snapshot["regime"],
            "wavelength_nm": snapshot["wavelength_nm"],
            "omega_optics": report.omega.omega_optics if report.omega else None,
            "verdict": report.omega.verdict.value if report.omega else None,
            "dominant_penalty": report.omega.dominant_penalty if report.omega else None,
        }
    except Exception:
        return None


def try_foundry_resonance_tick(
    field_t: float,
    nucleus: str = "1H",
    *,
    foundry: str = "generic_foundry",
    target_pdk: str = "rf_cmos_130",
) -> Optional[Dict[str, Any]]:
    """Magnetic Resonance → Foundry implementation readiness tick."""
    mod = _try_import("Foundry_Implementation_Engine", "foundry_impl")
    if mod is None:
        return None
    try:
        snap = resonance_to_em_snapshot(field_t, nucleus=nucleus)
        fit = 0.85 if snap["regime"] == "microwave" else 0.55
        payload = {
            "session": {
                "chip_id": f"mr_{nucleus}_{int(field_t * 1000)}mT",
                "target_pdk": target_pdk,
                "foundry": foundry,
                "milestone": "signoff_ready",
            },
            "artifacts": [
                {"kind": "netlist.gate", "uri": "file://mr/netlist.gate", "digest_sha256": "mr-gate"},
                {"kind": "layout.gdsii", "uri": "file://mr/layout.gds", "digest_sha256": "mr-gds"},
                {"kind": "timing.report", "uri": "file://mr/timing.rpt", "digest_sha256": "mr-timing"},
                {"kind": "power.report", "uri": "file://mr/power.rpt", "digest_sha256": "mr-power"},
            ],
            "gate_inputs": {
                "drc_violations": 0 if fit >= 0.6 else 2,
                "lvs_mismatches": 0 if fit >= 0.6 else 1,
                "timing_setup_slack_ns": 0.02 + 0.06 * fit,
                "timing_hold_slack_ns": 0.01 + 0.04 * fit,
                "power_margin": 0.20 + 0.60 * fit,
                "dfm_score": 0.35 + 0.60 * fit,
            },
            "release_signer": "magnetic_resonance_bridge",
        }
        out = mod.run_engine_ref_payload(payload)
        return {
            "omega_foundry": out.get("omega"),
            "verdict": out.get("verdict"),
            "stage": out.get("stage"),
            "target_pdk": out.get("session", {}).get("target_pdk"),
            "regime": snap["regime"],
        }
    except Exception:
        return None


def try_manufacturing_resonance_readiness(
    field_t: float,
    nucleus: str = "1H",
    *,
    coil_diameter_mm: float = 200.0,
    conductor_material: str = "NbTi",
) -> Optional[Dict[str, Any]]:
    """Magnetic Resonance → Manufacturing_Translation_Foundation handoff."""
    mod = _try_import("Manufacturing_Translation_Foundation", "manufacturing_translation.pipeline")
    if mod is None:
        return None
    try:
        snap = resonance_to_em_snapshot(field_t, nucleus=nucleus)
        payload = {
            "engine_name": "Magnetic_Resonance_Foundation",
            "engine_omega": 0.72 if snap["regime"] == "microwave" else 0.55,
            "engine_verdict": "PASS" if snap["regime"] == "microwave" else "REVIEW",
            "domain": "electromagnetic_hardware",
            "materials": [conductor_material, "Copper", "Ceramic", "Vacuum Housing"],
            "dimensions": {
                "coil_diameter_mm": coil_diameter_mm,
                "coil_height_mm": coil_diameter_mm * 0.3,
                "thickness_mm": 8.0,
            },
            "performance_targets": {
                "field_t": field_t,
                "frequency_mhz": snap["frequency_mhz"],
            },
            "thermal_budget": {"max_temp_c": 40.0},
            "electrical_specs": {"coil_current_a": 120.0, "rf_frequency_hz": snap["frequency_hz"]},
            "mechanical_specs": {"package_type": "cryogenic_coil_module", "mount_holes": 4, "bolt_size": "M4"},
            "environment": {"vacuum_required": True, "magnetic_shielding": True},
            "quantity": 1,
            "budget_usd": 0.0,
        }
        out = mod.translate_from_dict(payload)
        return {
            "omega_mfg": out.get("omega_manufacturing"),
            "athena_stage": out.get("athena_stage"),
            "verdict": out.get("verdict"),
            "best_process": out.get("best_process"),
        }
    except Exception:
        return None


def mri_to_manufacturing_payload(
    *,
    b0_field_t: float,
    bore_diameter_mm: float = 600.0,
    gradient_peak_mt_m: float = 40.0,
    rf_frequency_hz: float | None = None,
) -> Dict[str, Any]:
    """MRI 장비용 제조 payload."""
    snap = resonance_to_em_snapshot(b0_field_t, nucleus="1H")
    return {
        "engine_name": "Magnetic_Resonance_Foundation_MRI",
        "engine_omega": 0.82,
        "engine_verdict": "PASS",
        "domain": "medical_imaging_hardware",
        "materials": ["NbTi", "Copper", "Aluminum", "Cryostat Steel", "Ceramic"],
        "dimensions": {
            "bore_diameter_mm": bore_diameter_mm,
            "magnet_length_mm": bore_diameter_mm * 2.1,
            "thickness_mm": 30.0,
        },
        "performance_targets": {
            "b0_field_t": b0_field_t,
            "gradient_peak_mt_m": gradient_peak_mt_m,
            "rf_frequency_hz": rf_frequency_hz or snap["frequency_hz"],
        },
        "thermal_budget": {"max_temp_c": 35.0, "cryogenic_stage_k": 4.2},
        "electrical_specs": {"gradient_power_kw": 80.0, "rf_peak_power_kw": 15.0},
        "mechanical_specs": {"package_type": "mri_magnet_module", "mount_holes": 8, "bolt_size": "M10"},
        "environment": {"cryogenic": True, "medical_cleanliness": True, "magnetic_shielding": True},
        "quantity": 1,
        "budget_usd": 0.0,
    }


def gate_to_manufacturing_payload(
    *,
    field_t: float,
    nucleus: str = "1H",
    coil_diameter_mm: float = 200.0,
    conductor_material: str = "NbTi",
) -> Dict[str, Any]:
    """Gate/device concept용 제조 payload."""
    snap = resonance_to_em_snapshot(field_t, nucleus=nucleus)
    return {
        "engine_name": "Magnetic_Resonance_Foundation_Gate",
        "engine_omega": 0.58 if snap["regime"] == "microwave" else 0.45,
        "engine_verdict": "REVIEW",
        "domain": "electromagnetic_gateway_hardware",
        "materials": [conductor_material, "Copper", "Ceramic", "Vacuum Housing"],
        "dimensions": {
            "coil_diameter_mm": coil_diameter_mm,
            "coil_height_mm": coil_diameter_mm * 0.3,
            "thickness_mm": 8.0,
        },
        "performance_targets": {
            "field_t": field_t,
            "frequency_mhz": snap["frequency_mhz"],
        },
        "thermal_budget": {"max_temp_c": 40.0},
        "electrical_specs": {"coil_current_a": 120.0, "rf_frequency_hz": snap["frequency_hz"]},
        "mechanical_specs": {"package_type": "cryogenic_coil_module", "mount_holes": 4, "bolt_size": "M4"},
        "environment": {"vacuum_required": True, "magnetic_shielding": True},
        "quantity": 1,
        "budget_usd": 0.0,
    }


def try_mri_manufacturing_readiness(
    *,
    b0_field_t: float,
    bore_diameter_mm: float = 600.0,
    gradient_peak_mt_m: float = 40.0,
) -> Optional[Dict[str, Any]]:
    """MRI path → MTF 제조 readiness."""
    mod = _try_import("Manufacturing_Translation_Foundation", "manufacturing_translation.pipeline")
    if mod is None:
        return None
    try:
        out = mod.translate_from_dict(
            mri_to_manufacturing_payload(
                b0_field_t=b0_field_t,
                bore_diameter_mm=bore_diameter_mm,
                gradient_peak_mt_m=gradient_peak_mt_m,
            )
        )
        return {
            "omega_mfg": out.get("omega_manufacturing"),
            "athena_stage": out.get("athena_stage"),
            "verdict": out.get("verdict"),
            "best_process": out.get("best_process"),
        }
    except Exception:
        return None


def try_gate_manufacturing_readiness(
    *,
    field_t: float,
    nucleus: str = "1H",
    coil_diameter_mm: float = 200.0,
    conductor_material: str = "NbTi",
) -> Optional[Dict[str, Any]]:
    """Gate path → MTF 제조 readiness."""
    mod = _try_import("Manufacturing_Translation_Foundation", "manufacturing_translation.pipeline")
    if mod is None:
        return None
    try:
        out = mod.translate_from_dict(
            gate_to_manufacturing_payload(
                field_t=field_t,
                nucleus=nucleus,
                coil_diameter_mm=coil_diameter_mm,
                conductor_material=conductor_material,
            )
        )
        return {
            "omega_mfg": out.get("omega_manufacturing"),
            "athena_stage": out.get("athena_stage"),
            "verdict": out.get("verdict"),
            "best_process": out.get("best_process"),
        }
    except Exception:
        return None


def try_fabless_semiconductor_bridge(
    field_t: float,
    nucleus: str = "1H",
    *,
    target_node_nm: int = 130,
    die_size_mm2: float = 80.0,
) -> Optional[Dict[str, Any]]:
    """Magnetic Resonance → fabless-style semiconductor manufacturing bridge."""
    adapter_mod = _try_import(
        "Manufacturing_Translation_Foundation",
        "manufacturing_translation.engine_adapters.fabless_adapter",
    )
    pipeline_mod = _try_import("Manufacturing_Translation_Foundation", "manufacturing_translation.pipeline")
    if adapter_mod is None or pipeline_mod is None:
        return None
    try:
        snap = resonance_to_em_snapshot(field_t, nucleus=nucleus)
        obs = {
            "Omega_global": 0.68 if snap["regime"] == "microwave" else 0.50,
            "verdict": "PASS" if snap["regime"] == "microwave" else "REVIEW",
            "submetrics": {
                "power_w": 2.5,
                "frequency_ghz": snap["frequency_hz"] / 1e9,
                "tjunction_c": 75,
                "vdd_v": 1.2,
                "io_count": 96,
            },
        }
        di = adapter_mod.adapt_fabless(obs, target_node_nm=target_node_nm, die_size_mm2=die_size_mm2)
        report = pipeline_mod.translate(di)
        return {
            "omega_semiconductor_chain": report.semiconductor_omegas.get("omega_semiconductor_chain"),
            "omega_foundry": report.semiconductor_omegas.get("omega_foundry"),
            "verdict": report.verdict.value,
            "athena_stage": report.athena_stage.value,
            "target_node_nm": target_node_nm,
        }
    except Exception:
        return None


def try_satellite_gate_bridge(
    *,
    heat_load_w: float,
    data_rate_kbps: float = 5000.0,
    altitude_km: float = 550.0,
    design_life_years: float = 2.0,
) -> Optional[Dict[str, Any]]:
    """Magnetic Resonance → Satellite_Design_Stack readiness bridge."""
    sat_mod = _try_import("Satellite_Design_Stack", "satellite_design_stack")
    if sat_mod is None:
        return None
    try:
        mission = sat_mod.SatelliteMission(
            satellite_class=sat_mod.SatelliteClass.SMALLSAT,
            orbit_type=sat_mod.OrbitType.LEO,
            altitude_km=altitude_km,
            payload_type=sat_mod.PayloadType.EXPERIMENTAL,
            design_life_years=design_life_years,
            data_rate_kbps=data_rate_kbps,
            pointing_req_deg=1.0,
            power_req_w=max(5.0, heat_load_w * 0.35),
            mission_label="magnetic_resonance_gate_payload",
        )
        bp, report = sat_mod.SatelliteDesignPipeline().run(mission)
        return {
            "omega_satellite": report.omega,
            "verdict": report.verdict.value,
            "satellite_class": bp.satellite_class.value,
            "orbit_type": bp.orbit.orbit_type.value,
            "thermal_hot_case_c": bp.thermal.hot_case_temp_c if bp.thermal else None,
            "thermal_cold_case_c": bp.thermal.cold_case_temp_c if bp.thermal else None,
            "link_margin_db": bp.link.link_margin_db,
        }
    except Exception:
        return None


def try_orbital_gate_bridge(
    *,
    altitude_km: float = 550.0,
    eccentricity: float = 0.001,
    inclination_deg: float = 97.6,
    delta_v_remaining_ms: float = 120.0,
    mass_kg: float = 180.0,
    area_m2: float = 2.5,
) -> Optional[Dict[str, Any]]:
    """Magnetic Resonance → OrbitalCore_Engine health bridge."""
    contracts_mod = _try_import("OrbitalCore_Engine", "orbital_core.contracts")
    health_mod = _try_import("OrbitalCore_Engine", "orbital_core.health")
    constants_mod = _try_import("OrbitalCore_Engine", "orbital_core.constants")
    if contracts_mod is None or health_mod is None or constants_mod is None:
        return None


def try_terracore_gate_bridge(
    *,
    heat_load_w: float,
    crew_count: int = 1,
    mission_days: float = 14.0,
    closed_loop: bool = True,
    altitude_km: float = 550.0,
    data_rate_kbps: float = 5000.0,
    design_life_years: float = 2.0,
) -> Optional[Dict[str, Any]]:
    """MRF gate concept -> Satellite/TerraCore closed-loop habitat bridge."""
    sat_mod = _try_import("Satellite_Design_Stack", "satellite_design_stack")
    if sat_mod is None:
        return None
    try:
        mission = sat_mod.SatelliteMission(
            satellite_class=sat_mod.SatelliteClass.SMALLSAT,
            orbit_type=sat_mod.OrbitType.LEO,
            altitude_km=altitude_km,
            payload_type=sat_mod.PayloadType.EXPERIMENTAL,
            design_life_years=design_life_years,
            data_rate_kbps=data_rate_kbps,
            pointing_req_deg=1.0,
            power_req_w=max(20.0, heat_load_w * 0.40),
            mission_label="magnetic_resonance_terracore_gate",
        )
        bp, report = sat_mod.SatelliteDesignPipeline().run(mission)
        adapter = sat_mod.TerraCoreAdapter(
            crew_count=crew_count,
            mission_days=mission_days,
            closed_loop=closed_loop,
        )
        hab = adapter.evaluate(bp)
        score_terms = [
            1.0 if hab.get("volume_ok") else 0.0,
            1.0 if hab.get("power_ok") else 0.0,
            1.0 if hab.get("mass_ok") else 0.0,
            1.0 if hab.get("terracore_available") else 0.3,
            1.0 if closed_loop else 0.6,
        ]
        omega_terracore = round(sum(score_terms) / len(score_terms), 4)
        return {
            "omega_terracore": omega_terracore,
            "viable": hab.get("viable"),
            "closed_loop": closed_loop,
            "crew_count": crew_count,
            "mission_days": mission_days,
            "volume_ok": hab.get("volume_ok"),
            "power_ok": hab.get("power_ok"),
            "mass_ok": hab.get("mass_ok"),
            "habitat_volume_m3": hab.get("life_support", {}).get("habitat_volume_m3"),
            "eclss_power_w": hab.get("life_support", {}).get("eclss_power_w"),
            "terracore_available": hab.get("terracore_available"),
            "recommendation": hab.get("recommendation"),
            "satellite_omega": report.omega,
        }
    except Exception:
        return None
    try:
        r_earth = constants_mod.R_EARTH_M
        mu = constants_mod.MU_EARTH
        a = r_earth + altitude_km * 1000.0
        period_s = 2.0 * math.pi * math.sqrt((a ** 3) / mu)
        v_circ = math.sqrt(mu / a)
        elements = contracts_mod.OrbitalElements(
            semi_major_axis_m=a,
            eccentricity=eccentricity,
            inclination_rad=math.radians(inclination_deg),
            raan_rad=0.0,
            arg_of_perigee_rad=0.0,
            mean_anomaly_rad=0.0,
        )
        state = contracts_mod.OrbitalState(
            elements=elements,
            pos_eci_m=(a, 0.0, 0.0),
            vel_eci_ms=(0.0, v_circ, 0.0),
            altitude_m=altitude_km * 1000.0,
            period_s=period_s,
            orbit_type="LEO",
            time_s=0.0,
        )
        oh = health_mod.observe_orbital_health(
            state,
            mass_kg=mass_kg,
            area_m2=area_m2,
            delta_v_remaining_ms=delta_v_remaining_ms,
        )
        return {
            "omega_orb": oh.omega_orb,
            "anomaly_detected": oh.anomaly_detected,
            "anomaly_notes": list(oh.anomaly_notes),
            "altitude_health": oh.altitude_health,
            "drag_health": oh.drag_health,
            "maneuver_budget_health": oh.maneuver_budget_health,
        }
    except Exception:
        return None
