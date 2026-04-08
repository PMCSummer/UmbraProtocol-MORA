from __future__ import annotations
from dataclasses import replace

from substrate.contracts import (
    ContinuityDomainState,
    DomainWriteClaim,
    DomainWriteRoute,
    DomainWriterPhase,
    FailureCode,
    RegulationDomainState,
    RuntimeDomainUpdate,
    TransitionKind,
    TransitionRequest,
    ValidityDomainState,
    WriterIdentity,
)
from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    build_subject_tick_runtime_domain_update,
    build_subject_tick_runtime_route_auth_context,
    execute_subject_tick,
)
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-runtime-domain-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-08T00:00:00+00:00",
            event_id="ev-runtime-domain-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _seed_rt01_domain_payload(*, unresolved: bool = False):
    result = execute_subject_tick(
        SubjectTickInput(
            case_id="runtime-domain-auth-seed",
            energy=14.0 if unresolved else 66.0,
            cognitive=95.0 if unresolved else 44.0,
            safety=34.0 if unresolved else 74.0,
            unresolved_preference=unresolved,
        ),
        SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",) if unresolved else (),
        ),
    )
    domain_update = build_subject_tick_runtime_domain_update(result)
    route_auth = build_subject_tick_runtime_route_auth_context(
        result=result,
        domain_update=domain_update,
    )
    return result, domain_update, route_auth


def test_shared_runtime_domain_paths_materialize_with_typed_defaults() -> None:
    state = create_empty_state()
    assert state.domains.regulation.pressure_level is None
    assert state.domains.continuity.c04_mode_claim is None
    assert state.domains.validity.c05_validity_action is None
    assert state.domains.validity.selective_scope_targets == ()
    assert state.domains.self_boundary.status == "not_materialized"
    assert state.domains.world.status == "not_materialized"
    assert state.domains.memory_economics.status == "not_materialized"


def test_lawful_domain_writer_claims_can_update_allowed_shared_segment() -> None:
    state = _bootstrapped_state()
    _, update, route_auth = _seed_rt01_domain_payload(unresolved=True)
    result = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-lawful",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "runtime-domain"),
            requested_at="2026-04-08T00:01:00+00:00",
            event_id="ev-domain-lawful",
            event_payload={
                "turn_id": "turn-domain-lawful",
                "runtime_domain_update": update,
                "runtime_route_auth": route_auth,
            },
        ),
        state,
    )
    assert result.accepted is True
    assert result.state.domains.regulation.pressure_level is not None
    assert result.state.domains.regulation.updated_by_phase == "R04"
    assert "domains.regulation" in result.delta.changed_fields
    assert "domains.regulation" in result.provenance.attempted_paths


def test_unlawful_writer_cannot_mutate_runtime_domains() -> None:
    state = _bootstrapped_state()
    _, update, route_auth = _seed_rt01_domain_payload(unresolved=True)
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-denied-observer",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.OBSERVER,
            cause_chain=("test", "runtime-domain"),
            requested_at="2026-04-08T00:02:00+00:00",
            event_id="ev-domain-denied-observer",
            event_payload={
                "turn_id": "turn-domain-denied",
                "runtime_domain_update": update,
                "runtime_route_auth": route_auth,
            },
        ),
        state,
    )
    assert denied.accepted is False
    assert denied.failure is not None
    assert denied.failure.code == FailureCode.AUTHORITY_DENIED
    assert "domains.validity" in denied.authority.denied_paths
    assert denied.state.domains.validity.c05_validity_action is None


def test_wrong_transition_kind_blocks_domain_update_even_with_transition_engine_writer() -> None:
    state = _bootstrapped_state()
    _, update, route_auth = _seed_rt01_domain_payload(unresolved=False)
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-wrong-kind",
            transition_kind=TransitionKind.INGEST_EXTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "runtime-domain"),
            requested_at="2026-04-08T00:03:00+00:00",
            event_id="ev-domain-wrong-kind",
            event_payload={
                "turn_id": "turn-domain-wrong-kind",
                "runtime_domain_update": update,
                "runtime_route_auth": route_auth,
            },
        ),
        state,
    )
    assert denied.accepted is False
    assert denied.failure is not None
    assert denied.failure.code == FailureCode.AUTHORITY_DENIED
    assert "domains.continuity" in denied.authority.denied_paths
    assert denied.state.domains.continuity.c04_mode_claim is None


def test_foreign_domain_path_write_claim_is_blocked_by_phase_matrix() -> None:
    state = _bootstrapped_state()
    result, _, _ = _seed_rt01_domain_payload(unresolved=False)
    update = RuntimeDomainUpdate(
        continuity=ContinuityDomainState(
            c04_mode_claim="continue_stream",
            c04_selected_mode="hold_current_stream",
            mode_legitimacy=True,
            endogenous_tick_allowed=True,
            arbitration_confidence=0.8,
            source_state_ref="c04@3",
            updated_by_phase="C04",
            last_update_provenance="test.c04",
        ),
        write_claims=(
            DomainWriteClaim(
                phase=DomainWriterPhase.C05,
                domain_path="domains.continuity",
                transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
                route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
                checkpoint_id="rt01.c05_legality_checkpoint",
                reason="adversarial foreign path claim",
            ),
        ),
    )
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-foreign-path",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "runtime-domain"),
            requested_at="2026-04-08T00:04:00+00:00",
            event_id="ev-domain-foreign-path",
            event_payload={
                "turn_id": "turn-domain-foreign-path",
                "runtime_domain_update": update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=result,
                    domain_update=update,
                ),
            },
        ),
        state,
    )
    assert denied.accepted is False
    assert denied.failure is not None
    assert denied.failure.code == FailureCode.AUTHORITY_DENIED
    assert "domains.continuity" in denied.authority.denied_paths
    assert "cannot write domains.continuity" in denied.authority.reason
    assert denied.state.domains.continuity.c04_mode_claim is None


def test_f01_authority_boundary_cannot_originate_domain_authority_write_claims() -> None:
    state = _bootstrapped_state()
    update = RuntimeDomainUpdate(
        regulation=RegulationDomainState(
            pressure_level=0.5,
            escalation_stage="elevated",
            override_scope="narrow",
            no_strong_override_claim=True,
            gate_accepted=False,
            source_state_ref="regulation-step-7",
            updated_by_phase="F01",
            last_update_provenance="test.f01",
        ),
        write_claims=(
            DomainWriteClaim(
                phase=DomainWriterPhase.F01,
                domain_path="domains.regulation",
                transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
                route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
                checkpoint_id="rt01.f01_invalid_domain_claim",
                reason="adversarial f01 authority escalation",
            ),
        ),
    )
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-f01-forbidden",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "runtime-domain"),
            requested_at="2026-04-08T00:05:00+00:00",
            event_id="ev-domain-f01-forbidden",
            event_payload={"turn_id": "turn-domain-f01-forbidden", "runtime_domain_update": update},
        ),
        state,
    )
    assert denied.accepted is False
    assert denied.failure is not None
    assert denied.failure.code == FailureCode.AUTHORITY_DENIED
    assert "domains.regulation" in denied.authority.denied_paths
    assert denied.state.domains.regulation.pressure_level is None


def test_external_rt01_route_token_spoof_fails_without_lawful_route_auth_context() -> None:
    state = _bootstrapped_state()
    _, update, _ = _seed_rt01_domain_payload(unresolved=True)
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-rt01-route-spoof",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "runtime-domain", "spoof"),
            requested_at="2026-04-08T00:06:00+00:00",
            event_id="ev-domain-rt01-route-spoof",
            event_payload={
                "turn_id": "turn-domain-rt01-route-spoof",
                "runtime_domain_update": update,
            },
        ),
        state,
    )
    assert denied.accepted is False
    assert denied.failure is not None
    assert denied.failure.code == FailureCode.AUTHORITY_DENIED
    assert "domains.regulation" in denied.authority.denied_paths
    assert "RuntimeRouteAuthContext" in denied.authority.reason


def test_foreign_transition_cannot_gain_rt01_domain_authority_with_forged_route_auth() -> None:
    state = _bootstrapped_state()
    _, update, _ = _seed_rt01_domain_payload(unresolved=True)
    forged_route_auth = build_subject_tick_runtime_route_auth_context(
        result=execute_subject_tick(
            SubjectTickInput(
                case_id="runtime-domain-auth-forged",
                energy=66.0,
                cognitive=44.0,
                safety=74.0,
                unresolved_preference=False,
            )
        ),
        domain_update=update,
    )
    forged_route_auth = replace(forged_route_auth, origin_phase=DomainWriterPhase.C04)
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-domain-rt01-forged-origin",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "runtime-domain", "forged-origin"),
            requested_at="2026-04-08T00:06:30+00:00",
            event_id="ev-domain-rt01-forged-origin",
            event_payload={
                "turn_id": "turn-domain-rt01-forged-origin",
                "runtime_domain_update": update,
                "runtime_route_auth": forged_route_auth,
            },
        ),
        state,
    )
    assert denied.accepted is False
    assert denied.failure is not None
    assert denied.failure.code == FailureCode.AUTHORITY_DENIED
    assert "domains.regulation" in denied.authority.denied_paths
    assert "origin_phase must be RT01" in denied.authority.reason
