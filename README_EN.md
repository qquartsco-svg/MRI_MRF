# Magnetic Resonance Foundation

> **English.** Korean (정본): [README.md](README.md)  
> Concept & philosophy: [CONCEPT_EN.md](CONCEPT_EN.md)

| Item | Details |
|------|---------|
| Version | `v0.4.0` |
| Tests | `103 passed` |
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
├── space_gate_datacenter.py Space gate data center thermal stack
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

`SIGNATURE.sha256` records SHA-256 of the release files to detect tampering and track doc/code/test synchronization. See [BLOCKCHAIN_INFO_EN.md](BLOCKCHAIN_INFO_EN.md).

---

## Tests

```bash
python3 -m pytest tests/ -q    # 103 passed (v0.4.0)
```

## Sibling Engine Bridges

- `FrequencyCore_Engine` — resonance response reuse
- `Space_Thermal_Dynamics_Foundation` — radiation vs magnetic transport proxy
- `Optics_Foundation` — Larmor frequency → wavelength snapshot → optics screening
- `Satellite_Design_Stack` — project gate hardware into a satellite payload mission and readiness report
- `OrbitalCore_Engine` — project gate/node placement into orbital health language (`omega_orb`)
- `Manufacturing_Translation_Foundation` — coil/structure manufacturing readiness handoff
- `Foundry_Implementation_Engine` — process/signoff readiness tick
- `Fabless-style semiconductor flow` — indirect semiconductor-chain bridge via MTF adapters

### Factory handoff

MRF connects to factory-facing engines through two practical routes.

1. `MRI PATH -> MTF`
- RF coils, gradient housings, cryogenic or magnetic modules are lowered into
  manufacturing payloads.
- `Manufacturing_Translation_Foundation` then turns them into process, BOM,
  tolerance, assembly, test, `omega_mfg`, `athena_stage`, and `verdict`.

2. `GATE PATH -> MTF / Foundry / Fabless-style semiconductor flow`
- Coils, shielding, vacuum structures, and frames are lowered into prototype or
  process-readiness payloads.
- Those payloads can be screened by MTF, sent to foundry/signoff ticks, or
  passed through an indirect fabless-style semiconductor chain.

This means MRF does not stop at conceptual resonance analysis; it also provides
an entry path for turning coils, RF subsystems, shielding, and structural parts
into manufacturing language.

## Space gate data center thermal stack

If the gate itself is used as a data-center-like structure, cooling should be read as three separate layers.

1. `internal_air`
- enclosed-atmosphere forced-air path
- reuses `Space_Thermal_Dynamics_Foundation.terrestrial_convection`

2. `magnetic_assist`
- auxiliary transport through resonance/plasma/electromagnetic loops
- not the primary mechanism that directly drives ordinary air cooling

3. `external_radiator`
- final vacuum-side radiator rejection path
- reuses `Space_Thermal_Dynamics_Foundation.run_foundation()`

The stack is therefore:

```text
compute heat
-> internal air convection
-> magnetic auxiliary transport (optional)
-> external radiator
-> space radiation sink
```

This avoids the overclaim that “MRI-like rotation directly cools the air,” and fixes the roles more honestly:
**air cooling is internal, magnetic resonance is auxiliary, radiation is final**.

### Example

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

## Satellite / orbital integration

MRF now also has direct bridges into satellite and orbital engines.

1. `try_satellite_gate_bridge(...)`
- projects a gate or magnetic-resonance hardware concept into the `Satellite_Design_Stack` mission/pipeline language
- returns fields such as:
  - `omega_satellite`
  - `verdict`
  - `thermal_hot_case_c`
  - `link_margin_db`

2. `try_orbital_gate_bridge(...)`
- projects a gate node or orbital compute placement into `OrbitalCore_Engine` health language
- returns fields such as:
  - `omega_orb`
  - `drag_health`
  - `maneuver_budget_health`
  - `anomaly_notes`

So the repository can now connect:
**resonance / magnetic concepts -> satellite payload readiness -> orbital health -> manufacturing and process handoff**.

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
