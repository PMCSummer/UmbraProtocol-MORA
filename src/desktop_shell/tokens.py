from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True, slots=True)
class ColorTokens:
    app_background: str = "#070707"
    panel_primary: str = "#0F0F0F"
    panel_secondary: str = "#131313"
    text_primary: str = "#F2F2F2"
    text_secondary: str = "#B8B8B8"
    divider_subtle: str = "#272727"
    geometry_white: str = "#F5F5F5"
    accent_advisory: str = "#8A735A"
    accent_caution: str = "#A77D38"
    accent_warning: str = "#7B3A2A"
    state_muted: str = "#6D6D6D"
    input_background: str = "#0B0B0B"


@dataclass(frozen=True, slots=True)
class TypographyRole:
    families: tuple[str, ...]
    size: int
    weight: str = "normal"


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    display_title: TypographyRole = TypographyRole(
        families=("Tomorrow", "Bahnschrift", "Segoe UI", "Arial"),
        size=18,
        weight="bold",
    )
    section_title: TypographyRole = TypographyRole(
        families=("Oxanium", "Segoe UI Semibold", "Segoe UI", "Arial"),
        size=11,
        weight="bold",
    )
    status_label: TypographyRole = TypographyRole(
        families=("Oxanium", "Segoe UI", "Arial"),
        size=10,
        weight="normal",
    )
    body_text: TypographyRole = TypographyRole(
        families=("Inter", "Segoe UI", "Arial"),
        size=11,
        weight="normal",
    )
    secondary_text: TypographyRole = TypographyRole(
        families=("Inter", "Segoe UI", "Arial"),
        size=10,
        weight="normal",
    )
    mono_text: TypographyRole = TypographyRole(
        families=("IBM Plex Mono", "JetBrains Mono", "Consolas", "Courier New"),
        size=10,
        weight="normal",
    )


@dataclass(frozen=True, slots=True)
class SpacingTokens:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True, slots=True)
class RadiusTokens:
    sm: int = 4
    md: int = 8
    lg: int = 12


@dataclass(frozen=True, slots=True)
class LineTokens:
    thin: int = 1
    medium: int = 2


@dataclass(frozen=True, slots=True)
class TimingTokens:
    soft_standard_ms: int = 140
    slow_settle_ms: int = 260
    sharp_warning_ms: int = 90


@dataclass(frozen=True, slots=True)
class MotionGrammarTokens:
    fade_ms: int = 160
    line_reveal_ms: int = 280
    phase_shift_ms: int = 360
    convergence_ms: int = 300
    shear_drift_ms: int = 520
    ghost_echo_ms: int = 620
    easing_soft_standard: str = "soft_standard"
    easing_slow_settle: str = "slow_settle"
    easing_sharp_warning: str = "sharp_warning"
    reduced_duration_scale: float = 0.56
    reduced_distance_scale: float = 0.4


@dataclass(frozen=True, slots=True)
class PanelHierarchyTokens:
    entity_dialogue_weight: float = 0.58
    entity_side_weight: float = 0.42
    mirror_host_weight: float = 0.67
    critical_rail_weight: float = 0.33


@dataclass(frozen=True, slots=True)
class MirrorMotionTokens:
    min_target_interval_s: float = 6.0
    max_target_interval_s: float = 18.0
    slerp_response: float = 0.72
    base_motion_intensity: float = 1.0
    target_delta_min_deg: float = 18.0
    target_delta_max_deg: float = 52.0
    precession_intensity: float = 0.24
    precession_frequency_hz: float = 0.018
    precession_max_deg: float = 7.5
    reduced_motion_scale: float = 0.35
    reduced_interval_scale: float = 1.8


@dataclass(frozen=True, slots=True)
class MirrorSemanticTokens:
    advisory_gate: float = 0.34
    caution_gate: float = 0.64
    warning_gate: float = 0.9
    symmetry_conflict_influence: float = 0.24
    symmetry_recovery_restore: float = 0.2
    density_pressure_scale: float = 0.9
    density_conflict_scale: float = 0.45
    echo_uncertainty_scale: float = 0.72
    echo_recovery_damp: float = 0.5
    echo_distance_scale: float = 28.0
    center_offset_conflict_scale: float = 14.0
    center_offset_pressure_scale: float = 8.0
    center_offset_recovery_damp: float = 0.7
    orbital_activity_scale: float = 0.86
    orbital_radius: float = 126.0
    motion_pressure_speedup: float = 0.42
    motion_conflict_irregularity: float = 0.28
    motion_uncertainty_drift: float = 0.22
    motion_recovery_calm: float = 0.36
    reduced_semantic_scale: float = 0.5


@dataclass(frozen=True, slots=True)
class ShellTheme:
    colors: ColorTokens = field(default_factory=ColorTokens)
    typography: TypographyTokens = field(default_factory=TypographyTokens)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    radii: RadiusTokens = field(default_factory=RadiusTokens)
    lines: LineTokens = field(default_factory=LineTokens)
    timing: TimingTokens = field(default_factory=TimingTokens)
    motion: MotionGrammarTokens = field(default_factory=MotionGrammarTokens)
    hierarchy: PanelHierarchyTokens = field(default_factory=PanelHierarchyTokens)
    mirror: MirrorMotionTokens = field(default_factory=MirrorMotionTokens)
    mirror_semantics: MirrorSemanticTokens = field(default_factory=MirrorSemanticTokens)
    reduced_motion: bool = False


def default_shell_theme() -> ShellTheme:
    return ShellTheme()


def to_qml_theme_map(theme: ShellTheme | None = None) -> dict[str, object]:
    selected = theme or default_shell_theme()
    payload = asdict(selected)
    payload["version"] = "desktop-shell-foundation-v1-qt"
    return payload
