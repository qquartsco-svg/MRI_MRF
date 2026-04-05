# Magnetic Resonance Foundation — 개념 문서

> **한국어 (정본).** English: [CONCEPT_EN.md](CONCEPT_EN.md)  
> 사용법·API·CLI: [README.md](README.md)

---

이 문서는 **왜**, **어떻게**, **어디까지** 를 다룹니다.  
코드 사용법은 [README.md](README.md) 를 참고하세요.

---

## 핵심 질문

> **자기공명이라는 하나의 물리에서 출발하면, 의료 MRI와 우주 게이트는 얼마나 먼 거리에 있는가?**

이 엔진은 그 거리를 **측정**합니다.

---

## 왜 하나의 기반인가

MRI도, 우주 게이트 개념도, 출발점은 같습니다:

```
ω₀ = γ · B₀
```

- **MRI**: 자기장 안의 수소 원자가 특정 주파수로 공명 → 공간 인코딩 → 이미지
- **Gate**: 두 공간 노드의 자기장이 같으면 공명 주파수가 잠김(lock) → 네트워크 결합

차이는 **매질**(인체 vs 우주 플라즈마)과 **규모**(mm vs km~Mm)입니다.  
물리 방정식 자체는 동일합니다. *같은 물리, 다른 맥락.*

---

## 두 경로 철학

### MRI 경로: "이미 작동하는 것"

MRI는 1970년대 이후 수십 년간 검증된 기술입니다.

| 레이어 | 묻는 것 |
|--------|---------|
| Gradient | 어디를 볼 것인가? — 공간 인코딩 |
| RF Pulse | 얼마나 세게 여기할 것인가? |
| Bloch | 조직에서 실제로 얼마나 신호가 나오는가? |
| SNR | 얼마나 깨끗하게 보이는가? |
| SAR | 환자에게 안전한가? |

이 레이어들은 확립된 공학입니다. 점수가 높으면 실제 장비 설계에 가깝습니다.

### Gate 경로: "아직 묻고 있는 것"

우주 게이트는 확립된 것이 아닙니다. 하지만 그 아래는 확립 물리입니다:

| 레이어 | 성격 |
|--------|------|
| Confinement · Plasma Transport · Toroidal · RF Link · Lagrange | **확립 물리** |
| Gate Topology · Gate Resonance | **실험적** — ATHENA 보수 가중 |

이 엔진은 "게이트를 만들었다"가 아니라, **이 개념이 lower-layer physics와 얼마나 충돌 없이 놓일 수 있는가를 묻는 판정기**입니다.

---

## 확립식 vs 실험적 확장

### 확립식 (검증된 물리)

```
ω₀ = γB₀              라모어 공명
Δω(x) = γGx           경사장 공간 인코딩
M_z(t) = M₀(1−e^{−t/T₁})   종축 이완
M_xy(t) = M₀e^{−t/T₂}       횡축 이완
η = 5.2×10⁻⁵ Z lnΛ / T_e^{3/2}   Spitzer
P_r = P_t G_t G_r (λ/4πd)²       Friis
r_L1 ≈ R(μ/3)^{1/3}              L1 근사
```

이 식들은 실험·관측으로 반복 검증된 것들입니다.

### 스크리닝 Proxy (추정치)

```
SNR ∝ B₀ · V · SI / √(BW·T)       측정 환경에 따라 크게 달라짐
SAR ∝ f₀² · B₁² · duty / mass     IEC 기반 추정, EM 시뮬 아님
Q_thermal ∝ n · v_th · T · A      자기 열운반의 개념적 추정
```

이 추정치들은 방향성을 확인하는 도구이지, 설계 확정값이 아닙니다.

---

## 판정 철학

### `verdict` — "지금 입력이 얼마나 준비됐는가"

현재 파라미터 묶음의 실험/파일럿/제작 준비도를 말합니다.

### `athena_stage` — "이 분석을 어떻게 읽어야 하는가"

상위 해석 언어: `positive / neutral / cautious / negative`

핵심 규칙:
- 확립 물리만으로 구성 → 같은 점수에서 더 positive
- 개념층 비중이 높으면 → cautious/negative 쪽으로 이동
- 경고가 많으면 → 추가 하향

이 보수성이 이 엔진의 핵심입니다. **확실한 것만 확실하게 말합니다.**

---

## `thermal_transport.py`에 대한 명확한 설명

이 모듈은 `Space_Thermal_Dynamics_Foundation` (형제 엔진)과 다릅니다.

- `thermal_transport.py` → **자기장 기반 플라즈마 열운반 proxy**  
  (자기장 방향을 따라 플라즈마가 얼마나 열을 운반할 수 있는가의 개념적 추정)
- `Space_Thermal_Dynamics_Foundation` → 복사 열관리, 방열판 설계, 실사용 우주 열관리

두 모델을 나란히 비교하는 것이 `ecosystem_bridges.py`의 역할입니다.

---

## Ω 점수와 ATHENA 가중 내부 구조

```python
# foundation.py 내부 (간략화)
scores = []           # 확립 물리 점수 모음
conceptual_scores = [] # 실험적 레이어 점수 모음

# 확립 레이어
scores.append(confinement.omega_confinement)
scores.append(plasma.omega_transport)
# ...

# 실험적 레이어
conceptual_scores.append(topology.omega_topology)

# 가중 평균
weighted = scores + [s * 0.55 for s in conceptual_scores]
omega_overall = mean(weighted)

# ATHENA 해석
conceptual_fraction = len(conceptual_scores) / len(weighted)
athena_stage = map_athena_stage(omega_overall, conceptual_fraction, warning_count)
```

0.55 감쇠 계수는 "개념층은 확립 물리 대비 약 절반의 신뢰도"를 뜻합니다. 이 값은 고정값이 아니며, 향후 실험 데이터 피팅으로 조정 가능합니다.

---

## 00_BRAIN에서의 위치

이 저장소는 **물리 코어와 우주 개념 장치 사이의 완충층**입니다.

```text
물리 코어
  ├── FrequencyCore_Engine       공명 응답
  ├── Superconducting_Magnet_Stack  강자기장 코일
  └── Space_Thermal_Dynamics_Foundation  복사 열관리
          │
          ↕  ecosystem_bridges.py
          │
  Magnetic Resonance Foundation  ← 여기
          │
          ↕
  우주 게이트 서사 / 확장 개념
```

---

## 결론

Magnetic Resonance Foundation은 "MRI를 만들었다"도 아니고 "우주 게이트를 만들었다"도 아닙니다.

**하나의 `ω₀ = γB₀`에서 출발해:**
1. MRI가 현실에서 얼마나 잘 작동하는지 보여주고
2. 우주 게이트 개념이 그 물리에서 얼마나 떨어져 있는지 측정하고
3. 그 거리를 Ω / ATHENA / verdict 언어로 표현합니다

기초가 탄탄하면 다음 확장으로 자연스럽게 올라갑니다.
