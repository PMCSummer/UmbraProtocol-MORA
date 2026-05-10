from __future__ import annotations

from dataclasses import replace

from substrate.subject_tick import SubjectTickContext
from substrate.w02_regularity_extraction import (
    W02InputBundle,
    W02PresenceMode,
    W02RegularityCandidateType,
    W02TraceRef,
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


def _trace(case_id: str, *, trace_id: str, sequence: int, **overrides) -> W02TraceRef:
    base = W02TraceRef(
        trace_id=f"{case_id}:{trace_id}",
        sequence_index=sequence,
        entity_id=f"{case_id}:entity",
        source_authority="trusted_world_provider",
        presence_mode=W02PresenceMode.PRESENT,
        admission_state="admitted",
        confidence_band="high",
        provenance_ref=("tests.w02.integration", case_id),
        action_ref="action:a",
        effect_ref="effect:a",
        structural_signature="shape:cube",
        kind_label="kind:block",
        role_label="role:anchor",
        provider_label="provider:a",
        contradiction_markers=(),
        is_duplicate_packet=False,
        provider_bias_marker=False,
        text_artifact_marker=False,
        revoked=False,
        candidate_type=W02RegularityCandidateType.INSTANCE,
    )
    return replace(base, **overrides)


def _bundle(case_id: str, *, variant: str) -> W02InputBundle:
    if variant == "clean":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, source_authority="trusted_world_provider"),
            _trace(case_id, trace_id="t2", sequence=2, source_authority="weak_scaffold_provider"),
            _trace(case_id, trace_id="t3", sequence=3, source_authority="trusted_world_provider"),
        )
    elif variant == "scaffold_only":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            _trace(case_id, trace_id="t2", sequence=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        )
    elif variant == "contradiction":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, presence_mode=W02PresenceMode.PRESENT),
            _trace(case_id, trace_id="t2", sequence=2, presence_mode=W02PresenceMode.ABSENT),
        )
    elif variant == "no_basis":
        traces = ()
    elif variant == "blocked":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, provider_bias_marker=True),
            _trace(case_id, trace_id="t2", sequence=2, provider_bias_marker=True),
        )
    else:
        raise ValueError(variant)

    return W02InputBundle(
        bundle_id=f"{case_id}:w02:bundle",
        traces=traces,
        source_lineage=("tests.w02.integration", case_id),
        reason=variant,
    )


def _w02_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w02_regularity_extraction_checkpoint"
    )


def test_w02_checkpoint_is_after_w01_and_before_m01() -> None:
    case_id = "rt-w02-order"
    result = _result(case_id, context=replace(_base_context(), w02_input_bundle=_bundle(case_id, variant="clean")))
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.w01_bounded_world_loop_checkpoint") < ids.index(
        "rt01.w02_regularity_extraction_checkpoint"
    )
    assert ids.index("rt01.w02_regularity_extraction_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_subject_tick_state_includes_compact_w02_fields() -> None:
    case_id = "rt-w02-state"
    result = _result(case_id, context=replace(_base_context(), w02_input_bundle=_bundle(case_id, variant="clean")))
    assert result.state.w02_checkpoint_present is True
    assert result.state.w02_candidate_count >= 1
    assert result.state.w02_promoted_count >= 0


def test_same_checkpoint_envelope_with_different_w02_shape_changes_gate_behavior() -> None:
    common = {
        "disable_w02_enforcement": True,
        "require_w02_permission_packet_consumer": True,
    }
    strong_case = "rt-w02-envelope-strong"
    weak_case = "rt-w02-envelope-weak"

    strong = _result(
        strong_case,
        context=replace(_base_context(), **common, w02_input_bundle=_bundle(strong_case, variant="clean")),
    )
    weak = _result(
        weak_case,
        context=replace(_base_context(), **common, w02_input_bundle=_bundle(weak_case, variant="blocked")),
    )

    strong_checkpoint = _w02_checkpoint(strong)
    weak_checkpoint = _w02_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong.state.w02_consumer_ready is True
    assert weak.state.w02_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    strong_restrictions = {item.value for item in strong.downstream_gate.restrictions}
    weak_restrictions = {item.value for item in weak.downstream_gate.restrictions}
    assert "w02_permission_packet_consumer_required" in weak_restrictions
    assert "w02_no_clean_regularity_detour_required" not in strong_restrictions
    assert "w02_no_clean_regularity_detour_required" in weak_restrictions
    assert weak_restrictions != strong_restrictions
    assert len(weak_restrictions) > len(strong_restrictions)


def test_no_basis_path_does_not_fabricate_world_regularity() -> None:
    case_id = "rt-w02-no-basis"
    result = _result(case_id, context=replace(_base_context(), w02_input_bundle=_bundle(case_id, variant="no_basis")))
    checkpoint = _w02_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "w02_optional"
    assert result.state.w02_no_clean_regularities is True


def test_scaffold_only_state_produces_blocked_or_must_abstain_projection() -> None:
    case_id = "rt-w02-scaffold"
    result = _result(case_id, context=replace(_base_context(), w02_input_bundle=_bundle(case_id, variant="scaffold_only")))
    assert result.state.w02_must_abstain_count >= 0
    assert result.state.w02_promoted_count <= 1


def test_contradiction_state_causes_downstream_restriction() -> None:
    case_id = "rt-w02-contradiction"
    result = _result(case_id, context=replace(_base_context(), w02_input_bundle=_bundle(case_id, variant="contradiction")))
    assert result.state.w02_contradiction_count > 0
    restriction_values = {item.value for item in result.downstream_gate.restrictions}
    assert "w02_contradiction_review_required" in restriction_values


def test_clean_recurrent_scaffold_can_be_consumer_ready_without_stable_identity_claim() -> None:
    case_id = "rt-w02-clean"
    result = _result(case_id, context=replace(_base_context(), w02_input_bundle=_bundle(case_id, variant="clean")))
    assert result.state.w02_consumer_ready is True
    assert all(packet.may_claim_stable_identity is False for packet in result.w02_result.downstream_permission_packets)
