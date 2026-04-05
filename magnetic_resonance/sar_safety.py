"""
MRI Layer 5 — SAR & dB/dt Safety
==================================

환자 안전 한계 스크리닝 (IEC 60601-2-33 기반 간소화).

핵심 물리:

1) 전신 SAR (Whole-body SAR):
   SAR ∝ σ · B₁² · f₀² · duty_cycle · body_factor

   간소화 proxy:
   SAR_wb ≈ k · (B₀ · α · duty / TR)² / body_mass
   k 는 조직 전도도·형상 통합 상수

2) IEC 한계:
   Normal mode    : 2 W/kg (whole-body)
   First level    : 4 W/kg
   Second level   : > 4 W/kg (연구용, 별도 승인)

3) dB/dt 한계:
   dB/dt = B₁_peak / t_rise
   IEC 일반: 20 T/s (cardiac stimulation threshold 기준)

공유 연결:
- Gate 경로에서는 "SAR"이 아닌 "플라즈마 에너지 주입 한계"로 변환
  (물리: 전자기 에너지 흡수율 → 매질이 인체가 아닌 플라즈마)
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    GYROMAGNETIC_RATIOS,
    SARInput,
    SARResult,
)

SAR_NORMAL_LIMIT = 2.0    # W/kg
SAR_FIRST_LIMIT = 4.0     # W/kg
DBDT_LIMIT = 20.0          # T/s


def screen_sar(inp: SARInput) -> SARResult:
    """SAR 안전 스크리닝."""
    advisories: List[str] = []

    gamma = GYROMAGNETIC_RATIOS.get("1H", 2.6752e8)
    f0 = gamma * inp.b0_field_t / (2 * math.pi)

    alpha_rad = math.radians(inp.flip_angle_deg)
    t_pulse_s = inp.pulse_duration_ms / 1e3
    tr_s = inp.tr_ms / 1e3

    b1_peak = alpha_rad / (gamma * t_pulse_s) if t_pulse_s > 0 else 0.0

    k_sar = 0.4
    sar_proxy = k_sar * (f0 ** 2) * (b1_peak ** 2) * inp.duty_cycle / max(inp.body_mass_kg, 1.0)
    sar_proxy = sar_proxy / 1e10

    limit = SAR_FIRST_LIMIT if inp.mode == "first_level" else SAR_NORMAL_LIMIT
    sar_frac = sar_proxy / limit if limit > 0 else float("inf")

    db_dt = b1_peak / t_pulse_s if t_pulse_s > 0 else 0.0
    db_dt_ok = db_dt <= DBDT_LIMIT
    sar_ok = sar_proxy <= limit

    if not sar_ok:
        advisories.append(f"SAR {sar_proxy:.2f} W/kg > {limit} W/kg ({inp.mode}) — reduce flip angle, increase TR, or lower duty cycle.")
    if sar_frac > 0.8 and sar_ok:
        advisories.append(f"SAR at {sar_frac*100:.0f}% of limit — close to threshold.")
    if not db_dt_ok:
        advisories.append(f"dB/dt {db_dt:.1f} T/s > {DBDT_LIMIT} T/s — peripheral nerve stimulation risk.")

    omega = 0.0
    if sar_ok:
        omega += 0.35 * (1.0 - min(sar_frac, 1.0))
    if db_dt_ok:
        omega += 0.35 * (1.0 - min(db_dt / DBDT_LIMIT, 1.0))
    omega += 0.30 * (1.0 - min(len(advisories) / 3, 1.0))
    omega = round(max(0.0, min(1.0, omega)), 4)

    return SARResult(
        whole_body_sar_w_per_kg=round(sar_proxy, 4),
        sar_limit_w_per_kg=limit,
        sar_fraction=round(sar_frac, 4),
        db_dt_t_per_s=round(db_dt, 4),
        db_dt_limit_t_per_s=DBDT_LIMIT,
        db_dt_ok=db_dt_ok,
        sar_ok=sar_ok,
        omega_safety=omega,
        advisories=advisories,
    )
