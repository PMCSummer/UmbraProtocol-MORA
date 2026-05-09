from __future__ import annotations

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
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome
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


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set",
        reason="runtime topology w01",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.w01.runtime:{case_id}:c1",
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


def _a04_candidate_set(case_id: str) -> A04ExternalAffordanceCandidateSet:
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
                confidence=0.8,
                provenance=("tests.w01.runtime", case_id),
            ),
        ),
        world_scaffolds=(
            A04WorldEntityScaffold(
                entity_ref=f"entity:{case_id}",
                source_authority="authority.world_scaffold",
                scaffold_scope="frontier_entity_scope",
                admission_status=A04AdmissionStatus.ADMITTED,
                confidence=0.85,
                temporal_validity="valid_now",
                provenance=("tests.w01.runtime.scaffold", case_id),
                supported_affordance_classes=("world_directed_action",),
                object_ref=f"object:{case_id}",
            ),
        ),
        source_lineage=("tests.w01.runtime", case_id),
        reason="w01 runtime fixture",
    )


def _w01_packet_set(case_id: str, *, authority_missing: bool = False) -> W01WorldPacketSet:
    return W01WorldPacketSet(
        packet_set_id=f"{case_id}:w01:set",
        packets=(
            W01WorldPacket(
                packet_id=f"{case_id}:packet",
                sequence=1,
                entity_ref=f"entity:{case_id}",
                observation_payload="seen",
                action_ref="act:probe",
                effect_payload=None,
                source_authority=(
                    W01SourceAuthority.UNKNOWN_SOURCE
                    if authority_missing
                    else W01SourceAuthority.TRUSTED_WORLD_PROVIDER
                ),
                source_id="provider.world",
                timestamp_or_sequence="seq:1",
                presence_mode=W01PresenceMode.PRESENT,
                confidence=0.82,
                integrity_status=(
                    W01PacketIntegrityStatus.MISSING_AUTHORITY
                    if authority_missing
                    else W01PacketIntegrityStatus.VALID
                ),
                contradiction_markers=(),
                provenance_ref=("tests.w01.runtime", case_id),
                raw_packet_ref="raw.packet",
                object_label="CIRCLE",
                object_authority_tags=("provider",),
            ),
        ),
        source_lineage=("tests.w01.runtime", case_id),
        reason="w01 runtime packet fixture",
    )


def test_runtime_topology_graph_includes_w01_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.w01_bounded_world_loop_checkpoint" in graph.mandatory_checkpoint_ids
    assert "w01_bounded_world_loop.world_admission_result" in graph.source_of_truth_surfaces


def test_dispatch_w01_checkpoint_order_is_after_a04_before_outcome_resolution() -> None:
    case_id = "runtime-topology-w01-order"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=_candidate_set(case_id),
                a04_external_candidate_set=_a04_candidate_set(case_id),
                w01_world_packet_set=_w01_packet_set(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    assert ids.index("rt01.a04_external_affordance_binding_checkpoint") < ids.index(
        "rt01.w01_bounded_world_loop_checkpoint"
    )
    assert ids.index("rt01.w01_bounded_world_loop_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_dispatch_w01_require_path_is_enforced() -> None:
    case_id = "runtime-topology-w01-require"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=_candidate_set(case_id),
                a04_external_candidate_set=_a04_candidate_set(case_id),
                w01_world_packet_set=_w01_packet_set(case_id, authority_missing=True),
                require_w01_permission_packet_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w01_bounded_world_loop_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_w01_permission_packet_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_production_route_rejects_w01_gate_disabled_test_fixture() -> None:
    case_id = "runtime-topology-w01-disabled"
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                disable_w01_enforcement=True,
                a01_raw_affordance_candidate_set=_candidate_set(case_id),
                a04_external_candidate_set=_a04_candidate_set(case_id),
                w01_world_packet_set=_w01_packet_set(case_id, authority_missing=True),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert denied.decision.accepted is False
    assert denied.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in denied.decision.restrictions
