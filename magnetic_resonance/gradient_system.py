"""
MRI Layer 1 — Gradient System
===============================

경사장(gradient coil) 시스템의 기초 스크리닝.
MRI에서 "어느 위치의 공명을 켜고 끌 것인가"를 결정하는 핵심 하드웨어.

핵심 물리:

1) 공간 인코딩:
   Δω(x) = γ · G · x
   x 위치의 공명 주파수 = 중심 주파수 + γ·G·x

2) 픽셀 대역폭:
   Δf_pixel = γ/(2π) · G · Δx
   Δx = FOV / matrix_size

3) 라이즈 타임:
   t_rise = G_max / slew_rate

4) 최소 인코딩 시간:
   t_enc = matrix_size / (γ/(2π) · G · FOV)

공유 연결:
- larmor.py의 γ 를 그대로 사용 → MRI와 Gate 동일 물리 기반
- Gate에서는 G·x 대신 "노드별 B₀ 차이"로 detuning 제어
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    GYROMAGNETIC_RATIOS,
    GradientInput,
    GradientResult,
)


def screen_gradient(inp: GradientInput) -> GradientResult:
    """경사장 시스템 스크리닝."""
    advisories: List[str] = []

    gamma = GYROMAGNETIC_RATIOS.get(inp.nucleus)
    if gamma is None:
        raise ValueError(f"Unknown nucleus '{inp.nucleus}'")
    gamma_hz = gamma / (2 * math.pi)

    g_t_per_m = inp.max_amplitude_mt_per_m * 1e-3
    resolution_m = inp.fov_m / inp.matrix_size
    resolution_mm = resolution_m * 1e3

    pixel_bw = gamma_hz * g_t_per_m * resolution_m
    readout_bw = pixel_bw * inp.matrix_size

    rise_time_s = g_t_per_m / inp.max_slew_rate_t_per_m_per_s if inp.max_slew_rate_t_per_m_per_s > 0 else float("inf")
    rise_time_ms = rise_time_s * 1e3

    min_enc_time_s = inp.matrix_size / (gamma_hz * g_t_per_m * inp.fov_m) if (gamma_hz * g_t_per_m * inp.fov_m) > 0 else float("inf")
    min_enc_time_ms = min_enc_time_s * 1e3

    duty = 2 * rise_time_s / (min_enc_time_s + 2 * rise_time_s) if (min_enc_time_s + 2 * rise_time_s) > 0 else 1.0

    if inp.max_amplitude_mt_per_m < 20:
        advisories.append(f"Gradient amplitude {inp.max_amplitude_mt_per_m} mT/m is low — limited resolution or FOV.")
    if inp.max_slew_rate_t_per_m_per_s < 100:
        advisories.append(f"Slew rate {inp.max_slew_rate_t_per_m_per_s} T/m/s is slow — PNS risk lower but longer encoding.")
    if resolution_mm > 3.0:
        advisories.append(f"Resolution {resolution_mm:.1f} mm is coarse for diagnostic imaging.")

    omega = 0.0
    if resolution_mm <= 1.0:
        omega += 0.30
    elif resolution_mm <= 2.0:
        omega += 0.20
    elif resolution_mm <= 3.0:
        omega += 0.10
    omega += 0.25 * min(inp.max_amplitude_mt_per_m / 80.0, 1.0)
    omega += 0.25 * min(inp.max_slew_rate_t_per_m_per_s / 200.0, 1.0)
    if min_enc_time_ms < 10:
        omega += 0.20
    elif min_enc_time_ms < 50:
        omega += 0.10
    omega = round(max(0.0, min(1.0, omega)), 4)

    return GradientResult(
        pixel_bandwidth_hz=round(pixel_bw, 2),
        min_encoding_time_ms=round(min_enc_time_ms, 4),
        spatial_resolution_mm=round(resolution_mm, 4),
        max_readout_bandwidth_hz=round(readout_bw, 2),
        rise_time_ms=round(rise_time_ms, 4),
        duty_cycle_limit=round(duty, 4),
        omega_gradient=omega,
        advisories=advisories,
    )
