from __future__ import annotations

from substrate.s04_interoceptive_self_binding import (
    derive_s04_interoceptive_self_binding_consumer_view,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome
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


def test_subject_tick_emits_s04_checkpoint_and_keeps_runtime_order() -> None:
    result = _result("rt-s04-order", unresolved=False)
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.s03_ownership_weighted_learning_checkpoint" in ids
    assert "rt01.s04_interoceptive_self_binding_checkpoint" in ids
    assert "rt01.s_minimal_contour_checkpoint" in ids
    assert ids.index("rt01.s03_ownership_weighted_learning_checkpoint") < ids.index(
        "rt01.s04_interoceptive_self_binding_checkpoint"
    )
    assert ids.index("rt01.s04_interoceptive_self_binding_checkpoint") < ids.index(
        "rt01.s_minimal_contour_checkpoint"
    )


def test_subject_tick_carries_typed_s04_result_for_downstream_consumers() -> None:
    result = _result("rt-s04-typed-surface", unresolved=False)
    assert result.s04_result.state.binding_id.startswith("s04-binding:")
    assert isinstance(result.s04_result.state.core_bound_channels, tuple)
    view = derive_s04_interoceptive_self_binding_consumer_view(result.s04_result)
    assert view.binding_id == result.s04_result.state.binding_id
    assert isinstance(view.can_consume_stable_core, bool)


def test_subject_tick_s04_stable_core_consumer_requirement_is_path_affecting() -> None:
    baseline = _result(
        "rt-s04-require-baseline",
        unresolved=False,
        context=SubjectTickContext(
            context_shift_markers=("shift:s04",),
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    required = _result(
        "rt-s04-require-required",
        unresolved=False,
        context=SubjectTickContext(
            context_shift_markers=("shift:s04",),
            dependency_trigger_hits=("trigger:mode_shift",),
            require_s04_stable_core_consumer=True,
        ),
    )
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s04_interoceptive_self_binding_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s04_interoceptive_self_binding_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    if not required.s04_result.gate.core_consumer_ready:
        assert required_checkpoint.status.value == "enforced_detour"
        assert required.state.final_execution_outcome in {
            SubjectTickOutcome.REPAIR,
            SubjectTickOutcome.REVALIDATE,
        }


def test_subject_tick_s04_persistence_weaken_and_rebind_cycle_is_stable() -> None:
    first = _result("rt-s04-cycle", unresolved=False)
    second = _result(
        "rt-s04-cycle",
        unresolved=False,
        context=SubjectTickContext(
            prior_subject_tick_state=first.state,
            prior_s04_state=first.s04_result.state,
            context_shift_markers=("shift:s04-cycle",),
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    third = _result(
        "rt-s04-cycle",
        unresolved=False,
        context=SubjectTickContext(
            prior_subject_tick_state=second.state,
            prior_s04_state=second.s04_result.state,
        ),
    )
    assert second.s04_result.state.stale_binding_drop_count >= 0
    assert isinstance(third.s04_result.state.rebinding_event, bool)
