"""
Phase E — Lagrange Point Stability & Orbital Mechanics
========================================================

지구-달 (또는 임의 이체) 계의 라그랑주 점 안정성 분석.

핵심 물리:

1) 질량비:
   μ = M₂ / (M₁ + M₂)

2) L1 위치 (선형 근사):
   r_L1 ≈ R · (μ/3)^{1/3}    [M₂ 쪽에서 측정]
   → M₁에서의 거리 = R − r_L1

3) L2 위치:
   r_L2 ≈ R · (μ/3)^{1/3}    [M₂ 반대편]
   → M₁에서의 거리 = R + r_L2

4) L3 위치:
   r_L3 ≈ R · (1 − 5μ/12)    [M₁ 반대편]

5) L4/L5 안정성:
   Routh 조건: M₁/M₂ > 24.96 → 안정
   (지구/달 ≈ 81.3 → 안정)

6) Hill sphere:
   r_H = R · (M₂ / (3·M₁))^{1/3}

7) L1/L2 불안정 시간 (e-folding):
   τ ~ orbital_period / (2π) · sqrt(factor)
   간소화: τ ≈ T_orbit / (2π·√9) ≈ T_orbit / 18.85

8) Station-keeping ΔV:
   L1/L2: ~5–10 m/s/year (실측)
   L4/L5: ~0 (이론)
"""
from __future__ import annotations

import math
from typing import List, Optional

from .contracts import (
    G_CONST,
    LagrangeInput,
    LagrangePoint,
    LagrangeResult,
    LagrangeStabilityClass,
)

ROUTH_CRITICAL = 24.96


def _orbital_period(m1: float, m2: float, sep: float) -> float:
    """Kepler T = 2π√(a³/(G(M₁+M₂)))."""
    return 2 * math.pi * math.sqrt(sep ** 3 / (G_CONST * (m1 + m2)))


def screen_lagrange(inp: LagrangeInput) -> LagrangeResult:
    """라그랑주 점 스크리닝."""
    advisories: List[str] = []
    m1, m2, R = inp.primary_mass_kg, inp.secondary_mass_kg, inp.separation_m

    if m1 <= 0 or m2 <= 0 or R <= 0:
        raise ValueError("Masses and separation must be > 0")

    mu = m2 / (m1 + m2)
    mass_ratio_12 = m1 / m2 if m2 > 0 else float("inf")

    hill = R * (m2 / (3 * m1)) ** (1 / 3)
    cubic_root = (mu / 3) ** (1 / 3)
    t_orbit = _orbital_period(m1, m2, R)

    if inp.point == LagrangePoint.L1:
        r_from_m2 = R * cubic_root
        dist_primary = R - r_from_m2
        dist_secondary = r_from_m2
    elif inp.point == LagrangePoint.L2:
        r_from_m2 = R * cubic_root
        dist_primary = R + r_from_m2
        dist_secondary = r_from_m2
    elif inp.point == LagrangePoint.L3:
        dist_primary = R * (1 - 5 * mu / 12)
        dist_secondary = R + dist_primary
    elif inp.point in (LagrangePoint.L4, LagrangePoint.L5):
        dist_primary = R
        dist_secondary = R
    else:
        dist_primary = R
        dist_secondary = R

    # Stability classification
    instability_time: Optional[float] = None
    if inp.point in (LagrangePoint.L4, LagrangePoint.L5):
        if mass_ratio_12 > ROUTH_CRITICAL:
            stab_class = LagrangeStabilityClass.STABLE
        else:
            stab_class = LagrangeStabilityClass.UNSTABLE
            advisories.append(f"M₁/M₂ = {mass_ratio_12:.1f} < {ROUTH_CRITICAL} — L4/L5 unstable.")
        annual_dv = 0.0
    else:
        stab_class = LagrangeStabilityClass.QUASI_STABLE
        instability_time = t_orbit / (2 * math.pi * 3)
        annual_dv = 7.5 if inp.point in (LagrangePoint.L1, LagrangePoint.L2) else 12.0

    dv_ok = annual_dv <= inp.station_keeping_dv_budget_m_s

    if not dv_ok:
        advisories.append(
            f"Annual ΔV ~{annual_dv:.1f} m/s > budget {inp.station_keeping_dv_budget_m_s:.1f} m/s."
        )
    if instability_time is not None and instability_time < 86400 * 30:
        advisories.append(f"Instability e-folding ≈ {instability_time / 86400:.1f} days — frequent correction needed.")

    # Ω scoring
    omega = 0.0
    if stab_class == LagrangeStabilityClass.STABLE:
        omega += 0.40
    elif stab_class == LagrangeStabilityClass.QUASI_STABLE:
        omega += 0.20
    if dv_ok:
        omega += 0.25
    if hill > 1e6:
        omega += 0.15
    elif hill > 1e4:
        omega += 0.10
    omega += 0.20 * min(dist_primary / R, 1.0) if dist_primary > 0 else 0.0
    omega = round(max(0.0, min(1.0, omega)), 4)

    return LagrangeResult(
        point=inp.point,
        distance_from_primary_m=round(dist_primary, 2),
        distance_from_secondary_m=round(dist_secondary, 2),
        mass_ratio=round(mu, 8),
        hill_sphere_m=round(hill, 2),
        stability_class=stab_class,
        instability_time_s=round(instability_time, 2) if instability_time is not None else None,
        annual_dv_estimate_m_s=round(annual_dv, 2),
        dv_budget_ok=dv_ok,
        omega_lagrange=omega,
        advisories=advisories,
    )
