from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
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
    authority: str,
    relation: str,
    claim: str,
    referent: str = "user",
    quoted: bool = False,
    entity_id_hint: str | None = None,
) -> O01EntitySignal:
    return O01EntitySignal(
        signal_id=signal_id,
        entity_id_hint=entity_id_hint,
        referent_label=referent,
        source_authority=authority,
        relation_class=relation,
        claim_value=claim,
        confidence=0.78,
        grounded=True,
        quoted=quoted,
        turn_index=1,
        provenance=f"tests.o01.integration:{signal_id}",
        target_claim=None,
    )


def test_subject_tick_emits_o01_checkpoint_in_runtime_order_after_t04() -> None:
    result = _result("rt-o01-order")
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.t04_attention_schema_checkpoint" in ids
    assert "rt01.o01_other_entity_model_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.t04_attention_schema_checkpoint") < ids.index(
        "rt01.o01_other_entity_model_checkpoint"
    )
    assert ids.index("rt01.o01_other_entity_model_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_subject_tick_carries_typed_o01_result() -> None:
    context = SubjectTickContext(
        o01_entity_signals=(
            _signal(
                signal_id="typed1",
                authority="current_user_direct",
                relation="stable_claim",
                claim="prefers_concise_answers",
            ),
            _signal(
                signal_id="typed2",
                authority="current_user_direct",
                relation="stable_claim",
                claim="prefers_concise_answers",
            ),
        )
    )
    result = _result("rt-o01-typed", context=context)
    assert result.o01_result.state.model_id.startswith("o01-model:")
    assert result.o01_result.state.current_user_entity_id == "current_user"
    assert result.o01_result.gate.current_user_model_ready is True
    assert result.o01_result.scope_marker.rt01_hosted_only is True


def test_subject_tick_o01_entity_individuation_requirement_is_load_bearing() -> None:
    baseline = _result("rt-o01-entity-baseline", context=SubjectTickContext())
    required = _result(
        "rt-o01-entity-required",
        context=SubjectTickContext(require_o01_entity_individuation_consumer=True),
    )
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert required_checkpoint.status.value == "enforced_detour"
    assert required.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_o01_clarification_requirement_is_load_bearing() -> None:
    context = SubjectTickContext(
        require_o01_clarification_ready_consumer=True,
        o01_entity_signals=(
            _signal(
                signal_id="comp1",
                authority="referenced_other",
                relation="goal_hint",
                claim="needs_report",
                referent="manager",
                entity_id_hint="referenced_other:manager_v1",
            ),
            _signal(
                signal_id="comp2",
                authority="referenced_other",
                relation="goal_hint",
                claim="needs_report",
                referent="manager",
                entity_id_hint="referenced_other:manager_v2",
            ),
        ),
    )
    result = _result("rt-o01-clarification-required", context=context)
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o01_clarification_ready_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_o01_positive_ready_path_with_requirements() -> None:
    context = SubjectTickContext(
        require_o01_entity_individuation_consumer=True,
        require_o01_clarification_ready_consumer=True,
        o01_entity_signals=(
            _signal(
                signal_id="ok1",
                authority="current_user_direct",
                relation="stable_claim",
                claim="prefers_structured_lists",
            ),
            _signal(
                signal_id="ok2",
                authority="current_user_direct",
                relation="stable_claim",
                claim="prefers_structured_lists",
            ),
            _signal(
                signal_id="ok3",
                authority="current_user_direct",
                relation="knowledge_boundary",
                claim="knows_python_testing_basics",
            ),
        ),
    )
    result = _result("rt-o01-positive", context=context)
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert result.o01_result.gate.downstream_consumer_ready is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_subject_tick_o01_projection_guard_is_visible_downstream_restrictions() -> None:
    result = _result(
        "rt-o01-projection-guard",
        context=SubjectTickContext(
            o01_entity_signals=(
                _signal(
                    signal_id="pg1",
                    authority="self_internal_bias",
                    relation="stable_claim",
                    claim="prefers_storytelling",
                ),
            ),
        ),
    )
    restrictions = set(result.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.O01_OTHER_ENTITY_MODEL_CONTRACT_MUST_BE_READ in restrictions
    assert SubjectTickRestrictionCode.O01_PROJECTION_GUARD_REQUIRED in restrictions
