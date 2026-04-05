"""
MRI Path — Screening Orchestrator
====================================

MRI 설계 스크리닝 전용 오케스트레이터.
foundation.py (Gate 경로)와 독립적으로 실행 가능하지만,
둘 다 larmor.py를 공유 기반으로 쓴다.

실행 경로:
  Larmor (공유) → Gradient → RF Pulse → Bloch → SNR → SAR
  각 레이어는 입력이 있을 때만 실행.
"""
from __future__ import annotations

from typing import List, Optional

from .contracts import (
    BlochInput,
    GradientInput,
    LarmorInput,
    MRIScreeningReport,
    ReadinessVerdict,
    RFPulseInput,
    SARInput,
    SNRInput,
)
from .larmor import larmor_frequency
from .gradient_system import screen_gradient
from .rf_pulse import screen_rf_pulse
from .bloch_signal import screen_bloch_signal
from .snr_model import screen_snr
from .sar_safety import screen_sar


def _verdict(omega: float) -> ReadinessVerdict:
    if omega >= 0.85:
        return ReadinessVerdict.PRODUCTION_READY
    if omega >= 0.65:
        return ReadinessVerdict.PILOT_READY
    if omega >= 0.40:
        return ReadinessVerdict.PROTOTYPE_READY
    return ReadinessVerdict.NOT_READY


def screen_mri(
    larmor_input: Optional[LarmorInput] = None,
    gradient_input: Optional[GradientInput] = None,
    rf_pulse_input: Optional[RFPulseInput] = None,
    bloch_input: Optional[BlochInput] = None,
    snr_input: Optional[SNRInput] = None,
    sar_input: Optional[SARInput] = None,
) -> MRIScreeningReport:
    """MRI 경로 통합 스크리닝."""
    tags: List[str] = []
    advs: List[str] = []
    scores: List[float] = []

    larmor_result = None
    if larmor_input is not None:
        larmor_result = larmor_frequency(larmor_input)
        tags.append("larmor_nmr")

    grad_result = None
    if gradient_input is not None:
        grad_result = screen_gradient(gradient_input)
        tags.append("gradient_system")
        scores.append(grad_result.omega_gradient)
        advs.extend(grad_result.advisories)

    rf_result = None
    if rf_pulse_input is not None:
        rf_result = screen_rf_pulse(rf_pulse_input)
        tags.append("rf_pulse")
        scores.append(rf_result.omega_rf_pulse)
        advs.extend(rf_result.advisories)

    bloch_result = None
    if bloch_input is not None:
        bloch_result = screen_bloch_signal(bloch_input)
        tags.append("bloch_signal")
        scores.append(bloch_result.omega_signal)
        advs.extend(bloch_result.advisories)

    snr_result = None
    if snr_input is not None:
        snr_result = screen_snr(snr_input)
        tags.append("snr_model")
        scores.append(snr_result.omega_snr)
        advs.extend(snr_result.advisories)

    sar_result = None
    if sar_input is not None:
        sar_result = screen_sar(sar_input)
        tags.append("sar_safety")
        scores.append(sar_result.omega_safety)
        advs.extend(sar_result.advisories)

    omega = round(sum(scores) / len(scores), 4) if scores else 0.0

    return MRIScreeningReport(
        larmor=larmor_result,
        gradient=grad_result,
        rf_pulse=rf_result,
        bloch=bloch_result,
        snr=snr_result,
        sar=sar_result,
        omega_mri=omega,
        verdict=_verdict(omega),
        evidence_tags=tags,
        advisories=advs,
    )
