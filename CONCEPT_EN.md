# Magnetic Resonance Foundation — Concept

> **English.** Korean (정본): [CONCEPT.md](CONCEPT.md)  
> Usage, API, CLI: [README_EN.md](README_EN.md)

---

This document covers **why**, **how**, and **up to where**.  
For code usage, see [README_EN.md](README_EN.md).

---

## Core Question

> **Starting from one physics — magnetic resonance — how far apart are medical MRI and a space gate?**

This engine **measures that distance**.

---

## Why One Foundation

Both MRI and the space gate concept start from the same equation:

```
ω₀ = γ · B₀
```

- **MRI**: hydrogen atoms in a field resonate at a specific frequency → spatial encoding → image
- **Gate**: two spatial nodes with matching B₀ → frequency lock → network coupling

The difference is **medium** (human body vs. space plasma) and **scale** (mm vs. km–Mm).  
The physics equation is identical. *Same physics. Different context.*

---

## Two-Path Philosophy

### MRI Path: "What Already Works"

| Layer | The Question |
|-------|-------------|
| Gradient | Where to look? — spatial encoding |
| RF Pulse | How hard to excite? |
| Bloch | How much signal does tissue actually produce? |
| SNR | How clearly can we see? |
| SAR | Is it safe for the patient? |

These layers are established engineering. High scores mean the design is close to real equipment.

### Gate Path: "What We're Still Asking"

| Layer | Nature |
|-------|--------|
| Confinement · Plasma · Toroidal · RF Link · Lagrange | **Established physics** |
| Gate Topology · Gate Resonance | **Experimental** — conservatively weighted in ATHENA |

This engine does **not** claim "we built a gate." It asks **how far an idea can sit from lower-layer physics without contradiction**.

---

## Established vs Proxy

### Established (repeatedly verified)

```
ω₀ = γB₀                        Larmor resonance
Δω(x) = γGx                     Gradient spatial encoding
M_z(t) = M₀(1−e^{−t/T₁})       Longitudinal recovery
M_xy(t) = M₀e^{−t/T₂}           Transverse decay
η = 5.2×10⁻⁵ Z lnΛ / T_e^{3/2} Spitzer resistivity
P_r = P_t G_t G_r (λ/4πd)²     Friis received power
r_L1 ≈ R(μ/3)^{1/3}            L1 position
```

### Screening Proxy (directional estimates, not validated designs)

```
SNR ∝ B₀ · V · SI / √(BW·T)      varies heavily with measurement conditions
SAR ∝ f₀² · B₁² · duty / mass    IEC-based estimate, not EM simulation
Q_thermal ∝ n · v_th · T · A     conceptual magnetic heat transport estimate
```

---

## Judgment Philosophy

### `verdict` — "How ready is this input bundle?"

Readiness for experiment, pilot, or production given the current parameters.

### `athena_stage` — "How should we read this analysis?"

Interpretive language: `positive / neutral / cautious / negative`

Rules:
- Established-physics-only → more positive at the same score
- High conceptual-layer weight → shifts toward cautious/negative
- Many warnings → additional downgrade

**Confidence only in what is certain.** This conservatism is the engine's core value.

---

## Note on `thermal_transport.py`

This module is **distinct** from `Space_Thermal_Dynamics_Foundation` (sibling engine):

- `thermal_transport.py` → **plasma/magnetic heat transport proxy**  
  (conceptual estimate of how much heat plasma can carry along magnetic field lines)
- `Space_Thermal_Dynamics_Foundation` → radiative heat management, radiator design, actual spacecraft thermal

`ecosystem_bridges.py` places these two side-by-side for comparison.

---

## Ω Scoring Internals

```python
# foundation.py (simplified)
scores = []            # established physics scores
conceptual_scores = [] # experimental layer scores

scores.append(confinement.omega_confinement)   # established
conceptual_scores.append(topology.omega_topology)  # experimental

weighted = scores + [s * 0.55 for s in conceptual_scores]
omega_overall = mean(weighted)

conceptual_fraction = len(conceptual_scores) / len(weighted)
athena_stage = map_athena_stage(omega_overall, conceptual_fraction, warning_count)
```

The 0.55 damping factor encodes "conceptual layers carry roughly half the confidence of established physics." This is a fixed default adjustable by future experimental data fitting.

---

## Place in 00_BRAIN

```text
Physics cores
  ├── FrequencyCore_Engine
  ├── Superconducting_Magnet_Stack
  └── Space_Thermal_Dynamics_Foundation
          │
          ↕  ecosystem_bridges.py
          │
  Magnetic Resonance Foundation  ← here (buffer layer)
          │
          ↕
  Space gate narrative / speculative extensions
```

---

## Conclusion

**From one `ω₀ = γB₀`:**

1. Shows how well MRI works in reality
2. Measures how far a space-gate concept sits from that physics
3. Expresses that distance in Ω / ATHENA / verdict language

When the basics are solid, the next extension follows naturally.
