"""
Layer 2b — Magnetic Thermal Transport (Plasma Convection)
==========================================================

"우주 진공에서 자기장으로 가둔 플라즈마가 열을 운반한다"는 경로의 스크리닝.

핵심:
  열 운반 용량 Q_cap ≈ n · k_B · T · v_th · A_cross

  n      : 플라즈마 밀도 (m⁻³)
  k_B·T  : 플라즈마 온도 에너지 (J)
  v_th   : 열 속도 (m/s)
  A_cross: 자기 루프 단면적 (m²)

이건 지상 데이터센터의 "ṁ·cp·ΔT"를 플라즈마 버전으로 읽는 것이다.
차이:
  - 지상: 공기 밀도 ~1.2 kg/m³, cp ~1005 J/(kg·K)
  - 우주 플라즈마: 밀도가 극히 낮지만 온도가 수 eV~keV로 높을 수 있음
"""
from __future__ import annotations

import math

from .contracts import (
    BOLTZMANN_J_PER_K,
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    MagneticThermalInput,
    MagneticThermalResult,
    ThermalPathMode,
)


def _thermal_velocity_m_s(temp_ev: float, mass_kg: float = ELECTRON_MASS_KG) -> float:
    return math.sqrt(2 * temp_ev * ELEMENTARY_CHARGE_C / mass_kg)


def screen_magnetic_thermal(inp: MagneticThermalInput) -> MagneticThermalResult:
    """플라즈마 대류 열 운반 스크리닝.

    Returns Ω_thermal_transport and capacity estimate.
    """
    v_th = _thermal_velocity_m_s(inp.plasma_temp_ev)
    energy_per_particle_j = inp.plasma_temp_ev * ELEMENTARY_CHARGE_C
    q_cap = inp.plasma_density_m3 * energy_per_particle_j * v_th * inp.loop_cross_section_m2
    headroom = q_cap - inp.heat_load_w

    if q_cap <= 0:
        omega = 0.0
        path = ThermalPathMode.RADIATIVE_ONLY
        adv = "Plasma thermal capacity ≈ 0; fall back to radiative rejection."
    elif headroom < 0:
        ratio = q_cap / inp.heat_load_w
        omega = round(ratio * 0.5, 4)
        path = ThermalPathMode.PLASMA_CONVECTION
        adv = f"Plasma capacity {q_cap:.1f} W < load {inp.heat_load_w:.1f} W; supplement with radiation."
    else:
        omega = round(min(1.0, 0.5 + 0.5 * headroom / max(inp.heat_load_w, 1)), 4)
        path = ThermalPathMode.PLASMA_CONVECTION
        adv = f"Plasma convection can carry ~{q_cap:.1f} W with {headroom:.1f} W headroom."

    return MagneticThermalResult(
        path_mode=path,
        thermal_velocity_m_s=v_th,
        heat_capacity_w=round(q_cap, 4),
        heat_load_w=inp.heat_load_w,
        headroom_w=round(headroom, 4),
        omega_thermal_transport=omega,
        advisory=adv,
    )
