from __future__ import annotations

from dataclasses import replace

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.o04_rupture_hostility_coercion import O04InteractionEventInput
from substrate.p01_project_formation import P01AuthoritySourceKind, P01ProjectSignalInput
from substrate.r05_appraisal_sovereign_protective_regulation import R05ProtectiveTriggerInput
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickOutcome,
    SubjectTickRestrictionCode,
)
from tests.substrate.subject_tick_testkit import build_subject_tick


def _result(case_id: str, *, context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context=context,
    )


def _signal(
    *,
    signal_id: str,
    relation: str,
    claim: str,
    turn_index: int,
) -> O01EntitySignal:
    return O01EntitySignal(
        signal_id=signal_id,
        entity_id_hint=None,
        referent_label="user",
        source_authority="current_user_direct",
        relation_class=relation,
        claim_value=claim,
        confidence=0.82,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.r05.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="r05-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="r05-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="r05-g3",
            relation="knowledge_boundary",
            claim="knows_cli_basics",
            turn_index=3,
        ),
    )


def _transparent_o03_candidate(case_id: str) -> O03CandidateStrategyInput:
    return O03CandidateStrategyInput(
        candidate_move_id=f"{case_id}:transparent",
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=True,
        material_uncertainty_omitted=False,
        selective_omission_risk_marker=False,
        reversibility_preserved=True,
        repairability_preserved=True,
    )


def _project_signal(case_id: str) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=f"{case_id}:project",
        signal_kind="directive",
        authority_source_kind=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
        target_summary="stabilize bounded runtime response path",
        grounded_basis_present=True,
        provenance=f"tests.r05.integration:{case_id}:project",
    )


def _r05_trigger(
    *,
    trigger_id: str,
    threat_structure_score: float,
    o04_coercive_structure_present: bool = False,
    load_pressure_score: float = 0.0,
    project_continuation_requested: bool = True,
    p01_project_continuation_active: bool = True,
    release_signal_present: bool = False,
    counterevidence_present: bool = False,
    tone_only_discomfort: bool = False,
) -> R05ProtectiveTriggerInput:
    return R05ProtectiveTriggerInput(
        trigger_id=trigger_id,
        threat_structure_score=threat_structure_score,
        o04_coercive_structure_present=o04_coercive_structure_present,
        load_pressure_score=load_pressure_score,
        project_continuation_requested=project_continuation_requested,
        p01_project_continuation_active=p01_project_continuation_active,
        release_signal_present=release_signal_present,
        counterevidence_present=counterevidence_present,
        tone_only_discomfort=tone_only_discomfort,
        provenance=f"tests.r05.integration:{trigger_id}",
    )


def _o04_coercive_event(event_id: str) -> O04InteractionEventInput:
    return O04InteractionEventInput(
        event_id=event_id,
        actor_ref="agent_a",
        target_ref="agent_b",
        blocked_option_present=True,
        threatened_loss_present=True,
        dependency_surface_present=True,
        sanction_power_present=True,
        provenance=f"tests.r05.integration:{event_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o04_interaction_events=(),
        o01_entity_signals=_grounded_user_signals(),
        o03_candidate_strategy=_transparent_o03_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def test_subject_tick_emits_r05_checkpoint_in_runtime_order_after_o04() -> None:
    result = _result(
        "rt-r05-order",
        context=replace(
            _base_context("rt-r05-order"),
            r05_protective_triggers=(
                _r05_trigger(
                    trigger_id="order-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.o04_rupture_hostility_coercion_checkpoint" in ids
    assert "rt01.r05_protective_regulation_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.o04_rupture_hostility_coercion_checkpoint") < ids.index(
        "rt01.r05_protective_regulation_checkpoint"
    )
    assert ids.index("rt01.r05_protective_regulation_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_explicit_require_consumer_path_is_deterministic() -> None:
    result = _result(
        "rt-r05-require",
        context=replace(
            _base_context("rt-r05-require"),
            require_r05_protective_state_consumer=True,
            require_r05_surface_inhibition_consumer=True,
            require_r05_release_contract_consumer=True,
            r05_protective_triggers=(),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_r05_protective_state_consumer" in checkpoint.required_action
    assert "require_r05_surface_inhibition_consumer" in checkpoint.required_action
    assert "require_r05_release_contract_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_default_path_protective_override_detour_requires_real_basis() -> None:
    baseline = _result(
        "rt-r05-default-no-trigger",
        context=replace(
            _base_context("rt-r05-default-no-trigger"),
            r05_protective_triggers=(),
        ),
    )
    protective = _result(
        "rt-r05-default-protective",
        context=replace(
            _base_context("rt-r05-default-protective"),
            r05_protective_triggers=(
                _r05_trigger(
                    trigger_id="default-protective-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                ),
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    protective_checkpoint = next(
        item
        for item in protective.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert "default_r05_protective_override_detour" not in baseline_checkpoint.required_action
    assert "default_r05_surface_throttle_detour" not in baseline_checkpoint.required_action
    assert protective_checkpoint.status.value == "enforced_detour"
    assert "default_r05_protective_override_detour" in protective_checkpoint.required_action
    assert protective.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_no_trigger_path_produces_no_r05_default_friction() -> None:
    result = _result(
        "rt-r05-no-trigger",
        context=replace(
            _base_context("rt-r05-no-trigger"),
            r05_protective_triggers=(),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "insufficient_basis_for_override"
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_release_path_changes_route_deterministically() -> None:
    seed = _result(
        "rt-r05-release-seed",
        context=replace(
            _base_context("rt-r05-release-seed"),
            require_r05_protective_state_consumer=True,
            r05_protective_triggers=(
                _r05_trigger(
                    trigger_id="release-seed-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                ),
            ),
        ),
    )
    released = _result(
        "rt-r05-release-follow-up",
        context=replace(
            _base_context("rt-r05-release-follow-up"),
            prior_r05_state=seed.r05_result.state,
            r05_protective_triggers=(
                _r05_trigger(
                    trigger_id="release-follow-up-1",
                    threat_structure_score=0.5,
                    p01_project_continuation_active=False,
                    release_signal_present=True,
                    counterevidence_present=True,
                    o04_coercive_structure_present=False,
                ),
            ),
        ),
    )
    checkpoint = next(
        item
        for item in released.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert released.r05_result.state.protective_mode.value == "recovery_in_progress"
    assert checkpoint.status.value == "enforced_detour"
    assert "default_r05_release_recheck_detour" in checkpoint.required_action
    assert released.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_typed_r05_semantics_not_only_checkpoint_token_drive_policy() -> None:
    degraded = _result(
        "rt-r05-semantic-degraded",
        context=replace(
            _base_context("rt-r05-semantic-degraded"),
            require_r05_protective_state_consumer=True,
            require_r05_surface_inhibition_consumer=True,
            require_r05_release_contract_consumer=True,
            r05_protective_triggers=(
                _r05_trigger(
                    trigger_id="semantic-degraded-1",
                    threat_structure_score=0.55,
                    o04_coercive_structure_present=False,
                ),
            ),
        ),
    )
    active = _result(
        "rt-r05-semantic-active",
        context=replace(
            _base_context("rt-r05-semantic-active"),
            require_r05_protective_state_consumer=True,
            require_r05_surface_inhibition_consumer=True,
            require_r05_release_contract_consumer=True,
            o04_interaction_events=(_o04_coercive_event("semantic-active-o04-1"),),
            r05_protective_triggers=(
                _r05_trigger(
                    trigger_id="semantic-active-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                    p01_project_continuation_active=False,
                    release_signal_present=True,
                ),
            ),
        ),
    )
    degraded_checkpoint = next(
        item
        for item in degraded.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    active_checkpoint = next(
        item
        for item in active.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert degraded_checkpoint.status.value == "allowed"
    assert active_checkpoint.status.value == "allowed"
    assert degraded_checkpoint.required_action == active_checkpoint.required_action
    degraded_restrictions = set(degraded.downstream_gate.restrictions)
    active_restrictions = set(active.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.R05_SURFACE_THROTTLE_REQUIRED in degraded_restrictions
    assert SubjectTickRestrictionCode.R05_SURFACE_THROTTLE_REQUIRED not in active_restrictions
    assert degraded_restrictions != active_restrictions
