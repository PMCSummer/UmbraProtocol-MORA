from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QMessageBox

from roadmap_tracker.app import MainWindow


UI_FONT_FAMILY = "Exo 2"
FALLBACK_FONT_FAMILY = "Segoe UI"


def load_app_fonts() -> None:
    """
    Загружает локальные шрифты из папки fonts рядом с пакетом roadmap_tracker.
    Ожидаемая структура, например:
        project_root/
        ├─ main.py
        └─ roadmap_tracker/
           ├─ app.py
           ├─ model.py
           └─ fonts/
              ├─ Exo2-VariableFont_wght.ttf
              ├─ RussoOne-Regular.ttf
              └─ Jura-VariableFont_wght.ttf
    """
    package_dir = Path(__file__).resolve().parent / "roadmap_tracker"
    font_dir = package_dir / "fonts"

    if not font_dir.exists():
        return

    font_files = [
        "Exo2-VariableFont_wght.ttf",
        "RussoOne-Regular.ttf",
        "Jura-VariableFont_wght.ttf",
    ]

    for filename in font_files:
        font_path = font_dir / filename
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))


def resolve_initial_json(argv: list[str]) -> Optional[Path]:
    """
    Если передан путь к JSON первым аргументом командной строки,
    пытается использовать его как стартовый файл состояния.
    Иначе ищет дефолтный файл в текущей директории.
    """
    if len(argv) > 1:
        candidate = Path(argv[1]).expanduser().resolve()
        if candidate.exists() and candidate.suffix.lower() == ".json":
            return candidate

    default_json = Path("Aiko_vNextRoadmap_claim_honest_v3.json")
    if default_json.exists():
        return default_json.resolve()

    return None


def configure_application(app: QApplication) -> None:
    app.setApplicationName("Roadmap Research Tracker")
    app.setOrganizationName("roadmap_tracker")
    app.setStyle("Fusion")

    load_app_fonts()

    families = {family.lower() for family in QFontDatabase.families()}
    chosen_family = UI_FONT_FAMILY if UI_FONT_FAMILY.lower() in families else FALLBACK_FONT_FAMILY
    app.setFont(QFont(chosen_family, 10))


def run() -> int:
    app = QApplication(sys.argv)
    configure_application(app)

    try:
        initial_json = resolve_initial_json(sys.argv)
        window = MainWindow(initial_json=initial_json)
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Ошибка запуска",
            f"Не удалось запустить приложение:\n{exc}",
        )
        return 1


if __name__ == "__main__":
    sys.exit(run())