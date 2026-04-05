# Magnetic Resonance Foundation — 개념 문서

> **한국어 정본.** English: [CONCEPT_EN.md](CONCEPT_EN.md)

## 핵심 개념

이 엔진은 **하나의 `ω₀ = γB₀`** 를 공유 기반으로 삼아 두 개의 상이한 경로를 분리합니다.

- **MRI PATH**
  - 현실 장비 스크리닝
  - gradient, RF pulse, Bloch, SNR, SAR
- **GATE PATH**
  - 우주/플라즈마 확장 스크리닝
  - confinement, thermal proxy, plasma transport, toroidal geometry, RF link, Lagrange, topology

즉 이 저장소의 핵심은 “모든 것을 한 덩어리로 섞는다”가 아니라,  
**공유 공명 코어 위에 서로 다른 레이어를 독립 경로로 올리는 것** 입니다.

## 왜 이렇게 나누는가

MRI 경로는 비교적 현실적이고 확립된 공학 쪽에 가깝습니다.  
반면 Gate 경로는 lower-layer physics는 강하지만, 상부 topology는 여전히 실험적입니다.

그래서 이 엔진은 아래처럼 읽어야 합니다.

### 확립된 하부 물리

- `ω₀ = γB₀`
- 경사장 공간 인코딩
- RF 여기와 Bloch 이완
- SNR / SAR
- mirror ratio / loss cone
- Spitzer resistivity
- `κ_∥ ≫ κ_⊥`
- Friis / FSPL
- L1~L5 안정성 근사

### 실험적 상부 레이어

- `gate_topology.py`
- 자기 기반 열운반을 우주 시스템 scale로 확장하는 서사
- 지구-달-L1 배치를 공명 게이트 체인으로 읽는 해석

따라서 이 엔진은 “게이트를 만들었다”가 아니라,  
**개념이 lower-layer physics와 얼마나 멀리 떨어져 있는지 측정하는 판정기** 입니다.

## 레이어 구조

```text
Shared Core
  Larmor / Gate Resonance

MRI PATH
  Gradient System
  RF Pulse
  Bloch Signal
  SNR Model
  SAR Safety
  MRI Screening

GATE PATH
  Magnetic Confinement
  Thermal Proxy
  Plasma Transport
  Toroidal Geometry
  RF Energy Transfer
  Lagrange Stability
  Gate Topology (conceptual)

Master
  foundation.analyze()
```

## 판정 철학

### `verdict`

현재 입력 묶음이 실험/파일럿/제작 준비도로 어느 수준인지 말합니다.

### `athena_stage`

상위 해석 언어입니다.

- `positive`
- `neutral`
- `cautious`
- `negative`

여기서는 개념층 비중과 경고 수가 높아질수록 더 보수적으로 떨어집니다.

## 형제 엔진 연결

### 직접 연결

- `FrequencyCore_Engine`
  - 공명 응답 재사용
- `Space_Thermal_Dynamics_Foundation`
  - 복사 열관리와 자기 기반 열운반 proxy 비교
- `Optics_Foundation`
  - 공명 주파수를 전자기파/파장 snapshot으로 투영
- `Satellite_Design_Stack`
  - 게이트 하드웨어/탑재체를 위성 mission/readiness 언어로 투영
- `OrbitalCore_Engine`
  - 게이트 노드 배치를 `omega_orb` 건강도 언어로 투영
- `Manufacturing_Translation_Foundation`
  - 코일/구조물 제조 readiness handoff
- `Foundry_Implementation_Engine`
  - 공정 readiness / signoff tick

### 간접 연결

- fabless-style semiconductor flow
  - MTF의 `fabless_adapter`를 통해 간접 연결

즉 이 저장소는 **물리 코어, 의료 장비 스크리닝, 우주 개념층, 제조/공정 handoff 사이의 완충층** 입니다.

## 우주 게이트 데이터센터 열 스택

우주 게이트 자체를 데이터센터처럼 쓰려면, 열 문제는 한 식으로 뭉개면 안 됩니다.

### Layer 1 — 내부 대기 대류

- 게이트 내부를 밀폐된 대기/가스 환경으로 본다
- 서버/NPU 발열은 공기 순환과 열교환기로 먼저 모은다
- 이 층은 `Space_Thermal_Dynamics_Foundation`의 `terrestrial_convection` 경로를 재사용한다

### Layer 2 — 자기공명 보조 열수송

- 자기공명은 일반 공기를 직접 돌리는 주 냉각기가 아니다
- 대신 코일/플라즈마/전자기 루프를 통한 **보조 수송층**으로만 취급한다
- 이 층은 `thermal_transport.py`의 proxy를 보수적으로 사용한다

### Layer 3 — 외부 우주 복사

- 최종적으로 우주 바깥으로 나가는 열은 라디에이터 복사뿐이다
- 이 층은 `Space_Thermal_Dynamics_Foundation`의 `run_foundation()` 복사 경로를 재사용한다

즉 구조는 다음과 같습니다.

```text
compute heat
-> internal air convection
-> magnetic auxiliary transport (optional)
-> external radiator
-> space radiation sink
```

이 분리 원칙은 “MRI식 회전이 공기를 직접 냉각한다”는 과장을 피하고,
**자기공명은 보조층, 공냉은 내부층, 복사는 최종층**으로 역할을 고정합니다.

## 자가순환 지구환경형 우주선으로의 진화

이 저장소가 보는 장기 방향은 “바로 우주선을 만든다”가 아니라,
**작은 위성형 데이터센터에서 시작해 자가순환 지구환경형 우주선 개념으로 진화할 수 있는가**를 단계적으로 읽는 것입니다.

```text
satellite compute node
-> enclosed compute habitat
-> resonant orbital cluster
-> self-circulating gate habitat
-> earthlike starship concept
```

여기서 핵심은:

- `Satellite_Design_Stack`
  - 작은 위성형 노드가 실제로 성립하는가
- `Space_Thermal_Dynamics_Foundation`
  - 열을 내부 대류 + 외부 복사로 자립시킬 수 있는가
- `Superconducting_Magnet_Stack`
  - 강자기장 플랫폼이 quench/thermal 측면에서 버티는가
- `Satellite_Design_Stack.adapters.TerraCoreAdapter`
  - 내부 대기/물/전력/질량 조건이 폐회로 해비타트로 갈 수 있는가

즉 “gate”는 현재 시점에서 장치 명칭보다
**공명적으로 연결된 우주 인프라가 장기적으로 어떤 구조체로 발전할 수 있는지를 읽는 시스템 언어**에 가깝습니다.

## 결론

Magnetic Resonance Foundation v0.5.0은 “MRI와 우주 게이트를 섞어버린 저장소”가 아니라,  
**공유 자기공명 코어 위에 현실 경로와 실험 경로를 분리해 올리고, 필요할 때 광학·열·제조·파운드리·TerraCore로 브리징하며, 작은 위성형 데이터센터에서 자가순환 우주선 개념으로 이어지는 진화 로드맵까지 읽는 foundation** 입니다.
