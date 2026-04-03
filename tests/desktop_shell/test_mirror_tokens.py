from desktop_shell.tokens import default_shell_theme, to_qml_theme_map


def test_default_mirror_motion_tokens_are_bounded() -> None:
    theme = default_shell_theme()
    mirror = theme.mirror

    assert 6.0 <= mirror.min_target_interval_s <= mirror.max_target_interval_s <= 18.0
    assert 0.0 < mirror.slerp_response <= 2.0
    assert mirror.target_delta_min_deg < mirror.target_delta_max_deg
    assert 0.0 < mirror.precession_intensity < 1.0
    assert 0.0 < mirror.precession_frequency_hz < 0.2
    assert 0.0 < mirror.reduced_motion_scale < 1.0
    assert mirror.reduced_interval_scale >= 1.0


def test_qml_theme_payload_exposes_mirror_motion_tokens() -> None:
    payload = to_qml_theme_map(default_shell_theme())
    mirror = payload["mirror"]

    assert mirror["min_target_interval_s"] == 6.0
    assert mirror["max_target_interval_s"] == 18.0
    assert "slerp_response" in mirror
    assert "precession_intensity" in mirror
    assert "reduced_motion_scale" in mirror


def test_qml_theme_payload_exposes_mirror_semantic_tokens() -> None:
    payload = to_qml_theme_map(default_shell_theme())
    semantics = payload["mirror_semantics"]

    assert 0.0 < semantics["advisory_gate"] < semantics["caution_gate"] < semantics["warning_gate"] <= 1.0
    assert semantics["density_pressure_scale"] > 0.0
    assert semantics["echo_uncertainty_scale"] > 0.0
    assert semantics["center_offset_conflict_scale"] > 0.0
    assert semantics["orbital_activity_scale"] > 0.0
    assert semantics["motion_pressure_speedup"] > 0.0
    assert 0.0 < semantics["reduced_semantic_scale"] <= 1.0


def test_qml_theme_payload_exposes_motion_grammar_tokens() -> None:
    payload = to_qml_theme_map(default_shell_theme())
    motion = payload["motion"]

    assert motion["fade_ms"] > 0
    assert motion["line_reveal_ms"] >= motion["fade_ms"]
    assert motion["phase_shift_ms"] >= motion["convergence_ms"]
    assert motion["shear_drift_ms"] >= motion["phase_shift_ms"]
    assert motion["ghost_echo_ms"] >= motion["shear_drift_ms"]
    assert motion["easing_soft_standard"] == "soft_standard"
    assert motion["easing_slow_settle"] == "slow_settle"
    assert motion["easing_sharp_warning"] == "sharp_warning"
    assert 0.0 < motion["reduced_duration_scale"] <= 1.0
    assert 0.0 < motion["reduced_distance_scale"] <= 1.0
