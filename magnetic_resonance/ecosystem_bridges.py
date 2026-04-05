"""
Ecosystem Bridges — 형제 엔진 느슨한 결합
==========================================

FrequencyCore     → 공명 분석 재사용
Superconducting   → 코일/자기장 설계
SpaceThermal      → 복사+대류 병렬 비교
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Dict, Optional

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
