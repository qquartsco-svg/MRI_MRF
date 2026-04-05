"""
Layer 1b — Gate-to-Gate Resonance Matching
============================================

두 개의 자기공명 게이트(노드)가 있을 때:
  1) 각 게이트의 라모어 주파수 계산
  2) 주파수 불일치(detuning) 측정
  3) 공명 결합 효율 산출 — Tesla 주파수 응답 함수 모델
  4) 거리 계산

결합 효율:
    H(r) = 1 / √((1 − r²)² + (2ζr)²)
    r = f_B / f_A     (주파수 비)
    ζ = 감쇠비 (기본 0.02 — 초전도 공진기 수준)

이 모듈은 FrequencyCore_Engine의 공명 수식을 NMR 게이트에 특화한 것.
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    GYROMAGNETIC_RATIOS,
    GateNode,
    GatePairResonance,
    ResonanceMatchState,
)


def _gate_freq_hz(node: GateNode) -> float:
    gamma = GYROMAGNETIC_RATIOS.get(node.nucleus)
    if gamma is None:
        raise ValueError(f"Unknown nucleus '{node.nucleus}'")
    return gamma * node.field_strength_t / (2 * math.pi)


def _distance_km(a: GateNode, b: GateNode) -> float:
    dx = a.position_km[0] - b.position_km[0]
    dy = a.position_km[1] - b.position_km[1]
    dz = a.position_km[2] - b.position_km[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _match_state(frac: float) -> ResonanceMatchState:
    if frac < 0.01:
        return ResonanceMatchState.LOCKED
    if frac < 0.05:
        return ResonanceMatchState.NEAR
    if frac < 0.15:
        return ResonanceMatchState.DETUNED
    return ResonanceMatchState.DISCONNECTED


def _coupling_efficiency(freq_a: float, freq_b: float, damping: float = 0.02) -> float:
    """Tesla frequency response coupling."""
    if freq_a <= 0:
        return 0.0
    r = freq_b / freq_a
    denom_sq = (1 - r * r) ** 2 + (2 * damping * r) ** 2
    if denom_sq < 1e-20:
        return 1.0
    h = 1.0 / math.sqrt(denom_sq)
    return min(1.0, math.tanh(h * damping * 4))


def analyze_gate_pair(a: GateNode, b: GateNode, damping: float = 0.02) -> GatePairResonance:
    """두 게이트 간 공명 분석."""
    fa = _gate_freq_hz(a)
    fb = _gate_freq_hz(b)
    detuning = abs(fa - fb)
    frac = detuning / fa if fa > 0 else 1.0
    dist = _distance_km(a, b)
    coup = _coupling_efficiency(fa, fb, damping)

    return GatePairResonance(
        gate_a_id=a.gate_id,
        gate_b_id=b.gate_id,
        freq_a_hz=fa,
        freq_b_hz=fb,
        detuning_hz=round(detuning, 2),
        detuning_fraction=round(frac, 6),
        match_state=_match_state(frac),
        coupling_efficiency=round(coup, 4),
        distance_km=round(dist, 3),
    )


def analyze_gate_network(nodes: List[GateNode], damping: float = 0.02) -> List[GatePairResonance]:
    """모든 노드 쌍에 대해 공명 분석."""
    pairs: List[GatePairResonance] = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            pairs.append(analyze_gate_pair(nodes[i], nodes[j], damping))
    return pairs
