from __future__ import annotations

from .tokens import ShellTheme, default_shell_theme, to_qml_theme_map

__all__ = [
    "ShellTheme",
    "default_shell_theme",
    "to_qml_theme_map",
    "launch_entity_desktop_shell",
]


def launch_entity_desktop_shell(theme: ShellTheme | None = None) -> int:
    from .app import launch_entity_desktop_shell as _launch

    return _launch(theme=theme)
