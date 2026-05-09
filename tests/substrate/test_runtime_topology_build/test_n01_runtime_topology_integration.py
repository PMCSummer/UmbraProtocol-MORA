from __future__ import annotations

from substrate.n01_narrative_commitments import (
    N01CommitmentScope,
    N01GroundingBasisKind,
    N01InputBundle,
    N01NarrativeClaimCandidate,
    N01NarrativeClaimKind,
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


def _n01_input(case_id: str) -> N01InputBundle:
    candidate = N01NarrativeClaimCandidate(
        candidate_id=f"{case_id}:candidate",
        claim_text_or_semantic_form="I am operating in analysis mode",
        claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
        requested_scope=N01CommitmentScope.CURRENT_TURN,
        expression_channel="text",
        addressee_or_audience_scope="runtime",
        grounding_basis=(
            N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
            N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
            N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
            N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
        ),
        temporal_validity_status="fresh",
        attribution_status="self",
        self_side_confidence=0.9,
        mixed_cause_marker=False,
    )
    return N01InputBundle(
        bundle_id=f"{case_id}:n01:bundle",
        candidates=(candidate,),
        source_lineage=("tests.n01.runtime", case_id),
    )


def test_n01_runtime_topology_contains_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.n01_narrative_commitments_checkpoint" in graph.mandatory_checkpoint_ids
    assert "n01_narrative_commitments.commitment_registry_result" in graph.source_of_truth_surfaces


def test_n01_is_after_m02_before_outcome_resolution() -> None:
    case_id = "runtime-topology-n01-order"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                n01_input_bundle=_n01_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    assert ids.index("rt01.m02_predictive_relevance_checkpoint") < ids.index(
        "rt01.n01_narrative_commitments_checkpoint"
    )
    assert ids.index("rt01.n01_narrative_commitments_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_n01_disable_flag_rejected_in_production_route() -> None:
    case_id = "runtime-topology-n01-disabled"
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                disable_n01_enforcement=True,
                n01_input_bundle=_n01_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert denied.decision.accepted is False
    assert denied.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in denied.decision.restrictions


def test_n01_source_of_truth_surface_not_telemetry_only() -> None:
    case_id = "runtime-topology-n01-surface"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                n01_input_bundle=_n01_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.n01_result.commitment_entries
