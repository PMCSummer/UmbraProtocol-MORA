from __future__ import annotations

from substrate.contracts import Lifecycle, RuntimeState


def create_empty_state() -> RuntimeState:
    return RuntimeState()


def validate_runtime_state_shape(state: RuntimeState) -> tuple[bool, str | None]:
    if state.runtime.revision < 0:
        return False, "runtime.revision must be >= 0"
    if state.runtime.lifecycle == Lifecycle.INITIALIZED and state.meta.initialized_at is None:
        return False, "meta.initialized_at must be set for initialized lifecycle"
    if state.turn.last_event_ref is not None and not isinstance(state.turn.last_event_ref, str):
        return False, "turn.last_event_ref must be str or None"
    if not isinstance(state.trace.events, tuple):
        return False, "trace.events must be tuple"
    if not isinstance(state.trace.transitions, tuple):
        return False, "trace.transitions must be tuple"
    return True, None
