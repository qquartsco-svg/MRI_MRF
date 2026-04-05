# Magnetic Resonance Foundation

> **English.** Korean (정본): [README.md](README.md)  
> Concept & philosophy: [CONCEPT_EN.md](CONCEPT_EN.md)

| Item | Details |
|------|---------|
| Version | `v0.4.0` |
| Tests | `92 passed` |
| Deps | Runtime: stdlib only · Test: `pytest>=8.0` (optional) |
| Package | `magnetic-resonance-foundation` |
| Python | `>=3.10` |
| License | MIT |

---

## One-liner

**From a single `ω₀ = γ · B₀`, two independent paths — real-world MRI design and space-gate concept design — stacked as clean layers, producing Ω / ATHENA / verdict.**

*Same physics. Different context.*

---

## Two-Path Architecture

```text
                        ω₀ = γ · B₀
                     (shared base: larmor.py)
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

  †  magnetic/plasma heat proxy — not a spacecraft thermal design
  ‡  experimental — conservatively down-weighted in ATHENA
```

Every layer is fully independent. Layers with no input are skipped automatically.

---

## How Ω Is Calculated

| Layer Type | Calculation |
|------------|-------------|
| Established physics (MRI + Gate) | Full score |
| Experimental conceptual layers (`gate_topology`, etc.) | **× 0.55 damping** before averaging |
| Warning count | Lowers ATHENA confidence |

```python
weighted = established_scores + [s * 0.55 for s in conceptual_scores]
omega_overall = mean(weighted)
```

Conceptual layers are down-weighted in ATHENA interpretation even when raw omega is similar. Analyses composed entirely of established physics receive a more positive verdict at the same score.

---

## Judgment System

| Metric | Meaning | Range |
|--------|---------|-------|
| `omega_overall` | Overall screening score | 0.0 – 1.0 |
| `athena_stage` | Interpretive language | positive / neutral / cautious / negative |
| `athena_confidence` | Interpretation confidence | 0.0 – 1.0 |
| `verdict` | Readiness | production_ready / pilot_ready / prototype_ready / not_ready |

---

## Layer Map

```text
magnetic_resonance/
├── contracts.py            Data structures + physical constants
├── larmor.py               ω₀ = γB₀  ← shared base
├── gate_resonance.py       Node detuning/coupling
│
├── ── MRI PATH ───────────────────────────────────
├── gradient_system.py      Gradients: Δω(x)=γGx
├── rf_pulse.py             RF pulse: B₁=α/(γT)
├── bloch_signal.py         Bloch: T₁/T₂ relaxation
├── snr_model.py            SNR: B₀·V/√(BW·T)
├── sar_safety.py           SAR/dB·dt (IEC 60601-2-33)
├── mri_screening.py        MRI orchestrator
│
├── ── GATE PATH ──────────────────────────────────
├── magnetic_confinement.py Mirror/toroidal confinement
├── thermal_transport.py    † Magnetic heat transport proxy
├── plasma_transport.py     Spitzer resistivity, κ_∥/κ_⊥
├── toroidal_geometry.py    Tokamak/stellarator geometry
├── rf_energy_transfer.py   Friis link budget
├── lagrange_stability.py   L1–L5 stability
├── gate_topology.py        ‡ Gate network (experimental)
│
├── ── INTEGRATION ────────────────────────────────
├── foundation.py           Unified analyze()
├── athena_stage.py         ATHENA judgment
├── ecosystem_bridges.py    Sibling engine bridges
├── cli.py                  CLI entry point
└── __init__.py
```

---

## Key Equations

### Established

| Equation | Path | Meaning |
|----------|------|---------|
| `ω₀ = γ · B₀` | Shared | Larmor resonance frequency |
| `Δω(x) = γ · G · x` | MRI | Gradient spatial encoding |
| `BW = γ/(2π) · G · Δz` | MRI | Slice selection bandwidth |
| `M_z(t) = M₀(1 − e^{−t/T₁})` | MRI | Longitudinal recovery |
| `M_xy(t) = M₀ · e^{−t/T₂}` | MRI | Transverse decay (SE) |
| `α_Ernst = arccos(e^{−TR/T₁})` | MRI | Optimal flip angle |
| `R = B_max / B_min` | Gate | Mirror ratio |
| `η = 5.2×10⁻⁵ Z lnΛ / T_e^{3/2}` | Gate | Spitzer resistivity |
| `P_r = P_t · G_t · G_r · (λ/4πd)²` | Gate | Friis received power |
| `r_L1 ≈ R · (μ/3)^{1/3}` | Gate | L1 position |

### Screening Proxy (estimates, not validated)

| Equation | Path | Meaning |
|----------|------|---------|
| `SNR ∝ B₀ · V_voxel · SI / √(BW·T)` | MRI | SNR proxy |
| `SAR ∝ f₀² · B₁² · duty / mass` | MRI | Whole-body SAR proxy |
| `Q_thermal ∝ n · v_th · T · A` | Gate | Magnetic heat transport proxy |

---

## Quick Start

### Install

```bash
pip install -e "."          # basic
pip install -e ".[dev]"     # with tests
```

### MRI-only screening

```python
from magnetic_resonance import (
    screen_mri, LarmorInput, GradientInput,
    RFPulseInput, BlochInput, SNRInput, SARInput,
)

r = screen_mri(
    larmor_input=LarmorInput(nucleus="1H", field_strength_t=3.0),
    gradient_input=GradientInput(
        max_amplitude_mt_per_m=40,
        max_slew_rate_t_per_m_per_s=200,
        fov_m=0.40, matrix_size=256, b0_field_t=3.0,
    ),
    rf_pulse_input=RFPulseInput(flip_angle_deg=90, b0_field_t=3.0),
    bloch_input=BlochInput(flip_angle_deg=90, tr_ms=500, te_ms=10),
    snr_input=SNRInput(b0_field_t=3.0, coil_channels=32),
    sar_input=SARInput(b0_field_t=3.0, flip_angle_deg=90, tr_ms=500),
)
# r.larmor.frequency_mhz          → 127.73
# r.gradient.spatial_resolution_mm → 1.56
# r.sar.sar_ok                    → True
# r.omega_mri                     → 0.68
# r.verdict.value                 → "pilot_ready"
```

### Gate-only screening

```python
from magnetic_resonance import screen_plasma_transport, PlasmaTransportInput
from magnetic_resonance import screen_lagrange_stability, LagrangeInput, LagrangePoint

plasma = screen_plasma_transport(PlasmaTransportInput(
    electron_temp_ev=1000.0, electron_density_m3=1e20, b_field_t=5.0,
))
# plasma.coulomb_log              → 15.7
# plasma.spitzer_resistivity_ohm_m → 3.1e-8
# plasma.omega_transport          → 0.78

lagrange = screen_lagrange_stability(LagrangeInput(point=LagrangePoint.L1))
# lagrange.stability_class.value  → "quasi_stable"
# lagrange.annual_dv_estimate_m_s → 12.4
# lagrange.omega_lagrange         → 0.61
```

### Integrated (MRI + Gate)

```python
from magnetic_resonance import analyze
from magnetic_resonance import (
    LarmorInput, GradientInput, BlochInput, SARInput,
    ConfinementInput, ConfinementMode,
    PlasmaTransportInput, LagrangeInput, LagrangePoint,
)

report = analyze(
    larmor_input=LarmorInput(field_strength_t=3.0),
    gradient_input=GradientInput(b0_field_t=3.0),
    bloch_input=BlochInput(tr_ms=500, te_ms=10),
    sar_input=SARInput(b0_field_t=3.0),
    confinement_input=ConfinementInput(
        mode=ConfinementMode.MAGNETIC_MIRROR, b_max_t=6.0, b_min_t=1.0,
    ),
    plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
    lagrange_input=LagrangeInput(point=LagrangePoint.L1),
)
print(f"MRI   → Ω={report.mri.omega_mri:.3f}  [{report.mri.verdict.value}]")
print(f"Total → Ω={report.omega_overall:.3f}  {report.athena_stage.value}  [{report.verdict.value}]")
# MRI   → Ω=0.571  [pilot_ready]
# Total → Ω=0.541  neutral  [pilot_ready]
```

---

## CLI

```bash
mag-resonance mri --b0 3.0
mag-resonance mri --b0 1.5 --json
mag-resonance larmor --field 3.0 --nucleus 1H --json
mag-resonance plasma --temp 1000 --density 1e20 --bfield 5 --json
mag-resonance lagrange --point L1 --json
mag-resonance --help
```

---

## Current Limitations

### MRI Path

| Limitation | Impact |
|------------|--------|
| No k-space reconstruction | Cannot generate actual images |
| No EPI/multi-echo | Clinical fast sequence design limited |
| Uniform coil assumed | SNR is proxy-level |
| SAR is IEC proxy | Cannot replace regulatory EM simulation |

### Gate Path

| Limitation | Impact |
|------------|--------|
| gate_topology unproven | Not a device blueprint |
| thermal_transport is a plasma/magnetic proxy — not a full spacecraft thermal model | Cannot use for radiator design |
| Two-body orbit approximation | Precision orbits need GMAT/STK |
| Free-space RF link only | Ignores atmospheric/plasma attenuation |

> **Medical safety warning**: The MRI path is an educational/research screening tool. Do NOT use it for patient diagnosis or regulatory medical device design.

---

## Security & Integrity

```bash
python3 scripts/generate_signature.py   # SHA-256 sign
python3 scripts/verify_signature.py     # verify
```

`SIGNATURE.sha256` records SHA-256 of all 40 source files to detect tampering and track doc/code/test synchronization. See [BLOCKCHAIN_INFO_EN.md](BLOCKCHAIN_INFO_EN.md).

---

## Tests

```bash
python3 -m pytest tests/ -q    # 92 passed (v0.4.0)
```

---

## Version History

| Version | Changes |
|---------|---------|
| v0.1.0 | Larmor + Confinement + Thermal + Gate Topology |
| v0.2.0 | Plasma Transport + Toroidal + RF Link + Lagrange |
| v0.3.0 | ATHENA judgment · examples · CONCEPT_EN |
| **v0.4.0** | **MRI PATH: Gradient → RF Pulse → Bloch → SNR → SAR** |

---

Concept & philosophy: [CONCEPT_EN.md](CONCEPT_EN.md)
