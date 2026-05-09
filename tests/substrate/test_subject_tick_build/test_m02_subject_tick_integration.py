from __future__ import annotations

from dataclasses import replace

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.a04_external_affordance_binding import (
    A04AdmissionStatus,
    A04ExternalAffordanceCandidate,
    A04ExternalAffordanceCandidateSet,
    A04WorldEntityScaffold,
)
from substrate.m02_predictive_relevance import (
    M02InputBundle,
    M02PredictiveFeedback,
    M02PredictiveTrace,
    M02PredictionTarget,
    M02TargetType,
    M02TraceKind,
    M02UtilityHorizon,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome
from substrate.w01_bounded_world_loop import (
    W01PacketIntegrityStatus,
    W01PresenceMode,
    W01SourceAuthority,
    W01WorldPacket,
    W01WorldPacketSet,
)
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    a01_candidate,
    a01_candidate_set,
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


def _a01_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set",
        reason="m02 integration baseline",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.m02.integration:{case_id}:c1",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:internal_diagnostic_scan",
            ),
        ),
    )


def _a04_set(case_id: str):
    return A04ExternalAffordanceCandidateSet(
        candidate_set_id=f"{case_id}:a04:set",
        candidates=(
            A04ExternalAffordanceCandidate(
                candidate_id=f"{case_id}:cand",
                entity_ref=f"entity:{case_id}",
                object_ref=f"object:{case_id}",
                affordance_class="world_directed_action",
                candidate_label="turn_handle",
                source_authority="authority.world_scaffold",
                scaffold_scope="frontier_entity_scope",
                epistemic_basis=("world_scaffold",),
                permission_basis=("permitted",),
                temporal_validity="valid_now",
                confidence=0.82,
                provenance=("tests.m02.integration", case_id),
            ),
        ),
        world_scaffolds=(
            A04WorldEntityScaffold(
                entity_ref=f"entity:{case_id}",
                source_authority="authority.world_scaffold",
                scaffold_scope="frontier_entity_scope",
                admission_status=A04AdmissionStatus.ADMITTED,
                confidence=0.86,
                temporal_validity="valid_now",
                provenance=("tests.m02.integration.scaffold", case_id),
                supported_affordance_classes=("world_directed_action",),
                object_ref=f"object:{case_id}",
            ),
        ),
        source_lineage=("tests.m02.integration", case_id),
        reason="m02 integration fixture",
    )


def _w01_set(case_id: str) -> W01WorldPacketSet:
    return W01WorldPacketSet(
        packet_set_id=f"{case_id}:w01:set",
        packets=(
            W01WorldPacket(
                packet_id=f"{case_id}:p1",
                sequence=1,
                entity_ref=f"entity:{case_id}",
                observation_payload="obs",
                action_ref="act:probe",
                effect_payload=None,
                source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                source_id="provider.world",
                timestamp_or_sequence="seq:1",
                presence_mode=W01PresenceMode.PRESENT,
                confidence=0.82,
                integrity_status=W01PacketIntegrityStatus.VALID,
                contradiction_markers=(),
                provenance_ref=("tests.m02.integration", case_id),
                raw_packet_ref="raw.packet",
                object_label="CIRCLE",
                object_authority_tags=("provider",),
            ),
        ),
        source_lineage=("tests.m02.integration", case_id),
        reason="w01 integration fixture",
    )


def _m02_bundle(
    case_id: str,
    *,
    prediction_gain: float,
    corroboration_count: int,
    context_locked: bool = False,
    spurious_risk_score: float = 0.1,
) -> M02InputBundle:
    trace = M02PredictiveTrace(
        trace_id=f"{case_id}:trace",
        trace_kind=M02TraceKind.ROUTINE,
        semantic_label="boring_routine_trace",
        boredom_level=0.8,
        vividness_level=0.15,
        novelty_level=0.2,
        timestamp_or_sequence="seq:1",
        context_scope="runtime_scope",
        mode_context="mode:analysis",
        tool_context="tool:diagnostic",
        homeostatic_strength_hint=0.2,
        provenance=("tests.m02.integration", case_id),
    )
    target = M02PredictionTarget(
        target_id=f"{case_id}:target",
        target_type=M02TargetType.REGIME_DETECTION,
        utility_horizon=M02UtilityHorizon.SHORT,
        context_scope="runtime_scope",
        success_metric="prediction_gain",
        provenance=("tests.m02.integration", case_id),
    )
    feedback = M02PredictiveFeedback(
        feedback_id=f"{case_id}:feedback",
        trace_id=trace.trace_id,
        target_id=target.target_id,
        prediction_gain=prediction_gain,
        error_delta=0.0,
        corroboration_count=corroboration_count,
        failed_transfer_count=0,
        spurious_risk_score=spurious_risk_score,
        context_locked=context_locked,
        attribution_noise_risk=False,
        confidence=0.82,
        provenance=("tests.m02.integration", case_id),
    )
    return M02InputBundle(
        bundle_id=f"{case_id}:m02:bundle",
        traces=(trace,),
        prediction_targets=(target,),
        predictive_feedback=(feedback,),
        source_lineage=("tests.m02.integration", case_id),
        reason=case_id,
    )


def _m02_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.m02_predictive_relevance_checkpoint"
    )


def test_m02_checkpoint_is_after_m01_and_before_outcome_resolution() -> None:
    case_id = "rt-m02-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m02_input_bundle=_m02_bundle(case_id, prediction_gain=0.75, corroboration_count=3),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.m01_homeostatic_salience_imprint_checkpoint") < ids.index(
        "rt01.m02_predictive_relevance_checkpoint"
    )
    assert ids.index("rt01.m02_predictive_relevance_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_no_m02_basis_creates_no_false_friction() -> None:
    case_id = "rt-m02-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m02_input_bundle=None,
        ),
    )
    checkpoint = _m02_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "m02_optional"
    assert result.state.m02_explicit_basis_present is False


def test_explicit_spurious_m02_basis_changes_downstream_gate() -> None:
    case_id = "rt-m02-spurious"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m02_input_bundle=_m02_bundle(
                case_id,
                prediction_gain=0.8,
                corroboration_count=4,
                spurious_risk_score=0.9,
            ),
        ),
    )
    checkpoint = _m02_checkpoint(result)
    assert "default_m02_spurious_pattern_risk_detour" in checkpoint.required_action
    assert result.state.m02_spurious_risk_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_context_locked_m02_basis_preserves_must_not_generalize_restriction() -> None:
    case_id = "rt-m02-context-locked"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m02_input_bundle=_m02_bundle(
                case_id,
                prediction_gain=0.68,
                corroboration_count=3,
                context_locked=True,
            ),
        ),
    )
    assert result.state.m02_context_locked_count > 0
    assert result.state.m02_must_not_generalize is True


def test_same_checkpoint_envelope_with_different_typed_m02_shape_changes_gate() -> None:
    common = {
        "disable_m02_enforcement": True,
        "require_m02_predictive_packet_consumer": True,
    }
    strong_case = "rt-m02-envelope-strong"
    weak_case = "rt-m02-envelope-weak"
    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(strong_case),
            a04_external_candidate_set=_a04_set(strong_case),
            w01_world_packet_set=_w01_set(strong_case),
            m02_input_bundle=_m02_bundle(strong_case, prediction_gain=0.76, corroboration_count=4),
        ),
    )
    weak = _result(
        weak_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(weak_case),
            a04_external_candidate_set=_a04_set(weak_case),
            w01_world_packet_set=_w01_set(weak_case),
            m02_input_bundle=_m02_bundle(weak_case, prediction_gain=0.0, corroboration_count=4),
        ),
    )
    strong_checkpoint = _m02_checkpoint(strong)
    weak_checkpoint = _m02_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong_checkpoint.required_action == "require_m02_predictive_packet_consumer"
    assert strong.state.m02_downstream_consumer_ready is True
    assert weak.state.m02_downstream_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    assert weak.downstream_gate.usability_class.value == "degraded_bounded"


def test_m02_consumer_ready_requires_target_linked_utility_not_repetition_only() -> None:
    case_id = "rt-m02-repetition-only"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m02_input_bundle=_m02_bundle(case_id, prediction_gain=0.0, corroboration_count=8),
        ),
    )
    assert result.state.m02_no_safe_mark_count > 0
    assert result.state.m02_downstream_consumer_ready is False


def test_m02_does_not_claim_m03_memory_lifecycle() -> None:
    case_id = "rt-m02-m03-boundary"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m02_input_bundle=_m02_bundle(case_id, prediction_gain=0.74, corroboration_count=3),
        ),
    )
    assert result.m02_result.scope_marker.no_full_memory_lifecycle_claim is True
    assert result.m02_result.scope_marker.no_full_prediction_claim is True
