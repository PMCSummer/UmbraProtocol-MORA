from __future__ import annotations

from copy import deepcopy

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

    @Property("QVariantList", constant=True)
    def criticalRail(self) -> list[dict[str, str]]:
        return self._critical_rail

    entitySurfaceStateChanged = Signal()
    dialogueMessagesChanged = Signal()

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

    @Slot(str)
    def setEntitySurfaceState(self, state: str) -> None:
        normalized = state.strip().lower()
        if normalized not in self._entity_states:
            return
        if normalized == self._entity_state:
            return
        self._entity_state = normalized
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

    @Slot(result=bool)
    def reducedMotionPreferred(self) -> bool:
        # Hook for future motion/accessibility wiring.
        return False
