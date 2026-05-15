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
from substrate.w04_applicability_gating import build_w04_applicability_gating
from tests.substrate.subject_tick_testkit import build_subject_tick
from tests.substrate.w03_schema_consolidation_testkit import w03_input_from_w02
from tests.substrate.w04_applicability_gating_testkit import w04_input_from_w03_result
from tests.substrate.w05_predictive_prior_injection_testkit import (
    clone_input as clone_w05_input,
    w05_input_from_w04_result,
)
from substrate.w05_predictive_prior_injection import W05InjectionTarget


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
        provenance_ref=("tests.w05.integration", case_id),
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
        source_lineage=("tests.w05.integration", case_id),
        reason=variant,
    )


def _w03_bundle(case_id: str, *, w02_input: W02InputBundle):
    return w03_input_from_w02(
        case_id=case_id,
        w02_input=w02_input,
        source_lineage=("tests.w05.integration", case_id),
    )


def _w04_bundle(case_id: str, *, w03_input):
    w03_result = build_w03_schema_consolidation(
        tick_id=f"tests.w05.integration:{case_id}:w03",
        tick_index=1,
        input_bundle=w03_input,
        enforcement_enabled=True,
    )
    return w04_input_from_w03_result(case_id=case_id, w03_result=w03_result)


def _w05_bundle(case_id: str, *, w04_input):
    w04_result = build_w04_applicability_gating(
        tick_id=f"tests.w05.integration:{case_id}:w04",
        tick_index=1,
        input_bundle=w04_input,
        enforcement_enabled=True,
    )
    base = w05_input_from_w04_result(case_id=case_id, w04_result=w04_result)
    return clone_w05_input(
        base,
        permitted_signal=replace(
            base.permitted_signal,
            permitted_status="allowed",
            may_deploy_candidate=True,
            may_use_as_hint_only=False,
            may_use_after_revalidation=False,
            may_use_with_relaxation=False,
            must_abstain=False,
            must_block=False,
            must_revalidate=False,
        ),
    )


def _w05_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w05_predictive_prior_injection_checkpoint"
    )


def test_w05_checkpoint_emitted_after_w04_before_m01() -> None:
    case_id = "rt-w05-order"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.w04_applicability_gating_checkpoint") < ids.index(
        "rt01.w05_predictive_prior_injection_checkpoint"
    )
    assert ids.index("rt01.w05_predictive_prior_injection_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_w05_compact_fields_projected_into_subject_tick_state() -> None:
    case_id = "rt-w05-state"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
        ),
    )
    assert result.state.w05_checkpoint_present is True
    assert result.state.w05_signal_stack_count >= 1
    assert result.state.w05_must_not_execute_update_count >= 1


def test_clean_w05_path_is_less_restrictive_than_blocked_path() -> None:
    clean_case = "rt-w05-clean"
    blocked_case = "rt-w05-blocked"

    clean_w02 = _w02_bundle(clean_case, variant="clean")
    clean_w03 = _w03_bundle(clean_case, w02_input=clean_w02)
    clean_w04 = _w04_bundle(clean_case, w03_input=clean_w03)
    clean_w05 = _w05_bundle(clean_case, w04_input=clean_w04)

    blocked_w02 = _w02_bundle(blocked_case, variant="clean")
    blocked_w03 = _w03_bundle(blocked_case, w02_input=blocked_w02)
    blocked_w04 = _w04_bundle(blocked_case, w03_input=blocked_w03)
    blocked_w05 = _w05_bundle(blocked_case, w04_input=blocked_w04)
    blocked_w05 = clone_w05_input(
        blocked_w05,
        permitted_signal=replace(
            blocked_w05.permitted_signal,
            may_deploy_candidate=False,
            must_block=True,
        ),
    )

    clean = _result(
        clean_case,
        context=replace(_base_context(), w02_input_bundle=clean_w02, w03_input_bundle=clean_w03, w04_input_bundle=clean_w04, w05_input_bundle=clean_w05),
    )
    blocked = _result(
        blocked_case,
        context=replace(_base_context(), w02_input_bundle=blocked_w02, w03_input_bundle=blocked_w03, w04_input_bundle=blocked_w04, w05_input_bundle=blocked_w05),
    )

    clean_restrictions = {item.value for item in clean.downstream_gate.restrictions}
    blocked_restrictions = {item.value for item in blocked.downstream_gate.restrictions}
    assert "w05_permitted_channel_block_restriction" in blocked_restrictions
    assert "w05_permitted_channel_block_restriction" not in clean_restrictions


def test_w05_permitted_block_revalidate_escalate_abstain_change_gate_restrictions() -> None:
    case_id = "rt-w05-routes"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w05_input = clone_w05_input(
        w05_input,
            permitted_signal=replace(
                w05_input.permitted_signal,
                may_deploy_candidate=False,
                must_revalidate=True,
                protected_targets=(
                    W05InjectionTarget.POLICY_INTERFACE,
                ),
                must_abstain=True,
            ),
        )
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input, w05_input_bundle=w05_input),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w05_revalidate_route_restriction" in restrictions
    assert "w05_protected_target_block_restriction" in restrictions
    assert "w05_must_abstain_restriction" in restrictions


def test_same_checkpoint_same_required_action_different_w05_shape_changes_gate_result() -> None:
    common = {
        "disable_w05_enforcement": True,
        "require_w05_routing_packet_consumer": True,
    }
    strong_case = "rt-w05-envelope-strong"
    weak_case = "rt-w05-envelope-weak"

    strong_w02 = _w02_bundle(strong_case, variant="clean")
    strong_w03 = _w03_bundle(strong_case, w02_input=strong_w02)
    strong_w04 = _w04_bundle(strong_case, w03_input=strong_w03)
    strong_w05 = _w05_bundle(strong_case, w04_input=strong_w04)

    weak_w02 = _w02_bundle(weak_case, variant="clean")
    weak_w03 = _w03_bundle(weak_case, w02_input=weak_w02)
    weak_w04 = _w04_bundle(weak_case, w03_input=weak_w03)
    weak_w05 = _w05_bundle(weak_case, w04_input=weak_w04)
    weak_w05 = clone_w05_input(
        weak_w05,
        permitted_signal=replace(
            weak_w05.permitted_signal,
            may_deploy_candidate=False,
            must_block=True,
        ),
    )

    strong = _result(
        strong_case,
        context=replace(_base_context(), **common, w02_input_bundle=strong_w02, w03_input_bundle=strong_w03, w04_input_bundle=strong_w04, w05_input_bundle=strong_w05),
    )
    weak = _result(
        weak_case,
        context=replace(_base_context(), **common, w02_input_bundle=weak_w02, w03_input_bundle=weak_w03, w04_input_bundle=weak_w04, w05_input_bundle=weak_w05),
    )

    strong_checkpoint = _w05_checkpoint(strong)
    weak_checkpoint = _w05_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong.state.w05_consumer_ready is True
    assert weak.state.w05_consumer_ready is False
    strong_restrictions = {item.value for item in strong.downstream_gate.restrictions}
    weak_restrictions = {item.value for item in weak.downstream_gate.restrictions}
    assert "w05_routing_packet_consumer_required" in weak_restrictions
    assert weak_restrictions != strong_restrictions


def test_w04_compatibility_remains_intact_with_w05_enabled() -> None:
    case_id = "rt-w05-w04-compat"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input, w05_input_bundle=w05_input),
    )
    assert result.state.w04_checkpoint_present is True
    assert result.w04_result.downstream_permission_packets


def test_w05_no_clean_path_is_honest_and_non_crashing() -> None:
    case_id = "rt-w05-no-clean"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input, w05_input_bundle=None),
    )
    checkpoint = _w05_checkpoint(result)
    assert checkpoint.checkpoint_id == "rt01.w05_predictive_prior_injection_checkpoint"
    assert result.state.w05_no_clean_routing is True
    assert result.state.w05_consumer_ready is False


def test_w05_approval_is_not_update_execution_and_not_action_authorization() -> None:
    case_id = "rt-w05-not-exec"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input, w05_input_bundle=w05_input),
    )
    assert result.w05_result.downstream_routing_packets
    packet = result.w05_result.downstream_routing_packets[0]
    assert packet.must_not_execute_update is True
    assert packet.execution_authorization_granted is False


def test_ambiguous_mismatch_and_protected_target_block_add_exact_tokens() -> None:
    case_id = "rt-w05-ambiguous-protected"
    w02_input = _w02_bundle(case_id, variant="clean")
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w05_input = clone_w05_input(
        w05_input,
        observed_signal=replace(
            w05_input.observed_signal,
            observed_outcome="obs:other",
            evidence_precision=0.95,
            contradiction_markers=("c1",),
        ),
        permitted_signal=replace(
            w05_input.permitted_signal,
            protected_targets=(W05InjectionTarget.VALIDITY_MODEL,),
        ),
    )
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=w03_input, w04_input_bundle=w04_input, w05_input_bundle=w05_input),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w05_ambiguous_mismatch_restriction" in restrictions
    assert "w05_protected_target_block_restriction" in restrictions
