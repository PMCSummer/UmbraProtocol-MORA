from __future__ import annotations

from dataclasses import replace

from substrate.contracts import (
    ContinuityDomainState,
    RegulationDomainState,
    RuntimeDomainUpdate,
    TransitionKind,
    TransitionRequest,
    ValidityDomainState,
    WriterIdentity,
)
from substrate.downstream_obedience import ObedienceStatus, build_downstream_obedience_decision
from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    build_subject_tick_runtime_domain_update,
    build_subject_tick_runtime_route_auth_context,
    choose_runtime_execution_outcome,
    derive_subject_tick_contract_view,
    execute_subject_tick,
)
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-obey-build-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-08T04:00:00+00:00",
            event_id="ev-obey-build-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _tick(
    case_id: str,
    *,
    unresolved: bool = False,
    context: SubjectTickContext | None = None,
):
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


def _persist_domain_update(
    *,
    runtime_state,
    seed_result,
    domain_update: RuntimeDomainUpdate,
    transition_id: str,
):
    route_auth = build_subject_tick_runtime_route_auth_context(
        result=seed_result,
        domain_update=domain_update,
    )
    result = execute_transition(
        TransitionRequest(
            transition_id=transition_id,
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("obey-build", transition_id),
            requested_at="2026-04-08T04:01:00+00:00",
            event_id=f"ev-{transition_id}",
            event_payload={
                "turn_id": f"turn-{transition_id}",
                "runtime_domain_update": domain_update,
                "runtime_route_auth": route_auth,
            },
        ),
        runtime_state,
    )
    assert result.accepted is True
    return result.state


def _checkpoint(result, checkpoint_id: str):
    return next(
        checkpoint
        for checkpoint in result.state.execution_checkpoints
        if checkpoint.checkpoint_id == checkpoint_id
    )


def test_obedience_status_matrix_covers_required_protocol_states() -> None:
    base = dict(
        source_of_truth_surface="runtime_state.domains",
        c04_mode_legitimacy=True,
        c04_mode_claim="continue_stream",
        c04_authority_role="arbitration",
        c04_computational_role="scheduler",
        c05_legality_reuse_allowed=True,
        c05_revalidation_required=False,
        c05_no_safe_reuse=False,
        c05_action_claim="continue_stream",
        c05_authority_role="invalidation",
        c05_computational_role="evaluator",
        r04_override_scope="none",
        r04_no_strong_override_claim=True,
        r04_authority_role="gating",
        r04_computational_role="evaluator",
        c05_surface_invalidated=False,
    )
    statuses = {
        build_downstream_obedience_decision(**base).status,
        build_downstream_obedience_decision(
            **{**base, "r04_override_scope": "focused", "r04_no_strong_override_claim": False}
        ).status,
        build_downstream_obedience_decision(
            **{**base, "c04_mode_legitimacy": False}
        ).status,
        build_downstream_obedience_decision(
            **{**base, "c05_legality_reuse_allowed": False}
        ).status,
        build_downstream_obedience_decision(
            **{**base, "c05_no_safe_reuse": True}
        ).status,
        build_downstream_obedience_decision(
            **{**base, "c05_surface_invalidated": True}
        ).status,
        build_downstream_obedience_decision(
            **{**base, "c05_authority_role": "computational"}
        ).status,
        build_downstream_obedience_decision(
            **{
                **base,
                "r04_override_scope": "emergency",
                "r04_no_strong_override_claim": False,
            }
        ).status,
    }
    assert statuses >= {
        ObedienceStatus.ALLOW_CONTINUE,
        ObedienceStatus.ALLOW_CONTINUE_WITH_RESTRICTION,
        ObedienceStatus.MUST_REPAIR,
        ObedienceStatus.MUST_REVALIDATE,
        ObedienceStatus.MUST_HALT,
        ObedienceStatus.INSUFFICIENT_AUTHORITY_BASIS,
        ObedienceStatus.INVALIDATED_UPSTREAM_SURFACE,
        ObedienceStatus.BLOCKED_BY_SURVIVAL_OVERRIDE,
    }


def test_c05_restriction_cannot_be_bypassed_by_helper_path_when_obedience_enabled() -> None:
    seed = _tick("obey-c05-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        validity=replace(
            update.validity,
            legality_reuse_allowed=False,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-c05-legality-false",
    )
    result = _tick(
        "obey-c05-follow",
        context=SubjectTickContext(
            prior_runtime_state=runtime_state,
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
        ),
    )
    assert result.state.downstream_obedience_status == "must_revalidate"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert choose_runtime_execution_outcome(result) == "revalidate"


def test_ablation_disabling_obedience_changes_runtime_behavior() -> None:
    seed = _tick("obey-ablation-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        validity=replace(
            update.validity,
            legality_reuse_allowed=False,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-ablation-state",
    )
    enforced = _tick(
        "obey-ablation-enforced",
        context=SubjectTickContext(
            prior_runtime_state=runtime_state,
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
        ),
    )
    bypassed = _tick(
        "obey-ablation-bypassed",
        context=SubjectTickContext(
            prior_runtime_state=runtime_state,
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert bypassed.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_r04_survival_override_is_binding_obstruction_through_obedience() -> None:
    seed = _tick("obey-r04-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        regulation=replace(
            update.regulation,
            override_scope="emergency",
            no_strong_override_claim=False,
            pressure_level=0.99,
            escalation_stage="critical",
        ),
        continuity=replace(
            update.continuity,
            mode_legitimacy=True,
        ),
        validity=replace(
            update.validity,
            legality_reuse_allowed=True,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-r04-emergency",
    )
    result = _tick(
        "obey-r04-follow",
        context=SubjectTickContext(prior_runtime_state=runtime_state),
    )
    assert result.state.downstream_obedience_status == "blocked_by_survival_override"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_c04_mode_legitimacy_flows_through_obedience_contract() -> None:
    seed = _tick("obey-c04-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        continuity=replace(update.continuity, mode_legitimacy=False),
        validity=replace(
            update.validity,
            legality_reuse_allowed=True,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-c04-legitimacy-false",
    )
    result = _tick(
        "obey-c04-follow",
        context=SubjectTickContext(prior_runtime_state=runtime_state),
    )
    assert result.state.downstream_obedience_status == "must_repair"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.downstream_obedience_checkpoint"
        for checkpoint in result.state.execution_checkpoints
    )


def test_shared_domains_precedence_over_snapshot_is_path_affecting() -> None:
    seed = _tick("obey-precedence-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        validity=ValidityDomainState(
            c05_action_claim="run_selective_revalidation",
            c05_validity_action="run_selective_revalidation",
            legality_reuse_allowed=False,
            revalidation_required=True,
            no_safe_reuse=False,
            selective_scope_targets=("item",),
            source_state_ref="obey-precedence",
            updated_by_phase="C05",
            last_update_provenance="obey-precedence",
        ),
        continuity=replace(update.continuity, mode_legitimacy=True),
        regulation=RegulationDomainState(
            pressure_level=0.2,
            escalation_stage="stable",
            override_scope="none",
            no_strong_override_claim=True,
            gate_accepted=True,
            source_state_ref="obey-precedence",
            updated_by_phase="R04",
            last_update_provenance="obey-precedence",
        ),
    )
    route_auth = build_subject_tick_runtime_route_auth_context(result=seed, domain_update=update)
    state = execute_transition(
        TransitionRequest(
            transition_id="tr-obey-precedence-mixed",
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("obey-build", "precedence"),
            requested_at="2026-04-08T04:02:00+00:00",
            event_id="ev-obey-precedence-mixed",
            event_payload={
                "turn_id": "turn-obey-precedence-mixed",
                "subject_tick_snapshot": {
                    "state": {
                        "c05_execution_action_claim": "continue_stream",
                        "c04_execution_mode_claim": "continue_stream",
                    }
                },
                "runtime_domain_update": update,
                "runtime_route_auth": route_auth,
            },
        ),
        _bootstrapped_state(),
    )
    assert state.accepted is True
    result = _tick(
        "obey-precedence-follow",
        context=SubjectTickContext(prior_runtime_state=state.state),
    )
    view = derive_subject_tick_contract_view(result)
    assert view.downstream_obedience_source_of_truth_surface == "runtime_state.domains"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_insufficient_authority_basis_blocks_lawful_continue() -> None:
    result = _tick(
        "obey-insufficient-authority",
        context=SubjectTickContext(
            phase_authority_roles={"C05": "computational"},
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
        ),
    )
    assert result.state.downstream_obedience_status == "insufficient_authority_basis"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_obedience_checkpoint_and_state_fields_are_materialized_in_live_contour() -> None:
    result = _tick("obey-live-contour", unresolved=True)
    assert result.state.downstream_obedience_status
    assert result.state.downstream_obedience_fallback
    assert result.state.downstream_obedience_reason
    assert result.state.downstream_obedience_requires_restrictions_read is True
    assert any(
        checkpoint.checkpoint_id == "rt01.downstream_obedience_checkpoint"
        for checkpoint in result.state.execution_checkpoints
    )


def test_obedience_checkpoint_revalidate_case_is_post_enforcement_coherent() -> None:
    seed = _tick("obey-checkpoint-revalidate-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        validity=replace(
            update.validity,
            legality_reuse_allowed=False,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-checkpoint-revalidate",
    )
    result = _tick(
        "obey-checkpoint-revalidate-follow",
        context=SubjectTickContext(
            prior_runtime_state=runtime_state,
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
        ),
    )
    checkpoint = _checkpoint(result, "rt01.downstream_obedience_checkpoint")
    assert result.state.downstream_obedience_status == "must_revalidate"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert checkpoint.applied_action == result.state.active_execution_mode == "revalidate_scope"
    assert checkpoint.reason.endswith("action_transition=idle->revalidate_scope")


def test_obedience_checkpoint_repair_case_is_post_enforcement_coherent() -> None:
    seed = _tick("obey-checkpoint-repair-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        continuity=replace(update.continuity, mode_legitimacy=False),
        validity=replace(
            update.validity,
            legality_reuse_allowed=True,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-checkpoint-repair",
    )
    result = _tick(
        "obey-checkpoint-repair-follow",
        context=SubjectTickContext(prior_runtime_state=runtime_state),
    )
    checkpoint = _checkpoint(result, "rt01.downstream_obedience_checkpoint")
    assert result.state.downstream_obedience_status == "must_repair"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert checkpoint.applied_action == result.state.active_execution_mode == "repair_runtime_path"


def test_obedience_checkpoint_halt_case_is_post_enforcement_coherent() -> None:
    seed = _tick("obey-checkpoint-halt-seed")
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        validity=replace(
            update.validity,
            legality_reuse_allowed=False,
            revalidation_required=False,
            no_safe_reuse=True,
            selective_scope_targets=(),
        ),
    )
    runtime_state = _persist_domain_update(
        runtime_state=_bootstrapped_state(),
        seed_result=seed,
        domain_update=update,
        transition_id="tr-obey-checkpoint-halt",
    )
    result = _tick(
        "obey-checkpoint-halt-follow",
        context=SubjectTickContext(
            prior_runtime_state=runtime_state,
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
        ),
    )
    checkpoint = _checkpoint(result, "rt01.downstream_obedience_checkpoint")
    assert result.state.downstream_obedience_status == "must_halt"
    assert result.state.final_execution_outcome == SubjectTickOutcome.HALT
    assert checkpoint.applied_action == result.state.active_execution_mode == "halt_execution"


def test_obedience_checkpoint_continue_case_has_no_enforcement_regression() -> None:
    result = _tick("obey-checkpoint-continue")
    checkpoint = _checkpoint(result, "rt01.downstream_obedience_checkpoint")
    assert result.state.downstream_obedience_status == "allow_continue"
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert checkpoint.applied_action == result.state.active_execution_mode == "idle"
    assert "action_transition=" not in checkpoint.reason
