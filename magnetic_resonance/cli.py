"""
Magnetic Resonance Foundation CLI  v0.5.0
==========================================

Usage (Gate path):
  mag-resonance larmor --field 3.0 --nucleus 1H
  mag-resonance confine --bmax 6 --bmin 1 --temp 100
  mag-resonance topology --preset earth-l1-moon --json
  mag-resonance plasma --temp 1000 --density 1e20 --bfield 5
  mag-resonance toroidal --major 6.2 --minor 2.0 --bt 5.3 --ip 15
  mag-resonance rflink --freq 1.28e8 --dist 3.84e8 --power 1e4 --dish 30
  mag-resonance lagrange --point L1

Usage (MRI path):
  mag-resonance mri --b0 3.0 --json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict

from . import __version__
from .contracts import (
    BlochInput,
    ConfinementInput,
    ConfinementMode,
    GradientInput,
    LagrangeInput,
    LagrangePoint,
    LarmorInput,
    MagneticThermalInput,
    PlasmaTransportInput,
    RFPulseInput,
    RFTransferInput,
    SARInput,
    SNRInput,
    TissueParams,
    ToroidalInput,
)
from .foundation import analyze
from .gate_topology import preset_earth_l1_moon, preset_earth_moon_relay, preset_leo_ring
from .mri_screening import screen_mri


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="mag-resonance", description="Magnetic Resonance Foundation CLI")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd")

    # ── larmor ──
    lp = sub.add_parser("larmor", help="Larmor frequency calculation")
    lp.add_argument("--field", type=float, default=3.0, help="B₀ (Tesla)")
    lp.add_argument("--nucleus", default="1H")
    lp.add_argument("--json", action="store_true")

    # ── confine ──
    cp = sub.add_parser("confine", help="Magnetic confinement screening")
    cp.add_argument("--bmax", type=float, required=True, help="B_max (T)")
    cp.add_argument("--bmin", type=float, required=True, help="B_min (T)")
    cp.add_argument("--temp", type=float, default=10.0, help="plasma temp (eV)")
    cp.add_argument("--density", type=float, default=1e18, help="plasma density (m⁻³)")
    cp.add_argument("--length", type=float, default=10.0, help="confinement length (m)")
    cp.add_argument("--json", action="store_true")

    # ── topology ──
    tp = sub.add_parser("topology", help="Gate network topology")
    tp.add_argument("--preset", choices=["leo-ring", "earth-l1-moon", "earth-moon-relay"], required=True)
    tp.add_argument("--field", type=float, default=3.0, help="B₀ (T)")
    tp.add_argument("--json", action="store_true")

    # ── plasma (Phase B) ──
    pp = sub.add_parser("plasma", help="Plasma transport coefficients")
    pp.add_argument("--temp", type=float, default=100.0, help="electron temp (eV)")
    pp.add_argument("--density", type=float, default=1e19, help="electron density (m⁻³)")
    pp.add_argument("--z", type=int, default=1, help="ion charge Z")
    pp.add_argument("--bfield", type=float, default=1.0, help="B field (T)")
    pp.add_argument("--json", action="store_true")

    # ── toroidal (Phase C) ──
    trp = sub.add_parser("toroidal", help="Tokamak/stellarator geometry")
    trp.add_argument("--major", type=float, default=6.2, help="R₀ (m)")
    trp.add_argument("--minor", type=float, default=2.0, help="a (m)")
    trp.add_argument("--bt", type=float, default=5.3, help="toroidal B (T)")
    trp.add_argument("--ip", type=float, default=15.0, help="plasma current (MA)")
    trp.add_argument("--density", type=float, default=1e20, help="n_e (m⁻³)")
    trp.add_argument("--temp", type=float, default=1000.0, help="T_e (eV)")
    trp.add_argument("--json", action="store_true")

    # ── rflink (Phase D) ──
    rp = sub.add_parser("rflink", help="RF energy transfer link budget")
    rp.add_argument("--freq", type=float, required=True, help="frequency (Hz)")
    rp.add_argument("--dist", type=float, required=True, help="distance (m)")
    rp.add_argument("--power", type=float, default=1e3, help="transmit power (W)")
    rp.add_argument("--dish", type=float, default=10.0, help="antenna diameter (m)")
    rp.add_argument("--json", action="store_true")

    # ── lagrange (Phase E) ──
    lgp = sub.add_parser("lagrange", help="Lagrange point stability")
    lgp.add_argument("--point", choices=["L1", "L2", "L3", "L4", "L5"], default="L1")
    lgp.add_argument("--dv-budget", type=float, default=50.0, help="annual ΔV budget (m/s)")
    lgp.add_argument("--json", action="store_true")

    # ── mri (MRI path) ──
    mp = sub.add_parser("mri", help="MRI full screening (gradient + RF + Bloch + SNR + SAR)")
    mp.add_argument("--b0", type=float, default=3.0, help="B₀ field (T)")
    mp.add_argument("--json", action="store_true")

    args = p.parse_args(argv)

    if args.cmd == "larmor":
        report = analyze(larmor_input=LarmorInput(nucleus=args.nucleus, field_strength_t=args.field))
        if args.json:
            print(json.dumps(asdict(report.larmor), default=str, indent=2))
        else:
            lr = report.larmor
            print(f"=== Larmor: {lr.nucleus} @ {lr.field_strength_t} T ===")
            print(f"  ω₀        : {lr.omega_rad_per_s:.4e} rad/s")
            print(f"  f₀        : {lr.frequency_mhz} MHz")
            print(f"  λ         : {lr.wavelength_m} m")
            print(f"  E_photon  : {lr.photon_energy_ev:.4e} eV")

    elif args.cmd == "confine":
        ci = ConfinementInput(
            mode=ConfinementMode.MAGNETIC_BOTTLE,
            b_max_t=args.bmax, b_min_t=args.bmin,
            plasma_temp_ev=args.temp, plasma_density_m3=args.density,
            confinement_length_m=args.length,
        )
        report = analyze(confinement_input=ci)
        if args.json:
            print(json.dumps(asdict(report.confinement), default=str, indent=2))
        else:
            cr = report.confinement
            print(f"=== Confinement: {cr.mode.value} ===")
            print(f"  Mirror ratio : {cr.mirror_ratio}")
            print(f"  Loss cone    : {cr.loss_cone_deg}°")
            print(f"  Gyro radius  : {cr.gyro_radius_m:.4e} m")
            print(f"  β            : {cr.plasma_beta}")
            print(f"  τ_proxy      : {cr.confinement_time_proxy_s:.4e} s")
            print(f"  Ω_confine    : {cr.omega_confinement}")
            for a in cr.advisories:
                print(f"    ! {a}")

    elif args.cmd == "topology":
        if args.preset == "leo-ring":
            nodes = preset_leo_ring(field_t=args.field)
        elif args.preset == "earth-l1-moon":
            nodes = preset_earth_l1_moon(field_t=args.field)
        else:
            nodes = preset_earth_moon_relay(field_t=args.field)
        report = analyze(gate_nodes=nodes)
        topo = report.topology
        if args.json:
            d = {
                "nodes": len(topo.nodes), "pairs": topo.total_pairs,
                "locked": topo.fully_locked_pairs, "avg_coupling": topo.avg_coupling,
                "omega_topology": topo.omega_topology, "verdict": topo.verdict.value,
            }
            print(json.dumps(d, indent=2))
        else:
            print(f"=== Topology: {args.preset} ({len(topo.nodes)} gates) ===")
            print(f"  Pairs      : {topo.total_pairs}")
            print(f"  Locked     : {topo.fully_locked_pairs}")
            print(f"  Avg couple : {topo.avg_coupling}")
            print(f"  Ω_topology : {topo.omega_topology}  [{topo.verdict.value}]")
            for pr in topo.pairs:
                print(f"    {pr.gate_a_id} <-> {pr.gate_b_id}: {pr.match_state.value}  eff={pr.coupling_efficiency}  Δf={pr.detuning_hz} Hz  d={pr.distance_km} km")

    elif args.cmd == "plasma":
        pi = PlasmaTransportInput(
            electron_temp_ev=args.temp, electron_density_m3=args.density,
            ion_charge_z=args.z, b_field_t=args.bfield,
        )
        report = analyze(plasma_transport_input=pi)
        pt = report.plasma_transport
        if args.json:
            print(json.dumps(asdict(pt), default=str, indent=2))
        else:
            print(f"=== Plasma Transport ===")
            print(f"  ln Λ       : {pt.coulomb_log}")
            print(f"  ν_ei       : {pt.collision_freq_hz:.4e} Hz")
            print(f"  η_Spitzer  : {pt.spitzer_resistivity_ohm_m:.4e} Ω·m")
            print(f"  λ_mfp      : {pt.mean_free_path_m:.4e} m")
            print(f"  κ_∥        : {pt.thermal_conductivity_parallel:.4e}")
            print(f"  κ_⊥        : {pt.thermal_conductivity_perp:.4e}")
            print(f"  Ω_transport: {pt.omega_transport}")
            for a in pt.advisories:
                print(f"    ! {a}")

    elif args.cmd == "toroidal":
        ti = ToroidalInput(
            major_radius_m=args.major, minor_radius_m=args.minor,
            toroidal_field_t=args.bt, plasma_current_ma=args.ip,
            electron_density_m3=args.density, electron_temp_ev=args.temp,
        )
        report = analyze(toroidal_input=ti)
        tr = report.toroidal
        if args.json:
            print(json.dumps(asdict(tr), default=str, indent=2))
        else:
            print(f"=== Toroidal: {tr.device_type.value} ===")
            print(f"  A (R/a)    : {tr.aspect_ratio}")
            print(f"  q          : {tr.safety_factor_q}")
            print(f"  K-S ok     : {tr.kruskal_shafranov_ok}")
            print(f"  Volume     : {tr.plasma_volume_m3:.1f} m³")
            print(f"  n_G        : {tr.greenwald_density_limit_m3:.2e} m⁻³")
            print(f"  n/n_G      : {tr.greenwald_fraction}")
            print(f"  ι          : {tr.rotational_transform}")
            print(f"  Ω_geometry : {tr.omega_geometry}")
            for a in tr.advisories:
                print(f"    ! {a}")

    elif args.cmd == "rflink":
        ri = RFTransferInput(
            frequency_hz=args.freq, transmit_power_w=args.power,
            distance_m=args.dist, antenna_diameter_m=args.dish,
        )
        report = analyze(rf_input=ri)
        rf = report.rf_link
        if args.json:
            print(json.dumps(asdict(rf), default=str, indent=2))
        else:
            print(f"=== RF Link Budget ===")
            print(f"  λ          : {rf.wavelength_m} m")
            print(f"  FSPL       : {rf.fspl_db} dB")
            print(f"  Gain       : {rf.antenna_gain_dbi} dBi")
            print(f"  θ_beam     : {math.degrees(rf.beam_divergence_rad):.4f}°")
            print(f"  P_rx       : {rf.received_power_dbm} dBm")
            print(f"  Margin     : {rf.link_margin_db} dB")
            print(f"  Ω_link     : {rf.omega_link}")
            for a in rf.advisories:
                print(f"    ! {a}")

    elif args.cmd == "lagrange":
        li = LagrangeInput(
            point=LagrangePoint(args.point),
            station_keeping_dv_budget_m_s=args.dv_budget,
        )
        report = analyze(lagrange_input=li)
        lg = report.lagrange
        if args.json:
            print(json.dumps(asdict(lg), default=str, indent=2))
        else:
            print(f"=== Lagrange {lg.point.value} (Earth–Moon) ===")
            print(f"  d(M₁)     : {lg.distance_from_primary_m:.0f} m  ({lg.distance_from_primary_m / 1e6:.0f} km)")
            print(f"  d(M₂)     : {lg.distance_from_secondary_m:.0f} m")
            print(f"  μ          : {lg.mass_ratio}")
            print(f"  Hill sphere: {lg.hill_sphere_m:.0f} m  ({lg.hill_sphere_m / 1e6:.0f} km)")
            print(f"  Stability  : {lg.stability_class.value}")
            if lg.instability_time_s is not None:
                print(f"  τ_unstable : {lg.instability_time_s / 86400:.1f} days")
            print(f"  ΔV/year    : {lg.annual_dv_estimate_m_s} m/s  (budget ok: {lg.dv_budget_ok})")
            print(f"  Ω_lagrange : {lg.omega_lagrange}")
            for a in lg.advisories:
                print(f"    ! {a}")
    elif args.cmd == "mri":
        b0 = args.b0
        report = screen_mri(
            larmor_input=LarmorInput(field_strength_t=b0),
            gradient_input=GradientInput(b0_field_t=b0),
            rf_pulse_input=RFPulseInput(b0_field_t=b0),
            bloch_input=BlochInput(),
            snr_input=SNRInput(b0_field_t=b0),
            sar_input=SARInput(b0_field_t=b0),
        )
        if args.json:
            from dataclasses import asdict as _asdict
            d = {
                "omega_mri": report.omega_mri,
                "verdict": report.verdict.value,
                "evidence_tags": report.evidence_tags,
            }
            if report.larmor:
                d["larmor_mhz"] = report.larmor.frequency_mhz
            if report.gradient:
                d["resolution_mm"] = report.gradient.spatial_resolution_mm
                d["omega_gradient"] = report.gradient.omega_gradient
            if report.rf_pulse:
                d["pulse_ms"] = report.rf_pulse.pulse_duration_ms
                d["omega_rf_pulse"] = report.rf_pulse.omega_rf_pulse
            if report.bloch:
                d["signal_intensity"] = report.bloch.signal_intensity
                d["omega_signal"] = report.bloch.omega_signal
            if report.snr:
                d["snr_parallel"] = report.snr.snr_with_parallel
                d["omega_snr"] = report.snr.omega_snr
            if report.sar:
                d["sar_w_per_kg"] = report.sar.whole_body_sar_w_per_kg
                d["sar_ok"] = report.sar.sar_ok
                d["omega_safety"] = report.sar.omega_safety
            print(json.dumps(d, indent=2))
        else:
            print(f"=== MRI Screening @ {b0} T ===")
            if report.larmor:
                print(f"  f₀         : {report.larmor.frequency_mhz} MHz")
            if report.gradient:
                g = report.gradient
                print(f"  Resolution : {g.spatial_resolution_mm} mm  Ω_grad={g.omega_gradient}")
            if report.rf_pulse:
                rf = report.rf_pulse
                print(f"  Pulse      : {rf.pulse_duration_ms:.2f} ms  B₁={rf.b1_peak_ut:.1f} μT  Ω_rf={rf.omega_rf_pulse}")
            if report.bloch:
                bl = report.bloch
                print(f"  Signal     : SI={bl.signal_intensity:.4f}  Ernst={bl.ernst_angle_deg}°  Ω_sig={bl.omega_signal}")
            if report.snr:
                sn = report.snr
                print(f"  SNR        : {sn.snr_with_parallel:.1f} (par)  Ω_snr={sn.omega_snr}")
            if report.sar:
                sa = report.sar
                print(f"  SAR        : {sa.whole_body_sar_w_per_kg:.2f} W/kg  ok={sa.sar_ok}  Ω_safe={sa.omega_safety}")
            print(f"  ────────────")
            print(f"  Ω_mri      : {report.omega_mri}  [{report.verdict.value}]")
            for a in report.advisories:
                print(f"    ! {a}")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
