"""
Layer 1a — Larmor / NMR Resonance
==================================

라모어 방정식:
    ω₀ = γ · B₀

    ω₀  : 공명 각주파수 (rad/s)
    γ   : 자기회전비 (rad/(s·T))  — 핵종마다 고유
    B₀  : 외부 자기장 세기 (T)

    → f₀ = ω₀ / (2π)
    → λ  = c / f₀
    → E  = h · f₀    (단일 광자 에너지)

이 모듈은 주어진 핵종과 자기장에서:
  - 공명 주파수·파장·에너지를 산출
  - 여러 핵종의 스펙트럼 비교
"""
from __future__ import annotations

import math

from .contracts import (
    GYROMAGNETIC_RATIOS,
    SPEED_OF_LIGHT_M_S,
    LarmorInput,
    LarmorResult,
)

PLANCK_J_S: float = 6.626e-34


def larmor_frequency(inp: LarmorInput) -> LarmorResult:
    """라모어 공명 주파수 산출."""
    gamma = GYROMAGNETIC_RATIOS.get(inp.nucleus)
    if gamma is None:
        raise ValueError(f"Unknown nucleus '{inp.nucleus}'. Available: {list(GYROMAGNETIC_RATIOS.keys())}")

    omega = gamma * inp.field_strength_t
    freq_hz = omega / (2 * math.pi)
    freq_mhz = freq_hz / 1e6
    wavelength = SPEED_OF_LIGHT_M_S / freq_hz if freq_hz > 0 else float("inf")
    energy_j = PLANCK_J_S * freq_hz
    energy_ev = energy_j / 1.602e-19

    return LarmorResult(
        nucleus=inp.nucleus,
        gamma_rad_per_s_t=gamma,
        field_strength_t=inp.field_strength_t,
        omega_rad_per_s=omega,
        frequency_hz=freq_hz,
        frequency_mhz=round(freq_mhz, 4),
        wavelength_m=round(wavelength, 4),
        photon_energy_ev=energy_ev,
    )


def compare_nuclei(field_t: float, nuclei: list[str] | None = None) -> list[LarmorResult]:
    """여러 핵종의 라모어 주파수 비교."""
    if nuclei is None:
        nuclei = list(GYROMAGNETIC_RATIOS.keys())
    return [larmor_frequency(LarmorInput(nucleus=n, field_strength_t=field_t)) for n in nuclei]
