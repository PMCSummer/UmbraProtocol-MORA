from pathlib import Path


def _mirror_qml() -> str:
    path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "desktop_shell"
        / "qml"
        / "components"
        / "MirrorHost3D.qml"
    )
    return path.read_text(encoding="utf-8")


def test_mirror_uses_native_animation_core_instead_of_per_frame_tick_loop() -> None:
    qml = _mirror_qml()
    assert "QuaternionAnimation" in qml
    assert "function tick(" not in qml
    assert "id: ticker" not in qml


def test_mirror_runtime_is_lifecycle_gated() -> None:
    qml = _mirror_qml()
    assert "property bool runtimeActive: root.active && root.visible && (!Window.window || Window.window.active)" in qml
    assert "onRuntimeActiveChanged" in qml
    assert "stopRuntimeEngines()" in qml


def test_mirror_target_updates_are_interval_driven_not_frame_driven() -> None:
    qml = _mirror_qml()
    assert "id: targetTimer" in qml
    assert "scheduleNextTargetIntervalMs" in qml
    assert "repeat: false" in qml
