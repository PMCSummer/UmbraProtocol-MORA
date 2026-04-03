from __future__ import annotations

"""
LEGACY (non-primary) foundation shell on tkinter.

Primary desktop shell path is now:
PySide6 + QML/Qt Quick + Qt Quick 3D via `desktop_shell.app`.
This module is retained temporarily as a migration reference only.
"""

import tkinter as tk

from desktop_shell.theme import ThemeManager
from desktop_shell.tokens import ShellTheme


class EntityTabShell(tk.Frame):
    def __init__(self, parent: tk.Misc, *, theme: ShellTheme, theme_manager: ThemeManager) -> None:
        super().__init__(parent, bg=theme.colors.app_background, bd=0)
        self._theme = theme
        self._tm = theme_manager
        self._h_pane: tk.PanedWindow | None = None
        self._v_pane: tk.PanedWindow | None = None
        self._build()

    def _build(self) -> None:
        spacing = self._theme.spacing
        header = tk.Frame(self, bg=self._theme.colors.app_background)
        header.pack(fill="x", padx=spacing.xl, pady=(spacing.lg, spacing.md))
        tk.Label(
            header,
            text="Entity",
            bg=self._theme.colors.app_background,
            fg=self._theme.colors.text_primary,
            font=self._tm.get_font("display_title"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            header,
            text="Dialogue-first shell with bounded lexical and regulation surfaces.",
            bg=self._theme.colors.app_background,
            fg=self._theme.colors.text_secondary,
            font=self._tm.get_font("secondary_text"),
            anchor="w",
        ).pack(fill="x", pady=(spacing.xs, 0))

        self._h_pane = tk.PanedWindow(
            self,
            orient="horizontal",
            bg=self._theme.colors.app_background,
            sashwidth=4,
            sashpad=0,
            sashrelief="flat",
            bd=0,
            relief="flat",
        )
        self._h_pane.pack(fill="both", expand=True, padx=spacing.xl, pady=(0, spacing.xl))

        dialogue_panel = self._build_dialogue_panel(self._h_pane)
        side_panel = self._build_side_panel(self._h_pane)
        self._h_pane.add(dialogue_panel, minsize=480, stretch="always")
        self._h_pane.add(side_panel, minsize=340, stretch="always")

        self.bind("<Configure>", self._sync_split, add="+")

    def _build_dialogue_panel(self, parent: tk.Misc) -> tk.Frame:
        spacing = self._theme.spacing
        panel = self._tm.frame(parent)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        tk.Label(
            panel,
            text="Dialogue",
            bg=self._theme.colors.panel_primary,
            fg=self._theme.colors.text_primary,
            font=self._tm.get_font("section_title"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=spacing.lg, pady=(spacing.lg, spacing.sm))

        history = tk.Text(
            panel,
            wrap="word",
            relief="flat",
            bd=0,
            bg=self._theme.colors.input_background,
            fg=self._theme.colors.text_primary,
            insertbackground=self._theme.colors.geometry_white,
            font=self._tm.get_font("body_text"),
            padx=spacing.md,
            pady=spacing.md,
        )
        history.grid(row=1, column=0, sticky="nsew", padx=spacing.lg)
        history.insert(
            "end",
            "Entity presence shell initialized.\n"
            "No mirror engine yet. No semantic overreach.\n"
            "Use this pane as the primary conversation surface.",
        )
        history.configure(state="disabled")

        composer = tk.Frame(panel, bg=self._theme.colors.panel_primary)
        composer.grid(row=2, column=0, sticky="ew", padx=spacing.lg, pady=spacing.lg)
        composer.grid_columnconfigure(0, weight=1)

        input_box = tk.Text(
            composer,
            height=4,
            relief="flat",
            bd=0,
            bg=self._theme.colors.input_background,
            fg=self._theme.colors.text_primary,
            insertbackground=self._theme.colors.geometry_white,
            font=self._tm.get_font("body_text"),
            padx=spacing.md,
            pady=spacing.sm,
        )
        input_box.grid(row=0, column=0, sticky="ew")
        input_box.insert("1.0", "Type to engage the entity shell...")
        send_button = tk.Button(
            composer,
            text="Transmit",
            relief="flat",
            bd=0,
            bg=self._theme.colors.panel_secondary,
            fg=self._theme.colors.text_primary,
            activebackground=self._theme.colors.panel_secondary,
            activeforeground=self._theme.colors.text_primary,
            font=self._tm.get_font("status_label"),
            padx=spacing.lg,
            pady=spacing.sm,
            highlightthickness=1,
            highlightbackground=self._theme.colors.divider_subtle,
        )
        send_button.grid(row=0, column=1, sticky="nsw", padx=(spacing.sm, 0))
        return panel

    def _build_side_panel(self, parent: tk.Misc) -> tk.Frame:
        side = tk.Frame(parent, bg=self._theme.colors.app_background)
        self._v_pane = tk.PanedWindow(
            side,
            orient="vertical",
            bg=self._theme.colors.app_background,
            sashwidth=4,
            sashpad=0,
            sashrelief="flat",
            bd=0,
            relief="flat",
        )
        self._v_pane.pack(fill="both", expand=True)
        mirror = self._build_mirror_host(self._v_pane)
        critical = self._build_critical_rail(self._v_pane)
        self._v_pane.add(mirror, minsize=220, stretch="always")
        self._v_pane.add(critical, minsize=150, stretch="always")
        return side

    def _build_mirror_host(self, parent: tk.Misc) -> tk.Frame:
        spacing = self._theme.spacing
        panel = self._tm.frame(parent, secondary=True)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        tk.Label(
            panel,
            text="Mirror Host",
            bg=self._theme.colors.panel_secondary,
            fg=self._theme.colors.text_primary,
            font=self._tm.get_font("section_title"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=spacing.lg, pady=(spacing.lg, spacing.sm))

        canvas = tk.Canvas(
            panel,
            bg=self._theme.colors.input_background,
            bd=0,
            relief="flat",
            highlightthickness=1,
            highlightbackground=self._theme.colors.divider_subtle,
        )
        canvas.grid(row=1, column=0, sticky="nsew", padx=spacing.lg, pady=(0, spacing.lg))
        canvas.bind("<Configure>", lambda event: self._draw_mirror_placeholder(canvas, event.width, event.height))
        return panel

    def _draw_mirror_placeholder(self, canvas: tk.Canvas, width: int, height: int) -> None:
        canvas.delete("all")
        if width < 20 or height < 20:
            return
        color = self._theme.colors.geometry_white
        cx = width // 2
        cy = height // 2
        radius = min(width, height) * 0.32
        canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=1)
        canvas.create_line(cx - radius * 0.9, cy, cx + radius * 0.9, cy, fill=color, width=1)
        canvas.create_line(cx, cy - radius * 0.9, cx, cy + radius * 0.9, fill=color, width=1)
        canvas.create_polygon(
            cx,
            cy - radius * 0.75,
            cx + radius * 0.68,
            cy + radius * 0.4,
            cx - radius * 0.68,
            cy + radius * 0.4,
            outline=self._theme.colors.text_secondary,
            fill="",
            width=1,
        )
        canvas.create_text(
            width // 2,
            height - 18,
            fill=self._theme.colors.text_secondary,
            text="placeholder host only",
            font=self._tm.get_font("secondary_text"),
        )

    def _build_critical_rail(self, parent: tk.Misc) -> tk.Frame:
        spacing = self._theme.spacing
        panel = self._tm.frame(parent)
        panel.grid_columnconfigure(0, weight=1)
        tk.Label(
            panel,
            text="Critical Rail",
            bg=self._theme.colors.panel_primary,
            fg=self._theme.colors.text_primary,
            font=self._tm.get_font("section_title"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=spacing.lg, pady=(spacing.lg, spacing.sm))

        rail_data = (
            ("Current Mode", "bounded_shell"),
            ("Session Phase", "foundation_ui"),
            ("Runtime Revision", "r:0000"),
            ("Last Transition", "tr:none"),
            ("Last Event", "ev:none"),
            ("Failure Surface", "none"),
            ("Regulation Pressure", "baseline"),
            ("Uncertainty", "bounded"),
            ("Directive", "observe"),
            ("Recoverability", "unknown"),
            ("Confidence", "shell_only"),
        )
        for idx, (label, value) in enumerate(rail_data, start=1):
            row = tk.Frame(panel, bg=self._theme.colors.panel_primary)
            row.grid(row=idx, column=0, sticky="ew", padx=spacing.lg)
            row.grid_columnconfigure(1, weight=1)
            tk.Label(
                row,
                text=label,
                bg=self._theme.colors.panel_primary,
                fg=self._theme.colors.text_secondary,
                font=self._tm.get_font("status_label"),
                anchor="w",
            ).grid(row=0, column=0, sticky="w", pady=(0, spacing.xs))
            tk.Label(
                row,
                text=value,
                bg=self._theme.colors.panel_primary,
                fg=self._theme.colors.text_primary,
                font=self._tm.get_font("mono_text"),
                anchor="e",
            ).grid(row=0, column=1, sticky="e", pady=(0, spacing.xs))
        return panel

    def _sync_split(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is not self:
            return
        if self._h_pane is not None and self._h_pane.panes():
            try:
                target = int(max(0, event.width * self._theme.hierarchy.entity_dialogue_weight))
                self._h_pane.sash_place(0, target, 0)
            except tk.TclError:
                pass
        if self._v_pane is not None and self._v_pane.panes():
            try:
                body_height = max(0, event.height - 72)
                target = int(body_height * self._theme.hierarchy.mirror_host_weight)
                self._v_pane.sash_place(0, 0, target)
            except tk.TclError:
                pass


class PlaceholderTabShell(tk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        theme: ShellTheme,
        theme_manager: ThemeManager,
        title: str,
        subtitle: str,
        diagnostics_mode: bool = False,
    ) -> None:
        super().__init__(parent, bg=theme.colors.app_background, bd=0)
        self._theme = theme
        self._tm = theme_manager
        self._build(title=title, subtitle=subtitle, diagnostics_mode=diagnostics_mode)

    def _build(self, *, title: str, subtitle: str, diagnostics_mode: bool) -> None:
        spacing = self._theme.spacing
        tk.Label(
            self,
            text=title,
            bg=self._theme.colors.app_background,
            fg=self._theme.colors.text_primary,
            font=self._tm.get_font("display_title"),
            anchor="w",
        ).pack(fill="x", padx=spacing.xl, pady=(spacing.lg, spacing.xs))
        tk.Label(
            self,
            text=subtitle,
            bg=self._theme.colors.app_background,
            fg=self._theme.colors.text_secondary,
            font=self._tm.get_font("secondary_text"),
            anchor="w",
        ).pack(fill="x", padx=spacing.xl, pady=(0, spacing.lg))

        body = self._tm.frame(self, secondary=True)
        body.pack(fill="both", expand=True, padx=spacing.xl, pady=(0, spacing.xl))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)
        tk.Label(
            body,
            text="Shell Placeholder",
            bg=self._theme.colors.panel_secondary,
            fg=self._theme.colors.text_primary,
            font=self._tm.get_font("section_title"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=spacing.lg, pady=(spacing.lg, spacing.sm))

        content_font = self._tm.get_font("mono_text" if diagnostics_mode else "body_text")
        content_fg = self._theme.colors.text_secondary if diagnostics_mode else self._theme.colors.text_primary
        tk.Label(
            body,
            text=(
                "Foundation-only tab shell.\n"
                "No deep engine wiring in this increment.\n"
                "Reserved for next bounded implementation step."
            ),
            justify="left",
            bg=self._theme.colors.panel_secondary,
            fg=content_fg,
            font=content_font,
            anchor="nw",
        ).grid(row=1, column=0, sticky="nsew", padx=spacing.lg, pady=(0, spacing.lg))
