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
