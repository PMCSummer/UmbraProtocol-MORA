from __future__ import annotations

"""
LEGACY (non-primary) tkinter theme helper.

Primary desktop shell theme consumption now happens in QML via
`shellTheme` context payload from `desktop_shell.app`.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from desktop_shell.tokens import ShellTheme, TypographyRole


class ThemeManager:
    def __init__(self, root: tk.Misc, theme: ShellTheme) -> None:
        self._root = root
        self.theme = theme
        self._fonts: dict[str, tkfont.Font] = {}

    def apply(self) -> None:
        colors = self.theme.colors
        self._root.configure(bg=colors.app_background)
        self._configure_ttk_notebook()

    def get_font(self, role_name: str) -> tkfont.Font:
        existing = self._fonts.get(role_name)
        if existing is not None:
            return existing
        role = getattr(self.theme.typography, role_name)
        font = tkfont.Font(
            family=self._resolve_family(role),
            size=role.size,
            weight=role.weight,
        )
        self._fonts[role_name] = font
        return font

    def frame(self, parent: tk.Misc, *, secondary: bool = False) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.theme.colors.panel_secondary if secondary else self.theme.colors.panel_primary,
            highlightthickness=self.theme.lines.thin,
            highlightbackground=self.theme.colors.divider_subtle,
            bd=0,
        )

    def divider(self, parent: tk.Misc, *, vertical: bool = False) -> tk.Frame:
        if vertical:
            return tk.Frame(
                parent,
                bg=self.theme.colors.divider_subtle,
                width=self.theme.lines.thin,
                bd=0,
            )
        return tk.Frame(
            parent,
            bg=self.theme.colors.divider_subtle,
            height=self.theme.lines.thin,
            bd=0,
        )

    def _resolve_family(self, role: TypographyRole) -> str:
        try:
            available = set(tkfont.families(self._root))
        except tk.TclError:
            available = set()
        for family in role.families:
            if family in available:
                return family
        return role.families[-1]

    def _configure_ttk_notebook(self) -> None:
        colors = self.theme.colors
        style = ttk.Style(self._root)
        style.theme_use("clam")
        style.configure(
            "EntityShell.TNotebook",
            background=colors.app_background,
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "EntityShell.TNotebook.Tab",
            background=colors.panel_secondary,
            foreground=colors.text_secondary,
            borderwidth=0,
            padding=(16, 10),
            focuscolor=colors.panel_secondary,
            font=self.get_font("status_label"),
        )
        style.map(
            "EntityShell.TNotebook.Tab",
            background=[("selected", colors.panel_primary), ("active", colors.panel_primary)],
            foreground=[("selected", colors.text_primary), ("active", colors.text_primary)],
        )
