"""
Phase B — Plasma Transport Coefficients
=========================================

플라즈마 쿨롱 충돌과 수송 계수의 기초 스크리닝.

핵심 물리:

1) 쿨롱 로그 (Coulomb logarithm):
   ln Λ ≈ 23.5 − ln(n_e^{1/2} · T_e^{-5/4}) − √(10⁻⁵ + (lnT_e − 2)²/16)
   (간소화) ln Λ ≈ 23 − 0.5·ln(n_e) + 1.5·ln(T_e)    [T_e in eV]

2) 전자–이온 충돌 주파수:
   ν_ei = (n_e · Z² · e⁴ · lnΛ) / (12π^{3/2} · ε₀² · m_e^{1/2} · (kT_e)^{3/2})

3) 스피처 저항률 (Spitzer resistivity):
   η = (Z_eff · e² · m_e^{1/2} · lnΛ) / (3(2π)^{3/2} · ε₀² · (kT_e)^{3/2})
   ≈ 5.2 × 10⁻⁵ · Z_eff · lnΛ / T_e^{3/2}   [Ω·m]

4) 평균 자유 경로:
   λ_mfp = v_th / ν_ei

5) 열전도도 (Braginskii 간소화):
   κ_∥ ∝ n_e · T_e · τ_ei / m_e    (자기장 방향)
   κ_⊥ ∝ n_e · T_e / (ω_ce² · τ_ei · m_e)  (자기장 수직)
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    BOLTZMANN_J_PER_K,
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    EPSILON_0,
    PlasmaTransportInput,
    PlasmaTransportResult,
)


def coulomb_logarithm(n_e: float, t_ev: float) -> float:
    """쿨롱 로그 ln Λ — NRL Plasma Formulary 간소화."""
    if n_e <= 0 or t_ev <= 0:
        return 1.0
    return max(1.0, 23.0 - 0.5 * math.log(n_e) + 1.5 * math.log(t_ev))


def collision_frequency_ei(n_e: float, t_ev: float, z: int, ln_lambda: float) -> float:
    """전자–이온 쿨롱 충돌 주파수 ν_ei (Hz)."""
    kt = t_ev * ELEMENTARY_CHARGE_C
    numerator = n_e * z * z * ELEMENTARY_CHARGE_C ** 4 * ln_lambda
    denominator = (12 * math.pi ** 1.5 * EPSILON_0 ** 2
                   * math.sqrt(ELECTRON_MASS_KG) * kt ** 1.5)
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def spitzer_resistivity(t_ev: float, z_eff: int, ln_lambda: float) -> float:
    """스피처 저항률 η (Ω·m)."""
    if t_ev <= 0:
        return float("inf")
    return 5.2e-5 * z_eff * ln_lambda / (t_ev ** 1.5)


def screen_plasma_transport(inp: PlasmaTransportInput) -> PlasmaTransportResult:
    """플라즈마 수송 계수 스크리닝."""
    advisories: List[str] = []

    ln_lam = coulomb_logarithm(inp.electron_density_m3, inp.electron_temp_ev)
    nu_ei = collision_frequency_ei(
        inp.electron_density_m3, inp.electron_temp_ev,
        inp.ion_charge_z, ln_lam,
    )

    eta = spitzer_resistivity(inp.electron_temp_ev, inp.ion_charge_z, ln_lam)

    kt_j = inp.electron_temp_ev * ELEMENTARY_CHARGE_C
    v_th = math.sqrt(2 * kt_j / ELECTRON_MASS_KG) if kt_j > 0 else 0.0
    mfp = v_th / nu_ei if nu_ei > 0 else float("inf")

    # Braginskii parallel thermal conductivity (simplified)
    tau_ei = 1.0 / nu_ei if nu_ei > 0 else float("inf")
    kappa_par = (inp.electron_density_m3 * kt_j * tau_ei / ELECTRON_MASS_KG
                 if tau_ei != float("inf") else 0.0)

    # Perpendicular: κ_⊥ ≈ κ_∥ / (ω_ce·τ_ei)²
    omega_ce = ELEMENTARY_CHARGE_C * inp.b_field_t / ELECTRON_MASS_KG
    wt = omega_ce * tau_ei if tau_ei != float("inf") else float("inf")
    kappa_perp = kappa_par / (wt * wt) if wt > 0 and wt != float("inf") else 0.0

    if ln_lam < 5:
        advisories.append(f"lnΛ={ln_lam:.1f} is low — strongly coupled plasma, Spitzer model inaccurate.")
    if mfp < 0.01:
        advisories.append(f"Mean free path {mfp:.2e} m is very short — collisional regime.")
    if eta > 1e-3:
        advisories.append(f"Spitzer η={eta:.2e} Ω·m — high resistivity, poor conductor.")

    # Ω scoring: 좋은 플라즈마 도체 ≈ 높은 lnΛ, 긴 mfp, 낮은 η
    omega = 0.0
    omega += 0.25 * min(ln_lam / 20.0, 1.0)
    if mfp > 1.0:
        omega += 0.25
    elif mfp > 0.01:
        omega += 0.25 * (math.log10(mfp) + 2) / 2
    if eta < 1e-6:
        omega += 0.25
    elif eta < 1e-3:
        omega += 0.25 * (3 + math.log10(eta + 1e-20)) / 3
    if wt > 10:
        omega += 0.25
    elif wt > 1:
        omega += 0.25 * math.log10(wt)
    omega = round(max(0.0, min(1.0, omega)), 4)

    return PlasmaTransportResult(
        coulomb_log=round(ln_lam, 4),
        collision_freq_hz=nu_ei,
        spitzer_resistivity_ohm_m=eta,
        mean_free_path_m=mfp,
        thermal_conductivity_parallel=kappa_par,
        thermal_conductivity_perp=kappa_perp,
        omega_transport=omega,
        advisories=advisories,
    )
