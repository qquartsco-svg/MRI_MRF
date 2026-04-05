# Magnetic Resonance Foundation (gate_MRI)

> **English.** Korean (정본): [README.md](README.md)

| Item | Details |
|------|---------|
| Version | `v0.4.0` |
| Tests | `92 passed` |
| Deps | Runtime: stdlib only · Test: `pytest>=8.0` (optional) |
| License | MIT |
| Package | `magnetic-resonance-foundation` |
| Python | `>=3.10` |

---

## 1. What Is This Project

**Magnetic Resonance Foundation** starts from a single physics equation `ω₀ = γ · B₀` and builds two independent layer stacks: **real-world MRI equipment design** and **space gate concept design** — a unified magnetic resonance screening engine.

The core question:

> "Starting from the same magnetic resonance physics, how far apart are medical MRI and a space gate?"

This engine **measures that distance**. Layers grounded in established physics score higher; conceptual/experimental layers are weighted conservatively. The final output is `Ω_overall` (0–1 screening score), `athena_stage` (interpretive language), and `verdict` (readiness).

---

## 2. Core Concept: One Physics, Two Paths

### 2.1 Shared Foundation — Larmor Resonance

Everything starts from the **Larmor equation**:

```
ω₀ = γ · B₀
```

- `γ` = gyromagnetic ratio (nucleus-dependent; e.g. ¹H = 2.6752×10⁸ rad/(s·T))
- `B₀` = external magnetic field strength (T)
- `ω₀` = resonance angular frequency (rad/s)

In MRI this says **"hydrogen atoms resonate at 127.73 MHz in a 3T magnet."** In the Gate path it says **"two nodes with identical B₀ are frequency-locked."** Same physics, different context.

### 2.2 Two-Path Architecture

```text
                        ω₀ = γ · B₀
                     (shared base: larmor.py)
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
                └────────────┬────────────┘
                             │
                    foundation.analyze()
                  Ω_overall · ATHENA · verdict
```

**Every layer is fully independent**:
- `screen_gradient()` can run standalone
- `screen_mri()` bundles the MRI path only
- `analyze()` can run MRI + Gate simultaneously
- Layers with no input are automatically skipped

---

## 3. MRI Path — Real-World Design

The MRI path screens **core parameters of actual medical/research MRI equipment**.

### 3.1 Gradient System (`gradient_system.py`)

**Concept**: Gradient coils that determine *where* in space to excite.

```
Δω(x) = γ · G · x
```

The resonance frequency at position `x` shifts linearly with gradient `G`. This determines the "where" in MRI.

**Screening items**: Spatial resolution (mm), pixel bandwidth (Hz/pixel), rise time (ms), minimum encoding time (ms), duty cycle limit.

### 3.2 RF Pulse Design (`rf_pulse.py`)

**Concept**: Electromagnetic pulses that tip atomic spins to a desired angle.

```
B₁ = α / (γ · T_pulse)
```

**Screening items**: Pulse duration, excitation bandwidth, B₁ peak/RMS (μT), pulse energy proxy. Supports hard/sinc/gaussian types.

### 3.3 Bloch Signal Model (`bloch_signal.py`)

**Concept**: How MR signal is generated and decays in tissue.

```
M_z(t) = M₀ · (1 − e^{−t/T₁})       ← longitudinal recovery
M_xy(t) = M₀ · e^{−t/T₂}             ← transverse decay
α_Ernst = arccos(e^{−TR/T₁})          ← optimal flip angle
```

**Screening items**: T₁/T₂-based signal intensity, Ernst angle, spin echo / gradient echo modes, T₁/T₂ weighting.

### 3.4 SNR Model (`snr_model.py`)

**Concept**: Signal-to-noise ratio — the fundamental image quality metric.

```
SNR ∝ B₀ · V_voxel · SI / √(BW · T)
```

**Screening items**: Voxel-based SNR₀, averaging effect (×√N_avg), parallel coil effect (×√N_ch), diagnostic threshold warnings.

### 3.5 SAR Safety (`sar_safety.py`)

**Concept**: Patient safety limits for RF energy absorption (IEC 60601-2-33).

```
Whole-body SAR ∝ f₀² · B₁² · duty_cycle / body_mass
dB/dt ≤ 20 T/s (peripheral nerve stimulation threshold)
```

**Screening items**: SAR (W/kg) vs IEC limits (Normal: 2, First level: 4), dB/dt (T/s), SAR fraction, mode switching.

### 3.6 MRI Orchestrator (`mri_screening.py`)

Runs all five layers in sequence and produces an `MRIScreeningReport`.

---

## 4. Gate Path — Space Extension

The Gate path layers **experimental gate-network topology** on top of **established plasma/RF/orbital physics**.

### 4.1 Established Physics

| Module | Physics | Description |
|--------|---------|-------------|
| `magnetic_confinement.py` | R = B_max/B_min | Mirror/bottle/toroidal confinement |
| `thermal_transport.py` | v_th = √(2kT/m) | Magnetically guided heat capacity proxy |
| `plasma_transport.py` | Spitzer η, Coulomb ln Λ | Collisions, anisotropic κ_∥/κ_⊥ |
| `toroidal_geometry.py` | A = R₀/a, safety factor q | Tokamak/stellarator geometry |
| `rf_energy_transfer.py` | Friis P_r = P_t·G²/FSPL | Long-range RF link budget |
| `lagrange_stability.py` | L1 ≈ R·(μ/3)^(1/3) | L1–L5 stability & station-keeping |

### 4.2 Experimental Upper Layer

| Module | Nature | Description |
|--------|--------|-------------|
| `gate_topology.py` | **conceptual** | Resonance-node network, coupling efficiency |
| `gate_resonance.py` | mixed | Long-range detuning + coupling proxy |

This layer does **not** claim to have built a gate. It asks **how far the concept can sit from lower-layer physics without contradiction**.

---

## 5. Unified — `foundation.analyze()`

```python
from magnetic_resonance import analyze, LarmorInput, GradientInput, ...

report = analyze(
    larmor_input=LarmorInput(),
    gradient_input=GradientInput(),
    sar_input=SARInput(),
    plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
    lagrange_input=LagrangeInput(point=LagrangePoint.L1),
)
print(report.mri.omega_mri)
print(report.omega_overall, report.athena_stage.value, report.verdict.value)
```

### 5.1 Judgment System

| Metric | Meaning | Values |
|--------|---------|--------|
| `omega_overall` | Overall screening score | 0.0 – 1.0 |
| `athena_stage` | Interpretive language | positive / neutral / cautious / negative |
| `athena_confidence` | Interpretation confidence | 0.0 – 1.0 |
| `verdict` | Readiness | production_ready / pilot_ready / prototype_ready / not_ready |

**ATHENA conservatism**: When conceptual layers (gate_topology, etc.) dominate, `athena_stage` shifts toward cautious/negative. Analyses composed entirely of established physics receive a more positive interpretation at the same score.

---

## 6. Extensibility

### 6.1 MRI Path Extensions

| Next Step | Description | Difficulty |
|-----------|-------------|------------|
| k-space reconstruction | FFT-based image reconstruction simulation | Medium |
| Multi-echo / EPI | Fast sequence design | Medium |
| Imaging artifacts | Chemical shift, susceptibility, wrapping | Medium |
| Coil design | Birdcage/surface coil sensitivity patterns | High |
| fMRI BOLD | Functional MRI hemodynamic response | High |
| Measured data fitting | DICOM data comparison interface | High |

### 6.2 Gate Path Extensions

| Next Step | Description | Difficulty |
|-----------|-------------|------------|
| Superconducting magnet link | Real coil specifications | Medium |
| Orbit propagation + LoS | Line-of-sight availability | Medium |
| CRTBP refinement | Circular restricted three-body precision | High |
| Magnetic reconnection | Energy release modeling | High |
| Multi-body gate chain | Gate placement for 3+ body systems | High |

### 6.3 Sibling Engine Bridges

- **`FrequencyCore_Engine`** — resonance response functions
- **`Superconducting_Magnet_Stack`** — high-field coil design parameters
- **`Space_Thermal_Dynamics_Foundation`** — radiative vs magnetic heat transport comparison

If sibling engines are absent, bridges degrade to `None` and core runs independently.

---

## 7. Use Cases

### 7.1 MRI Research & Education

```bash
mag-resonance mri --b0 3.0
mag-resonance mri --b0 7.0 --json
```

- Parameter sensitivity simulation for MRI physics courses
- Initial spec screening for new MRI sequences
- Gradient / RF / SAR trade-off exploration

### 7.2 Space System Concept Design

```bash
mag-resonance lagrange --point L1 --json
mag-resonance rflink --freq 1.28e8 --dist 3.84e8 --power 1e4 --dish 30 --json
```

- Physical plausibility screening for space-gate concepts
- Plasma confinement / RF link / orbital placement trade-offs

### 7.3 Unified Analysis

```python
report = analyze(
    larmor_input=LarmorInput(),
    gradient_input=GradientInput(),
    sar_input=SARInput(),
    plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
    lagrange_input=LagrangeInput(point=LagrangePoint.L1),
)
```

---

## 8. Current Limitations

### 8.1 MRI Path

| Limitation | Description | Impact |
|------------|-------------|--------|
| **No k-space** | Frequency → image reconstruction not implemented | Cannot generate actual images |
| **No multi-echo** | No EPI, turbo SE, or fast sequences | Clinical sequence design limited |
| **No coil geometry** | Uniform coil assumption, no B₁ maps | SNR estimation is proxy-level |
| **Simple tissue model** | Single tissue, 3T white matter defaults | Multi-tissue contrast optimization unavailable |
| **SAR approximation** | IEC-based proxy, not EM simulation | Insufficient for regulatory design |
| **No artifacts** | Chemical shift, susceptibility not modeled | Image quality prediction limited |

### 8.2 Gate Path

| Limitation | Description | Impact |
|------------|-------------|--------|
| **Gate topology unproven** | Conceptual narrative, not established engineering | Not a device blueprint |
| **Simplified plasma** | Single ion species, steady-state assumption | Instabilities not captured |
| **Orbital approximation** | Two-body approximation, no perturbations | Precision orbits need GMAT/STK |
| **Thermal proxy** | Conceptual estimate, no validation data | Not usable for radiator design |
| **Idealized RF link** | Free space only, no atmospheric/plasma attenuation | Possible deviation from measurement |

### 8.3 Common

- **No measured data fitting**: Theoretical models only
- **Unit mixing**: Mostly SI, but mm/mT convenience units exist
- **Python 3.10+ required**

---

## 9. Security & Integrity

### 9.1 SHA-256 File Signatures

Every release is pinned with `SIGNATURE.sha256`.

```bash
python3 scripts/generate_signature.py     # Generate
python3 scripts/verify_signature.py       # Verify
python3 scripts/verify_package_identity.py  # Identity check
```

The signature records SHA-256 hashes of **all source files** to detect:
- Code tampering
- Document/code/test desynchronization
- Version drift

### 9.2 On-Chain Recording

This repository does not include on-chain smart contracts. `SIGNATURE.sha256` is an off-chain signature designed so hashes can be pinned to IPFS/Arweave if needed.

### 9.3 Security Considerations

| Item | Current State | Recommended Action |
|------|---------------|-------------------|
| Dependencies | stdlib only (runtime) | Minimal supply-chain attack surface |
| Input validation | Basic range checks | Add extreme-value fuzz testing |
| Medical safety | SAR/dB/dt warnings emitted | **Do NOT use for diagnosis/treatment** |
| Code signing | SHA-256 per file | Add GPG signing |
| Access control | Public repository | Mind sensitive parameter exposure |

> **Warning**: The MRI path is an educational/research screening tool. **Do NOT use it for medical device design or patient diagnosis.** SAR/dB/dt calculations are IEC-based proxies and do not replace regulatory-grade EM simulations.

---

## 10. Key Equations

### Shared

| Equation | Meaning |
|----------|---------|
| `ω₀ = γ · B₀` | Larmor resonance frequency |
| `f = ω₀ / 2π` | Frequency (Hz) |

### MRI-Specific

| Equation | Meaning |
|----------|---------|
| `Δω(x) = γ · G · x` | Gradient spatial encoding |
| `M_z(t) = M₀(1 − e^{−t/T₁})` | Longitudinal recovery |
| `M_xy(t) = M₀ · e^{−t/T₂}` | Transverse decay (SE) |
| `α_Ernst = arccos(e^{−TR/T₁})` | Ernst angle |
| `SNR ∝ B₀ · V · SI / √(BW·T)` | SNR proxy |
| `SAR ∝ f₀² · B₁² · duty / mass` | SAR proxy |

### Gate-Specific

| Equation | Meaning |
|----------|---------|
| `R = B_max / B_min` | Mirror ratio |
| `η ≈ 5.2×10⁻⁵ Z lnΛ / T_e^{3/2}` | Spitzer resistivity |
| `P_r = P_t · G_t · G_r / FSPL` | Friis received power |
| `r_L1 ≈ R · (μ/3)^{1/3}` | L1 approximation |

---

## 11. Quick Start

### Install

```bash
pip install -e "."          # Basic
pip install -e ".[dev]"     # With tests
```

### CLI

```bash
# MRI path
mag-resonance mri --b0 3.0
mag-resonance mri --b0 1.5 --json

# Gate path
mag-resonance larmor --field 3 --nucleus 1H --json
mag-resonance lagrange --point L1 --json

# Help
mag-resonance --help
```

---

## 12. Tests

```bash
python3 -m pytest tests/ -q
```

Current: **92 passed** (v0.4.0)

---

## 13. Version History

| Version | Changes |
|---------|---------|
| v0.1.0 | Larmor + Confinement + Thermal + Gate Topology |
| v0.2.0 | Plasma Transport + Toroidal + RF Link + Lagrange |
| v0.3.0 | ATHENA judgment, examples, CONCEPT_EN |
| **v0.4.0** | **MRI PATH: Gradient → RF Pulse → Bloch → SNR → SAR** |

---

## 14. License

MIT

---

## 15. Conclusion

**Magnetic Resonance Foundation v0.4.0 bridges two worlds from a single `ω₀ = γB₀`.**

The MRI path is grounded in real-world medical equipment screening — solid foundations. The Gate path stands on those foundations and measures how close a space-gate concept can sit to established physics. When the basics are solid, the next extension follows naturally. That is the design philosophy of this foundation.

Concept docs: [CONCEPT.md](CONCEPT.md) · [CONCEPT_EN.md](CONCEPT_EN.md)
