"""
Phase C — Toroidal Geometry (Tokamak / Stellarator)
=====================================================

자기 가두기의 토로이달(도넛) 형상 인자 스크리닝.

핵심 물리:

1) 종횡비 (Aspect Ratio):
   A = R₀ / a
   R₀ = 주반경 (major radius)
   a  = 부반경 (minor radius)
   A < 3: 구형(spherical) 토카막
   A ~ 3–4: 전통 토카막 (ITER)
   A > 5: 슬랜더

2) 안전 인자 (Safety Factor) q:
   q = (a · B_φ) / (R₀ · B_θ)
   B_θ ≈ μ₀ · I_p / (2π·a)    [토카막 근사]
   q > 1: 크루스칼-샤프라노프 안정성 조건
   q > 2: 에지 MHD 안정성 보장

3) 플라즈마 부피:
   V = 2π² · R₀ · a²   (원형 단면 토러스)

4) 그린왈드 밀도 한계:
   n_G = I_p / (π·a²)    [10²⁰ m⁻³, I_p in MA, a in m]
   n_e / n_G < 1 → 안전

5) 회전 변환 (stellarator convention):
   ι = 2π / q
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    MU_0,
    ToroidalInput,
    ToroidalResult,
    ToroidalType,
)


def screen_toroidal(inp: ToroidalInput) -> ToroidalResult:
    """토로이달 형상 스크리닝."""
    advisories: List[str] = []

    if inp.minor_radius_m <= 0 or inp.major_radius_m <= 0:
        raise ValueError("Radii must be > 0")
    if inp.minor_radius_m >= inp.major_radius_m:
        raise ValueError("minor_radius must be < major_radius")

    aspect = inp.major_radius_m / inp.minor_radius_m

    # Safety factor q — tokamak: cylindrical approximation
    b_theta = MU_0 * inp.plasma_current_ma * 1e6 / (2 * math.pi * inp.minor_radius_m)
    q = (inp.minor_radius_m * inp.toroidal_field_t) / (inp.major_radius_m * b_theta) if b_theta > 0 else float("inf")
    ks_ok = q > 1.0
    iota = 2 * math.pi / q if q > 0 and q != float("inf") else 0.0

    volume = 2 * math.pi ** 2 * inp.major_radius_m * inp.minor_radius_m ** 2

    # Greenwald density limit: n_G = I_p(MA) / (π·a²) → units 10²⁰ m⁻³
    n_g_1e20 = inp.plasma_current_ma / (math.pi * inp.minor_radius_m ** 2)
    n_g_m3 = n_g_1e20 * 1e20
    gw_frac = inp.electron_density_m3 / n_g_m3 if n_g_m3 > 0 else float("inf")

    if not ks_ok:
        advisories.append(f"q={q:.2f} < 1 — Kruskal-Shafranov instability expected.")
    if q < 2:
        advisories.append(f"q={q:.2f} < 2 — edge MHD stability marginal.")
    if gw_frac > 1.0:
        advisories.append(f"n_e/n_G = {gw_frac:.2f} > 1 — Greenwald density limit exceeded, disruption risk.")
    if aspect < 2.0:
        advisories.append(f"A={aspect:.2f} — extremely tight aspect ratio, non-standard.")

    # Ω scoring
    omega = 0.0
    if ks_ok:
        omega += 0.25
    if q >= 2.0:
        omega += 0.15 * min(q / 5.0, 1.0)
    if gw_frac < 0.85:
        omega += 0.25 * (1.0 - gw_frac / 0.85)
    elif gw_frac < 1.0:
        omega += 0.05
    if 2.5 <= aspect <= 5.0:
        omega += 0.20
    elif aspect > 5.0:
        omega += 0.10
    omega += 0.15 * min(volume / 1000.0, 1.0)
    omega = round(max(0.0, min(1.0, omega)), 4)

    return ToroidalResult(
        device_type=inp.device_type,
        aspect_ratio=round(aspect, 4),
        safety_factor_q=round(q, 4),
        kruskal_shafranov_ok=ks_ok,
        plasma_volume_m3=round(volume, 4),
        greenwald_density_limit_m3=n_g_m3,
        greenwald_fraction=round(gw_frac, 4),
        rotational_transform=round(iota, 6),
        omega_geometry=omega,
        advisories=advisories,
    )
