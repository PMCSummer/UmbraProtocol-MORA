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
from substrate.w05_predictive_prior_injection import build_w05_predictive_prior_injection
from substrate.w06_error_driven_revision import W06MismatchClass
from tests.substrate.subject_tick_testkit import build_subject_tick
from tests.substrate.w03_schema_consolidation_testkit import w03_input_from_w02
from tests.substrate.w04_applicability_gating_testkit import w04_input_from_w03_result
from tests.substrate.w05_predictive_prior_injection_testkit import w05_input_from_w04_result
from tests.substrate.w06_error_driven_revision_testkit import clone_bundle as clone_w06_bundle
from tests.substrate.w06_error_driven_revision_testkit import (
    w06_bundle,
    w06_context,
    w06_mismatch,
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
        provenance_ref=("tests.w06.integration", case_id),
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


def _w02_bundle(case_id: str) -> W02InputBundle:
    traces = (
        _trace(case_id, trace_id="t1", sequence=1, source_authority="trusted_world_provider"),
        _trace(case_id, trace_id="t2", sequence=2, source_authority="weak_scaffold_provider"),
        _trace(case_id, trace_id="t3", sequence=3, source_authority="trusted_world_provider"),
    )
    return W02InputBundle(
        bundle_id=f"{case_id}:w02:bundle",
        traces=traces,
        source_lineage=("tests.w06.integration", case_id),
        reason="integration fixture",
    )


def _w03_bundle(case_id: str, *, w02_input: W02InputBundle):
    return w03_input_from_w02(
        case_id=case_id,
        w02_input=w02_input,
        source_lineage=("tests.w06.integration", case_id),
    )


def _w04_bundle(case_id: str, *, w03_input):
    w03_result = build_w03_schema_consolidation(
        tick_id=f"tests.w06.integration:{case_id}:w03",
        tick_index=1,
        input_bundle=w03_input,
        enforcement_enabled=True,
    )
    return w04_input_from_w03_result(case_id=case_id, w03_result=w03_result)


def _w05_bundle(case_id: str, *, w04_input):
    w04_result = build_w04_applicability_gating(
        tick_id=f"tests.w06.integration:{case_id}:w04",
        tick_index=1,
        input_bundle=w04_input,
        enforcement_enabled=True,
    )
    return w05_input_from_w04_result(case_id=case_id, w04_result=w04_result)


def _w06_bundle(case_id: str, *, w05_input):
    w05_result = build_w05_predictive_prior_injection(
        tick_id=f"tests.w06.integration:{case_id}:w05",
        tick_index=1,
        input_bundle=w05_input,
        enforcement_enabled=True,
    )
    base = w06_bundle(case_id)
    mismatch = w05_result.mismatch_classifications[0] if w05_result.mismatch_classifications else None
    if mismatch is None:
        return base
    class_name = str(getattr(getattr(mismatch, "mismatch_class", ""), "value", "predicted_vs_observed")).upper()
    try:
        mapped = W06MismatchClass[class_name]
    except KeyError:
        mapped = W06MismatchClass.PREDICTED_VS_OBSERVED
    return clone_w06_bundle(
        base,
        mismatch_intake=w06_mismatch(
            case_id,
            mismatch_class=mapped,
            severity=str(getattr(mismatch, "severity", "medium")),
            confidence=float(getattr(mismatch, "confidence", 0.7)),
            evidence_refs=tuple(getattr(mismatch, "evidence_refs", ())),
            ambiguity_markers=tuple(getattr(mismatch, "ambiguity_markers", ())),
        ),
    )


def _w06_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w06_error_driven_revision_checkpoint"
    )


def test_w06_checkpoint_emitted_after_w05_before_m01() -> None:
    case_id = "rt-w06-order"
    w02_input = _w02_bundle(case_id)
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w06_input = _w06_bundle(case_id, w05_input=w05_input)
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
            w06_input_bundle=w06_input,
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.w05_predictive_prior_injection_checkpoint") < ids.index(
        "rt01.w06_error_driven_revision_checkpoint"
    )
    assert ids.index("rt01.w06_error_driven_revision_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_w06_compact_fields_projected_into_subject_tick_state() -> None:
    case_id = "rt-w06-state"
    w02_input = _w02_bundle(case_id)
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w06_input = _w06_bundle(case_id, w05_input=w05_input)
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
            w06_input_bundle=w06_input,
        ),
    )
    assert result.state.w06_checkpoint_present is True
    assert result.state.w06_revision_decision_count >= 1
    assert result.state.w06_must_not_execute_correction is True


def test_w06_typed_shape_divergence_changes_gate_under_same_checkpoint_envelope() -> None:
    common = {
        "disable_w06_enforcement": True,
        "require_w06_revision_packet_consumer": True,
    }
    strong_case = "rt-w06-envelope-strong"
    weak_case = "rt-w06-envelope-weak"
    strong_w02 = _w02_bundle(strong_case)
    strong_w03 = _w03_bundle(strong_case, w02_input=strong_w02)
    strong_w04 = _w04_bundle(strong_case, w03_input=strong_w03)
    strong_w05 = _w05_bundle(strong_case, w04_input=strong_w04)
    strong_w06 = clone_w06_bundle(
        _w06_bundle(strong_case, w05_input=strong_w05),
        contradiction_intake=(),
        mismatch_intake=w06_mismatch(strong_case, mismatch_class=W06MismatchClass.NO_MISMATCH),
    )
    weak_w02 = _w02_bundle(weak_case)
    weak_w03 = _w03_bundle(weak_case, w02_input=weak_w02)
    weak_w04 = _w04_bundle(weak_case, w03_input=weak_w03)
    weak_w05 = _w05_bundle(weak_case, w04_input=weak_w04)
    weak_w06 = clone_w06_bundle(
        _w06_bundle(weak_case, w05_input=weak_w05),
        mismatch_intake=w06_mismatch(weak_case, mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
    )
    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            **common,
            w02_input_bundle=strong_w02,
            w03_input_bundle=strong_w03,
            w04_input_bundle=strong_w04,
            w05_input_bundle=strong_w05,
            w06_input_bundle=strong_w06,
        ),
    )
    weak = _result(
        weak_case,
        context=replace(
            _base_context(),
            **common,
            w02_input_bundle=weak_w02,
            w03_input_bundle=weak_w03,
            w04_input_bundle=weak_w04,
            w05_input_bundle=weak_w05,
            w06_input_bundle=weak_w06,
        ),
    )
    strong_checkpoint = _w06_checkpoint(strong)
    weak_checkpoint = _w06_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    strong_restrictions = {item.value for item in strong.downstream_gate.restrictions}
    weak_restrictions = {item.value for item in weak.downstream_gate.restrictions}
    assert "w06_claim_blocked_restriction" in weak_restrictions
    assert weak_restrictions != strong_restrictions


def test_w06_claim_block_route_adds_exact_claim_block_token() -> None:
    case_id = "rt-w06-claim-block"
    w02_input = _w02_bundle(case_id)
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w06_input = clone_w06_bundle(
        _w06_bundle(case_id, w05_input=w05_input),
        mismatch_intake=w06_mismatch(case_id, mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
    )
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
            w06_input_bundle=w06_input,
        ),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w06_claim_blocked_restriction" in restrictions
    assert "w06_residual_uncertainty_restriction" in restrictions


def test_w06_repeated_revalidation_route_adds_anti_paralysis_token() -> None:
    case_id = "rt-w06-anti"
    w02_input = _w02_bundle(case_id)
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w06_input = clone_w06_bundle(
        _w06_bundle(case_id, w05_input=w05_input),
        contradiction_intake=(),
        mismatch_intake=w06_mismatch(case_id, mismatch_class=W06MismatchClass.VALIDITY),
        revision_context=w06_context(case_id, repeated_revalidation_count=5, progress_detected=False, loop_threshold=3),
    )
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
            w06_input_bundle=w06_input,
        ),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w06_anti_paralysis_restriction" in restrictions


def test_w06_identity_split_route_adds_identity_token() -> None:
    case_id = "rt-w06-identity"
    w02_input = _w02_bundle(case_id)
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w06_input = clone_w06_bundle(
        _w06_bundle(case_id, w05_input=w05_input),
        contradiction_intake=(),
        mismatch_intake=w06_mismatch(case_id, mismatch_class=W06MismatchClass.OWNERSHIP),
    )
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
            w06_input_bundle=w06_input,
        ),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w06_identity_split_restriction" in restrictions


def test_w06_route_does_not_authorize_action_or_execute_correction() -> None:
    case_id = "rt-w06-not-exec"
    w02_input = _w02_bundle(case_id)
    w03_input = _w03_bundle(case_id, w02_input=w02_input)
    w04_input = _w04_bundle(case_id, w03_input=w03_input)
    w05_input = _w05_bundle(case_id, w04_input=w04_input)
    w06_input = _w06_bundle(case_id, w05_input=w05_input)
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=w02_input,
            w03_input_bundle=w03_input,
            w04_input_bundle=w04_input,
            w05_input_bundle=w05_input,
            w06_input_bundle=w06_input,
        ),
    )
    assert result.w06_result.downstream_packet.must_not_execute_correction is True
    assert result.state.w06_must_not_execute_correction is True
