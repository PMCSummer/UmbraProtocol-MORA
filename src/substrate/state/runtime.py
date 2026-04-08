from __future__ import annotations

from substrate.contracts import (
    ContinuityDomainState,
    Lifecycle,
    MemoryEconomicsDomainState,
    RegulationDomainState,
    RuntimeDomainsState,
    RuntimeState,
    SelfBoundaryDomainState,
    ValidityDomainState,
    WorldDomainState,
)


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
    if not isinstance(state.domains, RuntimeDomainsState):
        return False, "domains must be RuntimeDomainsState"
    if not isinstance(state.domains.regulation, RegulationDomainState):
        return False, "domains.regulation must be RegulationDomainState"
    if not isinstance(state.domains.continuity, ContinuityDomainState):
        return False, "domains.continuity must be ContinuityDomainState"
    if not isinstance(state.domains.validity, ValidityDomainState):
        return False, "domains.validity must be ValidityDomainState"
    if not isinstance(state.domains.self_boundary, SelfBoundaryDomainState):
        return False, "domains.self_boundary must be SelfBoundaryDomainState"
    if not isinstance(state.domains.world, WorldDomainState):
        return False, "domains.world must be WorldDomainState"
    if not isinstance(state.domains.memory_economics, MemoryEconomicsDomainState):
        return False, "domains.memory_economics must be MemoryEconomicsDomainState"
    if not isinstance(state.domains.validity.selective_scope_targets, tuple):
        return False, "domains.validity.selective_scope_targets must be tuple"
    return True, None
