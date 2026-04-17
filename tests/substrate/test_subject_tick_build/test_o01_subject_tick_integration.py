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
    turn_index: int = 1,
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
        turn_index=turn_index,
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
                turn_index=2,
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
                turn_index=2,
            ),
            _signal(
                signal_id="ok3",
                authority="current_user_direct",
                relation="knowledge_boundary",
                claim="knows_python_testing_basics",
                turn_index=3,
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


def test_subject_tick_o01_default_path_competing_models_enforces_clarification_detour() -> None:
    baseline = _result("rt-o01-default-baseline", context=SubjectTickContext())
    competing = _result(
        "rt-o01-default-competing",
        context=SubjectTickContext(
            o01_entity_signals=(
                _signal(
                    signal_id="dc1",
                    authority="referenced_other",
                    relation="goal_hint",
                    claim="needs_report",
                    referent="manager",
                    entity_id_hint="referenced_other:manager_v1",
                ),
                _signal(
                    signal_id="dc2",
                    authority="referenced_other",
                    relation="goal_hint",
                    claim="needs_report",
                    referent="manager",
                    entity_id_hint="referenced_other:manager_v2",
                    turn_index=2,
                ),
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    competing_checkpoint = next(
        item
        for item in competing.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert competing_checkpoint.status.value == "enforced_detour"
    assert "default_o01_competing_entity_clarification" in competing_checkpoint.required_action
    assert competing.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_o01_overlay_ignorance_is_narrow_default_load_bearing_signal() -> None:
    stable = _result(
        "rt-o01-overlay-stable",
        context=SubjectTickContext(
            o01_entity_signals=(
                _signal(
                    signal_id="os1",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_concise",
                ),
                _signal(
                    signal_id="os2",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_concise",
                    turn_index=2,
                ),
            ),
        ),
    )
    ignorance = _result(
        "rt-o01-overlay-ignorance",
        context=SubjectTickContext(
            o01_entity_signals=(
                _signal(
                    signal_id="oi1",
                    authority="current_user_direct",
                    relation="ignorance",
                    claim="does_not_know_api_rate_limit",
                ),
            ),
        ),
    )
    stable_checkpoint = next(
        item
        for item in stable.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    ignorance_checkpoint = next(
        item
        for item in ignorance.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
    )
    assert stable_checkpoint.status.value == "allowed"
    assert ignorance_checkpoint.status.value == "enforced_detour"
    assert "default_o01_belief_overlay_clarification" in ignorance_checkpoint.required_action
    assert ignorance.o01_result.gate.clarification_ready is False
    assert ignorance.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_o01_multi_tick_revision_chain_is_deterministic_and_non_overwriting() -> None:
    tick1 = _result(
        "rt-o01-chain-1",
        context=SubjectTickContext(
            o01_entity_signals=(
                _signal(
                    signal_id="ch1",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_detailed_answers",
                    turn_index=1,
                ),
                _signal(
                    signal_id="ch2",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_detailed_answers",
                    turn_index=2,
                ),
            ),
        ),
    )
    tick2 = _result(
        "rt-o01-chain-2",
        context=SubjectTickContext(
            prior_o01_state=tick1.o01_result.state,
            o01_entity_signals=(
                _signal(
                    signal_id="ch3",
                    authority="current_user_direct",
                    relation="correction",
                    claim="not_detailed_anymore",
                    turn_index=3,
                    entity_id_hint=None,
                ),
            ),
        ),
    )
    tick3 = _result(
        "rt-o01-chain-3",
        context=SubjectTickContext(
            prior_o01_state=tick2.o01_result.state,
            o01_entity_signals=(
                _signal(
                    signal_id="ch4",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_detailed_answers",
                    turn_index=4,
                ),
            ),
        ),
    )
    tick4 = _result(
        "rt-o01-chain-4",
        context=SubjectTickContext(
            prior_o01_state=tick3.o01_result.state,
            o01_entity_signals=(
                _signal(
                    signal_id="ch5",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_bulleted_format",
                    turn_index=5,
                ),
                _signal(
                    signal_id="ch6",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_bulleted_format",
                    turn_index=6,
                ),
            ),
        ),
    )

    user2 = next(
        entity
        for entity in tick2.o01_result.state.entities
        if entity.entity_id == tick2.o01_result.state.current_user_entity_id
    )
    user3 = next(
        entity
        for entity in tick3.o01_result.state.entities
        if entity.entity_id == tick3.o01_result.state.current_user_entity_id
    )
    user4 = next(
        entity
        for entity in tick4.o01_result.state.entities
        if entity.entity_id == tick4.o01_result.state.current_user_entity_id
    )
    event_kinds_tick2 = {event.event_kind.value for event in user2.revision_history}

    assert "prefers_detailed_answers" in next(
        entity.stable_claims
        for entity in tick1.o01_result.state.entities
        if entity.entity_id == tick1.o01_result.state.current_user_entity_id
    )
    assert {"invalidate", "revise"} & event_kinds_tick2
    assert "prefers_detailed_answers" not in user2.stable_claims
    assert "prefers_detailed_answers" not in user3.stable_claims
    assert "prefers_bulleted_format" in user4.stable_claims
