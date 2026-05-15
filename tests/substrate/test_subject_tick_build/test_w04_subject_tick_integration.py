from __future__ import annotations

from dataclasses import replace

from substrate.subject_tick import SubjectTickContext
from substrate.w02_regularity_extraction import (
    W02InputBundle,
    W02PresenceMode,
    W02RegularityCandidateType,
    W02TraceRef,
)
from substrate.w03_schema_consolidation import build_w03_schema_consolidation
from tests.substrate.subject_tick_testkit import build_subject_tick
from tests.substrate.w03_schema_consolidation_testkit import w03_input_from_w02
from tests.substrate.w04_applicability_gating_testkit import (
    clone_input,
    w04_input_from_w03_result,
)


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
        provenance_ref=("tests.w04.integration", case_id),
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
        candidate_type=W02RegularityCandidateType.KIND,
    )
    return replace(base, **overrides)


def _w02_bundle(case_id: str, *, variant: str) -> W02InputBundle:
    if variant == "clean":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, source_authority="trusted_world_provider"),
            _trace(case_id, trace_id="t2", sequence=2, source_authority="weak_scaffold_provider"),
            _trace(case_id, trace_id="t3", sequence=3, source_authority="trusted_world_provider"),
        )
    elif variant == "contested":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, presence_mode=W02PresenceMode.PRESENT),
            _trace(case_id, trace_id="t2", sequence=2, presence_mode=W02PresenceMode.ABSENT),
        )
    elif variant == "scaffold":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            _trace(case_id, trace_id="t2", sequence=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        )
    else:
        raise ValueError(variant)

    return W02InputBundle(
        bundle_id=f"{case_id}:w02:bundle",
        traces=traces,
        source_lineage=("tests.w04.integration", case_id),
        reason=variant,
    )


def _w03_bundle(case_id: str, *, w02_input: W02InputBundle):
    return w03_input_from_w02(
        case_id=case_id,
        w02_input=w02_input,
        source_lineage=("tests.w04.integration", case_id),
    )


def _w04_bundle(case_id: str, *, w03_input):
    w03_result = build_w03_schema_consolidation(
        tick_id=f"tests.w04.integration:{case_id}",
        tick_index=1,
        input_bundle=w03_input,
        enforcement_enabled=True,
    )
    return w04_input_from_w03_result(case_id=case_id, w03_result=w03_result)


def _force_clean_w04_bundle(w04_input):
    if not w04_input.w03_intake_views:
        return w04_input
    intake_views = tuple(
        replace(
            item,
            may_use_as_bounded_prior=True,
            may_use_as_schema_hint=True,
            must_revalidate_before_use=False,
            must_preserve_contradiction=False,
            must_abstain=False,
            contradiction_status=(),
            stale_or_revalidation_status=(),
        )
        for item in w04_input.w03_intake_views
    )
    authority = intake_views[0].authority_scope[0] if intake_views[0].authority_scope else "trusted_authority"
    desired = replace(w04_input.desired_state_request, source_authority=authority)
    return clone_input(w04_input, w03_intake_views=intake_views, desired_state_request=desired)


def _w04_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w04_applicability_gating_checkpoint"
    )


def test_w04_checkpoint_emitted_after_w03_before_m01() -> None:
    case_id = "rt-w04-order"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.w03_schema_consolidation_checkpoint") < ids.index(
        "rt01.w04_applicability_gating_checkpoint"
    )
    assert ids.index("rt01.w04_applicability_gating_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_w04_compact_fields_projected_into_state() -> None:
    case_id = "rt-w04-state"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _force_clean_w04_bundle(_w04_bundle(case_id, w03_input=w03_input))
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
        ),
    )
    assert result.state.w04_checkpoint_present is True
    assert result.state.w04_applicability_decision_count >= 1
    assert result.state.w04_consumer_ready is True
    assert result.state.w04_no_clean_applicability is False
    assert result.state.w04_malformed_desired_state_count == 0
    assert result.state.w04_authority_block_count == 0


def test_clean_allowed_w04_path_is_less_restrictive() -> None:
    clean_case = "rt-w04-clean"
    blocked_case = "rt-w04-blocked"

    clean_w02 = _w02_bundle(clean_case, variant="clean")
    clean_w03 = _w03_bundle(clean_case, w02_input=clean_w02)
    clean_w04 = _force_clean_w04_bundle(_w04_bundle(clean_case, w03_input=clean_w03))

    blocked_w02 = _w02_bundle(blocked_case, variant="clean")
    blocked_w03 = _w03_bundle(blocked_case, w02_input=blocked_w02)
    blocked_w04 = _w04_bundle(blocked_case, w03_input=blocked_w03)
    blocked_w04 = clone_input(
        blocked_w04,
        desired_state_request=replace(blocked_w04.desired_state_request, source_authority="mismatch_authority"),
    )

    clean = _result(
        clean_case,
        context=replace(_base_context(), w02_input_bundle=clean_w02, w03_input_bundle=clean_w03, w04_input_bundle=clean_w04),
    )
    blocked = _result(
        blocked_case,
        context=replace(_base_context(), w02_input_bundle=blocked_w02, w03_input_bundle=blocked_w03, w04_input_bundle=blocked_w04),
    )

    clean_restrictions = {item.value for item in clean.downstream_gate.restrictions}
    blocked_restrictions = {item.value for item in blocked.downstream_gate.restrictions}
    assert "w04_authority_scope_restriction" in blocked_restrictions
    assert "w04_authority_scope_restriction" not in clean_restrictions


def test_blocked_revalidate_abstain_w04_paths_change_gate_restrictions() -> None:
    case_id = "rt-w04-guarded-malformed"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _force_clean_w04_bundle(_w04_bundle(case_id, w03_input=w03_input))
    w04_input = clone_input(
        w04_input,
        desired_state_request=replace(
            w04_input.desired_state_request,
            target_subject="",
        ),
    )
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w04_malformed_desired_state_restriction" in restrictions
    assert result.state.w04_malformed_desired_state_count > 0


def test_same_checkpoint_envelope_same_required_action_different_w04_shape_changes_gate_result() -> None:
    common = {
        "disable_w04_enforcement": True,
        "require_w04_applicability_packet_consumer": True,
    }
    strong_case = "rt-w04-envelope-strong"
    weak_case = "rt-w04-envelope-weak"

    strong_w02 = _w02_bundle(strong_case, variant="clean")
    strong_w03 = _w03_bundle(strong_case, w02_input=strong_w02)
    strong_w04 = _force_clean_w04_bundle(_w04_bundle(strong_case, w03_input=strong_w03))

    weak_w02 = _w02_bundle(weak_case, variant="clean")
    weak_w03 = _w03_bundle(weak_case, w02_input=weak_w02)
    weak_w04 = _force_clean_w04_bundle(_w04_bundle(weak_case, w03_input=weak_w03))
    weak_w04 = clone_input(
        weak_w04,
        desired_state_request=replace(weak_w04.desired_state_request, source_authority="other_authority"),
    )

    strong = _result(
        strong_case,
        context=replace(_base_context(), **common, w02_input_bundle=strong_w02, w03_input_bundle=strong_w03, w04_input_bundle=strong_w04),
    )
    weak = _result(
        weak_case,
        context=replace(_base_context(), **common, w02_input_bundle=weak_w02, w03_input_bundle=weak_w03, w04_input_bundle=weak_w04),
    )

    strong_checkpoint = _w04_checkpoint(strong)
    weak_checkpoint = _w04_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong.state.w04_consumer_ready is True
    assert weak.state.w04_consumer_ready is False
    strong_restrictions = {item.value for item in strong.downstream_gate.restrictions}
    weak_restrictions = {item.value for item in weak.downstream_gate.restrictions}
    assert "w04_applicability_packet_consumer_required" in weak_restrictions
    assert weak_restrictions != strong_restrictions


def test_w03_compatibility_remains_intact_when_w04_enabled() -> None:
    case_id = "rt-w04-w03-compat"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input),
    )
    assert result.state.w03_checkpoint_present is True
    assert result.w03_result.schema_candidates


def test_w04_no_clean_path_is_honest_and_non_crashing() -> None:
    case_id = "rt-w04-no-clean"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=None),
    )
    checkpoint = _w04_checkpoint(result)
    assert checkpoint.checkpoint_id == "rt01.w04_applicability_gating_checkpoint"
    assert result.state.w04_no_clean_applicability is True
    assert result.state.w04_consumer_ready is False


def test_w04_approval_is_not_action_authorization() -> None:
    case_id = "rt-w04-no-action-auth"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input),
    )
    assert result.w04_result.downstream_permission_packets
    assert result.w04_result.downstream_permission_packets[0].action_authorization_granted is False
