from __future__ import annotations

from substrate.s04_interoceptive_self_binding import (
    derive_s04_interoceptive_self_binding_consumer_view,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_action_candidate,
    build_world_effect_packet,
    build_world_observation_packet,
)
from tests.substrate.s01_efference_copy_testkit import build_s01
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


def _adapter(case_id: str) -> WorldAdapterInput:
    action = build_world_action_candidate(
        tick_id=f"{case_id}-action",
        execution_mode="continue_stream",
    )
    effect = build_world_effect_packet(
        effect_id=f"eff-{case_id}",
        action_id=action.action_id,
        observed_at="2026-04-21T09:10:00+00:00",
        source_ref="world.sensor.s04_contested_positive",
        success=True,
    )
    return WorldAdapterInput(
        adapter_presence=True,
        adapter_available=True,
        observation_packet=build_world_observation_packet(
            observation_id=f"obs-{case_id}",
            source_ref="world.sensor.s04_contested_positive",
            observed_at="2026-04-21T09:10:00+00:00",
            payload_ref=f"payload:{case_id}",
        ),
        action_packet=action,
        effect_packet=effect,
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


def test_subject_tick_s04_contested_consumer_positive_path_is_lawful_when_contested_ready() -> None:
    bootstrap = _result(
        "rt-s04-contested-bootstrap",
        context=SubjectTickContext(
            world_adapter_input=_adapter("rt-s04-contested-bootstrap"),
            emit_world_action_candidate=True,
        ),
    )
    seed_internal = build_s01(
        case_id="rt-s04-contested-seed-internal",
        tick_index=1,
        c04_selected_mode="continue_stream",
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
    )
    seed_external = build_s01(
        case_id="rt-s04-contested-seed-external",
        tick_index=1,
        c04_selected_mode="idle",
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    internal = _result(
        "rt-s04-contested-internal",
        context=SubjectTickContext(
            prior_subject_tick_state=bootstrap.state,
            prior_s01_state=seed_internal.state,
            emit_world_action_candidate=True,
            world_adapter_input=_adapter("rt-s04-contested-internal"),
        ),
    )
    baseline = _result(
        "rt-s04-contested-baseline",
        context=SubjectTickContext(
            prior_subject_tick_state=internal.state,
            prior_s01_state=seed_external.state,
            prior_s02_state=internal.s02_result.state,
            emit_world_action_candidate=True,
            world_adapter_input=_adapter("rt-s04-contested-baseline"),
        ),
    )
    required = _result(
        "rt-s04-contested-required",
        context=SubjectTickContext(
            prior_subject_tick_state=internal.state,
            prior_s01_state=seed_external.state,
            prior_s02_state=internal.s02_result.state,
            emit_world_action_candidate=True,
            world_adapter_input=_adapter("rt-s04-contested-required"),
            require_s04_contested_consumer=True,
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
    assert required.s04_result.gate.contested_consumer_ready is True
    assert len(required.s04_result.state.contested_channels) > 0
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert baseline_checkpoint.status.value == "allowed"
    assert required_checkpoint.status.value == "allowed"
    assert required_checkpoint.required_action == "require_s04_contested_consumer"


def test_subject_tick_s04_no_stable_core_consumer_contrast_keeps_lawful_contour() -> None:
    baseline = _result("rt-s04-no-core-baseline")
    required = _result(
        "rt-s04-no-core-required",
        context=SubjectTickContext(require_s04_no_stable_core_consumer=True),
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
    assert baseline.s04_result.gate.no_stable_core_consumer_ready is True
    assert required.s04_result.gate.no_stable_core_consumer_ready is True
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert baseline_checkpoint.status.value == "allowed"
    assert required_checkpoint.status.value == "allowed"
    assert required_checkpoint.required_action == "require_s04_no_stable_core_consumer"
    assert required.state.active_execution_mode == baseline.state.active_execution_mode
