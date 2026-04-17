from __future__ import annotations

from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickOutcome,
    SubjectTickRestrictionCode,
)
from tests.substrate.subject_tick_testkit import build_subject_tick


def _result(case_id: str, *, context: SubjectTickContext | None = None, unresolved: bool = False):
    return build_subject_tick(
        case_id=case_id,
        energy=14.0 if unresolved else 66.0,
        cognitive=95.0 if unresolved else 44.0,
        safety=34.0 if unresolved else 74.0,
        unresolved_preference=unresolved,
        context=context,
    )


def test_subject_tick_emits_s05_checkpoint_and_keeps_runtime_order() -> None:
    result = _result("rt-s05-order", unresolved=False)
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.s04_interoceptive_self_binding_checkpoint" in ids
    assert "rt01.s05_multi_cause_attribution_checkpoint" in ids
    assert "rt01.s_minimal_contour_checkpoint" in ids
    assert ids.index("rt01.s04_interoceptive_self_binding_checkpoint") < ids.index(
        "rt01.s05_multi_cause_attribution_checkpoint"
    )
    assert ids.index("rt01.s05_multi_cause_attribution_checkpoint") < ids.index(
        "rt01.s_minimal_contour_checkpoint"
    )


def test_subject_tick_carries_typed_s05_result_for_downstream_consumers() -> None:
    result = _result("rt-s05-typed")
    packet = result.s05_result.state.packets[-1]
    assert result.s05_result.state.factorization_id.startswith("s05-factorization:")
    assert packet.outcome_packet_id.startswith("s05-outcome:")
    assert isinstance(result.s05_result.state.dominant_cause_classes, tuple)
    assert isinstance(result.s05_result.state.unexplained_residual, float)
    assert isinstance(result.s05_result.gate.restrictions, tuple)


def test_subject_tick_s05_low_residual_route_requirement_is_load_bearing() -> None:
    baseline = _result(
        "rt-s05-low-residual-baseline",
        unresolved=True,
        context=SubjectTickContext(
            context_shift_markers=("shift:s05",),
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    required = _result(
        "rt-s05-low-residual-required",
        unresolved=True,
        context=SubjectTickContext(
            context_shift_markers=("shift:s05",),
            dependency_trigger_hits=("trigger:mode_shift",),
            require_s05_low_residual_learning_route=True,
        ),
    )
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    if not required.s05_result.gate.learning_route_ready:
        assert required_checkpoint.status.value == "enforced_detour"
        assert required.state.final_execution_outcome in {
            SubjectTickOutcome.REVALIDATE,
            SubjectTickOutcome.REPAIR,
            SubjectTickOutcome.HALT,
        }


def test_subject_tick_s05_checkpoint_restrictions_are_downstream_visible() -> None:
    result = _result(
        "rt-s05-restrictions",
        context=SubjectTickContext(
            require_s05_factorized_consumer=True,
            require_s05_low_residual_learning_route=True,
        ),
    )
    restrictions = set(result.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.S05_MULTI_CAUSE_ATTRIBUTION_CONTRACT_MUST_BE_READ in restrictions
    assert SubjectTickRestrictionCode.S05_FACTORIZED_CONSUMER_REQUIRED in restrictions
    assert (
        SubjectTickRestrictionCode.S05_LOW_RESIDUAL_LEARNING_ROUTE_REQUIRED
        in restrictions
    )
    assert SubjectTickRestrictionCode.S05_SINGLE_CAUSE_COLLAPSE_FORBIDDEN in restrictions


def test_subject_tick_s05_disabled_enforcement_marks_checkpoint_detour() -> None:
    result = _result(
        "rt-s05-disabled",
        context=SubjectTickContext(disable_s05_enforcement=True),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "disabled" in checkpoint.reason

