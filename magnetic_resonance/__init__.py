"""
Magnetic Resonance Foundation  v0.4.0
======================================
하나의 ω₀ = γ·B₀ 에서 두 경로로.

MRI Path : gradient_system → rf_pulse → bloch_signal → snr_model → sar_safety → mri_screening
Gate Path: magnetic_confinement → thermal_transport → plasma_transport → toroidal → rf_link → lagrange → gate_topology

공유 기반 : larmor.py, gate_resonance.py
통합      : foundation.py
"""
__version__ = "0.4.0"

from .contracts import (
    BlochInput,
    BlochResult,
    ConfinementInput,
    ConfinementMode,
    ConfinementResult,
    AthenaStage,
    GateNode,
    GradientInput,
    GradientResult,
    GatePairResonance,
    GateTopology,
    GateVerdict,
    GYROMAGNETIC_RATIOS,
    LagrangeInput,
    LagrangePoint,
    LagrangeResult,
    LagrangeStabilityClass,
    LarmorInput,
    LarmorResult,
    MagneticResonanceReport,
    MagneticThermalInput,
    MRIScreeningReport,
    MagneticThermalResult,
    PlasmaTransportInput,
    PlasmaTransportResult,
    ReadinessVerdict,
    ResonanceMatchState,
    RFPulseInput,
    RFPulseResult,
    RFPulseType,
    RFTransferInput,
    RFTransferResult,
    SARInput,
    SARResult,
    SNRInput,
    SNRResult,
    ThermalPathMode,
    TissueParams,
    ToroidalInput,
    ToroidalResult,
    ToroidalType,
)
from .larmor import larmor_frequency, compare_nuclei
from .gate_resonance import analyze_gate_pair, analyze_gate_network
from .magnetic_confinement import screen_confinement
from .thermal_transport import screen_magnetic_thermal
from .gate_topology import (
    evaluate_topology,
    preset_leo_ring,
    preset_earth_l1_moon,
    preset_earth_moon_relay,
)
from .plasma_transport import screen_plasma_transport, coulomb_logarithm
from .toroidal_geometry import screen_toroidal
from .rf_energy_transfer import screen_rf_link
from .lagrange_stability import screen_lagrange
from .gradient_system import screen_gradient
from .rf_pulse import screen_rf_pulse
from .bloch_signal import screen_bloch_signal
from .snr_model import screen_snr
from .sar_safety import screen_sar
from .mri_screening import screen_mri
from .foundation import analyze
from .athena_stage import map_athena_stage
from .ecosystem_bridges import (
    resonance_to_em_snapshot,
    try_frequency_resonance,
    try_superconducting_field,
    try_space_thermal_screen,
    try_optics_resonance_bridge,
    try_foundry_resonance_tick,
    try_manufacturing_resonance_readiness,
    mri_to_manufacturing_payload,
    gate_to_manufacturing_payload,
    try_mri_manufacturing_readiness,
    try_gate_manufacturing_readiness,
    try_fabless_semiconductor_bridge,
)

__all__ = [
    "analyze",
    "larmor_frequency",
    "compare_nuclei",
    "analyze_gate_pair",
    "analyze_gate_network",
    "screen_confinement",
    "screen_magnetic_thermal",
    "evaluate_topology",
    "preset_leo_ring",
    "preset_earth_l1_moon",
    "preset_earth_moon_relay",
    "screen_plasma_transport",
    "coulomb_logarithm",
    "screen_toroidal",
    "screen_rf_link",
    "screen_lagrange",
    "map_athena_stage",
    "AthenaStage",
    "ConfinementInput",
    "ConfinementMode",
    "ConfinementResult",
    "GateNode",
    "GatePairResonance",
    "GateTopology",
    "GateVerdict",
    "GYROMAGNETIC_RATIOS",
    "LagrangeInput",
    "LagrangePoint",
    "LagrangeResult",
    "LagrangeStabilityClass",
    "LarmorInput",
    "LarmorResult",
    "MagneticResonanceReport",
    "MagneticThermalInput",
    "MagneticThermalResult",
    "PlasmaTransportInput",
    "PlasmaTransportResult",
    "ReadinessVerdict",
    "screen_gradient",
    "screen_rf_pulse",
    "screen_bloch_signal",
    "screen_snr",
    "screen_sar",
    "screen_mri",
    "resonance_to_em_snapshot",
    "try_frequency_resonance",
    "try_superconducting_field",
    "try_space_thermal_screen",
    "try_optics_resonance_bridge",
    "try_foundry_resonance_tick",
    "try_manufacturing_resonance_readiness",
    "mri_to_manufacturing_payload",
    "gate_to_manufacturing_payload",
    "try_mri_manufacturing_readiness",
    "try_gate_manufacturing_readiness",
    "try_fabless_semiconductor_bridge",
    "GradientInput",
    "GradientResult",
    "RFPulseInput",
    "RFPulseResult",
    "RFPulseType",
    "TissueParams",
    "BlochInput",
    "BlochResult",
    "SNRInput",
    "SNRResult",
    "SARInput",
    "SARResult",
    "MRIScreeningReport",
    "ResonanceMatchState",
    "RFTransferInput",
    "RFTransferResult",
    "ThermalPathMode",
    "ToroidalInput",
    "ToroidalResult",
    "ToroidalType",
]
