# Magnetic Resonance Foundation — 개념 문서

> **한국어 (정본).** English: [CONCEPT_EN.md](CONCEPT_EN.md)

## 핵심 질문

> **자기공명이라는 하나의 물리에서 출발하면, 의료 MRI와 우주 게이트는 얼마나 먼 거리에 있는가?**

이 엔진은 그 거리를 **측정**합니다.

---

## 왜 하나의 기반인가

MRI도, 우주 게이트 개념도, 출발점은 같습니다:

```
ω₀ = γ · B₀
```

- MRI: 자기장 안의 수소 원자가 특정 주파수로 공명 → 공간 인코딩 → 이미지
- Gate: 두 공간 노드의 자기장이 같으면 공명 주파수가 잠김 → 네트워크 결합

차이는 **매질**(인체 vs 우주 플라즈마)과 **규모**(mm vs km~Mm)입니다.
물리 방정식 자체는 동일합니다.

---

## 두 경로 철학

### MRI 경로: "이미 작동하는 것"

MRI는 1970년대 이후 수십 년간 검증된 기술입니다.

- **Gradient**: 자기장 경사로 공간 위치 인코딩
- **RF Pulse**: 전자기파로 스핀 여기
- **Bloch 방정식**: T₁/T₂ 이완으로 신호 생성/감쇠
- **SNR**: 이미지 품질의 핵심 지표
- **SAR**: 환자 안전 한계

이 레이어들은 **확립된 물리와 공학**입니다. 점수가 높으면 실제 장비 설계에 가깝다는 뜻입니다.

### Gate 경로: "아직 묻고 있는 것"

우주 게이트는 확립된 것이 아닙니다. 하지만 그 아래 층은 확립 물리입니다:

- **확립**: mirror ratio, Spitzer resistivity, Friis link budget, Lagrange stability
- **실험적**: 멀리 떨어진 공명 노드를 네트워크로 해석하는 layer, 자기 기반 열운반을 우주 규모로 확장하는 서사

이 엔진은 "게이트를 만들었다"가 아니라, **이 개념이 lower-layer physics와 얼마나 충돌 없이 놓일 수 있는가를 묻는 판정기**입니다.

---

## 레이어별 해석

### 공유 기반: Larmor / Resonance

공명의 기준 주파수와 detuning을 제공합니다. MRI에서는 여기 주파수를, Gate에서는 노드 결합 조건을 결정합니다.

### MRI Layer 1: Gradient System

공간 인코딩의 하드웨어 한계를 봅니다. 해상도, 슬루율, 인코딩 시간 — 이것이 "얼마나 작은 것을 볼 수 있는가"를 결정합니다.

### MRI Layer 2: RF Pulse

여기 펄스의 물리적 제약을 봅니다. B₁ 세기, 대역폭, SAR 기여 — "얼마나 세게 때릴 수 있는가"입니다.

### MRI Layer 3: Bloch Signal

조직과 시퀀스 파라미터에서 실제로 얼마나 신호가 나오는지 봅니다. T₁/T₂ 가중, 에른스트 각 — "무엇이 보이는가"입니다.

### MRI Layer 4: SNR

신호 대 잡음비. "얼마나 깨끗하게 보이는가"입니다. 복셀 크기, 코일, 대역폭이 결정합니다.

### MRI Layer 5: SAR Safety

"환자에게 안전한가"입니다. IEC 한계를 넘으면 스캔을 돌릴 수 없습니다.

### Gate Layer: Confinement / Thermal

자기장 속 플라즈마의 가둠과 열운반. thermal transport는 **proxy**입니다 — 우주 냉각 확정 설계가 아닙니다.

### Gate Layer: Plasma Transport

충돌과 저항률, 비등방 수송. 확립 물리입니다.

### Gate Layer: Toroidal Geometry

토카막/스텔라레이터 수준의 형상 안정성. 확립 물리입니다.

### Gate Layer: RF Link

공명 개념을 실제 전송 예산과 잇는 층. Friis 방정식 기반으로 확립 물리입니다.

### Gate Layer: Lagrange Stability

공명 노드나 relay를 우주 어디에 둘 것인지. 2체 근사 기반으로 확립 물리입니다.

### Gate Layer: Gate Topology

**실험적 상부층**. 공명 잠김(lock), 결합 효율, 네트워크 점수 — 이것은 확립된 공학이 아닙니다. ATHENA 판정에서 보수적으로 가중됩니다.

---

## 판정 철학

### `verdict`

현재 입력 묶음이 실험/파일럿/제작 준비도로 어느 수준인지 말합니다.

### `athena_stage`

상위 해석 언어입니다: `positive / neutral / cautious / negative`.

- 확립 물리만으로 구성 → 점수가 같아도 더 positive
- 개념층 비중이 높으면 → cautious/negative 쪽으로 이동
- 경고가 많으면 → 추가 감점

이것이 이 엔진의 **보수성**입니다. 확실한 것만 확실하게 말합니다.

---

## 00_BRAIN에서의 위치

이 저장소는 **물리 코어와 우주 개념 장치 사이의 완충층**입니다.

- `FrequencyCore_Engine` — 공명 응답
- `Superconducting_Magnet_Stack` — 강자기장 코일
- `Space_Thermal_Dynamics_Foundation` — 복사 열관리와 자기 기반 열운반 비교

---

## 결론

Magnetic Resonance Foundation은 "MRI를 만들었다"도 아니고 "우주 게이트를 만들었다"도 아닙니다.

**하나의 `ω₀ = γB₀` 에서 출발해, MRI가 현실에서 얼마나 잘 작동하는지를 보여주고, 우주 게이트가 그 물리에서 얼마나 떨어져 있는지를 측정하는 foundation**입니다. 기초가 탄탄하면 다음 확장으로 자연스럽게 올라갑니다.
