"""
MRI Layer 2 — RF Pulse Design
===============================

RF 여기 펄스의 기초 스크리닝.

핵심 물리:

1) 슬라이스 선택 대역폭:
   BW = γ/(2π) · G_slice · Δz
   Δz = 슬라이스 두께

2) 펄스 길이 (sinc):
   T_pulse = TBW / BW
   TBW = time-bandwidth product (전형적 4)

3) B₁ 피크 (hard pulse 기준):
   B₁ = α / (γ · T_pulse)
   α = flip angle (rad)

4) 펄스 에너지 proxy:
   E ∝ B₁² · T_pulse

공유 연결:
- γ 는 larmor.py에서 공유
- Gate 경로의 rf_energy_transfer.py는 같은 RF 물리의 "먼 거리" 버전
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    GYROMAGNETIC_RATIOS,
    RFPulseInput,
    RFPulseResult,
    RFPulseType,
)


def screen_rf_pulse(inp: RFPulseInput) -> RFPulseResult:
    """RF 펄스 스크리닝."""
    advisories: List[str] = []

    gamma = GYROMAGNETIC_RATIOS.get("1H", 2.6752e8)
    gamma_hz = gamma / (2 * math.pi)

    g_t_per_m = inp.gradient_amplitude_mt_per_m * 1e-3
    bw = gamma_hz * g_t_per_m * inp.slice_thickness_m
    if bw <= 0:
        bw = 1000.0
        advisories.append("Calculated bandwidth ≤ 0; defaulting to 1 kHz.")

    t_pulse_s = inp.time_bandwidth_product / bw if bw > 0 else 0.01
    t_pulse_ms = t_pulse_s * 1e3

    alpha_rad = math.radians(inp.flip_angle_deg)

    if inp.pulse_type == RFPulseType.HARD:
        b1_peak = alpha_rad / (gamma * t_pulse_s) if t_pulse_s > 0 else 0.0
        shape_factor = 1.0
    elif inp.pulse_type == RFPulseType.SINC:
        b1_peak = alpha_rad * inp.time_bandwidth_product / (gamma * t_pulse_s * math.pi) if t_pulse_s > 0 else 0.0
        shape_factor = 0.45
    else:
        b1_peak = alpha_rad / (gamma * t_pulse_s * 0.4697) if t_pulse_s > 0 else 0.0
        shape_factor = 0.37

    b1_peak_ut = b1_peak * 1e6
    b1_rms_ut = b1_peak_ut * math.sqrt(shape_factor)
    energy_proxy = (b1_peak ** 2) * t_pulse_s * shape_factor

    if b1_peak_ut > 25:
        advisories.append(f"B₁ peak {b1_peak_ut:.1f} μT is high — check amplifier limits and SAR.")
    if t_pulse_ms > 10:
        advisories.append(f"Pulse duration {t_pulse_ms:.1f} ms is long — chemical shift artefacts may increase.")
    if t_pulse_ms < 0.5:
        advisories.append(f"Pulse duration {t_pulse_ms:.2f} ms is very short — high bandwidth demand on amplifier.")

    omega = 0.0
    if 1.0 <= t_pulse_ms <= 5.0:
        omega += 0.30
    elif 0.5 <= t_pulse_ms < 1.0 or 5.0 < t_pulse_ms <= 10.0:
        omega += 0.15
    if b1_peak_ut < 20:
        omega += 0.25
    elif b1_peak_ut < 30:
        omega += 0.10
    omega += 0.25 * min(bw / 5000.0, 1.0)
    omega += 0.20 * (1.0 - min(energy_proxy / 1e-8, 1.0))
    omega = round(max(0.0, min(1.0, omega)), 4)

    return RFPulseResult(
        pulse_duration_ms=round(t_pulse_ms, 4),
        bandwidth_hz=round(bw, 2),
        b1_peak_ut=round(b1_peak_ut, 4),
        b1_rms_ut=round(b1_rms_ut, 4),
        pulse_energy_j=energy_proxy,
        omega_rf_pulse=omega,
        advisories=advisories,
    )
