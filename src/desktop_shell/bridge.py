from __future__ import annotations

from PySide6.QtCore import QObject, Property, Slot


class ShellBridge(QObject):
    """Minimal shell bridge for QML placeholders.

    This bridge is intentionally narrow for foundation migration:
    no runtime orchestration, no engine semantics.
    """

    def __init__(self) -> None:
        super().__init__()
        self._critical_rail = [
            {"label": "Current Mode", "value": "bounded_shell"},
            {"label": "Session Phase", "value": "foundation_qml"},
            {"label": "Runtime Revision", "value": "r:0000"},
            {"label": "Last Transition", "value": "tr:none"},
            {"label": "Last Event", "value": "ev:none"},
            {"label": "Failure Surface", "value": "none"},
            {"label": "Regulation Pressure", "value": "baseline"},
            {"label": "Uncertainty", "value": "bounded"},
            {"label": "Directive", "value": "observe"},
            {"label": "Recoverability", "value": "unknown"},
            {"label": "Confidence", "value": "shell_only"},
        ]

    @Property("QVariantList", constant=True)
    def criticalRail(self) -> list[dict[str, str]]:
        return self._critical_rail

    @Slot(result=bool)
    def reducedMotionPreferred(self) -> bool:
        # Hook for future motion/accessibility wiring.
        return False

