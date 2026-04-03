from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

try:
    from .bridge import ShellBridge
    from .tokens import ShellTheme, default_shell_theme, to_qml_theme_map
except ImportError:  # pragma: no cover - direct file execution fallback
    from bridge import ShellBridge
    from tokens import ShellTheme, default_shell_theme, to_qml_theme_map


def _qml_main_file() -> Path:
    return Path(__file__).resolve().parent / "qml" / "Main.qml"


def launch_entity_desktop_shell(theme: ShellTheme | None = None) -> int:
    selected_theme = theme or default_shell_theme()
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    bridge = ShellBridge()
    root_context = engine.rootContext()
    root_context.setContextProperty("shellBridge", bridge)
    root_context.setContextProperty("shellTheme", to_qml_theme_map(selected_theme))

    qml_path = _qml_main_file()
    engine.addImportPath(str(qml_path.parent))
    engine.load(QUrl.fromLocalFile(os.fspath(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError("QML root failed to load for desktop shell foundation")
    return app.exec()


def main() -> int:
    return launch_entity_desktop_shell()


if __name__ == "__main__":
    raise SystemExit(main())
