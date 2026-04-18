from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.p01_project_formation import (
    P01AuthoritySourceKind,
    P01ProjectSignalInput,
)
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
        provenance=f"tests.p01.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="g3",
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


def _project_signal(
    *,
    signal_id: str,
    authority: P01AuthoritySourceKind,
    target: str,
    grounded: bool = True,
    missing_precondition_marker: bool = False,
    blocker_present: bool = False,
    temporal_validity_marker: bool = True,
    completion_evidence_present: bool = False,
    continuation_of_prior_project_id: str | None = None,
    conflict_group_id: str | None = None,
) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=signal_id,
        signal_kind="directive",
        authority_source_kind=authority,
        target_summary=target,
        grounded_basis_present=grounded,
        missing_precondition_marker=missing_precondition_marker,
        blocker_present=blocker_present,
        temporal_validity_marker=temporal_validity_marker,
        completion_evidence_present=completion_evidence_present,
        continuation_of_prior_project_id=continuation_of_prior_project_id,
        conflict_group_id=conflict_group_id,
        provenance=f"tests.p01.integration:{signal_id}",
    )


def test_subject_tick_emits_p01_checkpoint_in_runtime_order_after_o03() -> None:
    result = _result(
        "rt-p01-order",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-order"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-order-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.o03_strategy_class_evaluation_checkpoint" in ids
    assert "rt01.p01_project_formation_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.o03_strategy_class_evaluation_checkpoint") < ids.index(
        "rt01.p01_project_formation_checkpoint"
    )
    assert ids.index("rt01.p01_project_formation_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_subject_tick_carries_typed_p01_result() -> None:
    result = _result(
        "rt-p01-typed",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-typed"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-typed-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
    )
    assert result.p01_result.state.stack_id.startswith("p01-stack:")
    assert result.p01_result.state.active_projects
    assert result.p01_result.scope_marker.rt01_hosted_only is True
    assert result.p01_result.scope_marker.p01_first_slice_only is True


def test_subject_tick_default_path_missing_precondition_detour_is_load_bearing() -> None:
    baseline = _result(
        "rt-p01-default-baseline",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-default-baseline"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-base-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
    )
    blocked = _result(
        "rt-p01-default-blocked",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-default-blocked"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-block-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    missing_precondition_marker=True,
                    blocker_present=True,
                ),
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    blocked_checkpoint = next(
        item
        for item in blocked.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert blocked_checkpoint.status.value == "enforced_detour"
    assert "default_p01_missing_precondition_detour" in blocked_checkpoint.required_action
    assert blocked.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_subject_tick_default_conflict_arbitration_detour_is_load_bearing() -> None:
    result = _result(
        "rt-p01-default-conflict",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-default-conflict"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-conflict-a",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="maximize depth",
                    conflict_group_id="grp-1",
                ),
                _project_signal(
                    signal_id="p01-conflict-b",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="maximize speed",
                    conflict_group_id="grp-1",
                ),
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "default_p01_conflict_arbitration_detour" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_subject_tick_explicit_p01_require_paths_are_load_bearing() -> None:
    result = _result(
        "rt-p01-required",
        context=SubjectTickContext(
            require_p01_intention_stack_consumer=True,
            require_p01_authority_bound_consumer=True,
            require_p01_project_handoff_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-required"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-required-1",
                    authority=P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_p01_intention_stack_consumer" in checkpoint.required_action
    assert "require_p01_authority_bound_consumer" in checkpoint.required_action
    assert "require_p01_project_handoff_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_subject_tick_p01_positive_require_path_can_continue_lawfully() -> None:
    result = _result(
        "rt-p01-positive",
        context=SubjectTickContext(
            require_p01_intention_stack_consumer=True,
            require_p01_authority_bound_consumer=True,
            require_p01_project_handoff_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-positive"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-positive-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert result.p01_result.gate.intention_stack_consumer_ready is True
    assert result.p01_result.gate.authority_bound_consumer_ready is True
    assert result.p01_result.gate.project_handoff_consumer_ready is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_no_project_signals_no_default_p01_detour() -> None:
    result = _result(
        "rt-p01-no-signals",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-no-signals"),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert "default_p01_missing_precondition_detour" not in checkpoint.required_action
    assert "default_p01_conflict_arbitration_detour" not in checkpoint.required_action


def test_typed_p01_semantics_not_only_checkpoint_token_drive_policy_natural_flow() -> None:
    no_surface = _result(
        "rt-p01-natural-token-no-surface",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate(
                "rt-p01-natural-token-no-surface"
            ),
        ),
    )
    suspended_surface = _result(
        "rt-p01-natural-token-surface",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate(
                "rt-p01-natural-token-surface"
            ),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-natural-token-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    temporal_validity_marker=False,
                ),
            ),
        ),
    )
    no_surface_checkpoint = next(
        item
        for item in no_surface.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    suspended_surface_checkpoint = next(
        item
        for item in suspended_surface.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert no_surface_checkpoint.required_action == "no_safe_project_formation"
    assert suspended_surface_checkpoint.required_action == "no_safe_project_formation"
    assert no_surface.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert suspended_surface.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert no_surface.downstream_gate.accepted is True
    assert suspended_surface.downstream_gate.accepted is False
    assert (
        SubjectTickRestrictionCode.P01_PROJECT_HANDOFF_CONSUMER_REQUIRED
        in set(suspended_surface.downstream_gate.restrictions)
    )


def test_stale_active_project_detected_is_real_and_load_bearing() -> None:
    seed = _result(
        "rt-p01-stale-seed",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-stale-seed"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-stale-seed-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
    )
    prior_project_id = seed.p01_result.state.active_projects[0].project_id
    stale = _result(
        "rt-p01-stale-follow-up",
        context=SubjectTickContext(
            prior_p01_state=seed.p01_result.state,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-p01-stale-follow-up"),
            p01_project_signals=(
                _project_signal(
                    signal_id="p01-stale-follow-up-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    completion_evidence_present=True,
                    continuation_of_prior_project_id=prior_project_id,
                ),
            ),
        ),
    )
    checkpoint = next(
        item
        for item in stale.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert stale.p01_result.state.stale_active_project_detected is True
    assert checkpoint.status.value == "enforced_detour"
    assert "default_p01_stale_project_detour" in checkpoint.required_action
    assert stale.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
