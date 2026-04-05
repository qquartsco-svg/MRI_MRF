"""
Ecosystem Bridges — 형제 엔진 느슨한 결합
==========================================

FrequencyCore     → 공명 분석 재사용
Superconducting   → 코일/자기장 설계
SpaceThermal      → 복사+대류 병렬 비교
Optics            → 전자기파/파장 screening
Foundry           → 공정/테이프아웃 readiness tick
Manufacturing     → 코일/구조물 제조 readiness

형제 엔진이 없으면 None으로 조용히 degrade 된다.
"""
from __future__ import annotations

import importlib
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
    parent = os.path.dirname(pkg)
    if parent not in sys.path:
        sys.path.insert(0, parent)
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
    """Superconducting_Magnet_Stack → 자기장 설계 조회."""
    mod = _try_import("Superconducting_Magnet_Stack", "superconducting_magnet_stack.electromagnetic")
    if mod is None:
        return None
    try:
        return {"bridge": "superconducting_available"}
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
