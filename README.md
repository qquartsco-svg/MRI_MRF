# Magnetic Resonance Foundation

> **한국어 (정본).** English: [README_EN.md](README_EN.md)  
> 개념·철학·물리 배경: [CONCEPT.md](CONCEPT.md)

| 항목 | 내용 |
|------|------|
| 버전 | `v0.4.0` |
| 테스트 | `103 passed` |
| 의존성 | 런타임: 표준 라이브러리만 · 테스트: `pytest>=8.0` (선택) |
| 패키지명 | `magnetic-resonance-foundation` |
| Python | `>=3.10` |
| 라이선스 | MIT |

---

## 한 줄 정의

**하나의 `ω₀ = γ · B₀`에서 의료 MRI 설계(현실)와 우주 게이트 개념 설계(확장)를 독립 레이어로 쌓아, Ω / ATHENA / verdict를 내는 통합 자기공명 스크리닝 foundation.**

*같은 물리, 다른 맥락.*

---

## 두 경로 구조

```text
                        ω₀ = γ · B₀
                       (공유 기반: larmor.py)
                             │
                ┌────────────┴────────────┐
                │                         │
          ╔═══ MRI PATH ═══╗    ╔═══ GATE PATH ═══╗
          ║  gradient       ║    ║  confinement     ║
          ║  rf_pulse       ║    ║  thermal_proxy†  ║
          ║  bloch_signal   ║    ║  plasma_transport║
          ║  snr_model      ║    ║  toroidal_geom   ║
          ║  sar_safety     ║    ║  rf_link_budget  ║
          ╚═════════════════╝    ║  lagrange_stab   ║
                │                ║  gate_topology ‡ ║
                │                ╚═════════════════╝
                └────────────┬────────────┘
                             │
                    foundation.analyze()
                  Ω_overall · ATHENA · verdict

  †  magnetic/plasma heat proxy — 우주 방열 확정 설계 아님
  ‡  experimental — ATHENA 판정에서 보수적으로 가중
```

각 레이어는 완전히 독립이며, 입력이 없는 레이어는 자동으로 건너뜁니다.

---

## Ω 점수 계산 방식

| 레이어 종류 | 계산 방식 |
|-------------|-----------|
| 확립 물리 (MRI + Gate 공통) | 원점수 그대로 반영 |
| 실험적 개념층 (`gate_topology` 등) | **× 0.55 감쇠** 후 평균 포함 |
| 경고 수 | ATHENA 신뢰도 하향 |

```python
weighted = established_scores + [s * 0.55 for s in conceptual_scores]
omega_overall = mean(weighted)
```

같은 raw omega여도 개념층 비중이 높으면 `athena_stage`가 **cautious/negative**로 이동합니다. 확립 물리만으로 구성된 분석은 같은 점수에서 더 **positive** 해석을 받습니다.

---

## 판정 체계

| 지표 | 의미 | 범위 |
|------|------|------|
| `omega_overall` | 전체 스크리닝 점수 | 0.0 – 1.0 |
| `athena_stage` | 상위 해석 언어 | positive / neutral / cautious / negative |
| `athena_confidence` | 해석 확신도 | 0.0 – 1.0 |
| `verdict` | 준비도 판정 | production_ready / pilot_ready / prototype_ready / not_ready |

---

## 레이어 맵

```text
magnetic_resonance/
├── contracts.py            데이터 구조 + 물리 상수
├── larmor.py               ω₀ = γB₀  ← 공유 기반
├── gate_resonance.py       노드 간 detuning/coupling
│
├── ── MRI PATH ───────────────────────────────────
├── gradient_system.py      경사장: Δω(x)=γGx
├── rf_pulse.py             RF 펄스: B₁=α/(γT)
├── bloch_signal.py         블로흐: T₁/T₂ 이완
├── snr_model.py            SNR: B₀·V/√(BW·T)
├── sar_safety.py           SAR/dB·dt (IEC 60601-2-33)
├── mri_screening.py        MRI 오케스트레이터
│
├── ── GATE PATH ──────────────────────────────────
├── magnetic_confinement.py 자기거울/토로이달 가두기
├── thermal_transport.py    † 자기 열운반 proxy
├── plasma_transport.py     Spitzer 저항률, κ_∥/κ_⊥
├── toroidal_geometry.py    토카막/스텔라레이터 형상
├── rf_energy_transfer.py   Friis 링크 예산
├── lagrange_stability.py   L1~L5 안정성
├── gate_topology.py        ‡ 게이트 네트워크 (실험적)
│
├── ── INTEGRATION ────────────────────────────────
├── foundation.py           통합 analyze()
├── athena_stage.py         ATHENA 판정
├── space_gate_datacenter.py 우주 게이트 데이터센터 열 스택
├── ecosystem_bridges.py    형제 엔진 연결
├── cli.py                  CLI
└── __init__.py
```

---

## 핵심 물리 식

### 확립식 (Established)

| 식 | 층 | 의미 |
|----|-----|------|
| `ω₀ = γ · B₀` | 공유 | 라모어 공명 주파수 |
| `Δω(x) = γ · G · x` | MRI | 경사장 공간 인코딩 |
| `BW = γ/(2π) · G · Δz` | MRI | 슬라이스 선택 대역폭 |
| `M_z(t) = M₀(1 − e^{−t/T₁})` | MRI | 종축 이완 |
| `M_xy(t) = M₀ · e^{−t/T₂}` | MRI | 횡축 이완 (SE) |
| `α_Ernst = arccos(e^{−TR/T₁})` | MRI | 최적 flip angle |
| `R = B_max / B_min` | Gate | 자기거울 비 |
| `sin²θ = 1/R` | Gate | 손실원뿔 각 |
| `η = 5.2×10⁻⁵ · Z · lnΛ / T_e^{3/2}` | Gate | Spitzer 저항률 |
| `P_r = P_t · G_t · G_r · (λ/4πd)²` | Gate | Friis 수신 전력 |
| `r_L1 ≈ R · (μ/3)^{1/3}` | Gate | L1 위치 근사 |

### 스크리닝 Proxy (Proxy — 추정치, 검증 아님)

| 식 | 층 | 의미 |
|----|-----|------|
| `SNR ∝ B₀ · V_voxel · SI / √(BW · T)` | MRI | SNR 추정 proxy |
| `SAR ∝ f₀² · B₁² · duty / body_mass` | MRI | 전신 SAR proxy |
| `Q_thermal ∝ n · v_th · T · A` | Gate | 자기 열운반 proxy |

---

## 빠른 시작

### 설치

```bash
pip install -e "."          # 기본
pip install -e ".[dev]"     # 테스트 포함
```

### MRI 전용 스크리닝

```python
from magnetic_resonance import screen_mri, LarmorInput, GradientInput
from magnetic_resonance import RFPulseInput, BlochInput, SNRInput, SARInput

r = screen_mri(
    larmor_input=LarmorInput(nucleus="1H", field_strength_t=3.0),
    gradient_input=GradientInput(
        max_amplitude_mt_per_m=40,
        max_slew_rate_t_per_m_per_s=200,
        fov_m=0.40,
        matrix_size=256,
        b0_field_t=3.0,
    ),
    rf_pulse_input=RFPulseInput(flip_angle_deg=90, b0_field_t=3.0),
    bloch_input=BlochInput(flip_angle_deg=90, tr_ms=500, te_ms=10),
    snr_input=SNRInput(b0_field_t=3.0, coil_channels=32),
    sar_input=SARInput(b0_field_t=3.0, flip_angle_deg=90, tr_ms=500),
)
# 출력 예시:
# r.larmor.frequency_mhz  → 127.73
# r.gradient.spatial_resolution_mm → 1.56
# r.sar.sar_ok            → True
# r.omega_mri             → 0.68
# r.verdict.value         → "pilot_ready"
```

### Gate 전용 스크리닝

```python
from magnetic_resonance import screen_plasma_transport, PlasmaTransportInput
from magnetic_resonance import screen_lagrange_stability, LagrangeInput, LagrangePoint

plasma = screen_plasma_transport(PlasmaTransportInput(
    electron_temp_ev=1000.0,
    electron_density_m3=1e20,
    b_field_t=5.0,
))
# plasma.coulomb_log         → 15.7
# plasma.spitzer_resistivity_ohm_m → 3.1e-8
# plasma.omega_transport     → 0.78

lagrange = screen_lagrange_stability(LagrangeInput(point=LagrangePoint.L1))
# lagrange.stability_class.value  → "quasi_stable"
# lagrange.annual_dv_estimate_m_s → 12.4
# lagrange.omega_lagrange         → 0.61
```

### 통합 분석 (MRI + Gate 동시)

```python
from magnetic_resonance import analyze
from magnetic_resonance import (
    LarmorInput, GradientInput, BlochInput, SARInput,
    PlasmaTransportInput, LagrangeInput, LagrangePoint,
    ConfinementInput, ConfinementMode,
)

report = analyze(
    larmor_input=LarmorInput(field_strength_t=3.0),
    # MRI
    gradient_input=GradientInput(b0_field_t=3.0),
    bloch_input=BlochInput(tr_ms=500, te_ms=10),
    sar_input=SARInput(b0_field_t=3.0),
    # Gate
    confinement_input=ConfinementInput(
        mode=ConfinementMode.MAGNETIC_MIRROR,
        b_max_t=6.0, b_min_t=1.0,
    ),
    plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
    lagrange_input=LagrangeInput(point=LagrangePoint.L1),
)

print(f"MRI   → Ω={report.mri.omega_mri:.3f}  [{report.mri.verdict.value}]")
print(f"Gate  → confinement Ω={report.confinement.omega_confinement:.3f}")
print(f"Total → Ω={report.omega_overall:.3f}  {report.athena_stage.value}  [{report.verdict.value}]")
# 출력 예시:
# MRI   → Ω=0.571  [pilot_ready]
# Gate  → confinement Ω=0.720
# Total → Ω=0.541  neutral  [pilot_ready]
```

---

## CLI

```bash
# MRI 경로
mag-resonance mri --b0 3.0
mag-resonance mri --b0 1.5 --json

# Gate 경로
mag-resonance larmor --field 3.0 --nucleus 1H --json
mag-resonance plasma --temp 1000 --density 1e20 --bfield 5 --json
mag-resonance toroidal --major 6.2 --minor 2.0 --bt 5.3 --ip 15 --json
mag-resonance rflink --freq 1.28e8 --dist 3.84e8 --power 1e4 --dish 30 --json
mag-resonance lagrange --point L1 --json

# 도움말
mag-resonance --help
```

---

## 현재 한계

### MRI 경로

| 한계 | 영향 |
|------|------|
| k-space 재구성 미구현 | 실제 이미지 생성 불가 |
| EPI/multi-echo 미지원 | 고속 임상 시퀀스 설계 제한 |
| 균일 코일 가정 | SNR 추정이 proxy 수준 |
| SAR는 IEC 기반 proxy | 인허가용 EM 시뮬레이션 대체 불가 |
| 단일 조직 모델 | 다조직 대비 최적화 불가 |

### Gate 경로

| 한계 | 영향 |
|------|------|
| gate_topology 미입증 | 장치 청사진 아님 |
| thermal_transport는 proxy | 우주 방열 설계에 직접 사용 불가 |
| 2체 궤도 근사 | 정밀 궤도에는 GMAT/STK 필요 |
| RF 링크 자유공간 가정 | 대기/플라즈마 감쇠 미포함 |

> **의료 안전 경고**: MRI 경로는 교육/연구 스크리닝 도구입니다. 환자 진단이나 인허가용 의료기기 설계에 직접 사용하지 마십시오.

---

## 보안 및 무결성

```bash
python3 scripts/generate_signature.py    # SHA-256 서명 생성
python3 scripts/verify_signature.py      # 서명 검증
python3 scripts/verify_package_identity.py
python3 scripts/release_check.py
```

`SIGNATURE.sha256`은 릴리스 시점 파일들의 SHA-256을 기록합니다. 코드 변조 여부와 문서·코드·테스트 동기화를 추적합니다. 상세: [BLOCKCHAIN_INFO.md](BLOCKCHAIN_INFO.md)

---

## 테스트

```bash
python3 -m pytest tests/ -q
```

현재: **103 passed** (v0.4.0) — Larmor · Gate resonance · Confinement · Thermal · Plasma · Toroidal · RF link · Lagrange · Gradient · RF pulse · Bloch · SNR · SAR · MRI screening · Foundation MRI · Ecosystem bridges · Space gate datacenter stack · Satellite bridge · Orbital bridge · CLI · Integrity

---

## 형제 엔진 연결

| 엔진 | 연결 내용 |
|------|----------|
| `FrequencyCore_Engine` | 공명 응답 함수 재사용 |
| `Superconducting_Magnet_Stack` | 강자기장 코일 설계 파라미터 |
| `Space_Thermal_Dynamics_Foundation` | 복사 열관리 vs 자기 기반 열운반 비교 |
| `Optics_Foundation` | 라모어 주파수 → 파장 snapshot → 광학 screening |
| `Satellite_Design_Stack` | 게이트 하드웨어를 위성 payload mission으로 투영해 readiness 확인 |
| `OrbitalCore_Engine` | 게이트/노드 배치를 궤도 건강도 `omega_orb`로 스크리닝 |
| `Superconducting_Magnet_Stack` | 강자기장 코일을 quench/thermal/readiness 언어로 직접 스크리닝 |
| `Manufacturing_Translation_Foundation` | 코일/구조물 제조 readiness handoff |
| `Foundry_Implementation_Engine` | 공정/signoff readiness tick |
| `Fabless-style semiconductor flow` | MTF adapter를 통한 간접 semiconductor chain 연결 |

형제 엔진이 없으면 `None`으로 degrade되고, core는 독립 실행됩니다.

### Factory 계열 handoff

MRF가 Factory 계열에 실제로 연결되는 방식은 두 갈래입니다.

1. `MRI PATH -> MTF`
- RF coil, gradient housing, cryogenic or magnetic module 같은 의료/계측 장비형 부품을
  제조 payload로 내립니다.
- 그 payload는 `Manufacturing_Translation_Foundation`에서 공정, BOM, 공차, 조립, 테스트,
  `omega_mfg`, `athena_stage`, `verdict`로 다시 번역됩니다.

2. `GATE PATH -> MTF / Foundry / Fabless-style flow`
- 코일, 차폐, 진공 구조물, 프레임 같은 개념 장치를 시제품/공정 readiness 언어로 내립니다.
- `Foundry_Implementation_Engine`에는 공정/signoff tick으로,
  `fabless-style semiconductor flow`에는 MTF adapter 경유 chain screening으로 전달됩니다.

즉 이 저장소는 자기공명 개념을 여기서 끝내지 않고,
**코일·RF·차폐·구조물을 실제 제조와 공정 언어로 내리는 입구**까지 포함합니다.

## 우주 게이트 데이터센터 열 스택

우주 게이트 자체를 데이터센터처럼 쓰려면, 냉각은 세 층으로 나눠 읽어야 합니다.

1. `internal_air`
- 내부 밀폐 대기/가스를 돌리는 공냉/강제대류 층
- `Space_Thermal_Dynamics_Foundation`의 `terrestrial_convection` 경로 재사용

2. `magnetic_assist`
- 자기공명/플라즈마/전자기 루프를 통한 보조 수송층
- 일반 공기를 직접 돌리는 주 냉각기가 아니라 **보조층**으로만 사용

3. `external_radiator`
- 최종적으로 우주 바깥으로 열을 버리는 복사 층
- `Space_Thermal_Dynamics_Foundation.run_foundation()` 재사용

즉 구조는 다음과 같습니다.

```text
compute heat
-> internal air convection
-> magnetic auxiliary transport (optional)
-> external radiator
-> space radiation sink
```

이 설계는 “MRI 식 회전이 공기를 직접 냉각한다”는 과장을 피하고,
**공냉은 내부층, 자기공명은 보조층, 복사는 최종층**으로 역할을 고정합니다.

### 사용 예시

```python
from magnetic_resonance import SpaceGateDataCenterInput, screen_space_gate_datacenter

report = screen_space_gate_datacenter(
    SpaceGateDataCenterInput(
        gate_name="orbital_gate_dc_alpha",
        compute_heat_load_w=1200.0,
        radiator_area_m2=8.0,
        internal_air_supply_temp_c=20.0,
        internal_air_exhaust_limit_c=38.0,
        internal_air_volumetric_flow_m3_s=1.2,
        field_t=3.0,
        magnetic_assist_enabled=True,
        magnetic_assist_fraction_0_1=0.15,
    )
)
```

핵심 출력:
- `internal_air_omega`
- `external_radiator_omega`
- `magnetic_assist_omega`
- `overall_omega`
- `bottleneck_layer`
- `athena_stage`
- `verdict`

## 새틀라이트 / 오비탈 연결

현재 MRF는 위성/오비탈 쪽과도 **직접 브리지**를 가집니다.

1. `try_satellite_gate_bridge(...)`
- 게이트 하드웨어나 자기공명 payload를 `Satellite_Design_Stack`의 mission/pipeline 언어로 투영합니다.
- 반환 예:
  - `omega_satellite`
  - `verdict`
  - `thermal_hot_case_c`
  - `link_margin_db`

2. `try_orbital_gate_bridge(...)`
- 게이트 노드나 우주 데이터센터 배치를 `OrbitalCore_Engine`의 궤도 건강도 언어로 투영합니다.
- 반환 예:
  - `omega_orb`
  - `drag_health`
  - `maneuver_budget_health`
  - `anomaly_notes`

즉 MRF는 이제
**공명/자기장 개념 -> 위성 탑재체 readiness -> 궤도 건강도 -> 제조/공정 handoff**
까지 한 줄로 이어질 수 있습니다.

## 시스템 스택 문서

상위 연결 구조는 [SYSTEM_STACK.md](/Users/jazzin/Desktop/00_BRAIN/_staging/Magnetic_Resonance_Foundation/docs/SYSTEM_STACK.md) 에 정리했습니다.

추천 데모:
- [space_gate_datacenter_demo.py](/Users/jazzin/Desktop/00_BRAIN/_staging/Magnetic_Resonance_Foundation/examples/space_gate_datacenter_demo.py)
- [factory_handoff_demo.py](/Users/jazzin/Desktop/00_BRAIN/_staging/Magnetic_Resonance_Foundation/examples/factory_handoff_demo.py)
- [system_stack_demo.py](/Users/jazzin/Desktop/00_BRAIN/_staging/Magnetic_Resonance_Foundation/examples/system_stack_demo.py)

---

## 버전 이력

| 버전 | 변경 |
|------|------|
| v0.1.0 | Larmor + Confinement + Thermal + Gate Topology |
| v0.2.0 | Plasma Transport + Toroidal + RF Link + Lagrange |
| v0.3.0 | ATHENA 판정 · examples · CONCEPT_EN |
| **v0.4.0** | **MRI PATH: Gradient → RF Pulse → Bloch → SNR → SAR** |

---

개념·철학: [CONCEPT.md](CONCEPT.md) · [CONCEPT_EN.md](CONCEPT_EN.md)  
영문: [README_EN.md](README_EN.md)
