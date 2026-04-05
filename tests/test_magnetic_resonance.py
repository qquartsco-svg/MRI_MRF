"""Magnetic Resonance Foundation — comprehensive tests (v0.4.0)."""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import asdict

import pytest

_pkg = os.path.join(os.path.dirname(__file__), "..")
if _pkg not in sys.path:
    sys.path.insert(0, _pkg)

from magnetic_resonance.contracts import (
    ConfinementInput,
    ConfinementMode,
    GateNode,
    LagrangeInput,
    LagrangePoint,
    LarmorInput,
    MagneticThermalInput,
    PlasmaTransportInput,
    RFTransferInput,
    ToroidalInput,
    ToroidalType,
    GYROMAGNETIC_RATIOS,
    ResonanceMatchState,
    GateVerdict,
    LagrangeStabilityClass,
)
from magnetic_resonance.larmor import larmor_frequency, compare_nuclei
from magnetic_resonance.gate_resonance import analyze_gate_pair, analyze_gate_network
from magnetic_resonance.magnetic_confinement import screen_confinement
from magnetic_resonance.thermal_transport import screen_magnetic_thermal
from magnetic_resonance.plasma_transport import screen_plasma_transport, coulomb_logarithm
from magnetic_resonance.toroidal_geometry import screen_toroidal
from magnetic_resonance.rf_energy_transfer import screen_rf_link
from magnetic_resonance.lagrange_stability import screen_lagrange
from magnetic_resonance.gate_topology import (
    evaluate_topology,
    preset_leo_ring,
    preset_earth_l1_moon,
    preset_earth_moon_relay,
)
from magnetic_resonance.foundation import analyze


# ═══════════════════════════════════════════════════════
# 1. Larmor / NMR
# ═══════════════════════════════════════════════════════

class TestLarmor:
    def test_hydrogen_3t(self):
        r = larmor_frequency(LarmorInput(nucleus="1H", field_strength_t=3.0))
        assert 127 < r.frequency_mhz < 128

    def test_hydrogen_1_5t(self):
        r = larmor_frequency(LarmorInput(nucleus="1H", field_strength_t=1.5))
        assert 63 < r.frequency_mhz < 64

    def test_carbon_13(self):
        r = larmor_frequency(LarmorInput(nucleus="13C", field_strength_t=3.0))
        assert r.frequency_mhz < 40

    def test_electron_epr(self):
        r = larmor_frequency(LarmorInput(nucleus="e", field_strength_t=0.34))
        assert r.frequency_mhz > 9000

    def test_unknown_nucleus_raises(self):
        with pytest.raises(ValueError):
            larmor_frequency(LarmorInput(nucleus="X99"))

    def test_wavelength_positive(self):
        r = larmor_frequency(LarmorInput())
        assert r.wavelength_m > 0

    def test_photon_energy_positive(self):
        r = larmor_frequency(LarmorInput())
        assert r.photon_energy_ev > 0

    def test_compare_nuclei(self):
        results = compare_nuclei(3.0)
        assert len(results) == len(GYROMAGNETIC_RATIOS)
        assert all(r.frequency_hz > 0 for r in results)


# ═══════════════════════════════════════════════════════
# 2. Gate Resonance
# ═══════════════════════════════════════════════════════

class TestGateResonance:
    def test_identical_gates_locked(self):
        a = GateNode("A", (0, 0, 0), 3.0)
        b = GateNode("B", (100, 0, 0), 3.0)
        r = analyze_gate_pair(a, b)
        assert r.match_state == ResonanceMatchState.LOCKED
        assert r.coupling_efficiency > 0.9

    def test_detuned_gates(self):
        a = GateNode("A", (0, 0, 0), 3.0)
        b = GateNode("B", (100, 0, 0), 2.0)
        r = analyze_gate_pair(a, b)
        assert r.match_state in (ResonanceMatchState.DETUNED, ResonanceMatchState.DISCONNECTED)

    def test_distance_calculation(self):
        a = GateNode("A", (0, 0, 0), 3.0)
        b = GateNode("B", (3, 4, 0), 3.0)
        r = analyze_gate_pair(a, b)
        assert abs(r.distance_km - 5.0) < 0.01

    def test_network_pairs(self):
        nodes = [GateNode(f"N{i}", (i * 10, 0, 0), 3.0) for i in range(4)]
        pairs = analyze_gate_network(nodes)
        assert len(pairs) == 6


# ═══════════════════════════════════════════════════════
# 3. Magnetic Confinement
# ═══════════════════════════════════════════════════════

class TestConfinement:
    def test_basic_bottle(self):
        inp = ConfinementInput(mode=ConfinementMode.MAGNETIC_BOTTLE, b_max_t=6.0, b_min_t=1.0, plasma_temp_ev=10.0)
        r = screen_confinement(inp)
        assert r.mirror_ratio == 6.0
        assert r.omega_confinement > 0

    def test_high_mirror_ratio(self):
        inp = ConfinementInput(mode=ConfinementMode.MAGNETIC_MIRROR, b_max_t=20.0, b_min_t=1.0)
        r = screen_confinement(inp)
        assert r.omega_confinement > 0.3

    def test_low_ratio_advisory(self):
        inp = ConfinementInput(mode=ConfinementMode.MAGNETIC_MIRROR, b_max_t=1.5, b_min_t=1.0)
        r = screen_confinement(inp)
        assert any("Mirror ratio" in a for a in r.advisories)

    def test_high_beta_advisory(self):
        inp = ConfinementInput(mode=ConfinementMode.TOROIDAL, b_max_t=0.01, b_min_t=0.005,
                               plasma_temp_ev=1000.0, plasma_density_m3=1e22)
        r = screen_confinement(inp)
        assert any("β" in a for a in r.advisories)

    def test_zero_bmin_raises(self):
        with pytest.raises(ValueError):
            screen_confinement(ConfinementInput(mode=ConfinementMode.MAGNETIC_BOTTLE, b_max_t=5.0, b_min_t=0.0))


# ═══════════════════════════════════════════════════════
# 4. Thermal Transport
# ═══════════════════════════════════════════════════════

class TestThermalTransport:
    def test_basic_capacity(self):
        inp = MagneticThermalInput(heat_load_w=100.0, plasma_temp_ev=100.0, plasma_density_m3=1e20)
        r = screen_magnetic_thermal(inp)
        assert r.heat_capacity_w > 0

    def test_zero_density_fallback(self):
        inp = MagneticThermalInput(heat_load_w=100.0, plasma_density_m3=0.0)
        r = screen_magnetic_thermal(inp)
        assert r.path_mode.value == "radiative_only"

    def test_headroom_positive(self):
        inp = MagneticThermalInput(heat_load_w=1.0, plasma_temp_ev=1000.0,
                                   plasma_density_m3=1e22, loop_cross_section_m2=1.0)
        r = screen_magnetic_thermal(inp)
        assert r.headroom_w > 0


# ═══════════════════════════════════════════════════════
# 5. Gate Topology
# ═══════════════════════════════════════════════════════

class TestTopology:
    def test_leo_ring(self):
        nodes = preset_leo_ring(6, field_t=3.0)
        topo = evaluate_topology(nodes)
        assert topo.total_pairs == 15
        assert topo.fully_locked_pairs == 15

    def test_earth_l1_moon(self):
        topo = evaluate_topology(preset_earth_l1_moon())
        assert topo.total_pairs == 3

    def test_earth_moon_relay(self):
        topo = evaluate_topology(preset_earth_moon_relay(5))
        assert len(topo.nodes) == 5

    def test_single_node_empty(self):
        topo = evaluate_topology([GateNode("solo", (0, 0, 0), 3.0)])
        assert topo.verdict == GateVerdict.CONCEPTUAL

    def test_detuned_topology(self):
        nodes = [GateNode("A", (0, 0, 0), 3.0), GateNode("B", (100, 0, 0), 1.0)]
        topo = evaluate_topology(nodes)
        assert topo.fully_locked_pairs == 0


# ═══════════════════════════════════════════════════════
# 6. Plasma Transport (Phase B)
# ═══════════════════════════════════════════════════════

class TestPlasmaTransport:
    def test_coulomb_log_hot(self):
        ln_l = coulomb_logarithm(1e19, 1000.0)
        assert 10 < ln_l < 25

    def test_coulomb_log_cold(self):
        ln_l = coulomb_logarithm(1e19, 1.0)
        assert ln_l < 15

    def test_coulomb_log_edge_zero(self):
        assert coulomb_logarithm(0, 100) == 1.0
        assert coulomb_logarithm(1e19, 0) == 1.0

    def test_spitzer_decreases_with_temp(self):
        r1 = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=10.0))
        r2 = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=1000.0))
        assert r2.spitzer_resistivity_ohm_m < r1.spitzer_resistivity_ohm_m

    def test_mfp_increases_with_temp(self):
        r1 = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=10.0))
        r2 = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=1000.0))
        assert r2.mean_free_path_m > r1.mean_free_path_m

    def test_kappa_parallel_gt_perp(self):
        r = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=100.0, b_field_t=5.0))
        assert r.thermal_conductivity_parallel > r.thermal_conductivity_perp

    def test_omega_bounded(self):
        r = screen_plasma_transport(PlasmaTransportInput(electron_temp_ev=10000.0, electron_density_m3=1e18))
        assert 0 <= r.omega_transport <= 1


# ═══════════════════════════════════════════════════════
# 7. Toroidal Geometry (Phase C)
# ═══════════════════════════════════════════════════════

class TestToroidal:
    def test_iter_like(self):
        r = screen_toroidal(ToroidalInput(major_radius_m=6.2, minor_radius_m=2.0,
                                          toroidal_field_t=5.3, plasma_current_ma=15.0))
        assert 2.5 < r.aspect_ratio < 4.0
        assert r.kruskal_shafranov_ok

    def test_spherical_tokamak(self):
        r = screen_toroidal(ToroidalInput(major_radius_m=1.5, minor_radius_m=0.9,
                                          toroidal_field_t=2.0, plasma_current_ma=5.0))
        assert r.aspect_ratio < 2.0

    def test_greenwald_exceeded(self):
        r = screen_toroidal(ToroidalInput(electron_density_m3=1e22, plasma_current_ma=1.0))
        assert r.greenwald_fraction > 1.0
        assert any("Greenwald" in a for a in r.advisories)

    def test_low_q_advisory(self):
        r = screen_toroidal(ToroidalInput(toroidal_field_t=0.1, plasma_current_ma=50.0))
        assert any("q=" in a for a in r.advisories)

    def test_bad_radii_raises(self):
        with pytest.raises(ValueError):
            screen_toroidal(ToroidalInput(major_radius_m=1.0, minor_radius_m=2.0))

    def test_volume_positive(self):
        r = screen_toroidal(ToroidalInput())
        assert r.plasma_volume_m3 > 0

    def test_rotational_transform_positive(self):
        r = screen_toroidal(ToroidalInput())
        assert r.rotational_transform > 0


# ═══════════════════════════════════════════════════════
# 8. RF Energy Transfer (Phase D)
# ═══════════════════════════════════════════════════════

class TestRFLink:
    def test_basic_link(self):
        r = screen_rf_link(RFTransferInput(frequency_hz=1e9, distance_m=1e6,
                                           transmit_power_w=1e3, antenna_diameter_m=10.0))
        assert r.fspl_db > 0
        assert r.antenna_gain_dbi > 0

    def test_lunar_distance(self):
        r = screen_rf_link(RFTransferInput(frequency_hz=1.28e8, distance_m=3.84e8,
                                           transmit_power_w=1e4, antenna_diameter_m=30.0))
        assert r.wavelength_m > 2.0
        assert r.fspl_db > 100

    def test_close_range_high_power(self):
        r = screen_rf_link(RFTransferInput(frequency_hz=10e9, distance_m=1000.0,
                                           transmit_power_w=1e6, antenna_diameter_m=5.0))
        assert r.link_margin_db > 50
        assert r.omega_link > 0.5

    def test_zero_freq_raises(self):
        with pytest.raises(ValueError):
            screen_rf_link(RFTransferInput(frequency_hz=0, distance_m=1e6))

    def test_zero_dist_raises(self):
        with pytest.raises(ValueError):
            screen_rf_link(RFTransferInput(frequency_hz=1e9, distance_m=0))

    def test_omega_bounded(self):
        r = screen_rf_link(RFTransferInput(frequency_hz=1e9, distance_m=1e3))
        assert 0 <= r.omega_link <= 1


# ═══════════════════════════════════════════════════════
# 9. Lagrange Stability (Phase E)
# ═══════════════════════════════════════════════════════

class TestLagrange:
    def test_l1_earth_moon(self):
        r = screen_lagrange(LagrangeInput(point=LagrangePoint.L1))
        assert r.stability_class == LagrangeStabilityClass.QUASI_STABLE
        assert r.distance_from_primary_m > 0
        assert r.instability_time_s is not None

    def test_l2(self):
        r = screen_lagrange(LagrangeInput(point=LagrangePoint.L2))
        assert r.distance_from_primary_m > r.distance_from_secondary_m

    def test_l4_stable(self):
        r = screen_lagrange(LagrangeInput(point=LagrangePoint.L4))
        assert r.stability_class == LagrangeStabilityClass.STABLE
        assert r.annual_dv_estimate_m_s == 0.0

    def test_l5_stable(self):
        r = screen_lagrange(LagrangeInput(point=LagrangePoint.L5))
        assert r.stability_class == LagrangeStabilityClass.STABLE

    def test_l4_unstable_equal_mass(self):
        r = screen_lagrange(LagrangeInput(point=LagrangePoint.L4,
                                          primary_mass_kg=1e24, secondary_mass_kg=1e24))
        assert r.stability_class == LagrangeStabilityClass.UNSTABLE

    def test_dv_budget_exceeded(self):
        r = screen_lagrange(LagrangeInput(point=LagrangePoint.L1,
                                          station_keeping_dv_budget_m_s=1.0))
        assert not r.dv_budget_ok
        assert any("ΔV" in a for a in r.advisories)

    def test_hill_sphere_positive(self):
        r = screen_lagrange(LagrangeInput())
        assert r.hill_sphere_m > 0

    def test_mass_ratio(self):
        r = screen_lagrange(LagrangeInput())
        assert 0 < r.mass_ratio < 0.5

    def test_zero_mass_raises(self):
        with pytest.raises(ValueError):
            screen_lagrange(LagrangeInput(primary_mass_kg=0))


# ═══════════════════════════════════════════════════════
# 10. Foundation (Integration)
# ═══════════════════════════════════════════════════════

class TestFoundation:
    def test_larmor_only(self):
        r = analyze(larmor_input=LarmorInput())
        assert r.larmor is not None
        assert r.confinement is None

    def test_full_pipeline_original(self):
        r = analyze(
            larmor_input=LarmorInput(),
            confinement_input=ConfinementInput(mode=ConfinementMode.MAGNETIC_BOTTLE, b_max_t=6.0, b_min_t=1.0),
            thermal_input=MagneticThermalInput(heat_load_w=100.0),
            gate_nodes=preset_leo_ring(4),
        )
        assert r.larmor is not None
        assert r.confinement is not None
        assert r.thermal_transport is not None
        assert r.topology is not None
        assert 0 <= r.omega_overall <= 1

    def test_full_pipeline_expanded(self):
        r = analyze(
            larmor_input=LarmorInput(),
            plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
            toroidal_input=ToroidalInput(),
            rf_input=RFTransferInput(frequency_hz=1.28e8, distance_m=3.84e8),
            lagrange_input=LagrangeInput(point=LagrangePoint.L1),
        )
        assert r.plasma_transport is not None
        assert r.toroidal is not None
        assert r.rf_link is not None
        assert r.lagrange is not None
        assert len(r.evidence_tags) >= 4

    def test_json_serialisable(self):
        r = analyze(
            larmor_input=LarmorInput(),
            gate_nodes=preset_earth_l1_moon(),
            lagrange_input=LagrangeInput(),
        )
        j = json.dumps(asdict(r), default=str)
        assert len(j) > 200

    def test_athena_stage_present(self):
        r = analyze(
            larmor_input=LarmorInput(),
            plasma_transport_input=PlasmaTransportInput(electron_temp_ev=1000.0),
            rf_input=RFTransferInput(frequency_hz=1.28e8, distance_m=3.84e8),
        )
        assert r.athena_stage.value in {"positive", "neutral", "cautious", "negative"}
        assert 0 <= r.athena_confidence <= 1

    def test_conceptual_topology_penalised(self):
        base = analyze(larmor_input=LarmorInput(), rf_input=RFTransferInput(frequency_hz=1e9, distance_m=1e6))
        topo = analyze(
            larmor_input=LarmorInput(),
            rf_input=RFTransferInput(frequency_hz=1e9, distance_m=1e6),
            gate_nodes=preset_earth_l1_moon(),
        )
        assert topo.athena_confidence <= base.athena_confidence


# ═══════════════════════════════════════════════════════
# 11. CLI
# ═══════════════════════════════════════════════════════

class TestCLI:
    _CWD = os.path.join(os.path.dirname(__file__), "..")

    def test_larmor_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "magnetic_resonance.cli", "larmor", "--field", "3", "--json"],
            capture_output=True, text=True, cwd=self._CWD,
        )
        assert result.returncode == 0
        assert "frequency_mhz" in json.loads(result.stdout)

    def test_topology_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "magnetic_resonance.cli", "topology", "--preset", "earth-l1-moon", "--json"],
            capture_output=True, text=True, cwd=self._CWD,
        )
        assert result.returncode == 0
        assert "omega_topology" in json.loads(result.stdout)

    def test_plasma_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "magnetic_resonance.cli", "plasma", "--temp", "1000", "--json"],
            capture_output=True, text=True, cwd=self._CWD,
        )
        assert result.returncode == 0
        assert "coulomb_log" in json.loads(result.stdout)

    def test_toroidal_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "magnetic_resonance.cli", "toroidal", "--json"],
            capture_output=True, text=True, cwd=self._CWD,
        )
        assert result.returncode == 0
        assert "aspect_ratio" in json.loads(result.stdout)

    def test_rflink_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "magnetic_resonance.cli", "rflink",
             "--freq", "1e9", "--dist", "1e6", "--json"],
            capture_output=True, text=True, cwd=self._CWD,
        )
        assert result.returncode == 0
        assert "fspl_db" in json.loads(result.stdout)

    def test_lagrange_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "magnetic_resonance.cli", "lagrange", "--point", "L1", "--json"],
            capture_output=True, text=True, cwd=self._CWD,
        )
        assert result.returncode == 0
        assert "omega_lagrange" in json.loads(result.stdout)


# ═══════════════════════════════════════════════════════
# 12. Example script
# ═══════════════════════════════════════════════════════

class TestExamples:
    _ROOT = os.path.join(os.path.dirname(__file__), "..")

    def test_full_scenario_runs(self):
        result = subprocess.run(
            [sys.executable, "examples/full_scenario.py"],
            cwd=self._ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "omega_overall" in result.stdout
        assert "athena_stage" in result.stdout


# ═══════════════════════════════════════════════════════
# 13. Integrity
# ═══════════════════════════════════════════════════════

class TestIntegrity:
    REQUIRED = [
        "magnetic_resonance/__init__.py",
        "magnetic_resonance/contracts.py",
        "magnetic_resonance/larmor.py",
        "magnetic_resonance/gate_resonance.py",
        "magnetic_resonance/magnetic_confinement.py",
        "magnetic_resonance/thermal_transport.py",
        "magnetic_resonance/gate_topology.py",
        "magnetic_resonance/plasma_transport.py",
        "magnetic_resonance/toroidal_geometry.py",
        "magnetic_resonance/rf_energy_transfer.py",
        "magnetic_resonance/lagrange_stability.py",
        "magnetic_resonance/foundation.py",
        "magnetic_resonance/ecosystem_bridges.py",
        "magnetic_resonance/athena_stage.py",
        "magnetic_resonance/cli.py",
        "magnetic_resonance/gradient_system.py",
        "magnetic_resonance/rf_pulse.py",
        "magnetic_resonance/bloch_signal.py",
        "magnetic_resonance/snr_model.py",
        "magnetic_resonance/sar_safety.py",
        "magnetic_resonance/mri_screening.py",
        "VERSION",
        "pyproject.toml",
        "BLOCKCHAIN_INFO.md",
        "BLOCKCHAIN_INFO_EN.md",
        "scripts/verify_package_identity.py",
        "scripts/cleanup_generated.py",
        "scripts/release_check.py",
        "CONCEPT_EN.md",
        "examples/full_scenario.py",
        "examples/README.md",
        "examples/README_EN.md",
    ]

    def test_files_exist(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        for f in self.REQUIRED:
            assert os.path.isfile(os.path.join(root, f)), f"Missing: {f}"


# ═══════════════════════════════════════════════════════
# 14. MRI Layer — Gradient System
# ═══════════════════════════════════════════════════════

class TestGradientSystem:
    def test_default_3t(self):
        from magnetic_resonance.gradient_system import screen_gradient
        from magnetic_resonance.contracts import GradientInput
        r = screen_gradient(GradientInput())
        assert 0 < r.spatial_resolution_mm <= 5
        assert r.pixel_bandwidth_hz > 0
        assert r.rise_time_ms > 0
        assert 0 <= r.omega_gradient <= 1

    def test_high_performance(self):
        from magnetic_resonance.gradient_system import screen_gradient
        from magnetic_resonance.contracts import GradientInput
        r = screen_gradient(GradientInput(max_amplitude_mt_per_m=80, max_slew_rate_t_per_m_per_s=200, matrix_size=512))
        assert r.spatial_resolution_mm < 1.0
        assert r.omega_gradient > 0.5

    def test_low_gradient(self):
        from magnetic_resonance.gradient_system import screen_gradient
        from magnetic_resonance.contracts import GradientInput
        r = screen_gradient(GradientInput(max_amplitude_mt_per_m=10))
        assert any("low" in a.lower() for a in r.advisories)


# ═══════════════════════════════════════════════════════
# 15. MRI Layer — RF Pulse
# ═══════════════════════════════════════════════════════

class TestRFPulse:
    def test_sinc_default(self):
        from magnetic_resonance.rf_pulse import screen_rf_pulse
        from magnetic_resonance.contracts import RFPulseInput
        r = screen_rf_pulse(RFPulseInput())
        assert r.pulse_duration_ms > 0
        assert r.bandwidth_hz > 0
        assert r.b1_peak_ut > 0
        assert 0 <= r.omega_rf_pulse <= 1

    def test_hard_pulse(self):
        from magnetic_resonance.rf_pulse import screen_rf_pulse
        from magnetic_resonance.contracts import RFPulseInput, RFPulseType
        r = screen_rf_pulse(RFPulseInput(pulse_type=RFPulseType.HARD))
        assert r.pulse_duration_ms > 0

    def test_gaussian_pulse(self):
        from magnetic_resonance.rf_pulse import screen_rf_pulse
        from magnetic_resonance.contracts import RFPulseInput, RFPulseType
        r = screen_rf_pulse(RFPulseInput(pulse_type=RFPulseType.GAUSSIAN))
        assert r.b1_rms_ut > 0


# ═══════════════════════════════════════════════════════
# 16. MRI Layer — Bloch Signal
# ═══════════════════════════════════════════════════════

class TestBlochSignal:
    def test_spin_echo_default(self):
        from magnetic_resonance.bloch_signal import screen_bloch_signal
        from magnetic_resonance.contracts import BlochInput
        r = screen_bloch_signal(BlochInput())
        assert 0 < r.mz_recovery <= 1
        assert 0 < r.mxy_at_te <= 1
        assert r.ernst_angle_deg > 0
        assert 0 <= r.omega_signal <= 1

    def test_gradient_echo(self):
        from magnetic_resonance.bloch_signal import screen_bloch_signal
        from magnetic_resonance.contracts import BlochInput, TissueParams
        r = screen_bloch_signal(BlochInput(
            sequence_type="gradient_echo",
            flip_angle_deg=20,
            tr_ms=50,
            te_ms=5,
        ))
        assert r.signal_intensity > 0

    def test_long_te_warning(self):
        from magnetic_resonance.bloch_signal import screen_bloch_signal
        from magnetic_resonance.contracts import BlochInput, TissueParams
        r = screen_bloch_signal(BlochInput(te_ms=200))
        assert len(r.advisories) > 0

    def test_ernst_angle(self):
        from magnetic_resonance.bloch_signal import screen_bloch_signal
        from magnetic_resonance.contracts import BlochInput
        r = screen_bloch_signal(BlochInput(tr_ms=500))
        assert 0 < r.ernst_angle_deg < 90


# ═══════════════════════════════════════════════════════
# 17. MRI Layer — SNR Model
# ═══════════════════════════════════════════════════════

class TestSNRModel:
    def test_default(self):
        from magnetic_resonance.snr_model import screen_snr
        from magnetic_resonance.contracts import SNRInput
        r = screen_snr(SNRInput())
        assert r.voxel_volume_mm3 == 5.0
        assert r.snr_0 >= 0
        assert r.snr_with_averages >= r.snr_0
        assert r.snr_with_parallel >= r.snr_with_averages
        assert 0 <= r.omega_snr <= 1

    def test_tiny_voxel(self):
        from magnetic_resonance.snr_model import screen_snr
        from magnetic_resonance.contracts import SNRInput
        r = screen_snr(SNRInput(voxel_size_mm3=(0.5, 0.5, 0.5)))
        assert any("small" in a.lower() for a in r.advisories)

    def test_averages_boost(self):
        from magnetic_resonance.snr_model import screen_snr
        from magnetic_resonance.contracts import SNRInput
        r1 = screen_snr(SNRInput(n_averages=1))
        r4 = screen_snr(SNRInput(n_averages=4))
        assert r4.snr_with_averages > r1.snr_with_averages


# ═══════════════════════════════════════════════════════
# 18. MRI Layer — SAR Safety
# ═══════════════════════════════════════════════════════

class TestSARSafety:
    def test_normal_mode_safe(self):
        from magnetic_resonance.sar_safety import screen_sar
        from magnetic_resonance.contracts import SARInput
        r = screen_sar(SARInput())
        assert r.sar_limit_w_per_kg == 2.0
        assert isinstance(r.sar_ok, bool)
        assert isinstance(r.db_dt_ok, bool)
        assert 0 <= r.omega_safety <= 1

    def test_first_level(self):
        from magnetic_resonance.sar_safety import screen_sar
        from magnetic_resonance.contracts import SARInput
        r = screen_sar(SARInput(mode="first_level"))
        assert r.sar_limit_w_per_kg == 4.0

    def test_db_dt(self):
        from magnetic_resonance.sar_safety import screen_sar
        from magnetic_resonance.contracts import SARInput
        r = screen_sar(SARInput())
        assert r.db_dt_t_per_s >= 0


# ═══════════════════════════════════════════════════════
# 19. MRI Screening Orchestrator
# ═══════════════════════════════════════════════════════

class TestMRIScreening:
    def test_full_screening(self):
        from magnetic_resonance.mri_screening import screen_mri
        from magnetic_resonance.contracts import (
            LarmorInput, GradientInput, RFPulseInput,
            BlochInput, SNRInput, SARInput,
        )
        r = screen_mri(
            larmor_input=LarmorInput(),
            gradient_input=GradientInput(),
            rf_pulse_input=RFPulseInput(),
            bloch_input=BlochInput(),
            snr_input=SNRInput(),
            sar_input=SARInput(),
        )
        assert r.larmor is not None
        assert r.gradient is not None
        assert r.rf_pulse is not None
        assert r.bloch is not None
        assert r.snr is not None
        assert r.sar is not None
        assert 0 < r.omega_mri <= 1
        assert len(r.evidence_tags) == 6

    def test_partial_screening(self):
        from magnetic_resonance.mri_screening import screen_mri
        from magnetic_resonance.contracts import GradientInput, SARInput
        r = screen_mri(gradient_input=GradientInput(), sar_input=SARInput())
        assert r.gradient is not None
        assert r.sar is not None
        assert r.bloch is None
        assert len(r.evidence_tags) == 2

    def test_empty_screening(self):
        from magnetic_resonance.mri_screening import screen_mri
        r = screen_mri()
        assert r.omega_mri == 0.0


# ═══════════════════════════════════════════════════════
# 20. MRI → Foundation 통합
# ═══════════════════════════════════════════════════════

class TestFoundationMRI:
    def test_mri_path_in_foundation(self):
        from magnetic_resonance.foundation import analyze
        from magnetic_resonance.contracts import (
            LarmorInput, GradientInput, RFPulseInput,
            BlochInput, SNRInput, SARInput,
        )
        r = analyze(
            larmor_input=LarmorInput(),
            gradient_input=GradientInput(),
            rf_pulse_input=RFPulseInput(),
            bloch_input=BlochInput(),
            snr_input=SNRInput(),
            sar_input=SARInput(),
        )
        assert r.mri is not None
        assert r.mri.omega_mri > 0
        assert "mri_screening" in r.evidence_tags

    def test_both_paths_together(self):
        from magnetic_resonance.foundation import analyze
        from magnetic_resonance.contracts import (
            LarmorInput, GradientInput, BlochInput,
            ConfinementInput, ConfinementMode,
        )
        r = analyze(
            larmor_input=LarmorInput(),
            gradient_input=GradientInput(),
            bloch_input=BlochInput(),
            confinement_input=ConfinementInput(
                mode=ConfinementMode.MAGNETIC_MIRROR,
                b_max_t=6.0, b_min_t=1.0,
            ),
        )
        assert r.mri is not None
        assert r.confinement is not None
        assert r.omega_overall > 0

    def test_foundation_no_mri(self):
        from magnetic_resonance.foundation import analyze
        from magnetic_resonance.contracts import LarmorInput
        r = analyze(larmor_input=LarmorInput())
        assert r.mri is None


# ═══════════════════════════════════════════════════════
# 21. CLI MRI subcommand
# ═══════════════════════════════════════════════════════

class TestCLIMRI:
    def test_mri_text(self, capsys):
        from magnetic_resonance.cli import main as cli_main
        cli_main(["mri", "--b0", "1.5"])
        out = capsys.readouterr().out
        assert "MRI Screening" in out
        assert "Ω_mri" in out

    def test_mri_json(self, capsys):
        from magnetic_resonance.cli import main as cli_main
        cli_main(["mri", "--b0", "3.0", "--json"])
        out = capsys.readouterr().out
        d = json.loads(out)
        assert "omega_mri" in d
        assert "sar_ok" in d
