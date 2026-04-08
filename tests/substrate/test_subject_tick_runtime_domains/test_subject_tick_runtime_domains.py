from __future__ import annotations

from dataclasses import replace

from substrate.contracts import (
    DomainWriteClaim,
    DomainWriteRoute,
    DomainWriterPhase,
    RuntimeDomainUpdate,
    TransitionKind,
    TransitionRequest,
    WriterIdentity,
)
from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    build_subject_tick_runtime_domain_update,
    build_subject_tick_runtime_route_auth_context,
    choose_runtime_execution_outcome_from_runtime_state,
    derive_subject_tick_runtime_domain_contract_view,
    execute_subject_tick,
    persist_subject_tick_result_via_f01,
)
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domains-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-08T01:00:00+00:00",
            event_id="ev-rt-domains-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _tick(case_id: str, *, unresolved: bool = False, context: SubjectTickContext | None = None):
    return execute_subject_tick(
        SubjectTickInput(
            case_id=case_id,
            energy=14.0 if unresolved else 66.0,
            cognitive=95.0 if unresolved else 44.0,
            safety=34.0 if unresolved else 74.0,
            unresolved_preference=unresolved,
        ),
        context=context,
    )


def test_subject_tick_persistence_propagates_r04_c04_c05_authority_surfaces_into_shared_state() -> None:
    state = _bootstrapped_state()
    tick = _tick(
        "rt-domain-propagation",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    persisted = persist_subject_tick_result_via_f01(
        result=tick,
        runtime_state=state,
        transition_id="tr-rt-domain-propagation",
        requested_at="2026-04-08T01:01:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.domains.regulation.updated_by_phase == "R04"
    assert persisted.state.domains.continuity.updated_by_phase == "C04"
    assert persisted.state.domains.validity.updated_by_phase == "C05"
    assert persisted.state.domains.continuity.c04_mode_claim == tick.state.c04_execution_mode_claim
    assert persisted.state.domains.validity.c05_action_claim == tick.state.c05_execution_action_claim
    assert "domains.regulation" in persisted.delta.changed_fields
    assert "domains.continuity" in persisted.delta.changed_fields
    assert "domains.validity" in persisted.delta.changed_fields


def test_c04_shared_continuity_path_is_load_bearing_for_following_runtime_tick() -> None:
    seed = _tick("rt-domain-c04-seed", unresolved=False)
    domain_update = build_subject_tick_runtime_domain_update(seed)
    route_auth_with = build_subject_tick_runtime_route_auth_context(
        result=seed,
        domain_update=domain_update,
    )
    with_c04 = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-c04-with",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "c04-domain"),
            requested_at="2026-04-08T01:02:00+00:00",
            event_id="ev-rt-domain-c04-with",
            event_payload={
                "turn_id": "turn-rt-domain-c04-with",
                "runtime_domain_update": domain_update,
                "runtime_route_auth": route_auth_with,
            },
        ),
        _bootstrapped_state(),
    )
    without_c04_update = replace(
        domain_update,
        continuity=None,
        write_claims=tuple(
            claim for claim in domain_update.write_claims if claim.domain_path != "domains.continuity"
        ),
    )
    without_c04 = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-c04-without",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "c04-domain"),
            requested_at="2026-04-08T01:02:30+00:00",
            event_id="ev-rt-domain-c04-without",
            event_payload={
                "turn_id": "turn-rt-domain-c04-without",
                "runtime_domain_update": without_c04_update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=seed,
                    domain_update=without_c04_update,
                ),
            },
        ),
        _bootstrapped_state(),
    )
    assert with_c04.accepted is True
    assert without_c04.accepted is True

    with_shared = _tick(
        "rt-domain-c04-follow-up-with",
        unresolved=False,
        context=SubjectTickContext(prior_runtime_state=with_c04.state),
    )
    without_shared = _tick(
        "rt-domain-c04-follow-up-without",
        unresolved=False,
        context=SubjectTickContext(prior_runtime_state=without_c04.state),
    )
    assert with_shared.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert without_shared.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_c05_shared_validity_path_is_load_bearing_for_following_runtime_tick() -> None:
    restricted = _tick(
        "rt-domain-c05-seed",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    update = build_subject_tick_runtime_domain_update(restricted)
    with_validity = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-c05-with",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "c05-domain"),
            requested_at="2026-04-08T01:03:00+00:00",
            event_id="ev-rt-domain-c05-with",
            event_payload={
                "turn_id": "turn-rt-domain-c05-with",
                "runtime_domain_update": update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=restricted,
                    domain_update=update,
                ),
            },
        ),
        _bootstrapped_state(),
    )
    without_validity_update = replace(
        update,
        validity=None,
        write_claims=tuple(
            claim for claim in update.write_claims if claim.domain_path != "domains.validity"
        ),
    )
    without_validity = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-c05-without",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "c05-domain"),
            requested_at="2026-04-08T01:03:30+00:00",
            event_id="ev-rt-domain-c05-without",
            event_payload={
                "turn_id": "turn-rt-domain-c05-without",
                "runtime_domain_update": without_validity_update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=restricted,
                    domain_update=without_validity_update,
                ),
            },
        ),
        _bootstrapped_state(),
    )
    with_shared = _tick(
        "rt-domain-c05-follow-up-with",
        unresolved=False,
        context=SubjectTickContext(prior_runtime_state=with_validity.state),
    )
    without_shared = _tick(
        "rt-domain-c05-follow-up-without",
        unresolved=False,
        context=SubjectTickContext(prior_runtime_state=without_validity.state),
    )
    assert with_shared.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert without_shared.state.final_execution_outcome != SubjectTickOutcome.REVALIDATE


def test_r04_shared_regulation_path_can_enforce_runtime_detour_under_high_override_scope() -> None:
    seed = _tick("rt-domain-r04-seed", unresolved=False)
    base_update = build_subject_tick_runtime_domain_update(seed)
    escalated_update = replace(
        base_update,
        regulation=replace(
            base_update.regulation,
            override_scope="emergency",
            no_strong_override_claim=False,
            pressure_level=0.98,
            escalation_stage="critical",
        ),
        write_claims=tuple(
            DomainWriteClaim(
                phase=claim.phase,
                domain_path=claim.domain_path,
                transition_kind=claim.transition_kind,
                route=claim.route,
                checkpoint_id=claim.checkpoint_id,
                reason=claim.reason,
            )
            for claim in base_update.write_claims
        ),
    )
    persisted = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-r04-high",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "r04-domain"),
            requested_at="2026-04-08T01:04:00+00:00",
            event_id="ev-rt-domain-r04-high",
            event_payload={
                "turn_id": "turn-rt-domain-r04-high",
                "runtime_domain_update": escalated_update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=seed,
                    domain_update=escalated_update,
                ),
            },
        ),
        _bootstrapped_state(),
    )
    result = _tick(
        "rt-domain-r04-follow-up",
        unresolved=False,
        context=SubjectTickContext(prior_runtime_state=persisted.state),
    )
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.shared_runtime_domain_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in result.state.execution_checkpoints
    )


def test_adversarial_shortcut_snapshot_only_without_runtime_domain_update_does_not_change_shared_authority_surface() -> None:
    baseline_tick = _tick("rt-domain-snapshot-baseline", unresolved=False)
    baseline_state = persist_subject_tick_result_via_f01(
        result=baseline_tick,
        runtime_state=_bootstrapped_state(),
        transition_id="tr-rt-domain-snapshot-baseline",
        requested_at="2026-04-08T01:05:00+00:00",
    ).state
    restricted_tick = _tick(
        "rt-domain-snapshot-restricted",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    telemetry_only = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-snapshot-only",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "snapshot-only"),
            requested_at="2026-04-08T01:05:30+00:00",
            event_id="ev-rt-domain-snapshot-only",
            event_payload={
                "turn_id": "turn-rt-domain-snapshot-only",
                "subject_tick_snapshot": {
                    "state": {
                        "c05_execution_action_claim": restricted_tick.state.c05_execution_action_claim,
                        "c04_execution_mode_claim": restricted_tick.state.c04_execution_mode_claim,
                    }
                },
            },
        ),
        baseline_state,
    )
    assert telemetry_only.accepted is True
    before_view = derive_subject_tick_runtime_domain_contract_view(baseline_state)
    after_view = derive_subject_tick_runtime_domain_contract_view(telemetry_only.state)
    assert before_view.source_of_truth_surface == "runtime_state.domains"
    assert after_view.source_of_truth_surface == "runtime_state.domains"
    assert before_view.packet_snapshot_precedence_blocked is True
    assert after_view.packet_snapshot_precedence_blocked is True
    assert before_view.recommended_outcome == "continue"
    assert after_view.recommended_outcome == "continue"
    assert choose_runtime_execution_outcome_from_runtime_state(telemetry_only.state) == "continue"


def test_phase_claim_matrix_blocks_writer_mutation_of_foreign_domain_segment() -> None:
    seed = _tick("rt-domain-foreign-claim-seed", unresolved=False)
    lawful_update = build_subject_tick_runtime_domain_update(seed)
    adversarial_update = RuntimeDomainUpdate(
        regulation=lawful_update.regulation,
        continuity=lawful_update.continuity,
        validity=lawful_update.validity,
        write_claims=tuple(
            DomainWriteClaim(
                phase=DomainWriterPhase.C04 if claim.domain_path == "domains.validity" else claim.phase,
                domain_path=claim.domain_path,
                transition_kind=claim.transition_kind,
                route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
                checkpoint_id=claim.checkpoint_id,
                reason="adversarial claim rewrite",
            )
            for claim in lawful_update.write_claims
        ),
        reason="adversarial foreign claim matrix write",
    )
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-foreign-claim",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "foreign-domain-claim"),
            requested_at="2026-04-08T01:06:00+00:00",
            event_id="ev-rt-domain-foreign-claim",
            event_payload={
                "turn_id": "turn-rt-domain-foreign-claim",
                "runtime_domain_update": adversarial_update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=seed,
                    domain_update=adversarial_update,
                ),
            },
        ),
        _bootstrapped_state(),
    )
    assert denied.accepted is False
    assert "domains.validity" in denied.authority.denied_paths


def test_shared_domains_precedence_over_conflicting_snapshot_surface_is_path_affecting() -> None:
    baseline_tick = _tick("rt-domain-precedence-baseline", unresolved=False)
    baseline_state = persist_subject_tick_result_via_f01(
        result=baseline_tick,
        runtime_state=_bootstrapped_state(),
        transition_id="tr-rt-domain-precedence-baseline",
        requested_at="2026-04-08T01:07:00+00:00",
    ).state
    restricted = _tick(
        "rt-domain-precedence-restricted",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    restricted_update = build_subject_tick_runtime_domain_update(restricted)
    mixed_payload_state = execute_transition(
        TransitionRequest(
            transition_id="tr-rt-domain-precedence-mixed",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("test", "precedence", "mixed"),
            requested_at="2026-04-08T01:07:30+00:00",
            event_id="ev-rt-domain-precedence-mixed",
            event_payload={
                "turn_id": "turn-rt-domain-precedence-mixed",
                "subject_tick_snapshot": {
                    "state": {
                        "c05_execution_action_claim": "continue_stream",
                        "c04_execution_mode_claim": "continue_stream",
                    }
                },
                "runtime_domain_update": restricted_update,
                "runtime_route_auth": build_subject_tick_runtime_route_auth_context(
                    result=restricted,
                    domain_update=restricted_update,
                ),
            },
        ),
        baseline_state,
    ).state
    view = derive_subject_tick_runtime_domain_contract_view(mixed_payload_state)
    assert view.source_of_truth_surface == "runtime_state.domains"
    assert view.packet_snapshot_precedence_blocked is True
    assert view.recommended_outcome == "revalidate"
    follow_up = _tick(
        "rt-domain-precedence-follow-up",
        unresolved=False,
        context=SubjectTickContext(prior_runtime_state=mixed_payload_state),
    )
    assert follow_up.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
