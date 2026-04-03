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


def _main_qml() -> str:
    path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "desktop_shell"
        / "qml"
        / "Main.qml"
    )
    return path.read_text(encoding="utf-8")


def test_mirror_primary_path_is_2d_sigil_not_quick3d_or_shapes() -> None:
    qml = _mirror_qml()
    assert "import QtQuick3D" not in qml
    assert "View3D" not in qml
    assert "import QtQuick.Shapes" not in qml
    assert "ShapePath" not in qml
    assert "Repeater3D" not in qml


def test_mirror_runtime_is_lifecycle_gated() -> None:
    qml = _mirror_qml()
    assert "property bool runtimeActive: root.active && root.visible && (!Window.window || Window.window.active)" in qml
    assert "onRuntimeActiveChanged" in qml
    assert "stopRuntimeEngines()" in qml


def test_mirror_uses_interval_drift_not_frame_tick_loop_or_path_math() -> None:
    qml = _mirror_qml()
    assert "id: driftTimer" in qml
    assert "retargetAnomaly()" in qml
    assert "function tick(" not in qml
    assert "id: ticker" not in qml


def test_main_tabs_are_lazy_loaded_via_loaders() -> None:
    qml = _main_qml()
    assert "Loader {" in qml
    assert "sourceComponent: active ? entityTabComponent : undefined" in qml
    assert "sourceComponent: active ? languageTabComponent : undefined" in qml
    assert "sourceComponent: active ? diagnosticsTabComponent : undefined" in qml
