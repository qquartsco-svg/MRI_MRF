"""
Magnetic Resonance Foundation — Data Contracts
================================================
NMR/라모어 공명, 자기 가두기, 게이트 토폴로지를 위한 불변 데이터 구조.
SI 단위 기본.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ── Physical Constants ──────────────────────────────────
MU_0: float = 4e-7 * math.pi           # 진공 투자율 (T·m/A)
EPSILON_0: float = 8.854e-12            # 진공 유전율 (F/m)
SPEED_OF_LIGHT_M_S: float = 2.998e8
BOLTZMANN_J_PER_K: float = 1.381e-23
PLANCK_J_S: float = 6.626e-34
ELECTRON_MASS_KG: float = 9.109e-31
PROTON_MASS_KG: float = 1.673e-27
ELEMENTARY_CHARGE_C: float = 1.602e-19
G_CONST: float = 6.674e-11             # 만유인력 상수 (m³/(kg·s²))
EARTH_MASS_KG: float = 5.972e24
MOON_MASS_KG: float = 7.342e22
EARTH_MOON_DIST_M: float = 3.844e8     # 지구–달 평균 거리 (m)

# 자기회전비 γ (rad/(s·T)) — 주요 핵종
GYROMAGNETIC_RATIOS: Dict[str, float] = {
    "1H":   2.6752e8,    # 수소 (MRI 표준)
    "13C":  6.7283e7,    # 탄소-13
    "31P":  1.0839e8,    # 인-31
    "23Na": 7.0808e7,    # 나트륨-23
    "e":    1.7609e11,   # 전자 (EPR)
}


# ── Enums ───────────────────────────────────────────────

class ResonanceMatchState(Enum):
    """두 게이트 간 공명 일치 상태."""
    LOCKED = "locked"           # |Δω/ω| < 1%
    NEAR = "near"               # 1% ≤ |Δω/ω| < 5%
    DETUNED = "detuned"         # 5% ≤ |Δω/ω| < 15%
    DISCONNECTED = "disconnected"  # ≥ 15%


class ConfinementMode(Enum):
    """자기 가두기 형태."""
    MAGNETIC_MIRROR = "magnetic_mirror"      # 자기거울
    MAGNETIC_BOTTLE = "magnetic_bottle"      # 자기병 (양쪽 거울)
    TOROIDAL = "toroidal"                     # 토카막/스텔라레이터
    VAN_ALLEN = "van_allen"                   # 행성 자기장


class ThermalPathMode(Enum):
    """열 운반 경로."""
    PLASMA_CONVECTION = "plasma_convection"
    MAGNETIC_LOOP = "magnetic_loop"
    RADIATIVE_ONLY = "radiative_only"


class GateVerdict(Enum):
    """게이트 네트워크 판정."""
    OPERATIONAL = "operational"     # Ω ≥ 0.80
    MARGINAL = "marginal"          # 0.50 ≤ Ω < 0.80
    EXPERIMENTAL = "experimental"  # 0.25 ≤ Ω < 0.50
    CONCEPTUAL = "conceptual"      # < 0.25


class ReadinessVerdict(Enum):
    PRODUCTION_READY = "production_ready"
    PILOT_READY = "pilot_ready"
    PROTOTYPE_READY = "prototype_ready"
    NOT_READY = "not_ready"


class AthenaStage(Enum):
    """상위 해석 언어."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CAUTIOUS = "cautious"
    NEGATIVE = "negative"


# ── Layer 1: Larmor / NMR ──────────────────────────────

@dataclass(frozen=True)
class LarmorInput:
    """라모어 공명 계산 입력."""
    nucleus: str = "1H"
    field_strength_t: float = 3.0
    temperature_k: float = 300.0


@dataclass(frozen=True)
class LarmorResult:
    """라모어 주파수 결과."""
    nucleus: str
    gamma_rad_per_s_t: float
    field_strength_t: float
    omega_rad_per_s: float
    frequency_hz: float
    frequency_mhz: float
    wavelength_m: float
    photon_energy_ev: float


@dataclass(frozen=True)
class GateNode:
    """공명 게이트 노드 정의."""
    gate_id: str
    position_km: Tuple[float, float, float]  # (x, y, z) km
    field_strength_t: float
    nucleus: str = "1H"
    coil_radius_m: float = 1.0


@dataclass(frozen=True)
class GatePairResonance:
    """두 게이트 간 공명 분석."""
    gate_a_id: str
    gate_b_id: str
    freq_a_hz: float
    freq_b_hz: float
    detuning_hz: float
    detuning_fraction: float
    match_state: ResonanceMatchState
    coupling_efficiency: float
    distance_km: float


# ── Layer 2: Magnetic Confinement ──────────────────────

@dataclass(frozen=True)
class ConfinementInput:
    """자기 가두기 스크리닝 입력."""
    mode: ConfinementMode
    b_max_t: float              # 병목(거울) 최대 자기장
    b_min_t: float              # 중앙 최소 자기장
    plasma_temp_ev: float = 10.0  # 플라즈마 온도 (eV)
    plasma_density_m3: float = 1e18
    confinement_length_m: float = 10.0
    coil_radius_m: float = 1.0


@dataclass(frozen=True)
class ConfinementResult:
    """자기 가두기 스크리닝 결과."""
    mode: ConfinementMode
    mirror_ratio: float                # R = B_max / B_min
    loss_cone_deg: float               # sin²θ = 1/R
    gyro_radius_m: float               # 전자 자이로 반경
    plasma_beta: float                 # β = p_plasma / p_magnetic
    confinement_time_proxy_s: float    # 간이 가두기 시간 추정
    omega_confinement: float           # 0–1 스크리닝 점수
    advisories: List[str] = field(default_factory=list)


# ── Layer 2b: Thermal Transport ────────────────────────

@dataclass(frozen=True)
class MagneticThermalInput:
    """자기 가두기 기반 열 운반 입력."""
    heat_load_w: float
    plasma_temp_ev: float = 10.0
    plasma_density_m3: float = 1e18
    loop_length_m: float = 100.0
    loop_cross_section_m2: float = 0.01
    b_field_t: float = 1.0


@dataclass(frozen=True)
class MagneticThermalResult:
    """자기 대류 열 운반 추정 결과."""
    path_mode: ThermalPathMode
    thermal_velocity_m_s: float      # v_th = sqrt(2kT/m)
    heat_capacity_w: float           # 플라즈마 열 운반 용량 추정
    heat_load_w: float
    headroom_w: float
    omega_thermal_transport: float
    advisory: str


# ── Layer 3: Gate Topology ─────────────────────────────

@dataclass(frozen=True)
class GateTopology:
    """게이트 네트워크 토폴로지."""
    nodes: List[GateNode]
    pairs: List[GatePairResonance]
    avg_coupling: float
    min_coupling: float
    fully_locked_pairs: int
    total_pairs: int
    omega_topology: float
    verdict: GateVerdict


# ── Phase B: Plasma Transport ──────────────────────────

@dataclass(frozen=True)
class PlasmaTransportInput:
    """플라즈마 수송 계수 계산 입력."""
    electron_temp_ev: float = 100.0
    electron_density_m3: float = 1e19
    ion_charge_z: int = 1
    b_field_t: float = 1.0


@dataclass(frozen=True)
class PlasmaTransportResult:
    """플라즈마 수송 계수 결과."""
    coulomb_log: float              # ln Λ
    collision_freq_hz: float        # ν_ei (전자–이온 충돌)
    spitzer_resistivity_ohm_m: float  # η_Spitzer
    mean_free_path_m: float         # λ_mfp
    thermal_conductivity_parallel: float  # κ_∥ (W/(m·K) proxy)
    thermal_conductivity_perp: float      # κ_⊥
    omega_transport: float          # 0–1 수송 품질 점수
    advisories: List[str]


# ── Phase C: Toroidal Geometry ─────────────────────────

class ToroidalType(Enum):
    TOKAMAK = "tokamak"
    STELLARATOR = "stellarator"


@dataclass(frozen=True)
class ToroidalInput:
    """토로이달 가두기 형상 입력."""
    device_type: ToroidalType = ToroidalType.TOKAMAK
    major_radius_m: float = 6.2          # R₀
    minor_radius_m: float = 2.0          # a
    toroidal_field_t: float = 5.3        # B_φ
    plasma_current_ma: float = 15.0      # I_p (토카막)
    electron_density_m3: float = 1e20
    electron_temp_ev: float = 1000.0


@dataclass(frozen=True)
class ToroidalResult:
    """토로이달 형상 분석 결과."""
    device_type: ToroidalType
    aspect_ratio: float                  # A = R₀/a
    safety_factor_q: float               # q ≈ aB_φ / (R₀·B_θ)
    kruskal_shafranov_ok: bool           # q > 1
    plasma_volume_m3: float              # V = 2π²R₀a²
    greenwald_density_limit_m3: float    # n_G
    greenwald_fraction: float            # n_e / n_G
    rotational_transform: float          # ι = 2π/q
    omega_geometry: float
    advisories: List[str]


# ── Phase D: RF Energy Transfer ────────────────────────

@dataclass(frozen=True)
class RFTransferInput:
    """게이트 간 RF 에너지 전달 입력."""
    frequency_hz: float                  # 전송 주파수
    transmit_power_w: float = 1e3        # 송신 전력
    distance_m: float = 1e6             # 게이트 간 거리
    antenna_diameter_m: float = 10.0     # 안테나 직경 (송·수신 동일)
    antenna_efficiency: float = 0.65     # 안테나 효율


@dataclass(frozen=True)
class RFTransferResult:
    """RF 에너지 전달 결과."""
    wavelength_m: float
    fspl_db: float                       # Free-Space Path Loss
    antenna_gain_dbi: float              # 각 안테나 이득
    beam_divergence_rad: float           # 빔 발산각
    received_power_w: float
    received_power_dbm: float
    link_margin_db: float                # vs –120 dBm 수신 감도 기준
    omega_link: float
    advisories: List[str]


# ── Phase E: Lagrange Point Stability ──────────────────

class LagrangePoint(Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


class LagrangeStabilityClass(Enum):
    STABLE = "stable"               # L4/L5 (mass ratio OK)
    QUASI_STABLE = "quasi_stable"   # L1/L2/L3 with station-keeping
    UNSTABLE = "unstable"


@dataclass(frozen=True)
class LagrangeInput:
    """라그랑주 점 분석 입력."""
    point: LagrangePoint = LagrangePoint.L1
    primary_mass_kg: float = 5.972e24    # M₁ (지구)
    secondary_mass_kg: float = 7.342e22  # M₂ (달)
    separation_m: float = 3.844e8        # 두 천체 간 거리
    station_keeping_dv_budget_m_s: float = 50.0  # 연간 ΔV 예산


@dataclass(frozen=True)
class LagrangeResult:
    """라그랑주 점 분석 결과."""
    point: LagrangePoint
    distance_from_primary_m: float       # L 점 위치 (M₁ 기준)
    distance_from_secondary_m: float
    mass_ratio: float                    # μ = M₂/(M₁+M₂)
    hill_sphere_m: float                 # rH = a·(m₂/(3m₁))^(1/3)
    stability_class: LagrangeStabilityClass
    instability_time_s: Optional[float]  # L1/L2/L3: e-folding time
    annual_dv_estimate_m_s: float        # 연간 station-keeping ΔV 추정
    dv_budget_ok: bool
    omega_lagrange: float
    advisories: List[str]


# ══════════════════════════════════════════════════════
# MRI PATH — 실제 MRI 설계 스크리닝
# ══════════════════════════════════════════════════════

# ── MRI: Gradient System ──────────────────────────────

class GradientAxis(Enum):
    X = "x"
    Y = "y"
    Z = "z"


@dataclass(frozen=True)
class GradientInput:
    """경사장 시스템 입력."""
    max_amplitude_mt_per_m: float = 40.0   # 최대 경사장 세기 (mT/m)
    max_slew_rate_t_per_m_per_s: float = 200.0  # 최대 슬루율 (T/m/s)
    fov_m: float = 0.40                    # 시야 (Field of View, m)
    matrix_size: int = 256                 # 이미지 행렬 크기
    b0_field_t: float = 3.0               # 주자기장
    nucleus: str = "1H"


@dataclass(frozen=True)
class GradientResult:
    """경사장 스크리닝 결과."""
    pixel_bandwidth_hz: float              # Δf per pixel
    min_encoding_time_ms: float            # 최소 경사 인코딩 시간
    spatial_resolution_mm: float           # FOV / matrix
    max_readout_bandwidth_hz: float        # 전체 수신 대역폭
    rise_time_ms: float                    # 0 → max amplitude 시간
    duty_cycle_limit: float                # 슬루 기반 듀티 한계 (0–1)
    omega_gradient: float
    advisories: List[str]


# ── MRI: RF Pulse ─────────────────────────────────────

class RFPulseType(Enum):
    HARD = "hard"                  # 사각파
    SINC = "sinc"                  # 싱크 (슬라이스 선택 표준)
    GAUSSIAN = "gaussian"


@dataclass(frozen=True)
class RFPulseInput:
    """RF 펄스 설계 입력."""
    pulse_type: RFPulseType = RFPulseType.SINC
    flip_angle_deg: float = 90.0           # 목표 flip angle
    slice_thickness_m: float = 0.005       # 슬라이스 두께 5mm
    b0_field_t: float = 3.0
    gradient_amplitude_mt_per_m: float = 20.0  # 슬라이스 선택 경사
    time_bandwidth_product: float = 4.0    # sinc TBW
    body_mass_kg: float = 70.0             # SAR 계산용


@dataclass(frozen=True)
class RFPulseResult:
    """RF 펄스 설계 결과."""
    pulse_duration_ms: float               # 펄스 길이
    bandwidth_hz: float                    # 여기 대역폭
    b1_peak_ut: float                      # 피크 B₁ (μT)
    b1_rms_ut: float                       # RMS B₁
    pulse_energy_j: float                  # 펄스 에너지 proxy
    omega_rf_pulse: float
    advisories: List[str]


# ── MRI: Bloch Signal ────────────────────────────────

@dataclass(frozen=True)
class TissueParams:
    """조직별 이완 시간 (기본: 3T 뇌 백질)."""
    name: str = "white_matter_3T"
    t1_ms: float = 1084.0                 # T₁ (ms)
    t2_ms: float = 69.0                   # T₂ (ms)
    t2_star_ms: float = 33.5              # T₂* (ms)
    proton_density: float = 0.65          # 상대 양성자 밀도 (0–1)


@dataclass(frozen=True)
class BlochInput:
    """블로흐 신호 시뮬레이션 입력."""
    tissue: TissueParams = field(default_factory=TissueParams)
    flip_angle_deg: float = 90.0
    tr_ms: float = 500.0                  # 반복시간
    te_ms: float = 10.0                   # 에코시간
    sequence_type: str = "spin_echo"      # "spin_echo" | "gradient_echo"


@dataclass(frozen=True)
class BlochResult:
    """블로흐 신호 결과."""
    mz_recovery: float                    # M_z / M_0 at TR
    mxy_at_te: float                      # M_xy / M_0 at TE
    signal_intensity: float               # 전체 SI (PD × Mxy)
    ernst_angle_deg: float                # 최적 flip angle
    t1_weighting: float                   # T₁ 가중 정도 (0–1)
    t2_weighting: float                   # T₂ 가중 정도 (0–1)
    omega_signal: float
    advisories: List[str]


# ── MRI: SNR Model ────────────────────────────────────

@dataclass(frozen=True)
class SNRInput:
    """SNR 추정 입력."""
    b0_field_t: float = 3.0
    voxel_size_mm3: Tuple[float, float, float] = (1.0, 1.0, 5.0)
    receiver_bandwidth_hz: float = 32000.0
    n_averages: int = 1
    coil_channels: int = 32
    body_temp_k: float = 310.0            # 인체 ~37°C
    signal_intensity: float = 0.3         # BlochResult 연결


@dataclass(frozen=True)
class SNRResult:
    """SNR 추정 결과."""
    voxel_volume_mm3: float
    thermal_noise_proxy: float             # ∝ √(BW·T)
    snr_0: float                           # 기본 SNR
    snr_with_averages: float               # × √N_avg
    snr_with_parallel: float               # × √N_ch
    omega_snr: float
    advisories: List[str]


# ── MRI: SAR Safety ───────────────────────────────────

@dataclass(frozen=True)
class SARInput:
    """SAR 안전 한계 입력."""
    b0_field_t: float = 3.0
    flip_angle_deg: float = 90.0
    tr_ms: float = 500.0
    pulse_duration_ms: float = 3.0
    body_mass_kg: float = 70.0
    duty_cycle: float = 0.05              # RF 듀티사이클
    mode: str = "normal"                  # "normal" | "first_level"


@dataclass(frozen=True)
class SARResult:
    """SAR 안전 결과."""
    whole_body_sar_w_per_kg: float        # 전신 SAR
    sar_limit_w_per_kg: float             # 한계 (모드별)
    sar_fraction: float                   # SAR / limit
    db_dt_t_per_s: float                  # dB/dt 추정
    db_dt_limit_t_per_s: float            # IEC 한계 (20 T/s)
    db_dt_ok: bool
    sar_ok: bool
    omega_safety: float
    advisories: List[str]


# ── MRI: Screening Report ─────────────────────────────

@dataclass(frozen=True)
class MRIScreeningReport:
    """MRI 경로 통합 보고서."""
    larmor: Optional[LarmorResult] = None
    gradient: Optional[GradientResult] = None
    rf_pulse: Optional[RFPulseResult] = None
    bloch: Optional[BlochResult] = None
    snr: Optional[SNRResult] = None
    sar: Optional[SARResult] = None
    omega_mri: float = 0.0
    verdict: ReadinessVerdict = ReadinessVerdict.NOT_READY
    evidence_tags: List[str] = field(default_factory=list)
    advisories: List[str] = field(default_factory=list)


# ── Master Report ──────────────────────────────────────

@dataclass(frozen=True)
class MagneticResonanceReport:
    """Foundation 최종 보고서."""
    larmor: Optional[LarmorResult] = None
    confinement: Optional[ConfinementResult] = None
    thermal_transport: Optional[MagneticThermalResult] = None
    topology: Optional[GateTopology] = None
    plasma_transport: Optional[PlasmaTransportResult] = None
    toroidal: Optional[ToroidalResult] = None
    rf_link: Optional[RFTransferResult] = None
    lagrange: Optional[LagrangeResult] = None
    mri: Optional[MRIScreeningReport] = None
    omega_overall: float = 0.0
    athena_stage: AthenaStage = AthenaStage.NEGATIVE
    athena_confidence: float = 0.0
    verdict: ReadinessVerdict = ReadinessVerdict.NOT_READY
    evidence_tags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ── Space Gate Data Center Thermal Stack ──────────────

@dataclass(frozen=True)
class SpaceGateDataCenterInput:
    """우주 게이트 내부 데이터센터 열 스택 입력.

    레이어 분리 원칙:
    - 내부 공냉/대류: SpaceThermal terrestrial_convection
    - 중간 자기공명 보조: MagneticThermal proxy
    - 외부 우주 방열: SpaceThermal radiation/orbital path
    """

    gate_name: str
    compute_heat_load_w: float
    radiator_area_m2: float
    internal_air_supply_temp_c: float
    internal_air_exhaust_limit_c: float
    internal_air_mass_flow_kg_s: float | None = None
    internal_air_volumetric_flow_m3_s: float | None = None
    internal_heat_transfer_coeff_w_m2k: float | None = None
    internal_convection_area_m2: float | None = None
    field_t: float = 3.0
    magnetic_assist_fraction_0_1: float = 0.15
    magnetic_assist_enabled: bool = True
    emissivity: float = 0.85
    absorptivity: float = 0.18
    max_operating_temp_c: float = 50.0
    min_operating_temp_c: float = -20.0
    thermal_mass_j_per_k: float | None = None
    notes: str = ""


@dataclass(frozen=True)
class SpaceGateDataCenterReport:
    """우주 게이트 데이터센터 열 스택 요약 보고서."""

    gate_name: str
    internal_air_omega: float
    internal_air_verdict: str
    internal_air_outlet_temp_c: float
    external_radiator_omega: float
    external_radiator_verdict: str
    equilibrium_temp_c: float
    magnetic_assist_omega: float | None
    magnetic_assist_fraction_0_1: float
    heat_transport_efficiency_0_1: float
    overall_omega: float
    athena_stage: AthenaStage
    athena_confidence: float
    verdict: ReadinessVerdict
    bottleneck_layer: str
    recommendation: str
    evidence_tags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
