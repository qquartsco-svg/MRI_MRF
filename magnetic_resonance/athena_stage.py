"""
ATHENA Stage Mapping
====================

물리 스크리닝 결과를 상위 해석 언어로 번역한다.
"""
from __future__ import annotations

from .contracts import AthenaStage


def map_athena_stage(omega: float, conceptual_fraction: float = 0.0, warning_count: int = 0) -> tuple[AthenaStage, float]:
    """
    overall omega + 개념층 비중 + 경고 수를 바탕으로 보수적 단계 산정.

    conceptual_fraction:
        topology 등 실험/개념 레이어가 차지하는 비율. 높을수록 단계가 보수화된다.
    """
    confidence = max(0.0, min(1.0, omega * (1.0 - 0.35 * conceptual_fraction) * (1.0 - 0.03 * warning_count)))
    if confidence >= 0.80:
        return AthenaStage.POSITIVE, round(confidence, 4)
    if confidence >= 0.60:
        return AthenaStage.NEUTRAL, round(confidence, 4)
    if confidence >= 0.35:
        return AthenaStage.CAUTIOUS, round(confidence, 4)
    return AthenaStage.NEGATIVE, round(confidence, 4)
