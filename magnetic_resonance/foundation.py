"""
Magnetic Resonance Foundation — Master Entry Point
====================================================

전 레이어를 하나의 리포트로 묶는 통합 파이프라인.

Layer 1 : Larmor NMR + Gate Resonance
Layer 2 : Magnetic Confinement + Thermal Transport
Layer 3 : Gate Network Topology
Phase B : Plasma Transport Coefficients
Phase C : Toroidal Geometry (Tokamak/Stellarator)
Phase D : RF/Microwave Energy Transfer
Phase E : Lagrange Point Stability

각 레이어는 입력이 있을 때만 실행.
"""
from __future__ import annotations

from typing import List, Optional

from .athena_stage import map_athena_stage
from .contracts import (
    BlochInput,
    ConfinementInput,
    GateNode,
    GradientInput,
    LagrangeInput,
    LarmorInput,
    MagneticResonanceReport,
    MagneticThermalInput,
    PlasmaTransportInput,
    ReadinessVerdict,
    RFPulseInput,
    RFTransferInput,
    SARInput,
    SNRInput,
    ToroidalInput,
)
from .mri_screening import screen_mri
from .larmor import larmor_frequency
from .magnetic_confinement import screen_confinement
from .thermal_transport import screen_magnetic_thermal
from .gate_topology import evaluate_topology
from .plasma_transport import screen_plasma_transport
from .toroidal_geometry import screen_toroidal
from .rf_energy_transfer import screen_rf_link
from .lagrange_stability import screen_lagrange


def _verdict(omega: float) -> ReadinessVerdict:
    if omega >= 0.85:
        return ReadinessVerdict.PRODUCTION_READY
    if omega >= 0.65:
        return ReadinessVerdict.PILOT_READY
    if omega >= 0.40:
        return ReadinessVerdict.PROTOTYPE_READY
    return ReadinessVerdict.NOT_READY


def analyze(
    larmor_input: Optional[LarmorInput] = None,
    confinement_input: Optional[ConfinementInput] = None,
    thermal_input: Optional[MagneticThermalInput] = None,
    gate_nodes: Optional[List[GateNode]] = None,
    plasma_transport_input: Optional[PlasmaTransportInput] = None,
    toroidal_input: Optional[ToroidalInput] = None,
    rf_input: Optional[RFTransferInput] = None,
    lagrange_input: Optional[LagrangeInput] = None,
    gradient_input: Optional[GradientInput] = None,
    rf_pulse_input: Optional[RFPulseInput] = None,
    bloch_input: Optional[BlochInput] = None,
    snr_input: Optional[SNRInput] = None,
    sar_input: Optional[SARInput] = None,
    damping: float = 0.02,
) -> MagneticResonanceReport:
    """통합 분석 — 모든 레이어 선택적 실행."""
    tags: List[str] = []
    warnings: List[str] = []
    scores: List[float] = []
    conceptual_scores: List[float] = []

    larmor_result = None
    if larmor_input is not None:
        larmor_result = larmor_frequency(larmor_input)
        tags.append("larmor_nmr")

    conf_result = None
    if confinement_input is not None:
        conf_result = screen_confinement(confinement_input)
        tags.append("magnetic_confinement")
        scores.append(conf_result.omega_confinement)
        warnings.extend(conf_result.advisories)

    therm_result = None
    if thermal_input is not None:
        therm_result = screen_magnetic_thermal(thermal_input)
        tags.append("magnetic_thermal_transport")
        scores.append(therm_result.omega_thermal_transport)
        warnings.append(therm_result.advisory)

    topo_result = None
    if gate_nodes is not None and len(gate_nodes) >= 2:
        topo_result = evaluate_topology(gate_nodes, damping)
        tags.append("gate_topology")
        conceptual_scores.append(topo_result.omega_topology)
        warnings.append("Gate topology remains a conceptual/experimental extension layer.")

    plasma_result = None
    if plasma_transport_input is not None:
        plasma_result = screen_plasma_transport(plasma_transport_input)
        tags.append("plasma_transport")
        scores.append(plasma_result.omega_transport)
        warnings.extend(plasma_result.advisories)

    toroidal_result = None
    if toroidal_input is not None:
        toroidal_result = screen_toroidal(toroidal_input)
        tags.append("toroidal_geometry")
        scores.append(toroidal_result.omega_geometry)
        warnings.extend(toroidal_result.advisories)

    rf_result = None
    if rf_input is not None:
        rf_result = screen_rf_link(rf_input)
        tags.append("rf_link")
        scores.append(rf_result.omega_link)
        warnings.extend(rf_result.advisories)

    lagrange_result = None
    if lagrange_input is not None:
        lagrange_result = screen_lagrange(lagrange_input)
        tags.append("lagrange_stability")
        scores.append(lagrange_result.omega_lagrange)
        warnings.extend(lagrange_result.advisories)

    # MRI path (독립 실행 가능, 입력이 있으면 실행)
    mri_inputs_any = any([gradient_input, rf_pulse_input, bloch_input, snr_input, sar_input])
    mri_result = None
    if mri_inputs_any:
        mri_result = screen_mri(
            larmor_input=larmor_input,
            gradient_input=gradient_input,
            rf_pulse_input=rf_pulse_input,
            bloch_input=bloch_input,
            snr_input=snr_input,
            sar_input=sar_input,
        )
        tags.append("mri_screening")
        scores.append(mri_result.omega_mri)
        warnings.extend(mri_result.advisories)

    weighted_scores = scores + [s * 0.55 for s in conceptual_scores]
    if weighted_scores:
        omega = round(sum(weighted_scores) / len(weighted_scores), 4)
    else:
        omega = 0.0
    conceptual_fraction = (len(conceptual_scores) / len(weighted_scores)) if weighted_scores else 0.0
    athena_stage, athena_confidence = map_athena_stage(
        omega,
        conceptual_fraction=conceptual_fraction,
        warning_count=len(warnings),
    )

    return MagneticResonanceReport(
        larmor=larmor_result,
        confinement=conf_result,
        thermal_transport=therm_result,
        topology=topo_result,
        plasma_transport=plasma_result,
        toroidal=toroidal_result,
        rf_link=rf_result,
        lagrange=lagrange_result,
        mri=mri_result,
        omega_overall=omega,
        athena_stage=athena_stage,
        athena_confidence=athena_confidence,
        verdict=_verdict(omega),
        evidence_tags=tags,
        warnings=warnings,
    )
