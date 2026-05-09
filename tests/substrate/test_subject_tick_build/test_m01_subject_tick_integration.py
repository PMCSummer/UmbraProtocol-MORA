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
from substrate.m01_homeostatic_salience_imprint import (
    M01AttributionStatus,
    M01RegulatoryDirection,
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
from tests.substrate.m01_homeostatic_salience_imprint_testkit import (
    m01_attribution,
    m01_bundle,
    m01_coupling,
    m01_delta,
    m01_trace,
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
        reason="m01 integration baseline",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.m01.integration:{case_id}:c1",
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
                provenance=("tests.m01.integration", case_id),
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
                provenance=("tests.m01.integration.scaffold", case_id),
                supported_affordance_classes=("world_directed_action",),
                object_ref=f"object:{case_id}",
            ),
        ),
        source_lineage=("tests.m01.integration", case_id),
        reason="m01 integration fixture",
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
                provenance_ref=("tests.m01.integration", case_id),
                raw_packet_ref="raw.packet",
                object_label="CIRCLE",
                object_authority_tags=("provider",),
            ),
        ),
        source_lineage=("tests.m01.integration", case_id),
        reason="w01 integration fixture",
    )


def _m01_bundle(
    case_id: str,
    *,
    with_delta: bool,
    attribution_status: M01AttributionStatus = M01AttributionStatus.SELF_RELEVANT,
    recovery: bool = False,
):
    trace = m01_trace(trace_id=f"{case_id}:trace", semantic_signature="same_trace")
    deltas = ()
    coupling = ()
    if with_delta:
        delta = m01_delta(
            delta_id=f"{case_id}:delta",
            axis_id="axis:stress",
            direction=M01RegulatoryDirection.IMPROVING if recovery else M01RegulatoryDirection.WORSENING,
            intensity=0.82,
            recovery_marker=recovery,
            deviation_before=0.7,
            deviation_after=0.2 if recovery else 0.85,
        )
        deltas = (delta,)
        coupling = (m01_coupling(trace_id=trace.trace_id, delta_refs=(delta.delta_id,)),)
    return m01_bundle(
        bundle_id=f"{case_id}:m01:bundle",
        traces=(trace,),
        deltas=deltas,
        coupling=coupling,
        attribution=(m01_attribution(trace_id=trace.trace_id, attribution_status=attribution_status),),
        source_lineage=("tests.m01.integration", case_id),
        reason=case_id,
    )


def _m01_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_subject_tick_emits_m01_checkpoint_after_w01_before_outcome_resolution() -> None:
    case_id = "rt-m01-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m01_input_bundle=_m01_bundle(case_id, with_delta=True),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.w01_bounded_world_loop_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )
    assert ids.index("rt01.m01_homeostatic_salience_imprint_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_no_explicit_m01_basis_produces_no_default_friction() -> None:
    case_id = "rt-m01-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m01_input_bundle=None,
        ),
    )
    checkpoint = _m01_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "m01_optional"
    assert result.state.m01_explicit_basis_present is False


def test_strong_regulatory_delta_populates_m01_typed_state() -> None:
    case_id = "rt-m01-strong"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m01_input_bundle=_m01_bundle(case_id, with_delta=True),
        ),
    )
    assert result.state.m01_strong_imprint_count > 0
    assert result.state.m01_downstream_consumer_ready is True


def test_same_checkpoint_id_and_required_action_with_different_m01_shape_changes_gate_outcome() -> None:
    common = {
        "disable_m01_enforcement": True,
        "require_m01_imprint_packet_consumer": True,
    }
    strong_case = "rt-m01-envelope-strong"
    weak_case = "rt-m01-envelope-weak"

    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(strong_case),
            a04_external_candidate_set=_a04_set(strong_case),
            w01_world_packet_set=_w01_set(strong_case),
            m01_input_bundle=_m01_bundle(strong_case, with_delta=True),
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
            m01_input_bundle=_m01_bundle(weak_case, with_delta=False),
        ),
    )

    strong_checkpoint = _m01_checkpoint(strong)
    weak_checkpoint = _m01_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong_checkpoint.required_action == "require_m01_imprint_packet_consumer"
    assert strong.state.m01_downstream_consumer_ready is True
    assert weak.state.m01_downstream_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    assert weak.downstream_gate.usability_class.value == "degraded_bounded"


def test_disabling_m01_enforcement_in_fixture_changes_checkpoint_behavior() -> None:
    case_id = "rt-m01-disable"
    enforced = _result(
        f"{case_id}:enforced",
        context=replace(
            _base_context(),
            require_m01_imprint_packet_consumer=True,
            a01_raw_affordance_candidate_set=_a01_set(f"{case_id}:enforced"),
            a04_external_candidate_set=_a04_set(f"{case_id}:enforced"),
            w01_world_packet_set=_w01_set(f"{case_id}:enforced"),
            m01_input_bundle=_m01_bundle(f"{case_id}:enforced", with_delta=False),
        ),
    )
    disabled = _result(
        f"{case_id}:disabled",
        context=replace(
            _base_context(),
            require_m01_imprint_packet_consumer=True,
            disable_m01_enforcement=True,
            a01_raw_affordance_candidate_set=_a01_set(f"{case_id}:disabled"),
            a04_external_candidate_set=_a04_set(f"{case_id}:disabled"),
            w01_world_packet_set=_w01_set(f"{case_id}:disabled"),
            m01_input_bundle=_m01_bundle(f"{case_id}:disabled", with_delta=False),
        ),
    )
    assert _m01_checkpoint(enforced).status.value == "enforced_detour"
    assert _m01_checkpoint(disabled).status.value == "allowed"


def test_recovery_imprint_path_is_visible_in_subject_tick_typed_state() -> None:
    case_id = "rt-m01-recovery"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m01_input_bundle=_m01_bundle(case_id, with_delta=True, recovery=True),
        ),
    )
    checkpoint = _m01_checkpoint(result)
    assert result.state.m01_recovery_imprint_count > 0
    assert "default_m01_recovery_imprint_route" in checkpoint.required_action


def test_externally_dominated_attribution_downgrades_m01_typed_state() -> None:
    case_id = "rt-m01-external-attribution"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            m01_input_bundle=_m01_bundle(
                case_id,
                with_delta=True,
                attribution_status=M01AttributionStatus.EXTERNALLY_DOMINATED,
            ),
        ),
    )
    assert result.state.m01_attribution_limited_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE
