from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from substrate.authority import (
    allowed_changed_paths,
    check_authority,
    check_domain_route_authenticity,
    check_domain_writer_discipline,
    runtime_domain_paths_from_update,
    writer_transition_paths,
)
from substrate.contracts import (
    AuthorityDecision,
    FailureCode,
    FailureMarker,
    Lifecycle,
    ProvenanceRecord,
    ProvenanceStatus,
    RuntimeDomainUpdate,
    RuntimeRouteAuthContext,
    RuntimeDomainsState,
    RuntimeState,
    StateDelta,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.events import build_event_record
from substrate.failures import build_failure_marker
from substrate.provenance import build_provenance_record
from substrate.state import create_empty_state, validate_runtime_state_shape


@dataclass(slots=True)
class _TransitionContext:
    request: Any
    state: Any
    request_obj: TransitionRequest | None = None
    state_obj: RuntimeState | None = None
    kind: TransitionKind = TransitionKind.REJECTED_TRANSITION
    authority: AuthorityDecision = AuthorityDecision(
        allowed=False, denied_paths=(), reason="authority not evaluated"
    )
    failure: FailureMarker | None = None
    accepted: bool = False
    candidate_state: RuntimeState | None = None
    delta: StateDelta | None = None
    provenance: ProvenanceRecord | None = None
    emitted_event: Any = None
    transition_id: str = ""
    event_id: str = ""
    cause_chain: tuple[str, ...] = ()
    attempted_paths: tuple[str, ...] = ()
    domain_update: RuntimeDomainUpdate | None = None
    route_auth: RuntimeRouteAuthContext | None = None


def execute_transition(request: Any, state: Any) -> TransitionResult:
    context = _TransitionContext(request=request, state=state)
    validate_request_shape(context)
    validate_state_shape(context)
    resolve_transition_kind(context)
    check_authority_stage(context)
    apply_pure_transition(context)
    build_state_delta(context)
    build_provenance_record_stage(context)
    enforce_invariants(context)
    emit_failure_if_needed(context)
    return return_transition_result(context)


def validate_request_shape(context: _TransitionContext) -> None:
    if isinstance(context.request, TransitionRequest):
        context.request_obj = context.request
        context.transition_id = context.request.transition_id or _new_transition_id()
        context.cause_chain = context.request.cause_chain or ("direct",)
        context.event_id = context.request.event_id or _new_event_id()
        if not context.request.transition_id:
            _set_failure(
                context,
                code=FailureCode.INVALID_REQUEST_SHAPE,
                stage="validate_request_shape",
                message="request.transition_id must be non-empty",
            )
            return
        if not context.cause_chain:
            _set_failure(
                context,
                code=FailureCode.INVALID_REQUEST_SHAPE,
                stage="validate_request_shape",
                message="request.cause_chain must be non-empty",
            )
            return
        if context.request.transition_kind in {
            TransitionKind.INGEST_EXTERNAL_EVENT,
            TransitionKind.APPLY_INTERNAL_EVENT,
        } and context.request.event_payload is None:
            _set_failure(
                context,
                code=FailureCode.INVALID_REQUEST_SHAPE,
                stage="validate_request_shape",
                message="event transitions require event_payload",
            )
            return
        payload = context.request.event_payload or {}
        domain_update = payload.get("runtime_domain_update")
        if domain_update is not None and not isinstance(domain_update, RuntimeDomainUpdate):
            _set_failure(
                context,
                code=FailureCode.INVALID_REQUEST_SHAPE,
                stage="validate_request_shape",
                message="runtime_domain_update must be RuntimeDomainUpdate",
            )
            return
        route_auth = payload.get("runtime_route_auth")
        if route_auth is not None and not isinstance(route_auth, RuntimeRouteAuthContext):
            _set_failure(
                context,
                code=FailureCode.INVALID_REQUEST_SHAPE,
                stage="validate_request_shape",
                message="runtime_route_auth must be RuntimeRouteAuthContext",
            )
            return
        context.domain_update = domain_update
        context.route_auth = route_auth
        return

    context.transition_id = _new_transition_id()
    context.event_id = _new_event_id()
    context.cause_chain = ("invalid-request",)
    _set_failure(
        context,
        code=FailureCode.INVALID_REQUEST_SHAPE,
        stage="validate_request_shape",
        message="request must be TransitionRequest",
    )


def validate_state_shape(context: _TransitionContext) -> None:
    if isinstance(context.state, RuntimeState):
        context.state_obj = context.state
        ok, reason = validate_runtime_state_shape(context.state_obj)
        if not ok:
            _set_failure(
                context,
                code=FailureCode.INVALID_STATE_SHAPE,
                stage="validate_state_shape",
                message=reason or "invalid runtime state shape",
            )
        return

    context.state_obj = create_empty_state()
    _set_failure(
        context,
        code=FailureCode.INVALID_STATE_SHAPE,
        stage="validate_state_shape",
        message="state must be RuntimeState",
    )


def resolve_transition_kind(context: _TransitionContext) -> None:
    if context.request_obj is not None:
        context.kind = context.request_obj.transition_kind
        return
    context.kind = TransitionKind.REJECTED_TRANSITION


def check_authority_stage(context: _TransitionContext) -> None:
    writer = _resolve_writer(context)
    requested = set(writer_transition_paths(context.kind))
    requested.update(runtime_domain_paths_from_update(context.domain_update))
    requested_paths = frozenset(requested)
    context.attempted_paths = tuple(sorted(requested_paths))
    context.authority = check_authority(writer, requested_paths)
    if context.failure is not None:
        return
    if context.authority.allowed and context.domain_update is not None:
        domain_authority = check_domain_writer_discipline(
            domain_update=context.domain_update,
            transition_kind=context.kind,
        )
        context.authority = _merge_authority_decisions(context.authority, domain_authority)
        if not domain_authority.allowed:
            _set_failure(
                context,
                code=FailureCode.AUTHORITY_DENIED,
                stage="check_authority",
                message="domain writer discipline rejected runtime domain update",
            )
            return
        route_authority = check_domain_route_authenticity(
            domain_update=context.domain_update,
            route_auth=context.route_auth,
            transition_kind=context.kind,
        )
        context.authority = _merge_authority_decisions(context.authority, route_authority)
        if not route_authority.allowed:
            _set_failure(
                context,
                code=FailureCode.AUTHORITY_DENIED,
                stage="check_authority",
                message="domain route authenticity rejected runtime domain update",
            )
            return
    if not context.authority.allowed:
        _set_failure(
            context,
            code=FailureCode.AUTHORITY_DENIED,
            stage="check_authority",
            message="writer not authorized for requested transition fields",
        )


def apply_pure_transition(context: _TransitionContext) -> None:
    if context.state_obj is None:
        context.state_obj = create_empty_state()

    if context.failure is not None:
        _apply_rejected_outcome(context)
        return

    if context.kind == TransitionKind.REJECTED_TRANSITION:
        _set_failure(
            context,
            code=FailureCode.REQUESTED_REJECTION,
            stage="apply_pure_transition",
            message="rejected transition requested explicitly",
        )
        _apply_rejected_outcome(context)
        return

    base = context.state_obj
    payload = dict(context.request_obj.event_payload or {}) if context.request_obj else {}
    event_id = context.event_id or _new_event_id()

    next_meta = base.meta
    next_runtime = base.runtime
    next_turn = base.turn
    next_failures = replace(base.failures, current=None)
    next_domains = base.domains

    if context.kind == TransitionKind.BOOTSTRAP_INIT:
        schema_version = str(payload.get("schema_version", "f01"))
        next_meta = replace(
            base.meta,
            schema_version=schema_version,
            initialized_at=context.request_obj.requested_at,
        )
        next_runtime = replace(base.runtime, lifecycle=Lifecycle.INITIALIZED)
    elif context.kind in {
        TransitionKind.INGEST_EXTERNAL_EVENT,
        TransitionKind.APPLY_INTERNAL_EVENT,
    }:
        turn_id = str(payload.get("turn_id", f"turn:{context.transition_id}"))
        next_turn = replace(
            base.turn,
            current_turn_id=turn_id,
            last_event_ref=event_id,
        )
        if context.domain_update is not None:
            next_domains = _apply_runtime_domain_update(base.domains, context.domain_update)

    next_runtime = replace(
        next_runtime,
        revision=base.runtime.revision + 1,
        last_transition_id=context.transition_id,
        last_event_id=event_id,
    )

    event = build_event_record(
        event_id=event_id,
        transition_id=context.transition_id,
        transition_kind=context.kind,
        payload=payload,
        created_at=_now_iso(),
    )
    next_trace = replace(base.trace, events=base.trace.events + (event,))
    context.candidate_state = RuntimeState(
        meta=next_meta,
        runtime=next_runtime,
        turn=next_turn,
        failures=next_failures,
        trace=next_trace,
        domains=next_domains,
    )
    context.accepted = True
    context.emitted_event = event
    context.event_id = event_id


def build_state_delta(context: _TransitionContext) -> None:
    before = context.state_obj or create_empty_state()
    after = context.candidate_state or before
    changed_fields = _changed_fields(before, after)
    context.delta = StateDelta(
        changed_fields=changed_fields,
        before_revision=before.runtime.revision,
        after_revision=after.runtime.revision,
        transition_id=context.transition_id or _new_transition_id(),
        event_id=context.event_id or _new_event_id(),
    )


def build_provenance_record_stage(context: _TransitionContext) -> None:
    if context.state_obj is None:
        context.state_obj = create_empty_state()
    if context.candidate_state is None:
        context.candidate_state = context.state_obj

    status = ProvenanceStatus.APPLIED if context.accepted else ProvenanceStatus.REJECTED
    writer = _resolve_writer(context)
    delta_to_persist = context.delta or StateDelta(
        changed_fields=(),
        before_revision=context.state_obj.runtime.revision,
        after_revision=context.candidate_state.runtime.revision,
        transition_id=context.transition_id,
        event_id=context.event_id or _new_event_id(),
    )
    if "trace.transitions" not in delta_to_persist.changed_fields:
        delta_to_persist = replace(
            delta_to_persist,
            changed_fields=delta_to_persist.changed_fields + ("trace.transitions",),
        )
    context.delta = delta_to_persist

    provenance = build_provenance_record(
        transition_id=context.transition_id,
        writer=writer,
        transition_kind=context.kind,
        event_id=context.event_id or _new_event_id(),
        cause_chain=context.cause_chain or ("direct",),
        attempted_paths=context.attempted_paths,
        actual_delta=delta_to_persist,
        authority=context.authority,
        status=status,
        failure=context.failure,
        recorded_at=_now_iso(),
    )
    trace_with_provenance = replace(
        context.candidate_state.trace,
        transitions=context.candidate_state.trace.transitions + (provenance,),
    )
    context.candidate_state = replace(context.candidate_state, trace=trace_with_provenance)
    context.provenance = provenance


def enforce_invariants(context: _TransitionContext) -> None:
    if context.candidate_state is None or context.delta is None or context.provenance is None:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="transition result cannot be built without state/delta/provenance",
        )
        return

    if context.accepted and context.provenance.status != ProvenanceStatus.APPLIED:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="accepted transitions must carry APPLIED provenance",
        )
    if context.delta.changed_fields and context.emitted_event is None:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="eventless state changes are forbidden",
        )
    if context.provenance.actual_delta != context.delta:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="persisted provenance delta must match transition delta",
        )
    allowed_fields = allowed_changed_paths(
        transition_kind=context.kind,
        writer=_resolve_writer(context),
        accepted=context.accepted,
    )
    changed_fields = set(context.delta.changed_fields)
    if not changed_fields.issubset(allowed_fields):
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="state delta touched forbidden field paths",
        )
    if context.candidate_state.runtime.last_transition_id != context.transition_id:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="runtime.last_transition_id mismatch",
        )
    if context.candidate_state.runtime.last_event_id != context.event_id:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="enforce_invariants",
            message="runtime.last_event_id mismatch",
        )


def emit_failure_if_needed(context: _TransitionContext) -> None:
    if context.failure is None:
        return
    _apply_rejected_outcome(context)
    build_state_delta(context)
    build_provenance_record_stage(context)


def return_transition_result(context: _TransitionContext) -> TransitionResult:
    if context.state_obj is None:
        context.state_obj = create_empty_state()
    missing_components = (
        context.candidate_state is None
        or context.delta is None
        or context.provenance is None
        or context.emitted_event is None
    )
    if missing_components:
        _set_failure(
            context,
            code=FailureCode.INVARIANT_VIOLATION,
            stage="return_transition_result",
            message="transition result assembly incomplete",
        )
        emit_failure_if_needed(context)
    if (
        context.candidate_state is None
        or context.delta is None
        or context.provenance is None
        or context.emitted_event is None
    ):
        raise RuntimeError("transition pipeline failed to produce a complete TransitionResult")

    return TransitionResult(
        accepted=context.accepted,
        state=context.candidate_state,
        delta=context.delta,
        provenance=context.provenance,
        authority=context.authority,
        emitted_event=context.emitted_event,
        failure=context.failure,
    )


def _apply_rejected_outcome(context: _TransitionContext) -> None:
    base = context.state_obj or create_empty_state()
    failure = context.failure or build_failure_marker(
        code=FailureCode.INVARIANT_VIOLATION,
        stage="emit_failure_if_needed",
        message="rejected transition without explicit failure marker",
        transition_id=context.transition_id or _new_transition_id(),
    )
    event_id = context.event_id or _new_event_id()
    event = build_event_record(
        event_id=event_id,
        transition_id=context.transition_id,
        transition_kind=TransitionKind.REJECTED_TRANSITION,
        payload={"failure_code": failure.code.value, "stage": failure.stage},
        created_at=_now_iso(),
    )
    next_runtime = replace(
        base.runtime,
        revision=base.runtime.revision + 1,
        last_transition_id=context.transition_id,
        last_event_id=event_id,
    )
    next_failures = replace(base.failures, current=failure)
    next_trace = replace(base.trace, events=base.trace.events + (event,))
    context.candidate_state = replace(
        base, runtime=next_runtime, failures=next_failures, trace=next_trace
    )
    context.accepted = False
    context.emitted_event = event
    context.event_id = event_id
    context.failure = failure


def _set_failure(
    context: _TransitionContext, *, code: FailureCode, stage: str, message: str
) -> None:
    if context.failure is not None:
        return
    context.failure = build_failure_marker(
        code=code,
        stage=stage,
        message=message,
        transition_id=context.transition_id or _new_transition_id(),
    )


def _resolve_writer(context: _TransitionContext) -> WriterIdentity:
    if context.request_obj is not None:
        return context.request_obj.writer
    return WriterIdentity.UNKNOWN


def _flatten_state(state: RuntimeState) -> dict[str, object]:
    return {
        "meta.schema_version": state.meta.schema_version,
        "meta.initialized_at": state.meta.initialized_at,
        "runtime.lifecycle": state.runtime.lifecycle,
        "runtime.revision": state.runtime.revision,
        "runtime.last_transition_id": state.runtime.last_transition_id,
        "runtime.last_event_id": state.runtime.last_event_id,
        "turn.current_turn_id": state.turn.current_turn_id,
        "turn.last_event_ref": state.turn.last_event_ref,
        "failures.current": state.failures.current,
        "trace.transitions": state.trace.transitions,
        "trace.events": state.trace.events,
        "domains.regulation": state.domains.regulation,
        "domains.continuity": state.domains.continuity,
        "domains.validity": state.domains.validity,
        "domains.self_boundary": state.domains.self_boundary,
        "domains.world": state.domains.world,
        "domains.memory_economics": state.domains.memory_economics,
    }


def _changed_fields(before: RuntimeState, after: RuntimeState) -> tuple[str, ...]:
    before_flat = _flatten_state(before)
    after_flat = _flatten_state(after)
    changed = [path for path, old in before_flat.items() if old != after_flat[path]]
    return tuple(sorted(changed))


def _new_transition_id() -> str:
    return f"tr-{uuid4().hex}"


def _new_event_id() -> str:
    return f"ev-{uuid4().hex}"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _apply_runtime_domain_update(
    domains: RuntimeDomainsState,
    domain_update: RuntimeDomainUpdate,
) -> RuntimeDomainsState:
    updated = domains
    if domain_update.regulation is not None:
        updated = replace(updated, regulation=domain_update.regulation)
    if domain_update.continuity is not None:
        updated = replace(updated, continuity=domain_update.continuity)
    if domain_update.validity is not None:
        updated = replace(updated, validity=domain_update.validity)
    return updated


def _merge_authority_decisions(
    base: AuthorityDecision,
    overlay: AuthorityDecision,
) -> AuthorityDecision:
    denied = tuple(sorted(set(base.denied_paths).union(overlay.denied_paths)))
    allowed = base.allowed and overlay.allowed
    if allowed:
        reason = "writer authorized"
    else:
        reasons = [base.reason, overlay.reason]
        reason = "; ".join(dict.fromkeys(part for part in reasons if part))
    return AuthorityDecision(allowed=allowed, denied_paths=denied, reason=reason)
