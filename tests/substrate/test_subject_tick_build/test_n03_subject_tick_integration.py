from __future__ import annotations

from dataclasses import replace

from substrate.n03_autobiographical_relevance import (
    N03AutobiographicalTraceKind,
    N03CurrentTargetKind,
)
from substrate.subject_tick import SubjectTickContext
from tests.substrate.n03_autobiographical_relevance_testkit import (
    n03_bundle,
    n03_target,
    n03_trace,
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


def _base_context() -> SubjectTickContext:
    return SubjectTickContext()


def _bundle(case_id: str, *, variant: str):
    if variant == "strong":
        trace = n03_trace(
            source_trace_id=f"{case_id}:trace:strong",
            trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE,
            commitment_refs=("commitment:alpha",),
            recurrence_count=4,
            confidence=0.86,
        )
        target = n03_target(
            current_target_id=f"{case_id}:target:strong",
            target_kind=N03CurrentTargetKind.COMMITMENT_UNDER_LOAD,
            active_commitment_refs=("commitment:alpha",),
            regulation_or_planning_pressure=0.78,
        )
    elif variant == "semantic_only":
        trace = n03_trace(
            source_trace_id=f"{case_id}:trace:semantic",
            commitment_refs=(),
            capability_gap_refs=(),
            affordance_refs=(),
            internal_tool_refs=(),
            self_binding_refs=(),
            identity_region_refs=(),
            semantic_topic_tags=("topic:regulation",),
            recency_hint=0.9,
            vividness_hint=0.9,
        )
        target = n03_target(
            current_target_id=f"{case_id}:target:semantic",
            active_commitment_refs=(),
            active_capability_gap_refs=(),
            active_affordance_refs=(),
            active_internal_tool_refs=(),
            active_self_binding_refs=(),
            active_identity_region_refs=(),
            semantic_topic_tags=("topic:regulation",),
        )
    elif variant == "drift_blocked":
        trace = n03_trace(
            source_trace_id=f"{case_id}:trace:drift",
            trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY,
            commitment_refs=("commitment:alpha",),
            recurrence_count=3,
        )
        target = n03_target(
            current_target_id=f"{case_id}:target:drift",
            target_kind=N03CurrentTargetKind.RECOVERY_NEED,
            active_commitment_refs=("commitment:alpha",),
            active_drift_markers=("drift_fracture",),
        )
    elif variant == "conflict":
        trace = (
            n03_trace(
                source_trace_id=f"{case_id}:trace:failure",
                trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE,
                recurrence_count=3,
            ),
            n03_trace(
                source_trace_id=f"{case_id}:trace:recovery",
                trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY,
                recurrence_count=3,
            ),
        )
        target = (
            n03_target(
                current_target_id=f"{case_id}:target:conflict",
                target_kind=N03CurrentTargetKind.RECOVERY_NEED,
            ),
        )
        return n03_bundle(
            bundle_id=f"{case_id}:n03:bundle",
            traces=trace,
            targets=target,
            source_lineage=("tests.n03.integration", case_id),
            reason=variant,
        )
    else:
        raise ValueError(variant)

    return n03_bundle(
        bundle_id=f"{case_id}:n03:bundle",
        traces=(trace,),
        targets=(target,),
        source_lineage=("tests.n03.integration", case_id),
        reason=variant,
    )


def _n03_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.n03_autobiographical_relevance_checkpoint"
    )


def test_n03_checkpoint_is_after_n02_and_before_outcome_resolution() -> None:
    case_id = "rt-n03-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n03_input_bundle=_bundle(case_id, variant="strong"),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.n02_identity_drift_reflection_checkpoint") < ids.index(
        "rt01.n03_autobiographical_relevance_checkpoint"
    )
    assert ids.index("rt01.n03_autobiographical_relevance_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_no_n03_basis_does_not_add_false_friction() -> None:
    case_id = "rt-n03-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n03_input_bundle=None,
        ),
    )
    checkpoint = _n03_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "n03_optional"
    assert result.state.n03_explicit_basis_present is False


def test_consumer_ready_autobiographical_packet_is_visible_in_typed_state() -> None:
    case_id = "rt-n03-consumer-ready"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n03_input_bundle=_bundle(case_id, variant="strong"),
        ),
    )
    assert result.state.n03_consumer_ready is True
    assert result.state.n03_relevant_trace_count > 0


def test_same_checkpoint_envelope_with_different_typed_n03_shape_changes_gate_outcome() -> None:
    common = {
        "disable_n03_enforcement": True,
        "require_n03_transfer_packet_consumer": True,
    }
    strong_case = "rt-n03-envelope-strong"
    weak_case = "rt-n03-envelope-weak"

    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            **common,
            n03_input_bundle=_bundle(strong_case, variant="strong"),
        ),
    )
    weak = _result(
        weak_case,
        context=replace(
            _base_context(),
            **common,
            n03_input_bundle=_bundle(weak_case, variant="semantic_only"),
        ),
    )

    strong_checkpoint = _n03_checkpoint(strong)
    weak_checkpoint = _n03_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong_checkpoint.required_action == "require_n03_transfer_packet_consumer"
    assert strong.state.n03_consumer_ready is True
    assert weak.state.n03_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    assert weak.downstream_gate.accepted is False


def test_drift_blocked_old_trace_produces_restriction_not_clean_transfer() -> None:
    case_id = "rt-n03-drift-blocked"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n03_input_bundle=_bundle(case_id, variant="drift_blocked"),
        ),
    )
    assert result.state.n03_provisional_transfer_count > 0 or result.state.n03_blocked_transfer_count > 0
    restriction_values = {item.value for item in result.downstream_gate.restrictions}
    assert (
        "n03_caution_route_required" in restriction_values
        or "n03_blocked_transfer_detour_required" in restriction_values
    )


def test_conflicting_autobiographical_traces_produce_guarded_gate_state() -> None:
    case_id = "rt-n03-conflict"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n03_input_bundle=_bundle(case_id, variant="conflict"),
        ),
    )
    assert result.state.n03_conflict_count > 0
    assert result.downstream_gate.usability_class.value in {"degraded_bounded", "blocked"}
    restriction_values = {item.value for item in result.downstream_gate.restrictions}
    assert "n03_conflict_review_required" in restriction_values


def test_semantic_only_trace_does_not_behave_like_structural_autobiographical_relevance() -> None:
    strong_case = "rt-n03-semantic-contrast-strong"
    weak_case = "rt-n03-semantic-contrast-weak"
    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            n03_input_bundle=_bundle(strong_case, variant="strong"),
        ),
    )
    weak = _result(
        weak_case,
        context=replace(
            _base_context(),
            n03_input_bundle=_bundle(weak_case, variant="semantic_only"),
        ),
    )
    assert strong.state.n03_relevant_trace_count > weak.state.n03_relevant_trace_count
    assert weak.state.n03_blocked_transfer_count > 0
    assert strong.downstream_gate.accepted is True
    assert weak.downstream_gate.usability_class.value in {"degraded_bounded", "blocked"}
