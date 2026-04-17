from __future__ import annotations

from dataclasses import replace

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o02_intersubjective_allostasis import O02InteractionDiagnosticsInput
from substrate.subject_tick.policy import evaluate_subject_tick_downstream_gate
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
        confidence=0.8,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.o02.integration:{signal_id}",
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


def test_subject_tick_emits_o02_checkpoint_in_runtime_order_after_o01() -> None:
    result = _result("rt-o02-order")
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.o01_other_entity_model_checkpoint" in ids
    assert "rt01.o02_intersubjective_allostasis_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.o01_other_entity_model_checkpoint") < ids.index(
        "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert ids.index("rt01.o02_intersubjective_allostasis_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_subject_tick_carries_typed_o02_result() -> None:
    result = _result(
        "rt-o02-typed",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                precision_request=True,
            ),
        ),
    )
    assert result.o02_result.state.regulation_id.startswith("o02-regulation:")
    assert result.o02_result.state.lever_preferences
    assert result.o02_result.scope_marker.rt01_hosted_only is True
    assert result.o02_result.scope_marker.o02_first_slice_only is True


def test_subject_tick_default_path_repair_heavy_detour_is_load_bearing() -> None:
    baseline = _result(
        "rt-o02-default-baseline",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(),
        ),
    )
    repair_heavy = _result(
        "rt-o02-default-repair-heavy",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_corrections_count=2,
                recent_misunderstanding_count=2,
                clarification_failures=1,
                repetition_request_count=1,
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    repair_checkpoint = next(
        item
        for item in repair_heavy.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert repair_checkpoint.status.value == "enforced_detour"
    assert "default_o02_repair_sensitive_clarification_detour" in repair_checkpoint.required_action
    assert repair_heavy.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_underconstrained_other_model_triggers_default_conservative_detour() -> None:
    result = _result(
        "rt-o02-default-conservative",
        context=SubjectTickContext(
            o01_entity_signals=(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_misunderstanding_count=2,
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "default_o02_conservative_clarification_detour" in checkpoint.required_action
    assert result.o02_result.state.interaction_mode.value == "conservative_mode_only"


def test_subject_tick_explicit_require_consumer_path_is_load_bearing() -> None:
    result = _result(
        "rt-o02-require-repair",
        context=SubjectTickContext(
            require_o02_repair_sensitive_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_corrections_count=0,
                recent_misunderstanding_count=0,
                clarification_failures=0,
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o02_repair_sensitive_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_explicit_boundary_preserving_consumer_path_is_load_bearing() -> None:
    result = _result(
        "rt-o02-require-boundary",
        context=SubjectTickContext(
            require_o02_boundary_preserving_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
                self_side_caution_required=True,
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o02_boundary_preserving_consumer" in checkpoint.required_action
    assert result.o02_result.state.self_other_constraint_conflict is True


def test_subject_tick_o02_positive_consumer_ready_path_has_no_detour() -> None:
    result = _result(
        "rt-o02-positive",
        context=SubjectTickContext(
            require_o02_repair_sensitive_consumer=True,
            require_o02_boundary_preserving_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_corrections_count=1,
                recent_misunderstanding_count=1,
                clarification_failures=0,
                precision_request=True,
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert result.o02_result.gate.repair_sensitive_consumer_ready is True
    assert result.o02_result.gate.boundary_preserving_consumer_ready is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_subject_tick_o02_politeness_collapse_guard_is_visible_downstream() -> None:
    result = _result(
        "rt-o02-politeness-guard",
        context=SubjectTickContext(
            o01_entity_signals=(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
            ),
        ),
    )
    restrictions = set(result.downstream_gate.restrictions)
    assert (
        SubjectTickRestrictionCode.O02_INTERSUBJECTIVE_ALLOSTASIS_CONTRACT_MUST_BE_READ
        in restrictions
    )
    assert SubjectTickRestrictionCode.O02_POLITENESS_ONLY_COLLAPSE_FORBIDDEN in restrictions


def test_subject_tick_politeness_baseline_does_not_match_disagreement_guard_path() -> None:
    baseline = _result(
        "rt-o02-politeness-baseline",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
            ),
        ),
    )
    guarded = _result(
        "rt-o02-politeness-guarded",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
                strong_disagreement_risk=True,
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    guarded_checkpoint = next(
        item
        for item in guarded.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert baseline.state.o02_strong_disagreement_guard_applied is False
    assert guarded.state.o02_strong_disagreement_guard_applied is True
    assert baseline.state.o02_interaction_mode != guarded.state.o02_interaction_mode
    assert baseline_checkpoint.status.value == "allowed"
    assert guarded_checkpoint.status.value == "enforced_detour"


def test_subject_tick_o02_prior_state_carry_and_revision_is_bounded() -> None:
    tick1 = _result(
        "rt-o02-carry-1",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_corrections_count=2,
                recent_misunderstanding_count=2,
            ),
        ),
    )
    tick2 = _result(
        "rt-o02-carry-2",
        context=SubjectTickContext(
            prior_o02_state=tick1.o02_result.state,
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_misunderstanding_count=2,
            ),
        ),
    )
    tick3 = _result(
        "rt-o02-carry-3",
        context=SubjectTickContext(
            prior_o02_state=tick2.o02_result.state,
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(),
        ),
    )
    assert tick1.state.o02_interaction_mode == "repair_heavy"
    assert tick2.state.o02_prior_mode_carry_applied is True
    assert tick2.state.o02_interaction_mode == "repair_heavy"
    assert tick3.state.o02_prior_mode_carry_applied is False
    assert tick3.state.o02_interaction_mode != "repair_heavy"


def test_subject_tick_policy_reads_typed_o02_semantics_not_only_checkpoint_tokens() -> None:
    baseline = _result(
        "rt-o02-typed-policy-branch",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o02_interaction_diagnostics=O02InteractionDiagnosticsInput(),
        ),
    )
    o02_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert "require_o02_repair_sensitive_consumer" not in o02_checkpoint.required_action
    plain_state = replace(
        baseline.state,
        o02_s05_shape_modulation_applied=False,
    )
    semantic_state = replace(
        baseline.state,
        o02_s05_shape_modulation_applied=True,
    )
    plain_gate = evaluate_subject_tick_downstream_gate(plain_state)
    semantic_gate = evaluate_subject_tick_downstream_gate(semantic_state)
    assert (
        SubjectTickRestrictionCode.O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED
        not in set(plain_gate.restrictions)
    )
    assert (
        SubjectTickRestrictionCode.O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED
        in set(semantic_gate.restrictions)
    )
