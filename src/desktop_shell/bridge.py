from __future__ import annotations

from copy import deepcopy
import os

from PySide6.QtCore import QObject, Property, Signal, Slot


class ShellBridge(QObject):
    """Minimal shell bridge for QML placeholders.

    This bridge is intentionally narrow for foundation migration:
    no runtime orchestration, no engine semantics.
    """

    def __init__(self) -> None:
        super().__init__()
        self._entity_states = ("empty", "active", "waiting", "subject-speaking")
        self._entity_state = "empty"
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
        self._messages_by_state: dict[str, list[dict[str, str]]] = {
            "empty": [],
            "active": [
                {
                    "source": "subject",
                    "text": "Presence acknowledged. Dialogue lane is stable.",
                    "meta": "subject",
                },
                {
                    "source": "operator",
                    "text": "Maintain bounded contact and report uncertainty plainly.",
                    "meta": "operator",
                },
                {
                    "source": "subject",
                    "text": "Bounded mode retained. No overclaim in lexical or dictum layers.",
                    "meta": "subject",
                },
            ],
            "waiting": [
                {
                    "source": "operator",
                    "text": "Next prompt pending. Holding contact surface.",
                    "meta": "operator",
                },
                {
                    "source": "system",
                    "text": "Awaiting next turn...",
                    "meta": "state",
                },
            ],
            "subject-speaking": [
                {
                    "source": "operator",
                    "text": "Provide current bounded state summary.",
                    "meta": "operator",
                },
                {
                    "source": "subject",
                    "text": "Composing response...",
                    "meta": "state",
                },
            ],
        }
        self._state_badge = {
            "empty": "empty",
            "active": "contact-active",
            "waiting": "waiting",
            "subject-speaking": "subject-speaking",
        }
        self._semantic_presets: dict[str, dict[str, float]] = {
            "empty": {
                "pressure_level": 0.12,
                "uncertainty_level": 0.1,
                "conflict_level": 0.08,
                "recovery_level": 0.76,
                "warning_level": 0.0,
            },
            "active": {
                "pressure_level": 0.34,
                "uncertainty_level": 0.22,
                "conflict_level": 0.18,
                "recovery_level": 0.58,
                "warning_level": 0.0,
            },
            "waiting": {
                "pressure_level": 0.44,
                "uncertainty_level": 0.5,
                "conflict_level": 0.22,
                "recovery_level": 0.42,
                "warning_level": 0.0,
            },
            "subject-speaking": {
                "pressure_level": 0.56,
                "uncertainty_level": 0.34,
                "conflict_level": 0.28,
                "recovery_level": 0.36,
                "warning_level": 0.0,
            },
        }
        self._mirror_semantic_input = deepcopy(self._semantic_presets[self._entity_state])
        self._reduced_motion_enabled = os.getenv("UMBRA_REDUCED_MOTION", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @Property("QVariantList", constant=True)
    def criticalRail(self) -> list[dict[str, str]]:
        return self._critical_rail

    entitySurfaceStateChanged = Signal()
    dialogueMessagesChanged = Signal()
    mirrorSemanticInputChanged = Signal()
    reducedMotionChanged = Signal()

    @Property("QVariantList", constant=True)
    def entityStates(self) -> list[str]:
        return list(self._entity_states)

    @Property(str, notify=entitySurfaceStateChanged)
    def entitySurfaceState(self) -> str:
        return self._entity_state

    @Property(str, notify=entitySurfaceStateChanged)
    def entityStateBadge(self) -> str:
        return self._state_badge.get(self._entity_state, "unknown")

    @Property(bool, notify=entitySurfaceStateChanged)
    def composerEnabled(self) -> bool:
        return self._entity_state in {"empty", "active"}

    @Property("QVariantList", notify=dialogueMessagesChanged)
    def dialogueMessages(self) -> list[dict[str, str]]:
        return deepcopy(self._messages_by_state.get(self._entity_state, []))

    @Property("QVariantMap", notify=mirrorSemanticInputChanged)
    def mirrorSemanticInput(self) -> dict[str, float]:
        return deepcopy(self._mirror_semantic_input)

    @Property(bool, notify=reducedMotionChanged)
    def reducedMotionEnabled(self) -> bool:
        return self._reduced_motion_enabled

    def _clamp_level(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _set_semantic_levels(
        self,
        *,
        pressure: float,
        uncertainty: float,
        conflict: float,
        recovery: float,
        warning: float,
    ) -> None:
        self._mirror_semantic_input = {
            "pressure_level": self._clamp_level(pressure),
            "uncertainty_level": self._clamp_level(uncertainty),
            "conflict_level": self._clamp_level(conflict),
            "recovery_level": self._clamp_level(recovery),
            "warning_level": self._clamp_level(warning),
        }
        self.mirrorSemanticInputChanged.emit()

    @Slot(str)
    def setEntitySurfaceState(self, state: str) -> None:
        normalized = state.strip().lower()
        if normalized not in self._entity_states:
            return
        if normalized == self._entity_state:
            return
        self._entity_state = normalized
        preset = self._semantic_presets.get(self._entity_state)
        if preset is not None:
            self._set_semantic_levels(
                pressure=preset["pressure_level"],
                uncertainty=preset["uncertainty_level"],
                conflict=preset["conflict_level"],
                recovery=preset["recovery_level"],
                warning=preset["warning_level"],
            )
        self.entitySurfaceStateChanged.emit()
        self.dialogueMessagesChanged.emit()

    @Slot(str)
    def submitDraftMessage(self, text: str) -> None:
        payload = text.strip()
        if not payload or not self.composerEnabled:
            return
        if self._entity_state == "empty":
            self._entity_state = "active"
        messages = self._messages_by_state.setdefault(self._entity_state, [])
        messages.append({"source": "operator", "text": payload, "meta": "operator"})
        self._entity_state = "subject-speaking"
        self._messages_by_state["subject-speaking"] = messages + [
            {"source": "subject", "text": "Composing response...", "meta": "state"}
        ]
        self.entitySurfaceStateChanged.emit()
        self.dialogueMessagesChanged.emit()

    @Slot(float, float, float, float, result=bool)
    def setMirrorSemanticLevels(
        self,
        pressure_level: float,
        uncertainty_level: float,
        conflict_level: float,
        recovery_level: float,
    ) -> bool:
        self._set_semantic_levels(
            pressure=pressure_level,
            uncertainty=uncertainty_level,
            conflict=conflict_level,
            recovery=recovery_level,
            warning=0.0,
        )
        return True

    @Slot(float, float, float, float, float, result=bool)
    def setMirrorSemanticLevelsWithWarning(
        self,
        pressure_level: float,
        uncertainty_level: float,
        conflict_level: float,
        recovery_level: float,
        warning_level: float,
    ) -> bool:
        self._set_semantic_levels(
            pressure=pressure_level,
            uncertainty=uncertainty_level,
            conflict=conflict_level,
            recovery=recovery_level,
            warning=warning_level,
        )
        return True

    @Slot(bool)
    def setReducedMotionEnabled(self, enabled: bool) -> None:
        normalized = bool(enabled)
        if normalized == self._reduced_motion_enabled:
            return
        self._reduced_motion_enabled = normalized
        self.reducedMotionChanged.emit()

    @Slot(result=bool)
    def reducedMotionPreferred(self) -> bool:
        return self._reduced_motion_enabled
