# examples

> **English.** Korean (정본): [README.md](README.md)

## full_scenario.py

From the repository root:

```bash
python3 examples/full_scenario.py
```

Calls `analyze()` with Larmor, magnetic confinement, thermal proxy, Earth–L1–Moon gate topology, plasma transport, toroidal geometry, RF link, and Lagrange L1 in one shot, printing rolled-up **Ω, ATHENA stage, and verdict**.

## space_gate_datacenter_demo.py

From the repository root:

```bash
python3 examples/space_gate_datacenter_demo.py
```

This demo treats the space gate itself as an enclosed data-center-like structure and screens:

- internal air convection
- magnetic resonance auxiliary transport
- external radiator rejection

as separate layers instead of mixing them into one thermal formula.

For the conceptual frame, see [CONCEPT_EN.md](../CONCEPT_EN.md) (or the Korean [CONCEPT.md](../CONCEPT.md)).
