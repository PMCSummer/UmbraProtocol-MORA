from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome, SubjectTickRestrictionCode
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
        confidence=0.81,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.o03.integration:{signal_id}",
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


def _transparent_candidate(candidate_id: str) -> O03CandidateStrategyInput:
    return O03CandidateStrategyInput(
        candidate_move_id=candidate_id,
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=True,
        material_uncertainty_omitted=False,
        selective_omission_risk_marker=False,
        reversibility_preserved=True,
        repairability_preserved=True,
    )


def _concealed_candidate(candidate_id: str) -> O03CandidateStrategyInput:
    return O03CandidateStrategyInput(
        candidate_move_id=candidate_id,
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=False,
        material_uncertainty_omitted=True,
        selective_omission_risk_marker=True,
        asymmetry_opportunity_marker=True,
        dependency_shaping_marker=True,
        autonomy_narrowing_marker=True,
        reversibility_preserved=False,
        repairability_preserved=False,
        strong_compliance_pull_marker=True,
    )


def test_subject_tick_emits_o03_checkpoint_in_runtime_order_after_o02() -> None:
    result = _result(
        "rt-o03-order",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_candidate("rt-o03-order"),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.o02_intersubjective_allostasis_checkpoint" in ids
    assert "rt01.o03_strategy_class_evaluation_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.o02_intersubjective_allostasis_checkpoint") < ids.index(
        "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    assert ids.index("rt01.o03_strategy_class_evaluation_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_subject_tick_carries_typed_o03_result() -> None:
    result = _result(
        "rt-o03-typed",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_candidate("rt-o03-typed"),
        ),
    )
    assert result.o03_result.state.strategy_id.startswith("o03-strategy:")
    assert result.o03_result.state.strategy_lever_preferences
    assert result.o03_result.scope_marker.rt01_hosted_only is True
    assert result.o03_result.scope_marker.o03_first_slice_only is True


def test_subject_tick_default_path_high_entropy_detour_is_load_bearing() -> None:
    baseline = _result(
        "rt-o03-default-baseline",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_candidate("rt-o03-default-baseline"),
        ),
    )
    risky = _result(
        "rt-o03-default-high-entropy",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_concealed_candidate("rt-o03-default-high-entropy"),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    risky_checkpoint = next(
        item
        for item in risky.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "enforced_detour"
    assert (
        "default_o03_transparency_clarification_detour" in risky_checkpoint.required_action
        or "default_o03_exploitative_candidate_block_detour" in risky_checkpoint.required_action
    )
    assert risky.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_explicit_o03_require_paths_are_load_bearing() -> None:
    result = _result(
        "rt-o03-required",
        context=SubjectTickContext(
            require_o03_strategy_contract_consumer=True,
            require_o03_cooperative_selection_consumer=True,
            require_o03_transparency_preserving_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_concealed_candidate("rt-o03-required"),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o03_strategy_contract_consumer" in checkpoint.required_action
    assert "require_o03_cooperative_selection_consumer" in checkpoint.required_action
    assert "require_o03_transparency_preserving_consumer" in checkpoint.required_action


def test_subject_tick_o03_positive_require_path_can_continue_lawfully() -> None:
    result = _result(
        "rt-o03-positive",
        context=SubjectTickContext(
            require_o03_strategy_contract_consumer=True,
            require_o03_cooperative_selection_consumer=True,
            require_o03_transparency_preserving_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_candidate("rt-o03-positive"),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert result.o03_result.gate.strategy_contract_consumer_ready is True
    assert result.o03_result.gate.cooperative_selection_consumer_ready is True
    assert result.o03_result.gate.transparency_preserving_consumer_ready is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_subject_tick_policy_reads_typed_o03_semantics_not_only_checkpoint_tokens() -> None:
    result = _result(
        "rt-o03-typed-policy-branch",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_concealed_candidate("rt-o03-typed-policy-branch"),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    restrictions = set(result.downstream_gate.restrictions)
    assert "require_o03_cooperative_selection_consumer" not in checkpoint.required_action
    assert (
        SubjectTickRestrictionCode.O03_COOPERATIVE_DEFAULT_REQUIRED in restrictions
        or SubjectTickRestrictionCode.O03_EXPLOITATIVE_CANDIDATE_BLOCK_REQUIRED in restrictions
    )
    assert SubjectTickRestrictionCode.O03_POLITENESS_EQUIVALENCE_FORBIDDEN in restrictions
