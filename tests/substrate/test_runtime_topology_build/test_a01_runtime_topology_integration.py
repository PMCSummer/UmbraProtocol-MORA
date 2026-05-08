from __future__ import annotations

from dataclasses import replace

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome
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


def _canonical_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:canonical",
        reason="canonical",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.runtime:{case_id}:c1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:pause_and_recover",
            ),
        ),
    )


def _granularity_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:granularity",
        reason="granularity",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:g1",
                local_label="repair_sequence",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.runtime:{case_id}:g1",
                preconditions=("rupture_detected",),
                primary_outcomes=("repair_progress",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("repair_open",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:repair_sequence",
                granularity_level=1,
            ),
            a01_candidate(
                candidate_id=f"{case_id}:g2",
                local_label="repair_sequence",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.runtime:{case_id}:g2",
                preconditions=("rupture_detected",),
                primary_outcomes=("repair_progress",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("clarify_then_repair",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:repair_sequence.step",
                granularity_level=3,
            ),
        ),
    )


def _legacy_only_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:legacy",
        reason="legacy only",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:l1",
                local_label="legacy_pause",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.runtime:{case_id}:l1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=None,
                legacy_local_label_only=True,
            ),
        ),
    )


def test_runtime_topology_graph_includes_a01_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.a01_affordance_ontology_cleanup_checkpoint" in graph.mandatory_checkpoint_ids
    assert (
        "a01_internal_affordance_ontology_cleanup.canonical_ontology_snapshot"
        in graph.source_of_truth_surfaces
    )
    a_line_node = next(item for item in graph.nodes if item.node_id == "node.a_line")
    assert "rt01.a01_affordance_ontology_cleanup_checkpoint" in a_line_node.checkpoint_ids
    assert (
        "a01_internal_affordance_ontology_cleanup.canonical_ontology_snapshot"
        in a_line_node.surfaces
    )


def test_dispatch_a01_require_paths_are_enforced() -> None:
    case_id = "runtime-topology-a01-require"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=None,
                require_a01_canonical_affordance_consumer=True,
                require_a01_contested_affordance_consumer=True,
                require_a01_deprecated_affordance_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a01_affordance_ontology_cleanup_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_a01_canonical_affordance_consumer" in checkpoint.required_action
    assert "require_a01_contested_affordance_consumer" in checkpoint.required_action
    assert "require_a01_deprecated_affordance_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_same_a01_checkpoint_envelope_can_diverge_by_typed_shape() -> None:
    clean_case = "runtime-topology-a01-envelope-clean"
    granular_case = "runtime-topology-a01-envelope-granular"
    clean = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(clean_case),
            context=SubjectTickContext(
                require_a01_canonical_affordance_consumer=True,
                a01_raw_affordance_candidate_set=_canonical_candidate_set(clean_case),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    granular = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(granular_case),
            context=SubjectTickContext(
                require_a01_canonical_affordance_consumer=True,
                a01_raw_affordance_candidate_set=_granularity_candidate_set(granular_case),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert clean.subject_tick_result is not None
    assert granular.subject_tick_result is not None
    clean_checkpoint = next(
        item
        for item in clean.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a01_affordance_ontology_cleanup_checkpoint"
    )
    granular_checkpoint = next(
        item
        for item in granular.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a01_affordance_ontology_cleanup_checkpoint"
    )
    assert clean_checkpoint.status.value == "allowed"
    assert granular_checkpoint.status.value == "allowed"
    assert clean_checkpoint.required_action == "require_a01_canonical_affordance_consumer"
    assert clean_checkpoint.required_action == granular_checkpoint.required_action
    assert clean.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert granular.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert clean.subject_tick_result.downstream_gate.accepted is True
    assert granular.subject_tick_result.downstream_gate.accepted is False
    assert (
        clean.subject_tick_result.downstream_gate.usability_class.value
        != granular.subject_tick_result.downstream_gate.usability_class.value
    )


def test_dispatch_disable_a01_enforcement_is_rejected_on_production_route() -> None:
    case_id = "runtime-topology-a01-no-bypass"
    enabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=_legacy_only_candidate_set(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert enabled.decision.accepted is True
    assert enabled.subject_tick_result is not None
    enabled_checkpoint = next(
        item
        for item in enabled.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a01_affordance_ontology_cleanup_checkpoint"
    )
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a01_legacy_label_bypass_forbidden" in enabled_checkpoint.required_action

    disabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(f"{case_id}-disabled"),
            context=SubjectTickContext(
                disable_a01_enforcement=True,
                a01_raw_affordance_candidate_set=_legacy_only_candidate_set(f"{case_id}-disabled"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert disabled.decision.accepted is False
    assert disabled.subject_tick_result is None
    assert (
        RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS
        in disabled.decision.restrictions
    )
