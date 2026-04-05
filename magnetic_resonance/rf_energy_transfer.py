"""
Phase D — RF / Microwave Energy Transfer Between Gates
========================================================

우주 게이트 간 전자기파(RF/마이크로파) 에너지 전달 스크리닝.

두 게이트가 공명 결합(LOCKED)된 상태에서, 실제로 에너지를 보내려면
전파 링크가 필요하다. 이 모듈은 그 링크 예산(link budget)을 스크리닝.

핵심 물리:

1) 자유공간 경로 손실 (FSPL):
   FSPL = (4πd/λ)²
   FSPL_dB = 20·log₁₀(4πd/λ)

2) 안테나 이득:
   G = η · (πD/λ)²
   G_dBi = 10·log₁₀(G)

3) Friis 전송 방정식:
   P_r = P_t · G_t · G_r · (λ/(4πd))²

4) 빔 발산각 (회절 한계):
   θ_beam ≈ 1.22 · λ / D

5) 수신 전력 → dBm:
   P_dBm = 10·log₁₀(P_r × 1000)

우주 진공: 대기 감쇠 = 0. 순수 FSPL 만 적용.
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    SPEED_OF_LIGHT_M_S,
    RFTransferInput,
    RFTransferResult,
)


def screen_rf_link(inp: RFTransferInput) -> RFTransferResult:
    """RF 링크 예산 스크리닝."""
    advisories: List[str] = []

    if inp.frequency_hz <= 0:
        raise ValueError("frequency_hz must be > 0")
    if inp.distance_m <= 0:
        raise ValueError("distance_m must be > 0")

    lam = SPEED_OF_LIGHT_M_S / inp.frequency_hz

    # FSPL
    fspl_linear = (4 * math.pi * inp.distance_m / lam) ** 2
    fspl_db = 10 * math.log10(fspl_linear) if fspl_linear > 0 else 0.0

    # Antenna gain (parabolic dish model)
    gain_linear = inp.antenna_efficiency * (math.pi * inp.antenna_diameter_m / lam) ** 2
    gain_dbi = 10 * math.log10(gain_linear) if gain_linear > 0 else 0.0

    # Beam divergence
    theta = 1.22 * lam / inp.antenna_diameter_m if inp.antenna_diameter_m > 0 else math.pi

    # Friis: received power
    p_r = inp.transmit_power_w * gain_linear * gain_linear / fspl_linear if fspl_linear > 0 else 0.0
    p_dbm = 10 * math.log10(p_r * 1e3) if p_r > 0 else -999.0

    # Link margin vs reference sensitivity –120 dBm
    sensitivity_dbm = -120.0
    margin_db = p_dbm - sensitivity_dbm

    if margin_db < 0:
        advisories.append(f"Link margin {margin_db:.1f} dB < 0 — signal below receiver sensitivity.")
    elif margin_db < 10:
        advisories.append(f"Link margin {margin_db:.1f} dB — tight budget, consider larger antenna or higher power.")
    if theta > 0.1:
        advisories.append(f"Beam divergence {math.degrees(theta):.2f}° — wide beam at this frequency/antenna size.")

    # Ω scoring
    omega = 0.0
    if margin_db > 30:
        omega += 0.40
    elif margin_db > 10:
        omega += 0.40 * (margin_db - 10) / 20
    elif margin_db > 0:
        omega += 0.10

    if theta < 0.001:
        omega += 0.30
    elif theta < 0.01:
        omega += 0.30 * (1 - theta / 0.01)
    elif theta < 0.1:
        omega += 0.10

    omega += 0.30 * min(gain_dbi / 60.0, 1.0)
    omega = round(max(0.0, min(1.0, omega)), 4)

    return RFTransferResult(
        wavelength_m=round(lam, 6),
        fspl_db=round(fspl_db, 2),
        antenna_gain_dbi=round(gain_dbi, 2),
        beam_divergence_rad=round(theta, 6),
        received_power_w=p_r,
        received_power_dbm=round(p_dbm, 2),
        link_margin_db=round(margin_db, 2),
        omega_link=omega,
        advisories=advisories,
    )
