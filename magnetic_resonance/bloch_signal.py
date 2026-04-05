"""
MRI Layer 3 — Bloch Signal Model
==================================

블로흐 방정식 기반 MRI 신호 모델.

핵심 물리:

1) 종축 이완 (T₁ recovery):
   M_z(t) = M_0 · (1 − e^{−t/T₁})

2) 횡축 이완 (T₂ / T₂* decay):
   M_xy(t) = M_0 · e^{−t/T₂}      (spin echo)
   M_xy(t) = M_0 · e^{−t/T₂*}     (gradient echo)

3) 정상 상태 신호 (spoiled GRE):
   S ∝ PD · sinα · (1 − E₁) / (1 − cosα·E₁) · E₂
   E₁ = e^{−TR/T₁},  E₂ = e^{−TE/T₂*}

4) 에른스트 각 (최대 SNR):
   α_Ernst = arccos(E₁)

5) 가중(weighting):
   T₁W: short TR, short TE
   T₂W: long TR, long TE
   PDW: long TR, short TE

공유 연결:
- 이 모듈의 "조직 이완"은 MRI 전용이지만,
  Gate 경로의 "공명 결합 지속시간"과 수학적 구조가 같음
  (지수 감쇠 + 정상 상태 = 동일 미분방정식)
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    BlochInput,
    BlochResult,
)


def screen_bloch_signal(inp: BlochInput) -> BlochResult:
    """블로흐 신호 스크리닝."""
    advisories: List[str] = []

    t1_s = inp.tissue.t1_ms / 1e3
    t2_s = inp.tissue.t2_ms / 1e3
    t2s_s = inp.tissue.t2_star_ms / 1e3
    tr_s = inp.tr_ms / 1e3
    te_s = inp.te_ms / 1e3
    alpha = math.radians(inp.flip_angle_deg)

    if te_s > t2_s and inp.sequence_type == "spin_echo":
        advisories.append(f"TE ({inp.te_ms} ms) > T₂ ({inp.tissue.t2_ms} ms) — heavy signal loss.")
    if te_s > t2s_s and inp.sequence_type == "gradient_echo":
        advisories.append(f"TE ({inp.te_ms} ms) > T₂* ({inp.tissue.t2_star_ms} ms) — extreme signal loss.")

    e1 = math.exp(-tr_s / t1_s) if t1_s > 0 else 0.0
    mz_recovery = 1.0 - e1

    if inp.sequence_type == "spin_echo":
        e2 = math.exp(-te_s / t2_s) if t2_s > 0 else 0.0
    else:
        e2 = math.exp(-te_s / t2s_s) if t2s_s > 0 else 0.0

    sin_a = math.sin(alpha)
    cos_a = math.cos(alpha)
    denom = 1.0 - cos_a * e1
    mxy = sin_a * (1 - e1) / denom * e2 if denom != 0 else 0.0

    si = inp.tissue.proton_density * mxy

    ernst_rad = math.acos(e1) if 0 < e1 < 1 else 0.0
    ernst_deg = math.degrees(ernst_rad)

    t1w = 1.0 - mz_recovery
    t2w = 1.0 - e2

    if mxy < 0.05:
        advisories.append(f"Signal intensity proxy {mxy:.3f} is very low.")
    if abs(inp.flip_angle_deg - ernst_deg) > 30:
        advisories.append(f"Flip angle {inp.flip_angle_deg}° far from Ernst angle {ernst_deg:.1f}° — not SNR-optimal for steady-state.")

    omega = 0.0
    omega += 0.30 * min(si / 0.3, 1.0)
    omega += 0.20 * min(mxy / 0.5, 1.0)
    omega += 0.20 * mz_recovery
    if abs(inp.flip_angle_deg - ernst_deg) < 10:
        omega += 0.15
    elif abs(inp.flip_angle_deg - ernst_deg) < 20:
        omega += 0.08
    omega += 0.15 * (1.0 - min(len(advisories) / 3, 1.0))
    omega = round(max(0.0, min(1.0, omega)), 4)

    return BlochResult(
        mz_recovery=round(mz_recovery, 6),
        mxy_at_te=round(mxy, 6),
        signal_intensity=round(si, 6),
        ernst_angle_deg=round(ernst_deg, 2),
        t1_weighting=round(t1w, 4),
        t2_weighting=round(t2w, 4),
        omega_signal=omega,
        advisories=advisories,
    )
