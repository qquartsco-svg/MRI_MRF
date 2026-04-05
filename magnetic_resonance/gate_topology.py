"""
Layer 3 — Space Gate Topology
===============================

우주 공간에 배치된 자기공명 게이트 네트워크의 토폴로지 분석.

개념:
  - 각 게이트는 특정 위치에 초전도 코일(또는 대형 자기장 생성기)을 가진 노드
  - 두 게이트가 같은 라모어 주파수에 LOCKED 되면 "공명 채널"이 열림
  - 네트워크 전체의 연결 상태·결합도·경로를 평가

시나리오 프리셋:
  - LEO 궤도 게이트 링
  - 지구–L1–달 삼각 배치
  - 지구–달 직선 중계

이 레이어는 아직 **개념/실험** 영역이 크다.
실측값 없이 위치·자기장·공명 주파수만으로 "이 토폴로지가 물리적으로
얼마나 말이 되는지" 를 Ω와 함께 판정한다.
"""
from __future__ import annotations

import math
from typing import List

from .contracts import (
    GateNode,
    GatePairResonance,
    GateTopology,
    GateVerdict,
)
from .gate_resonance import analyze_gate_network


# ── Preset Scenarios ────────────────────────────────────

EARTH_RADIUS_KM = 6_371.0
MOON_DISTANCE_KM = 384_400.0
L1_EARTH_MOON_KM = 326_000.0  # 지구–달 L1 근사

def preset_leo_ring(n_gates: int = 6, altitude_km: float = 400.0, field_t: float = 3.0) -> List[GateNode]:
    """LEO 궤도 균등 배치 게이트 링."""
    r = EARTH_RADIUS_KM + altitude_km
    nodes: List[GateNode] = []
    for i in range(n_gates):
        angle = 2 * math.pi * i / n_gates
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        nodes.append(GateNode(
            gate_id=f"LEO_{i}",
            position_km=(round(x, 1), round(y, 1), 0.0),
            field_strength_t=field_t,
        ))
    return nodes


def preset_earth_l1_moon(field_t: float = 3.0) -> List[GateNode]:
    """지구 표면 – L1 – 달 표면 삼각 배치."""
    return [
        GateNode(gate_id="Earth_Surface", position_km=(EARTH_RADIUS_KM, 0.0, 0.0), field_strength_t=field_t),
        GateNode(gate_id="L1_EarthMoon", position_km=(L1_EARTH_MOON_KM, 0.0, 0.0), field_strength_t=field_t),
        GateNode(gate_id="Moon_Surface", position_km=(MOON_DISTANCE_KM, 0.0, 0.0), field_strength_t=field_t),
    ]


def preset_earth_moon_relay(n_relays: int = 5, field_t: float = 3.0) -> List[GateNode]:
    """지구–달 직선 중계 체인 (등간격)."""
    nodes: List[GateNode] = []
    for i in range(n_relays):
        x = EARTH_RADIUS_KM + (MOON_DISTANCE_KM - EARTH_RADIUS_KM) * i / (n_relays - 1)
        label = "Earth" if i == 0 else ("Moon" if i == n_relays - 1 else f"Relay_{i}")
        nodes.append(GateNode(gate_id=label, position_km=(round(x, 1), 0.0, 0.0), field_strength_t=field_t))
    return nodes


# ── Topology Evaluator ──────────────────────────────────

def _gate_verdict(omega: float) -> GateVerdict:
    if omega >= 0.80:
        return GateVerdict.OPERATIONAL
    if omega >= 0.50:
        return GateVerdict.MARGINAL
    if omega >= 0.25:
        return GateVerdict.EXPERIMENTAL
    return GateVerdict.CONCEPTUAL


def evaluate_topology(nodes: List[GateNode], damping: float = 0.02) -> GateTopology:
    """게이트 네트워크 토폴로지 평가."""
    pairs = analyze_gate_network(nodes, damping)
    if not pairs:
        return GateTopology(
            nodes=nodes, pairs=[], avg_coupling=0.0, min_coupling=0.0,
            fully_locked_pairs=0, total_pairs=0, omega_topology=0.0,
            verdict=GateVerdict.CONCEPTUAL,
        )

    couplings = [p.coupling_efficiency for p in pairs]
    avg_c = sum(couplings) / len(couplings)
    min_c = min(couplings)
    locked = sum(1 for p in pairs if p.match_state.value == "locked")

    locked_frac = locked / len(pairs)
    omega = round(0.50 * avg_c + 0.30 * locked_frac + 0.20 * min_c, 4)
    omega = max(0.0, min(1.0, omega))

    return GateTopology(
        nodes=nodes,
        pairs=pairs,
        avg_coupling=round(avg_c, 4),
        min_coupling=round(min_c, 4),
        fully_locked_pairs=locked,
        total_pairs=len(pairs),
        omega_topology=omega,
        verdict=_gate_verdict(omega),
    )
