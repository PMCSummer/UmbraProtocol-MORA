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
from tests.substrate.w03_schema_consolidation_testkit import w03_input_from_w02


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
        provenance_ref=("tests.w03.integration", case_id),
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
    elif variant == "stale":
        traces = (
            _trace(case_id, trace_id="t1", sequence=1),
            _trace(case_id, trace_id="t2", sequence=1),
        )
    else:
        raise ValueError(variant)

    return W02InputBundle(
        bundle_id=f"{case_id}:w02:bundle",
        traces=traces,
        source_lineage=("tests.w03.integration", case_id),
        reason=variant,
    )


def _w03_bundle(case_id: str, *, w02_input: W02InputBundle):
    return w03_input_from_w02(
        case_id=case_id,
        w02_input=w02_input,
        source_lineage=("tests.w03.integration", case_id),
    )


def _w03_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w03_schema_consolidation_checkpoint"
    )


def test_w03_checkpoint_after_w02_before_m01() -> None:
    case_id = "rt-w03-order"
    w02_input = _w02_bundle(case_id, variant="clean")
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=_w03_bundle(case_id, w02_input=w02_input)),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.w02_regularity_extraction_checkpoint") < ids.index(
        "rt01.w03_schema_consolidation_checkpoint"
    )
    assert ids.index("rt01.w03_schema_consolidation_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_compact_w03_fields_are_projected_into_state() -> None:
    case_id = "rt-w03-state"
    w02_input = _w02_bundle(case_id, variant="clean")
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=_w03_bundle(case_id, w02_input=w02_input)),
    )
    assert result.state.w03_checkpoint_present is True
    assert result.state.w03_schema_candidate_count >= 1
    assert result.state.w03_everyday_prior_count >= 0
    assert result.state.w03_version_update_count >= 1


def test_clean_bounded_prior_path_is_less_restrictive() -> None:
    clean_case = "rt-w03-clean"
    contested_case = "rt-w03-contested"
    clean_w02 = _w02_bundle(clean_case, variant="clean")
    contested_w02 = _w02_bundle(contested_case, variant="contested")

    clean = _result(
        clean_case,
        context=replace(_base_context(), w02_input_bundle=clean_w02, w03_input_bundle=_w03_bundle(clean_case, w02_input=clean_w02)),
    )
    contested = _result(
        contested_case,
        context=replace(_base_context(), w02_input_bundle=contested_w02, w03_input_bundle=_w03_bundle(contested_case, w02_input=contested_w02)),
    )

    assert clean.state.w03_consumer_ready is True
    assert contested.state.w03_contradiction_count > 0
    assert clean.downstream_gate.accepted is True
    clean_restrictions = {item.value for item in clean.downstream_gate.restrictions}
    contested_restrictions = {item.value for item in contested.downstream_gate.restrictions}
    assert "w03_contradiction_review_required" in contested_restrictions
    assert "w03_contradiction_review_required" not in clean_restrictions


def test_contested_or_stale_w03_paths_add_restrictions() -> None:
    case_id = "rt-w03-restrict"
    w02_input = _w02_bundle(case_id, variant="stale")
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=_w03_bundle(case_id, w02_input=w02_input)),
    )
    restrictions = {item.value for item in result.downstream_gate.restrictions}
    assert "w03_stale_schema_revalidation_required" in restrictions
    assert result.state.w03_must_revalidate_count >= 1


def test_same_checkpoint_envelope_with_different_w03_shape_changes_gate_result() -> None:
    common = {
        "disable_w03_enforcement": True,
        "require_w03_schema_packet_consumer": True,
    }
    strong_case = "rt-w03-envelope-strong"
    weak_case = "rt-w03-envelope-weak"

    strong_w02 = _w02_bundle(strong_case, variant="clean")
    weak_w02 = _w02_bundle(weak_case, variant="scaffold")

    strong = _result(
        strong_case,
        context=replace(_base_context(), **common, w02_input_bundle=strong_w02, w03_input_bundle=_w03_bundle(strong_case, w02_input=strong_w02)),
    )
    weak = _result(
        weak_case,
        context=replace(_base_context(), **common, w02_input_bundle=weak_w02, w03_input_bundle=_w03_bundle(weak_case, w02_input=weak_w02)),
    )

    strong_checkpoint = _w03_checkpoint(strong)
    weak_checkpoint = _w03_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong.state.w03_consumer_ready is True
    assert weak.state.w03_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    strong_restrictions = {item.value for item in strong.downstream_gate.restrictions}
    weak_restrictions = {item.value for item in weak.downstream_gate.restrictions}
    assert "w03_schema_packet_consumer_required" in weak_restrictions
    assert weak_restrictions != strong_restrictions
    assert weak.state.w03_no_clean_schema is True
    assert strong.state.w03_no_clean_schema is False


def test_w02_compatibility_remains_intact_when_w03_enabled() -> None:
    case_id = "rt-w03-w02-compat"
    w02_input = _w02_bundle(case_id, variant="clean")
    result = _result(
        case_id,
        context=replace(_base_context(), w02_input_bundle=w02_input, w03_input_bundle=_w03_bundle(case_id, w02_input=w02_input)),
    )
    assert result.state.w02_checkpoint_present is True
    assert result.state.w02_candidate_count >= 1
    assert result.w02_result.regularity_records


def test_w03_no_clean_path_is_honest_and_non_crashing() -> None:
    case_id = "rt-w03-no-clean"
    empty_bundle = _w02_bundle(case_id, variant="clean")
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            w02_input_bundle=empty_bundle,
            w03_input_bundle=w03_input_from_w02(case_id=case_id, w02_input=W02InputBundle(bundle_id=f"{case_id}:empty", traces=(), source_lineage=("tests.w03.integration", case_id), reason="empty")),
        ),
    )
    checkpoint = _w03_checkpoint(result)
    assert checkpoint.checkpoint_id == "rt01.w03_schema_consolidation_checkpoint"
    assert result.state.w03_no_clean_schema is True
    assert result.state.w03_consumer_ready is False
