"""
Layer 2a — Magnetic Confinement Screening
===========================================

자기 가두기(Magnetic Confinement)의 기초 스크리닝.
"우주 진공에서 플라즈마를 자기장으로 가둬 대류를 만든다"는 아이디어의 물리 기반.

핵심 물리:

1) 자기거울비 (Mirror Ratio):
   R = B_max / B_min
   손실원뿔각: sin²θ_loss = 1/R

2) 전자 자이로 반경 (Larmor radius):
   r_g = m·v_⊥ / (q·B)
   v_th = √(2·k_B·T / m)   (T in eV → k_B·T = eV × 1.602e-19)

3) 플라즈마 β (자기압 대비):
   β = n·k_B·T / (B²/(2μ₀))
   β < 1: 자기장이 플라즈마를 제어
   β > 1: 플라즈마가 자기장 벗어남

4) 간이 가두기 시간:
   τ ∝ R · L / v_th   (R = mirror ratio, L = 가두기 길이)
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    BOLTZMANN_J_PER_K,
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    MU_0,
    ConfinementInput,
    ConfinementMode,
    ConfinementResult,
)


def _thermal_velocity(temp_ev: float, mass_kg: float = ELECTRON_MASS_KG) -> float:
    """열 속도 v_th = √(2 k_B T / m).  T given in eV."""
    energy_j = temp_ev * ELEMENTARY_CHARGE_C
    return math.sqrt(2 * energy_j / mass_kg)


def _gyro_radius(v_perp: float, b: float, mass_kg: float = ELECTRON_MASS_KG, charge_c: float = ELEMENTARY_CHARGE_C) -> float:
    if b <= 0:
        return float("inf")
    return mass_kg * v_perp / (charge_c * b)


def _plasma_beta(density_m3: float, temp_ev: float, b_t: float) -> float:
    p_plasma = density_m3 * temp_ev * ELEMENTARY_CHARGE_C
    p_mag = b_t ** 2 / (2 * MU_0)
    if p_mag <= 0:
        return float("inf")
    return p_plasma / p_mag


def screen_confinement(inp: ConfinementInput) -> ConfinementResult:
    """자기 가두기 스크리닝.

    Returns
    -------
    ConfinementResult
        mirror_ratio, loss_cone, gyro_radius, beta, τ, Ω 등.
    """
    advisories: List[str] = []

    if inp.b_min_t <= 0:
        raise ValueError("b_min_t must be > 0")
    mirror_ratio = inp.b_max_t / inp.b_min_t
    loss_cone_rad = math.asin(min(1.0, 1.0 / math.sqrt(mirror_ratio)))
    loss_cone_deg = math.degrees(loss_cone_rad)

    v_th = _thermal_velocity(inp.plasma_temp_ev)
    rg = _gyro_radius(v_th, inp.b_min_t)
    beta = _plasma_beta(inp.plasma_density_m3, inp.plasma_temp_ev, inp.b_min_t)

    if beta > 1.0:
        advisories.append(f"β={beta:.2f} > 1 — plasma pressure exceeds magnetic pressure; confinement unstable.")
    if mirror_ratio < 2.0:
        advisories.append(f"Mirror ratio {mirror_ratio:.2f} is low — large loss cone, poor confinement.")
    if rg > inp.coil_radius_m * 0.1:
        advisories.append("Gyro radius > 10% of coil radius — particle orbits may not fit.")

    # Simple confinement time proxy: τ ∝ R·L/v_th (not a rigorous Lawson)
    tau = mirror_ratio * inp.confinement_length_m / v_th if v_th > 0 else 0.0

    # Ω scoring
    omega = 0.0
    if mirror_ratio >= 2.0:
        omega += 0.30 * min(mirror_ratio / 10.0, 1.0)
    if beta < 1.0:
        omega += 0.30 * (1.0 - beta)
    if rg < inp.coil_radius_m * 0.01:
        omega += 0.20
    elif rg < inp.coil_radius_m * 0.1:
        omega += 0.10
    if tau > 1e-3:
        omega += 0.20 * min(math.log10(tau + 1e-10) / 3 + 1, 1.0)
    omega = round(max(0.0, min(1.0, omega)), 4)

    return ConfinementResult(
        mode=inp.mode,
        mirror_ratio=round(mirror_ratio, 4),
        loss_cone_deg=round(loss_cone_deg, 4),
        gyro_radius_m=rg,
        plasma_beta=round(beta, 6),
        confinement_time_proxy_s=tau,
        omega_confinement=omega,
        advisories=advisories,
    )
