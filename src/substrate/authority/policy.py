from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from substrate.contracts import (
    AuthorityDecision,
    DomainWriteRoute,
    DomainWriterPhase,
    RuntimeDomainUpdate,
    RuntimeRouteAuthContext,
    TransitionKind,
    WriterIdentity,
)


DOMAIN_PATH_REGULATION = "domains.regulation"
DOMAIN_PATH_CONTINUITY = "domains.continuity"
DOMAIN_PATH_VALIDITY = "domains.validity"
DOMAIN_PATH_SELF_BOUNDARY = "domains.self_boundary"
DOMAIN_PATH_WORLD = "domains.world"
DOMAIN_PATH_MEMORY_ECONOMICS = "domains.memory_economics"

DOMAIN_WRITABLE_PATHS: frozenset[str] = frozenset(
    {
        DOMAIN_PATH_REGULATION,
        DOMAIN_PATH_CONTINUITY,
        DOMAIN_PATH_VALIDITY,
    }
)

DOMAIN_PHASE_ALLOWED_PATHS: dict[DomainWriterPhase, frozenset[str]] = {
    DomainWriterPhase.R04: frozenset({DOMAIN_PATH_REGULATION}),
    DomainWriterPhase.C04: frozenset({DOMAIN_PATH_CONTINUITY}),
    DomainWriterPhase.C05: frozenset({DOMAIN_PATH_VALIDITY}),
    DomainWriterPhase.RT01: frozenset({DOMAIN_PATH_CONTINUITY}),
    DomainWriterPhase.F01: frozenset(),
    DomainWriterPhase.UNKNOWN: frozenset(),
}

DOMAIN_PHASE_ALLOWED_ROUTES: dict[DomainWriterPhase, frozenset[DomainWriteRoute]] = {
    DomainWriterPhase.R04: frozenset({DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR}),
    DomainWriterPhase.C04: frozenset({DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR}),
    DomainWriterPhase.C05: frozenset({DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR}),
    DomainWriterPhase.RT01: frozenset({DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR}),
    DomainWriterPhase.F01: frozenset(),
    DomainWriterPhase.UNKNOWN: frozenset(),
}

DOMAIN_PHASE_ALLOWED_TRANSITIONS: dict[DomainWriterPhase, frozenset[TransitionKind]] = {
    DomainWriterPhase.R04: frozenset({TransitionKind.APPLY_INTERNAL_EVENT}),
    DomainWriterPhase.C04: frozenset({TransitionKind.APPLY_INTERNAL_EVENT}),
    DomainWriterPhase.C05: frozenset({TransitionKind.APPLY_INTERNAL_EVENT}),
    DomainWriterPhase.RT01: frozenset({TransitionKind.APPLY_INTERNAL_EVENT}),
    DomainWriterPhase.F01: frozenset(),
    DomainWriterPhase.UNKNOWN: frozenset(),
}


@dataclass(frozen=True, slots=True)
class _Rt01RouteAuthNonceRecord:
    route: DomainWriteRoute
    origin_phase: DomainWriterPhase
    transition_kind: TransitionKind
    tick_id: str
    authorized_domain_paths: tuple[str, ...]
    checkpoint_ids: tuple[str, ...]
    origin_contract: str


_RT01_ROUTE_AUTH_NONCE_REGISTRY: dict[str, _Rt01RouteAuthNonceRecord] = {}


WRITER_ALLOWED_PATHS: dict[WriterIdentity, frozenset[str]] = {
    WriterIdentity.BOOTSTRAPPER: frozenset(
        {
            "meta.schema_version",
            "meta.initialized_at",
            "runtime.lifecycle",
            "runtime.revision",
        }
    ),
    WriterIdentity.TRANSITION_ENGINE: frozenset(
        {
            "runtime.revision",
            "runtime.last_transition_id",
            "runtime.last_event_id",
            "turn.current_turn_id",
            "turn.last_event_ref",
            "failures.current",
            "trace.transitions",
            "trace.events",
            DOMAIN_PATH_REGULATION,
            DOMAIN_PATH_CONTINUITY,
            DOMAIN_PATH_VALIDITY,
        }
    ),
    WriterIdentity.OBSERVER: frozenset(),
    WriterIdentity.UNKNOWN: frozenset(),
}


ENGINE_INTERNAL_WRITES: frozenset[str] = frozenset(
    {
        "runtime.revision",
        "runtime.last_transition_id",
        "runtime.last_event_id",
        "failures.current",
        "trace.transitions",
        "trace.events",
    }
)


def writer_transition_paths(transition_kind: TransitionKind) -> frozenset[str]:
    if transition_kind == TransitionKind.BOOTSTRAP_INIT:
        return frozenset({"meta.schema_version", "meta.initialized_at", "runtime.lifecycle"})
    if transition_kind in {
        TransitionKind.INGEST_EXTERNAL_EVENT,
        TransitionKind.APPLY_INTERNAL_EVENT,
    }:
        return frozenset({"turn.current_turn_id", "turn.last_event_ref"})
    return frozenset()


def runtime_domain_paths_from_update(domain_update: RuntimeDomainUpdate | None) -> frozenset[str]:
    if domain_update is None:
        return frozenset()
    claimed = {claim.domain_path for claim in domain_update.write_claims}
    return frozenset(claimed)


def check_domain_writer_discipline(
    *,
    domain_update: RuntimeDomainUpdate | None,
    transition_kind: TransitionKind,
) -> AuthorityDecision:
    if domain_update is None:
        return AuthorityDecision(allowed=True, denied_paths=(), reason="no domain write claims")

    denied: set[str] = set()
    reasons: list[str] = []
    claimed_paths = {claim.domain_path for claim in domain_update.write_claims}
    updated_paths = set(_updated_runtime_domain_paths(domain_update))

    if updated_paths != claimed_paths:
        denied.update(sorted(updated_paths.symmetric_difference(claimed_paths)))
        reasons.append("domain updates must be fully claimed and claims must map to concrete updates")

    for path in updated_paths:
        if path not in DOMAIN_WRITABLE_PATHS:
            denied.add(path)
            reasons.append("attempted writes outside bounded writable runtime domains")

    for claim in domain_update.write_claims:
        allowed_paths = DOMAIN_PHASE_ALLOWED_PATHS.get(claim.phase, frozenset())
        allowed_routes = DOMAIN_PHASE_ALLOWED_ROUTES.get(claim.phase, frozenset())
        allowed_transitions = DOMAIN_PHASE_ALLOWED_TRANSITIONS.get(claim.phase, frozenset())
        if claim.domain_path not in allowed_paths:
            denied.add(claim.domain_path)
            reasons.append(f"{claim.phase.value} cannot write {claim.domain_path}")
        if claim.route not in allowed_routes:
            denied.add(claim.domain_path)
            reasons.append(f"{claim.phase.value} cannot use route {claim.route.value}")
        if transition_kind not in allowed_transitions:
            denied.add(claim.domain_path)
            reasons.append(f"{claim.phase.value} cannot write during {transition_kind.value}")
        if claim.transition_kind != transition_kind:
            denied.add(claim.domain_path)
            reasons.append(
                f"claim transition_kind {claim.transition_kind.value} mismatches actual {transition_kind.value}"
            )

    if denied:
        return AuthorityDecision(
            allowed=False,
            denied_paths=tuple(sorted(denied)),
            reason="; ".join(dict.fromkeys(reasons)),
        )
    return AuthorityDecision(allowed=True, denied_paths=(), reason="domain writer discipline satisfied")


def issue_rt01_route_auth_nonce(
    *,
    route: DomainWriteRoute,
    origin_phase: DomainWriterPhase,
    transition_kind: TransitionKind,
    tick_id: str,
    authorized_domain_paths: tuple[str, ...],
    checkpoint_ids: tuple[str, ...],
    origin_contract: str,
) -> str:
    nonce = f"rt01-auth-{uuid4().hex}"
    _RT01_ROUTE_AUTH_NONCE_REGISTRY[nonce] = _Rt01RouteAuthNonceRecord(
        route=route,
        origin_phase=origin_phase,
        transition_kind=transition_kind,
        tick_id=tick_id,
        authorized_domain_paths=tuple(sorted(set(authorized_domain_paths))),
        checkpoint_ids=tuple(sorted(set(checkpoint_ids))),
        origin_contract=origin_contract,
    )
    return nonce


def check_domain_route_authenticity(
    *,
    domain_update: RuntimeDomainUpdate | None,
    route_auth: RuntimeRouteAuthContext | None,
    transition_kind: TransitionKind,
) -> AuthorityDecision:
    if domain_update is None:
        return AuthorityDecision(allowed=True, denied_paths=(), reason="no domain route auth required")

    rt01_claims = tuple(
        claim
        for claim in domain_update.write_claims
        if claim.route == DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR
    )
    if not rt01_claims:
        return AuthorityDecision(allowed=True, denied_paths=(), reason="no rt01 route claims")

    denied_paths = tuple(sorted({claim.domain_path for claim in rt01_claims}))
    reasons: list[str] = []
    if not isinstance(route_auth, RuntimeRouteAuthContext):
        reasons.append("rt01 route claims require RuntimeRouteAuthContext")
    else:
        if route_auth.route != DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR:
            reasons.append("runtime route auth route must be rt01_subject_tick_contour")
        if route_auth.origin_phase != DomainWriterPhase.RT01:
            reasons.append("runtime route auth origin_phase must be RT01")
        if route_auth.transition_kind != transition_kind:
            reasons.append(
                f"runtime route auth transition_kind {route_auth.transition_kind.value} mismatches actual {transition_kind.value}"
            )
        if route_auth.origin_contract != "subject_tick.runtime_contour_from_r_to_c05":
            reasons.append("runtime route auth origin_contract mismatch")
        if not route_auth.tick_id.strip():
            reasons.append("runtime route auth tick_id must be non-empty")
        claimed_paths = tuple(sorted({claim.domain_path for claim in rt01_claims}))
        if tuple(sorted(set(route_auth.authorized_domain_paths))) != claimed_paths:
            reasons.append("runtime route auth authorized_domain_paths mismatch claimed paths")
        required_checkpoints = {claim.checkpoint_id for claim in rt01_claims}
        if not required_checkpoints.issubset(set(route_auth.checkpoint_ids)):
            reasons.append("runtime route auth checkpoint_ids missing claimed checkpoints")
        if not _consume_rt01_route_auth_nonce(route_auth):
            reasons.append("runtime route auth nonce is missing, stale, or mismatched")

    if reasons:
        return AuthorityDecision(
            allowed=False,
            denied_paths=denied_paths,
            reason="; ".join(dict.fromkeys(reasons)),
        )
    return AuthorityDecision(
        allowed=True,
        denied_paths=(),
        reason="domain route authenticity satisfied",
    )


def check_authority(
    writer: WriterIdentity, requested_paths: frozenset[str]
) -> AuthorityDecision:
    allowed_paths = WRITER_ALLOWED_PATHS.get(writer, frozenset())
    denied_paths = tuple(sorted(requested_paths - allowed_paths))
    if denied_paths:
        return AuthorityDecision(
            allowed=False,
            denied_paths=denied_paths,
            reason="writer attempted forbidden field writes",
        )
    return AuthorityDecision(allowed=True, denied_paths=(), reason="writer authorized")


def allowed_changed_paths(
    *,
    transition_kind: TransitionKind,
    writer: WriterIdentity,
    accepted: bool,
) -> frozenset[str]:
    base = set(ENGINE_INTERNAL_WRITES)
    if accepted:
        base |= WRITER_ALLOWED_PATHS.get(writer, frozenset())
        base |= writer_transition_paths(transition_kind)
    return frozenset(base)


def _updated_runtime_domain_paths(domain_update: RuntimeDomainUpdate) -> tuple[str, ...]:
    paths: list[str] = []
    if domain_update.regulation is not None:
        paths.append(DOMAIN_PATH_REGULATION)
    if domain_update.continuity is not None:
        paths.append(DOMAIN_PATH_CONTINUITY)
    if domain_update.validity is not None:
        paths.append(DOMAIN_PATH_VALIDITY)
    return tuple(paths)


def _consume_rt01_route_auth_nonce(route_auth: RuntimeRouteAuthContext) -> bool:
    expected = _RT01_ROUTE_AUTH_NONCE_REGISTRY.pop(route_auth.auth_nonce, None)
    if expected is None:
        return False
    return expected == _Rt01RouteAuthNonceRecord(
        route=route_auth.route,
        origin_phase=route_auth.origin_phase,
        transition_kind=route_auth.transition_kind,
        tick_id=route_auth.tick_id,
        authorized_domain_paths=tuple(sorted(set(route_auth.authorized_domain_paths))),
        checkpoint_ids=tuple(sorted(set(route_auth.checkpoint_ids))),
        origin_contract=route_auth.origin_contract,
    )
