# Magnetic Resonance Foundation (gate_MRI)

> **한국어 (정본).** English: [README_EN.md](README_EN.md)

| 항목 | 내용 |
|------|------|
| 버전 | `v0.4.0` |
| 테스트 | `92 passed` |
| 의존성 | 런타임: 표준 라이브러리만 · 테스트: `pytest>=8.0` (선택) |
| 라이선스 | MIT |
| 패키지명 | `magnetic-resonance-foundation` |
| Python | `>=3.10` |

---

## 1. 이 프로젝트가 무엇인가

**Magnetic Resonance Foundation**은 하나의 물리 방정식 `ω₀ = γ · B₀` 에서 출발해, **현실 세계의 MRI 장비 설계**와 **우주 공간 게이트 개념 설계**를 독립 레이어로 쌓아 올리는 통합 자기공명 스크리닝 엔진입니다.

핵심 물음:

> "자기공명이라는 하나의 물리에서 출발하면, 의료 MRI와 우주 게이트는 얼마나 먼 거리에 있는가?"

이 엔진은 그 **거리를 측정**합니다. 각 레이어가 확립된 물리일수록 점수가 높고, 개념적/실험적 레이어일수록 보수적으로 가중됩니다. 최종 출력은 `Ω_overall` (0~1 스크리닝 점수), `athena_stage` (상위 해석), `verdict` (준비도)입니다.

---

## 2. 핵심 개념: 하나의 물리, 두 개의 경로

### 2.1 공유 기반 — 라모어 공명

모든 것의 시작은 **라모어 방정식**입니다:

```
ω₀ = γ · B₀
```

- `γ` = 자기회전비 (핵종에 따라 결정, 예: ¹H = 2.6752×10⁸ rad/(s·T))
- `B₀` = 외부 자기장 세기 (T)
- `ω₀` = 공명 각주파수 (rad/s)

MRI에서 이 식은 **"3T 자석에서 수소 원자는 127.73 MHz로 공명한다"**를 말하고, Gate 경로에서는 **"두 노드의 자기장이 같으면 공명 주파수가 잠김(lock)된다"**를 말합니다. 같은 물리, 다른 맥락입니다.

### 2.2 두 경로 아키텍처

```text
                        ω₀ = γ · B₀
                       (공유 기반: larmor.py)
                             │
                ┌────────────┴────────────┐
                │                         │
          ╔═══ MRI PATH ═══╗    ╔═══ GATE PATH ═══╗
          ║                 ║    ║                  ║
          ║  gradient_system║    ║  confinement     ║
          ║  rf_pulse       ║    ║  thermal_proxy   ║
          ║  bloch_signal   ║    ║  plasma_transport║
          ║  snr_model      ║    ║  toroidal_geom   ║
          ║  sar_safety     ║    ║  rf_link_budget  ║
          ║                 ║    ║  lagrange_stab   ║
          ╚═════════════════╝    ║  gate_topology   ║
                │                ╚══════════════════╝
                │                         │
                └────────────┬────────────┘
                             │
                    foundation.analyze()
                  Ω_overall · ATHENA · verdict
```

**각 레이어는 완전히 독립**입니다:
- `screen_gradient()` 단독 실행 가능
- `screen_mri()` 로 MRI 경로만 묶어서 실행 가능
- `analyze()` 로 MRI + Gate 양쪽을 동시에 실행 가능
- 입력이 없는 레이어는 자동으로 건너뜁니다

---

## 3. MRI 경로 — 현실 설계

MRI 경로는 **실제 의료/연구용 MRI 장비의 핵심 파라미터**를 스크리닝합니다.

### 3.1 Gradient System (`gradient_system.py`)

**개념**: 공간의 어느 위치를 여기(excite)할지 결정하는 경사장 코일 시스템.

```
Δω(x) = γ · G · x
```

위치 `x`의 공명 주파수가 경사장 `G`에 의해 선형으로 이동합니다. 이것이 MRI의 "어디를"을 결정합니다.

**스크리닝 항목**:
- 공간 해상도 (FOV / matrix, mm)
- 픽셀 대역폭 (Hz/pixel)
- 슬루율 기반 라이즈 타임 (ms)
- 최소 인코딩 시간 (ms)
- 듀티사이클 한계

### 3.2 RF Pulse Design (`rf_pulse.py`)

**개념**: 원자 스핀을 원하는 각도로 기울이는 전자기파 펄스.

```
B₁ = α / (γ · T_pulse)
```

flip angle `α`를 달성하기 위한 B₁ 세기를 결정합니다.

**스크리닝 항목**:
- 펄스 길이 (ms)
- 여기 대역폭 (Hz)
- B₁ 피크/RMS (μT)
- 펄스 에너지 proxy
- hard / sinc / gaussian 타입 지원

### 3.3 Bloch Signal Model (`bloch_signal.py`)

**개념**: 조직에서 자기 공명 신호가 어떻게 생성되고 감쇠하는지.

```
M_z(t) = M₀ · (1 − e^{−t/T₁})       ← 종축 이완 (recovery)
M_xy(t) = M₀ · e^{−t/T₂}             ← 횡축 이완 (decay)
α_Ernst = arccos(e^{−TR/T₁})          ← 최적 flip angle
```

**스크리닝 항목**:
- T₁/T₂ 이완 기반 신호 세기
- 에른스트 각 (최대 SNR flip angle)
- 스핀 에코 / 그래디언트 에코 모드
- T₁/T₂ 가중 정도

### 3.4 SNR Model (`snr_model.py`)

**개념**: 이미지에서 실제 정보(신호) vs 잡음(noise)의 비.

```
SNR ∝ B₀ · V_voxel · SI / √(BW · T)
```

**스크리닝 항목**:
- 복셀 크기 기반 SNR₀
- 평균 효과: SNR × √N_avg
- 병렬 코일 효과: SNR × √N_ch
- 진단 임계 (SNR < 5 경고)

### 3.5 SAR Safety (`sar_safety.py`)

**개념**: 환자 체내에 흡수되는 RF 에너지의 안전 한계 (IEC 60601-2-33).

```
전신 SAR ∝ f₀² · B₁² · duty_cycle / body_mass
dB/dt ≤ 20 T/s (말초 신경 자극 한계)
```

**스크리닝 항목**:
- 전신 SAR (W/kg) vs IEC 한계 (Normal: 2, First level: 4)
- dB/dt (T/s)
- SAR 여유율 (fraction)
- 모드별 한계 전환

### 3.6 MRI Orchestrator (`mri_screening.py`)

위 5개 레이어를 순서대로 실행하고 `MRIScreeningReport`로 묶습니다.

```python
from magnetic_resonance import screen_mri, LarmorInput, GradientInput, ...

report = screen_mri(
    larmor_input=LarmorInput(field_strength_t=3.0),
    gradient_input=GradientInput(b0_field_t=3.0),
    rf_pulse_input=RFPulseInput(b0_field_t=3.0),
    bloch_input=BlochInput(),
    snr_input=SNRInput(b0_field_t=3.0),
    sar_input=SARInput(b0_field_t=3.0),
)
print(f"Ω_mri={report.omega_mri}  verdict={report.verdict.value}")
```

---

## 4. Gate 경로 — 우주 확장

Gate 경로는 **확립된 플라즈마/RF/궤도역학 물리** 위에 **실험적 게이트 네트워크 토폴로지**를 얹어 스크리닝합니다.

### 4.1 확립 물리층

| 모듈 | 물리 | 설명 |
|------|------|------|
| `magnetic_confinement.py` | Mirror ratio R = B_max/B_min | 자기거울/자기병/토로이달 가두기 |
| `thermal_transport.py` | 플라즈마 열속도 v_th = √(2kT/m) | 자기장 기반 열운반 용량 proxy |
| `plasma_transport.py` | Spitzer η, Coulomb ln Λ | 충돌·저항률·비등방 수송 κ_∥/κ_⊥ |
| `toroidal_geometry.py` | 종횡비 A = R₀/a, 안전 인자 q | 토카막/스텔라레이터 형상 |
| `rf_energy_transfer.py` | Friis P_r = P_t·G²/FSPL | 원거리 RF 링크 예산 |
| `lagrange_stability.py` | L1 ≈ R·(μ/3)^(1/3) | L1~L5 안정성·station-keeping |

### 4.2 실험적 상부층

| 모듈 | 성격 | 설명 |
|------|------|------|
| `gate_topology.py` | **conceptual** | 공명 노드 네트워크, 결합 효율 |
| `gate_resonance.py` | mixed | 원거리 공명 detuning + 결합 proxy |

이 층은 확립된 것이 아니라 **"이 개념이 아래 물리와 얼마나 충돌 없이 놓일 수 있는가"를 묻는** 스크리닝입니다.

---

## 5. 통합 — `foundation.analyze()`

```python
from magnetic_resonance import analyze, LarmorInput, GradientInput, ...

report = analyze(
    # 공유
    larmor_input=LarmorInput(),
    # MRI 경로
    gradient_input=GradientInput(),
    bloch_input=BlochInput(),
    sar_input=SARInput(),
    # Gate 경로
    plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
    lagrange_input=LagrangeInput(point=LagrangePoint.L1),
)

# MRI 결과
print(report.mri.omega_mri, report.mri.verdict.value)

# 전체 결과
print(report.omega_overall, report.athena_stage.value, report.verdict.value)
```

### 5.1 판정 체계

| 지표 | 의미 | 값 |
|------|------|-----|
| `omega_overall` | 전체 스크리닝 점수 | 0.0 ~ 1.0 |
| `athena_stage` | 상위 해석 언어 | positive / neutral / cautious / negative |
| `athena_confidence` | 해석 확신도 | 0.0 ~ 1.0 |
| `verdict` | 준비도 판정 | production_ready / pilot_ready / prototype_ready / not_ready |

**ATHENA 보수성**: 개념층(gate_topology 등)의 비중이 높으면 `athena_stage`가 cautious/negative 쪽으로 이동합니다. 확립 물리만으로 구성된 분석은 점수가 같아도 더 positive한 해석을 받습니다.

---

## 6. 확장성

### 6.1 MRI 경로 확장

| 다음 단계 | 내용 | 난이도 |
|-----------|------|--------|
| k-space 재구성 | FFT 기반 이미지 재구성 시뮬레이션 | 중 |
| Multi-echo / EPI | 고속 시퀀스 설계 | 중 |
| 이미징 아티팩트 | 화학적 이동, 감수성, 래핑 | 중 |
| 코일 설계 | Birdcage/surface coil 감도 패턴 | 상 |
| fMRI BOLD | 기능적 MRI 혈류역학 응답 | 상 |
| 실측 데이터 피팅 | DICOM 데이터 대조 인터페이스 | 상 |

### 6.2 Gate 경로 확장

| 다음 단계 | 내용 | 난이도 |
|-----------|------|--------|
| Superconducting Magnet 연결 | 실제 초전도 코일 사양 연결 | 중 |
| Orbit propagation + LoS | 시선(Line-of-Sight) 가용성 | 중 |
| CRTBP 심화 | 원형 제한 삼체 문제 정밀 해석 | 상 |
| Magnetic reconnection | 자기 재결합 에너지 방출 모델 | 상 |
| Multi-body gate chain | 3개 이상 천체 계의 게이트 배치 | 상 |

### 6.3 형제 엔진 연결

이 엔진은 `00_BRAIN` 생태계에서 다른 엔진과 브리지합니다:

- **`FrequencyCore_Engine`** — 공명 응답 함수 재사용
- **`Superconducting_Magnet_Stack`** — 강자기장 코일 설계 파라미터
- **`Space_Thermal_Dynamics_Foundation`** — 복사 열관리와 자기 기반 열운반 비교

형제 엔진이 없으면 브리지는 `None`으로 degrade되고, 코어는 독립 실행됩니다.

---

## 7. 활용 시나리오

### 7.1 MRI 연구/교육

```bash
# 3T MRI 전체 스크리닝
mag-resonance mri --b0 3.0

# 1.5T vs 7T 비교
mag-resonance mri --b0 1.5 --json > result_1.5T.json
mag-resonance mri --b0 7.0 --json > result_7T.json
```

- 학부/대학원 MRI 물리 수업에서 파라미터 변화의 영향 시뮬레이션
- 새 MRI 시퀀스 설계 시 초기 사양 스크리닝
- 경사장/RF/SAR 트레이드오프 탐색

### 7.2 우주 시스템 개념 설계

```bash
# 라그랑주 L1 게이트 배치
mag-resonance lagrange --point L1 --json

# 지구-달 RF 링크 예산
mag-resonance rflink --freq 1.28e8 --dist 3.84e8 --power 1e4 --dish 30 --json
```

- 우주 게이트 개념의 물리적 타당성 초기 스크리닝
- 플라즈마 가두기 / RF 링크 / 궤도 배치 트레이드오프
- 서사(narrative) 기반 시나리오의 정량적 근거 확인

### 7.3 통합 분석

```python
# MRI 설계 파라미터와 우주 게이트 물리를 하나의 분석으로
report = analyze(
    larmor_input=LarmorInput(),
    gradient_input=GradientInput(),
    sar_input=SARInput(),
    plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
    lagrange_input=LagrangeInput(point=LagrangePoint.L1),
)
```

---

## 8. 현재 한계점

### 8.1 MRI 경로

| 한계 | 설명 | 영향 |
|------|------|------|
| **k-space 없음** | 주파수 영역 → 이미지 재구성 미구현 | 실제 이미지 생성 불가 |
| **다중 에코 미지원** | EPI, turbo SE 등 고속 시퀀스 없음 | 임상 시퀀스 설계에 직접 사용 어려움 |
| **코일 형상 미포함** | 균일 코일 가정, 실제 B₁ 맵 없음 | SNR 추정이 proxy 수준 |
| **조직 모델 단순** | 단일 조직, 3T 백질 기본값 | 다조직 대비(contrast) 최적화 불가 |
| **SAR 근사** | IEC 기반 proxy, 전자기 시뮬레이션 아님 | 인허가용 설계에는 부족 |
| **아티팩트 미포함** | 화학적 이동, 감수성, 절첩 등 미모델링 | 실제 이미지 품질 예측 제한 |

### 8.2 Gate 경로

| 한계 | 설명 | 영향 |
|------|------|------|
| **게이트 토폴로지 미입증** | 확립된 공학이 아닌 개념적 서사 | 장치 설계 청사진이 아님 |
| **플라즈마 모델 간소화** | 단일 이온종, 정상 상태 가정 | 실제 불안정성 미포착 |
| **궤도역학 근사** | 2체 근사, 섭동 미포함 | 정밀 궤도에는 GMAT/STK 필요 |
| **자기 열운반 proxy** | 개념적 추정, 검증 데이터 없음 | 우주 방열 설계에 직접 사용 불가 |
| **RF 링크 이상화** | 자유공간만, 대기/플라즈마 감쇠 미포함 | 실측과 차이 가능 |

### 8.3 공통

- **실측 데이터 피팅 없음**: 이론적 모델만, 실험 데이터 대조 인터페이스 미구현
- **단위 시스템 혼재 가능성**: 대부분 SI이지만, mm/mT 등 편의 단위 혼재
- **Python 3.10+ 필요**: f-string 등 문법 요구

---

## 9. 보안 및 무결성

### 9.1 SHA-256 파일 서명

모든 릴리스는 `SIGNATURE.sha256` 파일로 고정됩니다.

```bash
# 서명 생성
python3 scripts/generate_signature.py

# 서명 검증
python3 scripts/verify_signature.py

# 패키지 정체성 확인
python3 scripts/verify_package_identity.py
```

서명은 릴리스 시점의 **모든 소스 파일의 SHA-256 해시**를 기록하여:
- 코드 변조 여부 검출
- 문서·코드·테스트 동기화 확인
- 버전 간 차이 추적

### 9.2 온체인 기록

현재 이 저장소는 온체인 스마트컨트랙트를 포함하지 않습니다. `SIGNATURE.sha256`은 오프체인 서명이며, 필요 시 IPFS/Arweave 등에 해시를 고정할 수 있도록 설계되어 있습니다.

### 9.3 보안 고려사항

| 항목 | 현재 상태 | 권장 조치 |
|------|-----------|-----------|
| 의존성 | stdlib only (런타임) | 공급망 공격 표면 최소 |
| 입력 검증 | 기본 범위 체크 | 극단값 퍼징 테스트 추가 권장 |
| 의료 안전 | SAR/dB/dt 경고 출력 | **진단/치료 목적 사용 금지** |
| 코드 서명 | SHA-256 파일별 | GPG 서명 추가 권장 |
| 접근 제어 | 공개 저장소 | 민감 파라미터 노출 주의 |

> **경고**: 이 엔진의 MRI 경로는 교육/연구 목적의 스크리닝 도구입니다. **의료 기기 설계나 환자 진단에 직접 사용해서는 안 됩니다.** SAR/dB/dt 계산은 IEC 기반 proxy이며, 인허가용 전자기 시뮬레이션을 대체하지 않습니다.

---

## 10. 레이어 구조 (모듈 맵)

```text
magnetic_resonance/
├── contracts.py            # 데이터 구조 + 물리 상수 (전체 공유)
├── larmor.py               # ω₀ = γB₀ (공유 기반)
├── gate_resonance.py       # 노드 간 공명 매칭 (공유)
│
├── ─── MRI PATH ─────────────────────
├── gradient_system.py      # 경사장 스크리닝
├── rf_pulse.py             # RF 펄스 설계
├── bloch_signal.py         # 블로흐 신호 모델
├── snr_model.py            # SNR 추정
├── sar_safety.py           # SAR/dB/dt 안전
├── mri_screening.py        # MRI 오케스트레이터
│
├── ─── GATE PATH ────────────────────
├── magnetic_confinement.py # 자기 가두기
├── thermal_transport.py    # 열운반 proxy
├── plasma_transport.py     # 플라즈마 수송
├── toroidal_geometry.py    # 토로이달 형상
├── rf_energy_transfer.py   # RF 링크 예산
├── lagrange_stability.py   # 라그랑주 안정성
├── gate_topology.py        # 게이트 토폴로지 (실험적)
│
├── ─── INTEGRATION ──────────────────
├── foundation.py           # 통합 analyze()
├── athena_stage.py         # ATHENA 판정
├── ecosystem_bridges.py    # 형제 엔진 연결
├── cli.py                  # CLI 진입점
└── __init__.py             # 패키지 초기화
```

---

## 11. 핵심 물리 식 모음

### 공유

| 식 | 의미 |
|----|------|
| `ω₀ = γ · B₀` | 라모어 공명 주파수 |
| `f = ω₀ / 2π` | 주파수 (Hz) |
| `λ = c / f` | 파장 |

### MRI 전용

| 식 | 의미 |
|----|------|
| `Δω(x) = γ · G · x` | 경사장 공간 인코딩 |
| `BW = γ/(2π) · G · Δz` | 슬라이스 선택 대역폭 |
| `M_z(t) = M₀(1 − e^{−t/T₁})` | 종축 이완 |
| `M_xy(t) = M₀ · e^{−t/T₂}` | 횡축 이완 (SE) |
| `α_Ernst = arccos(e^{−TR/T₁})` | 에른스트 각 |
| `SNR ∝ B₀ · V · SI / √(BW·T)` | SNR proxy |
| `SAR ∝ f₀² · B₁² · duty / mass` | SAR proxy |

### Gate 전용

| 식 | 의미 |
|----|------|
| `R = B_max / B_min` | 자기거울 비 |
| `sin²θ_LC = 1/R` | 손실원뿔 각 |
| `η_Spitzer ≈ 5.2×10⁻⁵ Z lnΛ / T_e^{3/2}` | Spitzer 저항률 |
| `P_r = P_t · G_t · G_r / FSPL` | Friis 수신 전력 |
| `r_L1 ≈ R · (μ/3)^{1/3}` | L1 근사 위치 |

---

## 12. 빠른 시작

### 설치

```bash
pip install -e "."          # 기본 설치
pip install -e ".[dev]"     # 테스트 포함
```

### CLI 사용

```bash
# MRI 경로
mag-resonance mri --b0 3.0
mag-resonance mri --b0 1.5 --json

# Gate 경로
mag-resonance larmor --field 3 --nucleus 1H --json
mag-resonance plasma --temp 1000 --density 1e20 --bfield 5
mag-resonance lagrange --point L1

# 도움말
mag-resonance --help
```

### Python API

```python
# MRI만
from magnetic_resonance import screen_mri, LarmorInput, GradientInput, ...
report = screen_mri(larmor_input=LarmorInput(field_strength_t=3.0), ...)

# Gate만
from magnetic_resonance import screen_plasma_transport, PlasmaTransportInput
result = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=1000.0))

# 통합
from magnetic_resonance import analyze
report = analyze(larmor_input=..., gradient_input=..., plasma_transport_input=...)
```

---

## 13. 테스트

```bash
python3 -m pytest tests/ -q
```

현재: **92 passed** (v0.4.0)

| 범주 | 테스트 수 |
|------|-----------|
| Larmor / NMR | 5 |
| Gate resonance | 4 |
| Magnetic confinement | 5 |
| Thermal transport | 4 |
| Plasma transport | 5 |
| Toroidal geometry | 5 |
| RF energy transfer | 4 |
| Lagrange stability | 5 |
| Foundation roll-up | 3 |
| ATHENA stage | 4 |
| CLI (Gate) | 5 |
| Example script | 1 |
| Integrity | 1 |
| **Gradient system** | **3** |
| **RF pulse** | **3** |
| **Bloch signal** | **4** |
| **SNR model** | **3** |
| **SAR safety** | **3** |
| **MRI screening** | **3** |
| **Foundation MRI** | **3** |
| **CLI MRI** | **2** |

---

## 14. 무결성

```bash
python3 scripts/generate_signature.py    # 서명 생성
python3 scripts/verify_signature.py      # 서명 검증
python3 scripts/verify_package_identity.py  # 정체성
python3 scripts/release_check.py         # 통합 릴리스 체크
```

상세: [BLOCKCHAIN_INFO.md](BLOCKCHAIN_INFO.md) · [BLOCKCHAIN_INFO_EN.md](BLOCKCHAIN_INFO_EN.md)

---

## 15. 버전 이력

| 버전 | 변경 |
|------|------|
| v0.1.0 | Larmor + Confinement + Thermal + Gate Topology |
| v0.2.0 | Plasma Transport + Toroidal + RF Link + Lagrange |
| v0.3.0 | ATHENA 판정, examples, CONCEPT_EN |
| **v0.4.0** | **MRI PATH: Gradient → RF Pulse → Bloch → SNR → SAR** |

---

## 16. 라이선스

MIT

---

## 17. 결론

**Magnetic Resonance Foundation v0.4.0은 하나의 `ω₀ = γB₀` 에서 두 세계를 잇습니다.**

MRI 경로는 현실의 의료 장비 스크리닝으로, 기초가 탄탄합니다. Gate 경로는 그 기초 위에 서서 우주 게이트라는 개념이 물리와 얼마나 가까운지를 측정합니다. 기초가 쌓이면 다음 확장으로 자연스럽게 올라가는 구조 — 이것이 이 foundation의 설계 철학입니다.

개념 정본: [CONCEPT.md](CONCEPT.md) · [CONCEPT_EN.md](CONCEPT_EN.md)
