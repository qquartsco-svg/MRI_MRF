"""
Space Gate Evolution Roadmap Evaluator
======================================

소형 위성형 데이터센터에서 자가순환 지구환경형 우주선 개념으로
어떻게 진화할 수 있는지를 단계적으로 읽는 보수적 evaluator.

이 모듈은 물리 장치를 주장하지 않는다.
현재 연결된 하위 엔진들의 readiness를 모아
"어디까지 왔는가 / 다음에 무엇이 필요한가"를 정리한다.
"""
from __future__ import annotations

from .contracts import (
    SpaceGateEvolutionInput,
    SpaceGateEvolutionPhase,
    SpaceGateEvolutionReport,
)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _mean(values: list[float]) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def evaluate_space_gate_evolution(inp: SpaceGateEvolutionInput) -> SpaceGateEvolutionReport:
    """Evaluate staged evolution from a small compute satellite to a habitat-grade concept."""
    satellite_node = _mean([
        inp.thermal_omega,
        inp.satellite_omega,
        inp.manufacturing_omega,
    ])

    enclosed_habitat = _mean([
        inp.thermal_omega,
        inp.satellite_omega,
        inp.orbital_omega,
        1.0 if inp.internal_air_enabled else 0.0,
    ])

    resonant_cluster = _mean([
        inp.resonance_network_omega,
        inp.orbital_omega,
        inp.manufacturing_omega,
        inp.superconducting_omega if inp.superconducting_omega is not None else 0.35,
    ])

    self_circulating = _mean([
        inp.thermal_omega,
        inp.orbital_omega,
        inp.manufacturing_omega,
        inp.terracore_viability_0_1 if inp.terracore_viability_0_1 is not None else 0.0,
        1.0 if inp.closed_loop_life_support_enabled else 0.0,
    ])

    earthlike_starship = _mean([
        satellite_node,
        resonant_cluster,
        self_circulating,
        inp.superconducting_omega if inp.superconducting_omega is not None else 0.30,
    ])

    phase_scores = {
        SpaceGateEvolutionPhase.SATELLITE_COMPUTE_NODE.value: round(_clip01(satellite_node), 4),
        SpaceGateEvolutionPhase.ENCLOSED_COMPUTE_HABITAT.value: round(_clip01(enclosed_habitat), 4),
        SpaceGateEvolutionPhase.RESONANT_ORBITAL_CLUSTER.value: round(_clip01(resonant_cluster), 4),
        SpaceGateEvolutionPhase.SELF_CIRCULATING_GATE_HABITAT.value: round(_clip01(self_circulating), 4),
        SpaceGateEvolutionPhase.EARTHLIKE_STARSHIP_CONCEPT.value: round(_clip01(earthlike_starship), 4),
    }

    reached = SpaceGateEvolutionPhase.SATELLITE_COMPUTE_NODE
    next_phase: SpaceGateEvolutionPhase | None = SpaceGateEvolutionPhase.ENCLOSED_COMPUTE_HABITAT

    if satellite_node >= 0.60 and inp.internal_air_enabled:
        reached = SpaceGateEvolutionPhase.ENCLOSED_COMPUTE_HABITAT
        next_phase = SpaceGateEvolutionPhase.RESONANT_ORBITAL_CLUSTER
    if (
        reached == SpaceGateEvolutionPhase.ENCLOSED_COMPUTE_HABITAT
        and resonant_cluster >= 0.62
        and inp.resonance_network_omega >= 0.55
        and (inp.superconducting_omega is not None and inp.superconducting_omega >= 0.50)
    ):
        reached = SpaceGateEvolutionPhase.RESONANT_ORBITAL_CLUSTER
        next_phase = SpaceGateEvolutionPhase.SELF_CIRCULATING_GATE_HABITAT
    if (
        reached == SpaceGateEvolutionPhase.RESONANT_ORBITAL_CLUSTER
        and self_circulating >= 0.58
        and inp.terracore_viability_0_1 is not None
        and inp.closed_loop_life_support_enabled
    ):
        reached = SpaceGateEvolutionPhase.SELF_CIRCULATING_GATE_HABITAT
        next_phase = SpaceGateEvolutionPhase.EARTHLIKE_STARSHIP_CONCEPT
    if (
        reached == SpaceGateEvolutionPhase.SELF_CIRCULATING_GATE_HABITAT
        and earthlike_starship >= 0.65
        and resonant_cluster >= 0.60
        and self_circulating >= 0.60
    ):
        reached = SpaceGateEvolutionPhase.EARTHLIKE_STARSHIP_CONCEPT
        next_phase = None

    bottlenecks: list[str] = []
    if inp.thermal_omega < 0.60:
        bottlenecks.append("thermal_autonomy")
    if inp.satellite_omega < 0.60:
        bottlenecks.append("satellite_readiness")
    if inp.orbital_omega < 0.60:
        bottlenecks.append("orbital_health")
    if inp.manufacturing_omega < 0.60:
        bottlenecks.append("manufacturing_readiness")
    if inp.resonance_network_omega < 0.55:
        bottlenecks.append("resonance_network")
    if inp.superconducting_omega is None or inp.superconducting_omega < 0.50:
        bottlenecks.append("superconducting_field_platform")
    if inp.terracore_viability_0_1 is None or inp.terracore_viability_0_1 < 0.55:
        bottlenecks.append("terracore_self_circulation")
    if not inp.closed_loop_life_support_enabled:
        bottlenecks.append("closed_loop_life_support")

    if reached == SpaceGateEvolutionPhase.SATELLITE_COMPUTE_NODE:
        recommendation = (
            "작은 위성형 컴퓨트 노드 단계입니다. 먼저 내부 공냉/외부 복사 자립과 "
            "제작 가능성을 안정화한 뒤, 공명 네트워크 단계로 올라가세요."
        )
    elif reached == SpaceGateEvolutionPhase.ENCLOSED_COMPUTE_HABITAT:
        recommendation = (
            "밀폐 대기형 데이터센터 위성 단계입니다. 다음 단계는 다중 노드 공명 연결과 "
            "초전도 자기장 플랫폼 보강입니다."
        )
    elif reached == SpaceGateEvolutionPhase.RESONANT_ORBITAL_CLUSTER:
        recommendation = (
            "공명형 궤도 클러스터 단계입니다. 이제 TerraCore 기반 자가순환 생존성과 "
            "폐회로 환경 유지 능력을 붙여야 합니다."
        )
    elif reached == SpaceGateEvolutionPhase.SELF_CIRCULATING_GATE_HABITAT:
        recommendation = (
            "자가순환 게이트-해비타트 단계입니다. 지구환경형 우주선 개념으로 가려면 "
            "열·생명유지·제조·초전도 기반을 동시에 끌어올려야 합니다."
        )
    else:
        recommendation = (
            "지구환경형 우주선 개념 단계입니다. 이 단계는 아직 개념/시스템 수준이며, "
            "추진·항법·장기 거주성은 별도 엔진 레이어로 확장해야 합니다."
        )

    return SpaceGateEvolutionReport(
        system_name=inp.system_name,
        current_phase=reached,
        next_phase=next_phase,
        overall_omega=round(phase_scores[reached.value], 4),
        phase_scores=phase_scores,
        bottlenecks=bottlenecks,
        recommendation=recommendation,
        evidence_tags=[
            "space_gate_evolution",
            "satellite_compute_node",
            "self_circulating_starship_roadmap",
        ],
    )
