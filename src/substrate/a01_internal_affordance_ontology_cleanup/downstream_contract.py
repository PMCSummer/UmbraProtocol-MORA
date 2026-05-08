from __future__ import annotations

from dataclasses import dataclass

from substrate.a01_internal_affordance_ontology_cleanup.models import (
    A01CanonicalOntologyResult,
)


@dataclass(frozen=True, slots=True)
class A01OntologyContractView:
    raw_candidate_count: int
    canonical_entry_count: int
    merged_alias_group_count: int
    split_decision_count: int
    contested_entry_count: int
    deprecated_entry_count: int
    parent_child_relation_count: int
    same_label_diff_precondition_count: int
    class_conflict_count: int
    legacy_label_bypass_detected: bool
    canonical_affordance_consumer_ready: bool
    contested_affordance_consumer_ready: bool
    deprecated_affordance_consumer_ready: bool
    downstream_consumer_ready: bool
    downstream_readiness_status: str
    restrictions: tuple[str, ...]
    scope: str
    scope_frontier_only: bool
    scope_narrow_slice_only: bool
    scope_ontology_cleanup_not_planner_selection: bool
    scope_no_hidden_planner_selection_authority: bool
    scope_no_map_wide_migration_claim: bool
    scope_no_world_ontology_completeness_claim: bool
    scope_no_affordance_discovery_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class A01OntologyConsumerView:
    raw_candidate_count: int
    canonical_entry_count: int
    merged_alias_group_count: int
    split_decision_count: int
    contested_entry_count: int
    deprecated_entry_count: int
    parent_child_relation_count: int
    same_label_diff_precondition_count: int
    class_conflict_count: int
    legacy_label_bypass_detected: bool
    canonical_affordance_consumer_ready: bool
    contested_affordance_consumer_ready: bool
    deprecated_affordance_consumer_ready: bool
    downstream_consumer_ready: bool
    downstream_readiness_status: str
    restrictions: tuple[str, ...]
    reason: str


def derive_a01_ontology_contract_view(result: A01CanonicalOntologyResult) -> A01OntologyContractView:
    if not isinstance(result, A01CanonicalOntologyResult):
        raise TypeError("derive_a01_ontology_contract_view requires A01CanonicalOntologyResult")
    telemetry = result.telemetry
    gate = result.gate
    scope = result.scope_marker
    return A01OntologyContractView(
        raw_candidate_count=telemetry.raw_candidate_count,
        canonical_entry_count=telemetry.canonical_entry_count,
        merged_alias_group_count=telemetry.merged_alias_group_count,
        split_decision_count=telemetry.split_decision_count,
        contested_entry_count=telemetry.contested_entry_count,
        deprecated_entry_count=telemetry.deprecated_entry_count,
        parent_child_relation_count=telemetry.parent_child_relation_count,
        same_label_diff_precondition_count=telemetry.same_label_diff_precondition_count,
        class_conflict_count=telemetry.class_conflict_count,
        legacy_label_bypass_detected=telemetry.legacy_label_bypass_detected,
        canonical_affordance_consumer_ready=gate.canonical_affordance_consumer_ready,
        contested_affordance_consumer_ready=gate.contested_affordance_consumer_ready,
        deprecated_affordance_consumer_ready=gate.deprecated_affordance_consumer_ready,
        downstream_consumer_ready=telemetry.downstream_consumer_ready,
        downstream_readiness_status=gate.downstream_readiness_status.value,
        restrictions=gate.restrictions,
        scope=scope.scope,
        scope_frontier_only=scope.frontier_only,
        scope_narrow_slice_only=scope.narrow_slice_only,
        scope_ontology_cleanup_not_planner_selection=scope.ontology_cleanup_not_planner_selection,
        scope_no_hidden_planner_selection_authority=scope.no_hidden_planner_selection_authority,
        scope_no_map_wide_migration_claim=scope.no_map_wide_migration_claim,
        scope_no_world_ontology_completeness_claim=scope.no_world_ontology_completeness_claim,
        scope_no_affordance_discovery_claim=scope.no_affordance_discovery_claim,
        scope_reason=scope.reason,
        reason=result.reason,
    )


def derive_a01_ontology_consumer_view(
    result_or_view: A01CanonicalOntologyResult | A01OntologyContractView,
) -> A01OntologyConsumerView:
    view = (
        derive_a01_ontology_contract_view(result_or_view)
        if isinstance(result_or_view, A01CanonicalOntologyResult)
        else result_or_view
    )
    if not isinstance(view, A01OntologyContractView):
        raise TypeError(
            "derive_a01_ontology_consumer_view requires A01CanonicalOntologyResult/A01OntologyContractView"
        )
    return A01OntologyConsumerView(
        raw_candidate_count=view.raw_candidate_count,
        canonical_entry_count=view.canonical_entry_count,
        merged_alias_group_count=view.merged_alias_group_count,
        split_decision_count=view.split_decision_count,
        contested_entry_count=view.contested_entry_count,
        deprecated_entry_count=view.deprecated_entry_count,
        parent_child_relation_count=view.parent_child_relation_count,
        same_label_diff_precondition_count=view.same_label_diff_precondition_count,
        class_conflict_count=view.class_conflict_count,
        legacy_label_bypass_detected=view.legacy_label_bypass_detected,
        canonical_affordance_consumer_ready=view.canonical_affordance_consumer_ready,
        contested_affordance_consumer_ready=view.contested_affordance_consumer_ready,
        deprecated_affordance_consumer_ready=view.deprecated_affordance_consumer_ready,
        downstream_consumer_ready=view.downstream_consumer_ready,
        downstream_readiness_status=view.downstream_readiness_status,
        restrictions=view.restrictions,
        reason="a01 ontology consumer view",
    )


def require_a01_canonical_affordance_consumer(
    result_or_view: A01CanonicalOntologyResult | A01OntologyContractView,
) -> A01OntologyConsumerView:
    view = derive_a01_ontology_consumer_view(result_or_view)
    if not view.canonical_affordance_consumer_ready:
        raise PermissionError("a01 canonical-affordance consumer requires canonical entries")
    return view


def require_a01_contested_affordance_consumer(
    result_or_view: A01CanonicalOntologyResult | A01OntologyContractView,
) -> A01OntologyConsumerView:
    view = derive_a01_ontology_consumer_view(result_or_view)
    if not view.contested_affordance_consumer_ready:
        raise PermissionError("a01 contested-affordance consumer requires contested entries")
    return view


def require_a01_deprecated_affordance_consumer(
    result_or_view: A01CanonicalOntologyResult | A01OntologyContractView,
) -> A01OntologyConsumerView:
    view = derive_a01_ontology_consumer_view(result_or_view)
    if not view.deprecated_affordance_consumer_ready:
        raise PermissionError("a01 deprecated-affordance consumer requires deprecated/narrowed entries")
    return view
