from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.s05_multi_cause_attribution_factorization import (
    S05CauseClass,
    S05DownstreamRouteClass,
)
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


def _force_s05_shape(
    result,
    *,
    route_class: S05DownstreamRouteClass,
    dominant: tuple[S05CauseClass, ...],
    residual: float,
    factorization_ready: bool,
    learning_ready: bool,
    no_binary_recollapse_required: bool,
):
    latest = result.state.packets[-1]
    latest = replace(
        latest,
        downstream_route_class=route_class,
        unexplained_residual=residual,
    )
    state = replace(
        result.state,
        packets=(*result.state.packets[:-1], latest),
        dominant_cause_classes=dominant,
        unexplained_residual=residual,
    )
    gate = replace(
        result.gate,
        factorization_consumer_ready=factorization_ready,
        learning_route_ready=learning_ready,
        no_binary_recollapse_required=no_binary_recollapse_required,
    )
    telemetry = replace(
        result.telemetry,
        downstream_route_class=route_class,
        dominant_slot_count=len(dominant),
        residual_share=residual,
        factorization_consumer_ready=factorization_ready,
        learning_route_ready=learning_ready,
    )
    return replace(
        result,
        state=state,
        gate=gate,
        telemetry=telemetry,
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


def test_subject_tick_s05_low_residual_route_requirement_is_load_bearing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import substrate.subject_tick.update as subject_tick_update

    original = subject_tick_update.build_s05_multi_cause_attribution_factorization

    def _patched_builder(*, tick_id: str, **kwargs):
        result = original(tick_id=tick_id, **kwargs)
        if "rt-s05-low-residual-required" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
                dominant=(S05CauseClass.UNEXPLAINED_RESIDUAL,),
                residual=0.62,
                factorization_ready=True,
                learning_ready=False,
                no_binary_recollapse_required=True,
            )
        if "rt-s05-low-residual-baseline" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.WORLD_HEAVY,
                dominant=(S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,),
                residual=0.34,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=False,
            )
        return result

    monkeypatch.setattr(
        subject_tick_update,
        "build_s05_multi_cause_attribution_factorization",
        _patched_builder,
    )
    baseline = _result(
        "rt-s05-low-residual-baseline",
        unresolved=False,
        context=SubjectTickContext(),
    )
    required = _result(
        "rt-s05-low-residual-required",
        unresolved=False,
        context=SubjectTickContext(
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
    assert required.s05_result.gate.learning_route_ready is False
    assert required_checkpoint.status.value == "enforced_detour"
    assert required.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_s05_default_split_sensitive_contrast_with_matched_residual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import substrate.subject_tick.update as subject_tick_update

    original = subject_tick_update.build_s05_multi_cause_attribution_factorization

    def _patched_builder(*, tick_id: str, **kwargs):
        result = original(tick_id=tick_id, **kwargs)
        if "rt-s05-shape-mixed" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.MIXED_FACTORIZED,
                dominant=(
                    S05CauseClass.SELF_INITIATED_ACT,
                    S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
                ),
                residual=0.36,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=True,
            )
        if "rt-s05-shape-world" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.WORLD_HEAVY,
                dominant=(S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,),
                residual=0.35,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=False,
            )
        return result

    monkeypatch.setattr(
        subject_tick_update,
        "build_s05_multi_cause_attribution_factorization",
        _patched_builder,
    )
    mixed = _result("rt-s05-shape-mixed", unresolved=False, context=SubjectTickContext())
    world = _result("rt-s05-shape-world", unresolved=False, context=SubjectTickContext())
    mixed_checkpoint = next(
        checkpoint
        for checkpoint in mixed.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    world_checkpoint = next(
        checkpoint
        for checkpoint in world.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    assert abs(mixed.s05_result.state.unexplained_residual - world.s05_result.state.unexplained_residual) <= 0.02
    assert mixed.s05_result.state.packets[-1].downstream_route_class.value == "mixed_factorized"
    assert world.s05_result.state.packets[-1].downstream_route_class.value == "world_heavy"
    assert mixed_checkpoint.status.value == "enforced_detour"
    assert "split_shape_mixed_internal_external" in mixed_checkpoint.required_action
    assert mixed.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert world_checkpoint.status.value == "allowed"
    assert "split_shape_world_or_artifact_heavy" in world_checkpoint.required_action
    assert world.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_subject_tick_s05_single_cause_collapse_restriction_is_shape_aware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import substrate.subject_tick.update as subject_tick_update

    original = subject_tick_update.build_s05_multi_cause_attribution_factorization

    def _patched_builder(*, tick_id: str, **kwargs):
        result = original(tick_id=tick_id, **kwargs)
        if "rt-s05-collapse-mixed" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.MIXED_FACTORIZED,
                dominant=(
                    S05CauseClass.SELF_INITIATED_ACT,
                    S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
                ),
                residual=0.34,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=True,
            )
        if "rt-s05-collapse-world" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.WORLD_HEAVY,
                dominant=(S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,),
                residual=0.33,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=False,
            )
        return result

    monkeypatch.setattr(
        subject_tick_update,
        "build_s05_multi_cause_attribution_factorization",
        _patched_builder,
    )
    mixed = _result("rt-s05-collapse-mixed", unresolved=False)
    world = _result("rt-s05-collapse-world", unresolved=False)
    mixed_restrictions = set(mixed.downstream_gate.restrictions)
    world_restrictions = set(world.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.S05_SINGLE_CAUSE_COLLAPSE_FORBIDDEN in mixed_restrictions
    assert SubjectTickRestrictionCode.S05_SINGLE_CAUSE_COLLAPSE_FORBIDDEN not in world_restrictions


def test_subject_tick_s05_checkpoint_restrictions_are_downstream_visible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import substrate.subject_tick.update as subject_tick_update

    original = subject_tick_update.build_s05_multi_cause_attribution_factorization

    def _patched_builder(*, tick_id: str, **kwargs):
        result = original(tick_id=tick_id, **kwargs)
        if "rt-s05-restrictions" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.MIXED_FACTORIZED,
                dominant=(
                    S05CauseClass.SELF_INITIATED_ACT,
                    S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
                ),
                residual=0.34,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=True,
            )
        return result

    monkeypatch.setattr(
        subject_tick_update,
        "build_s05_multi_cause_attribution_factorization",
        _patched_builder,
    )
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
