from __future__ import annotations

from substrate.n02_identity_drift_reflection import (
    N02BaselineReference,
    N02BaselineValidityStatus,
    N02CurrentIdentityEvidence,
    N02IdentityRegionKind,
    N02InputBundle,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _n02_input(case_id: str) -> N02InputBundle:
    return N02InputBundle(
        bundle_id=f"{case_id}:n02:bundle",
        baseline_references=(
            N02BaselineReference(
                baseline_id=f"{case_id}:baseline",
                baseline_kind=N02IdentityRegionKind.SELF_DESCRIPTION,
                time_scope="context:analysis",
                source_commitment_ids=(f"{case_id}:commitment:baseline",),
                source_region_ids=(f"{case_id}:region:self",),
                validity_status=N02BaselineValidityStatus.VALID,
                confidence=0.84,
                provenance=("tests.n02.runtime", case_id),
            ),
        ),
        current_references=(
            N02CurrentIdentityEvidence(
                current_reference_id=f"{case_id}:current",
                observed_region=N02IdentityRegionKind.SELF_DESCRIPTION,
                current_commitment_ids=(f"{case_id}:commitment:current",),
                current_self_binding_refs=(),
                capability_or_affordance_refs=(),
                context_scope="context:analysis",
                evidence_window="window:now",
                confidence=0.8,
                provenance=("tests.n02.runtime", case_id),
            ),
        ),
        substrate_changes=(),
        source_lineage=("tests.n02.runtime", case_id),
    )


def test_n02_runtime_topology_contains_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.n02_identity_drift_reflection_checkpoint" in graph.mandatory_checkpoint_ids
    assert "n02_identity_drift_reflection.identity_drift_result" in graph.source_of_truth_surfaces


def test_n02_is_after_n01_before_outcome_resolution() -> None:
    case_id = "runtime-topology-n02-order"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                n02_input_bundle=_n02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    assert ids.index("rt01.n01_narrative_commitments_checkpoint") < ids.index(
        "rt01.n02_identity_drift_reflection_checkpoint"
    )
    assert ids.index("rt01.n02_identity_drift_reflection_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_n02_disable_flag_rejected_in_production_route() -> None:
    case_id = "runtime-topology-n02-disabled"
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                disable_n02_enforcement=True,
                n02_input_bundle=_n02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert denied.decision.accepted is False
    assert denied.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in denied.decision.restrictions


def test_n02_source_of_truth_surface_not_telemetry_only() -> None:
    case_id = "runtime-topology-n02-surface"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                n02_input_bundle=_n02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.n02_result.drift_entries
