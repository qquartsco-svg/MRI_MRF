"""
MRI Layer 4 — SNR Model
=========================

MRI 신호 대 잡음비(SNR) 기초 모델.

핵심 물리:

1) 기본 SNR:
   SNR₀ ∝ B₀ · V_voxel · SI / √(BW · T_body)

2) 평균 효과:
   SNR = SNR₀ · √N_avg

3) 병렬 코일 효과 (간소화):
   SNR_parallel ≈ SNR · √N_ch × g_factor
   g_factor ≈ 1 (비가속, 최적)

실제 SNR은 코일 형상, 부하 조건, 시퀀스 효율 등에 크게 의존하므로
이 모델은 screening proxy이다.

공유 연결:
- Gate 경로의 rf_energy_transfer.py에서 link_margin이
  MRI에서의 SNR과 물리적으로 같은 "수신 에너지 / 잡음" 비율
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    BOLTZMANN_J_PER_K,
    SNRInput,
    SNRResult,
)


def screen_snr(inp: SNRInput) -> SNRResult:
    """SNR 스크리닝."""
    advisories: List[str] = []

    voxel_vol = inp.voxel_size_mm3[0] * inp.voxel_size_mm3[1] * inp.voxel_size_mm3[2]

    noise_proxy = math.sqrt(inp.receiver_bandwidth_hz * inp.body_temp_k * BOLTZMANN_J_PER_K)

    snr_0 = (inp.b0_field_t * voxel_vol * inp.signal_intensity) / (noise_proxy * 1e12) if noise_proxy > 0 else 0.0
    snr_avg = snr_0 * math.sqrt(inp.n_averages)
    snr_par = snr_avg * math.sqrt(inp.coil_channels)

    if voxel_vol < 1.0:
        advisories.append(f"Voxel {voxel_vol:.2f} mm³ is very small — expect low SNR.")
    if inp.receiver_bandwidth_hz > 100_000:
        advisories.append(f"BW {inp.receiver_bandwidth_hz/1e3:.0f} kHz is wide — more noise.")
    if snr_par < 5:
        advisories.append("Final SNR < 5 — image may be non-diagnostic.")

    omega = 0.0
    if snr_par >= 30:
        omega += 0.40
    elif snr_par >= 10:
        omega += 0.40 * (snr_par - 10) / 20
    elif snr_par >= 5:
        omega += 0.10
    omega += 0.20 * min(voxel_vol / 10.0, 1.0)
    omega += 0.20 * min(inp.b0_field_t / 7.0, 1.0)
    omega += 0.20 * min(inp.coil_channels / 64.0, 1.0)
    omega = round(max(0.0, min(1.0, omega)), 4)

    return SNRResult(
        voxel_volume_mm3=round(voxel_vol, 4),
        thermal_noise_proxy=noise_proxy,
        snr_0=round(snr_0, 4),
        snr_with_averages=round(snr_avg, 4),
        snr_with_parallel=round(snr_par, 4),
        omega_snr=omega,
        advisories=advisories,
    )
