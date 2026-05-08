from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01CanonicalOntologyResult,
    A01ControllabilityClass,
    A01ValidityStatus,
    derive_a01_ontology_consumer_view,
)
from substrate.a02_capability_gap_detection.models import (
    A02AffordanceCoverageCandidate,
    A02BlockingConstraint,
    A02BlockingKind,
    A02CapabilityGapEntry,
    A02CapabilityGapGateDecision,
    A02CapabilityGapInput,
    A02CapabilityGapLedger,
    A02CapabilityGapResult,
    A02CompositionRoute,
    A02CompositionStatus,
    A02CompositionStep,
    A02ConfidenceBand,
    A02ControllabilityStatus,
    A02CoverageEvidence,
    A02CoverageStatus,
    A02DemandClass,
    A02DemandLegitimacyStatus,
    A02DownstreamReadinessStatus,
    A02DownstreamRouteHint,
    A02GapKind,
    A02GapLedgerEntry,
    A02PartialCoverageRecord,
    A02ScopeMarker,
    A02Telemetry,
)


def build_a02_capability_gap_detection(
    *,
    tick_id: str,
    tick_index: int,
    capability_input: A02CapabilityGapInput | None,
    a01_result: A01CanonicalOntologyResult | None,
    gap_detection_enabled: bool = True,
) -> A02CapabilityGapResult:
    if not gap_detection_enabled:
        return _build_minimal_result(
            demand_set_id=f"a02:{tick_id}:demand_set:none",
            reason="a02 gap detection disabled in ablation context",
            restrictions=("a02_disabled", "capability_gap_not_evaluated"),
        )
    if not isinstance(capability_input, A02CapabilityGapInput):
        return _build_minimal_result(
            demand_set_id=f"a02:{tick_id}:demand_set:none",
            reason="a02 requires typed capability input; no narrative fallback allowed",
            restrictions=("insufficient_a02_basis", "a02_no_clean_coverage_claim"),
        )

    demand_set = capability_input.demand_set
    if demand_set is None or not demand_set.demands:
        return _build_minimal_result(
            demand_set_id=demand_set.demand_set_id if demand_set else f"a02:{tick_id}:demand_set:none",
            reason="a02 received no typed demand packets and will not fabricate capability gaps",
            restrictions=("insufficient_a02_basis", "a02_no_clean_coverage_claim"),
        )

    if not isinstance(a01_result, A01CanonicalOntologyResult):
        return _build_no_clean_result(
            tick_id=tick_id,
            tick_index=tick_index,
            demand_set=demand_set,
            reason="a02 requires a01 canonical ontology input and will not reconstruct affordances from labels",
            restrictions=("a02_requires_a01_canonical_ontology", "a02_no_clean_coverage_claim"),
            capability_input=capability_input,
        )

    a01_view = derive_a01_ontology_consumer_view(a01_result)
    canonical_entries = a01_result.ontology_snapshot.canonical_entries
    if not canonical_entries:
        return _build_no_clean_result(
            tick_id=tick_id,
            tick_index=tick_index,
            demand_set=demand_set,
            reason="a02 cannot assess capability gaps because a01 canonical entries are unavailable",
            restrictions=("a02_requires_a01_canonical_coverage", "a02_no_clean_coverage_claim"),
            capability_input=capability_input,
            canonical_hint_used_count=a01_view.canonical_id_hint_used_count,
            canonical_generated_count=a01_view.canonical_id_generated_count,
            canonical_coverage_complete=a01_view.canonical_id_coverage_complete,
        )

    runtime_lineage = tuple(dict.fromkeys(capability_input.source_lineage))
    demand_lineage = tuple(dict.fromkeys(demand_set.source_lineage))
    source_lineage_refs = tuple(dict.fromkeys((*runtime_lineage, *demand_lineage)))
    source_lineage_complete = bool(runtime_lineage and demand_lineage)

    gap_entries: list[A02CapabilityGapEntry] = []
    ledger_entries: list[A02GapLedgerEntry] = []
    composition_routes_seen: list[A02CompositionRoute] = []

    for demand in demand_set.demands:
        matching_entries = _matching_entries(
            demanded_class=demand.demanded_change_class,
            demanded_scope=demand.demanded_scope,
            demanded_channels=demand.target_channels,
            canonical_entries=canonical_entries,
        )
        entry, routes = _classify_gap_entry(
            tick_id=tick_id,
            tick_index=tick_index,
            demand=demand,
            matching_entries=matching_entries,
            composition_enabled=capability_input.composition_enabled,
            ownership_boundary_basis=capability_input.ownership_boundary_basis,
        )
        gap_entries.append(entry)
        composition_routes_seen.extend(routes)
        ledger_entries.append(
            A02GapLedgerEntry(
                ledger_entry_id=f"a02:{tick_id}:{tick_index}:ledger:{demand.demand_id}",
                demand_id=demand.demand_id,
                coverage_status=entry.coverage_status,
                gap_kind=entry.gap_kind,
                reason=f"{entry.coverage_status.value}:{entry.gap_kind.value}",
            )
        )

    telemetry = _build_telemetry(
        gap_entries=tuple(gap_entries),
        source_lineage_count=len(source_lineage_refs),
        source_lineage_complete=source_lineage_complete,
        canonical_hint_used_count=a01_view.canonical_id_hint_used_count,
        canonical_generated_count=a01_view.canonical_id_generated_count,
        canonical_coverage_complete=a01_view.canonical_id_coverage_complete,
    )
    ledger = A02CapabilityGapLedger(
        ledger_id=f"a02:{tick_id}:{tick_index}:ledger",
        entries=tuple(ledger_entries),
        source_lineage_refs=source_lineage_refs,
        source_lineage_count=len(source_lineage_refs),
        source_lineage_complete=source_lineage_complete,
        canonical_id_hint_used_count=a01_view.canonical_id_hint_used_count,
        canonical_id_generated_count=a01_view.canonical_id_generated_count,
        canonical_id_coverage_complete=a01_view.canonical_id_coverage_complete,
        no_affordance_invention_observed=True,
        reason="a02 ledger records typed demand-to-affordance gap decisions without inventing affordances",
    )
    gate = _build_gate(
        entries=tuple(gap_entries),
        telemetry=telemetry,
        demand_count=len(demand_set.demands),
    )
    scope = A02ScopeMarker(
        scope="frontier_hosted_a02_capability_gap_detection_slice",
        frontier_only=True,
        narrow_slice_only=True,
        capability_gap_not_planner=True,
        depends_on_a01_canonical_ontology=True,
        no_map_wide_claim=True,
        no_affordance_discovery_claim=True,
        no_hidden_action_execution_claim=True,
        reason=(
            "a02 compares typed demands against a01 canonical affordance ontology and current constraints in narrow frontier slice"
        ),
    )
    return A02CapabilityGapResult(
        demand_set_id=demand_set.demand_set_id,
        gap_entries=tuple(gap_entries),
        ledger=ledger,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason="a02 produced typed capability-gap ledger with missing/blocked/partial/composition/ownership distinctions",
    )


def _classify_gap_entry(
    *,
    tick_id: str,
    tick_index: int,
    demand,
    matching_entries,
    composition_enabled: bool,
    ownership_boundary_basis: tuple[str, ...],
) -> tuple[A02CapabilityGapEntry, list[A02CompositionRoute]]:
    required_scope = tuple(dict.fromkeys(demand.demanded_scope))
    required_channels = tuple(dict.fromkeys(demand.target_channels))
    composition_routes: list[A02CompositionRoute] = []
    non_authoritative_refs = _non_authoritative_signal_refs(demand)

    if (
        demand.legitimacy_status
        in {
            A02DemandLegitimacyStatus.NARRATIVE_WISH_ONLY,
            A02DemandLegitimacyStatus.INVALID_NO_EFFECT_SCOPE,
            A02DemandLegitimacyStatus.WEAKLY_TYPED,
        }
        or not required_scope
    ):
        evidence = A02CoverageEvidence(
            demand_id=demand.demand_id,
            matched_scope=(),
            unmatched_scope=required_scope,
            matched_channels=(),
            unmatched_channels=required_channels,
            basis_refs=tuple(
                dict.fromkeys(("demand_not_legitimate_for_strong_gap_claim", *non_authoritative_refs))
            ),
        )
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=A02CoverageStatus.NO_CLEAN_COVERAGE_CLAIM,
                gap_kind=A02GapKind.UNKNOWN_CAPABILITY_STATUS,
                matching_affordance_candidates=(),
                blocked_by=(),
                required_conditions=("typed_demand_legitimacy_required",),
                composition_status=A02CompositionStatus.COMPOSITION_UNKNOWN,
                composition_route_refs=(),
                partial_coverage=None,
                controllability_status=A02ControllabilityStatus.UNKNOWN,
                ownership_boundary_status="not_evaluated",
                severity=demand.severity,
                confidence=A02ConfidenceBand.INSUFFICIENT_BASIS,
                downstream_route_hint=A02DownstreamRouteHint.REVALIDATE_ONTOLOGY_OR_DEMAND,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    if (
        demand.world_side_requirement == "required"
        and demand.required_controllability
        in {
            A02ControllabilityStatus.OUTSIDE_CURRENT_CONTROL,
            A02ControllabilityStatus.MIXED_OR_CONTAMINATED,
        }
    ):
        evidence = A02CoverageEvidence(
            demand_id=demand.demand_id,
            matched_scope=(),
            unmatched_scope=required_scope,
            matched_channels=(),
            unmatched_channels=required_channels,
            basis_refs=tuple(
                dict.fromkeys((*ownership_boundary_basis, "world_side_requirement", *non_authoritative_refs))
            ),
        )
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=A02CoverageStatus.BLOCKED,
                gap_kind=A02GapKind.OWNERSHIP_BOUNDARY_GAP,
                matching_affordance_candidates=(),
                blocked_by=(
                    A02BlockingConstraint(
                        kind=A02BlockingKind.OWNERSHIP_BOUNDARY_BLOCKED,
                        detail="demand requires externally dominated world-side outcome",
                        source_ref=demand.source_ref,
                    ),
                ),
                required_conditions=("ownership_boundary_resolution",),
                composition_status=A02CompositionStatus.COMPOSITION_FORBIDDEN,
                composition_route_refs=(),
                partial_coverage=None,
                controllability_status=A02ControllabilityStatus.OUTSIDE_CURRENT_CONTROL,
                ownership_boundary_status="outside_owner_surface",
                severity=demand.severity,
                confidence=A02ConfidenceBand.MEDIUM,
                downstream_route_hint=A02DownstreamRouteHint.SUPPRESS_AGENCY_OVERCLAIM,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    if not matching_entries:
        evidence = A02CoverageEvidence(
            demand_id=demand.demand_id,
            matched_scope=(),
            unmatched_scope=required_scope,
            matched_channels=(),
            unmatched_channels=required_channels,
            basis_refs=tuple(dict.fromkeys(("no_matching_canonical_affordance", *non_authoritative_refs))),
        )
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=A02CoverageStatus.NOT_COVERED,
                gap_kind=A02GapKind.MISSING_AFFORDANCE,
                matching_affordance_candidates=(),
                blocked_by=(),
                required_conditions=("missing_canonical_affordance",),
                composition_status=A02CompositionStatus.COMPOSITION_MISSING,
                composition_route_refs=(),
                partial_coverage=None,
                controllability_status=A02ControllabilityStatus.UNKNOWN,
                ownership_boundary_status="not_triggered",
                severity=demand.severity,
                confidence=A02ConfidenceBand.MEDIUM,
                downstream_route_hint=A02DownstreamRouteHint.EXPLORE_MISSING_AFFORDANCE,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    coverage_candidates = tuple(
        A02AffordanceCoverageCandidate(
            demand_id=demand.demand_id,
            affordance_id=item.affordance_id,
            coverage_scope=tuple(
                sorted(set(required_scope).intersection(set(item.effect_scope.primary_outcomes)))
            ),
            missing_scope=tuple(
                sorted(set(required_scope).difference(set(item.effect_scope.primary_outcomes)))
            ),
            target_channel_overlap=tuple(
                sorted(set(required_channels).intersection(set(item.target_channels)))
            ),
            validity_status=item.validity_status.value,
        )
        for item in matching_entries
    )
    blocked_constraints: list[A02BlockingConstraint] = []
    blocked_validity = True
    for item in matching_entries:
        if item.validity_status not in {A01ValidityStatus.DEPRECATED, A01ValidityStatus.UNAVAILABLE}:
            blocked_validity = False
        if any("disabled_effector" in req for req in item.preconditions.requirements):
            blocked_constraints.append(
                A02BlockingConstraint(
                    kind=A02BlockingKind.DISABLED_EFFECTOR,
                    detail=f"disabled effector in {item.affordance_id}",
                    source_ref=item.affordance_id,
                )
            )
        if any("invalid_assumption" in req for req in item.preconditions.requirements):
            blocked_constraints.append(
                A02BlockingConstraint(
                    kind=A02BlockingKind.INVALIDATED_ASSUMPTION,
                    detail=f"invalidated assumption in {item.affordance_id}",
                    source_ref=item.affordance_id,
                )
            )
        if any("resource_limited" in req or "resource_budget_exhausted" in req for req in item.preconditions.requirements):
            blocked_constraints.append(
                A02BlockingConstraint(
                    kind=A02BlockingKind.RESOURCE_LIMITED,
                    detail=f"resource-limited availability in {item.affordance_id}",
                    source_ref=item.affordance_id,
                )
            )
        if any("mode_restricted" in req for req in item.preconditions.requirements):
            blocked_constraints.append(
                A02BlockingConstraint(
                    kind=A02BlockingKind.MODE_RESTRICTED,
                    detail=f"mode-restricted availability in {item.affordance_id}",
                    source_ref=item.affordance_id,
                )
            )

    if blocked_validity or blocked_constraints:
        blocked_kind = (
            A02GapKind.INVALIDATED_AFFORDANCE_GAP
            if any(item.kind is A02BlockingKind.INVALIDATED_ASSUMPTION for item in blocked_constraints)
            else A02GapKind.RESOURCE_BLOCKED_GAP
            if any(
                item.kind in {A02BlockingKind.RESOURCE_LIMITED, A02BlockingKind.MODE_RESTRICTED}
                for item in blocked_constraints
            )
            else A02GapKind.PRECONDITION_UNSATISFIED_GAP
            if blocked_constraints
            else A02GapKind.UNAVAILABLE_AFFORDANCE
        )
        evidence = _build_evidence(
            demand_id=demand.demand_id,
            required_scope=required_scope,
            required_channels=required_channels,
            matching_entries=matching_entries,
            additional_basis_refs=non_authoritative_refs,
        )
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=A02CoverageStatus.BLOCKED,
                gap_kind=blocked_kind,
                matching_affordance_candidates=coverage_candidates,
                blocked_by=tuple(blocked_constraints),
                required_conditions=("restore_preconditions",),
                composition_status=A02CompositionStatus.NO_COMPOSITION_NEEDED,
                composition_route_refs=(),
                partial_coverage=None,
                controllability_status=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
                ownership_boundary_status="not_triggered",
                severity=demand.severity,
                confidence=A02ConfidenceBand.MEDIUM,
                downstream_route_hint=A02DownstreamRouteHint.RESTORE_BLOCKING_CONDITION,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    contested_candidates = tuple(
        item for item in matching_entries if item.validity_status is A01ValidityStatus.CONTESTED
    )
    contested_preconditions = {
        tuple(sorted(item.preconditions.requirements)) for item in matching_entries
    }
    contested_channels = {tuple(sorted(item.target_channels)) for item in matching_entries}
    contested_mapping_ambiguous = len(contested_preconditions) > 1 or len(contested_channels) > 1
    if (
        len(matching_entries) > 1
        and contested_candidates
        and len(contested_candidates) == len(matching_entries)
        and contested_mapping_ambiguous
    ):
        evidence = _build_evidence(
            demand_id=demand.demand_id,
            required_scope=required_scope,
            required_channels=required_channels,
            matching_entries=matching_entries,
            additional_basis_refs=tuple(dict.fromkeys((*non_authoritative_refs, "all_matching_affordances_contested"))),
        )
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=A02CoverageStatus.CONTESTED,
                gap_kind=A02GapKind.UNKNOWN_CAPABILITY_STATUS,
                matching_affordance_candidates=coverage_candidates,
                blocked_by=(),
                required_conditions=("contested_affordance_resolution_required",),
                composition_status=A02CompositionStatus.COMPOSITION_UNKNOWN,
                composition_route_refs=(),
                partial_coverage=None,
                controllability_status=A02ControllabilityStatus.MIXED_OR_CONTAMINATED,
                ownership_boundary_status="not_triggered",
                severity=demand.severity,
                confidence=A02ConfidenceBand.LOW,
                downstream_route_hint=A02DownstreamRouteHint.REVALIDATE_ONTOLOGY_OR_DEMAND,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    covered_scope = set()
    covered_channels = set()
    for item in matching_entries:
        covered_scope.update(set(item.effect_scope.primary_outcomes))
        covered_channels.update(set(item.target_channels))
    missing_scope = tuple(sorted(set(required_scope).difference(covered_scope)))
    missing_channels = tuple(sorted(set(required_channels).difference(covered_channels)))

    if not missing_scope and not missing_channels:
        best = _best_controllability(matching_entries)
        evidence = _build_evidence(
            demand_id=demand.demand_id,
            required_scope=required_scope,
            required_channels=required_channels,
            matching_entries=matching_entries,
            additional_basis_refs=non_authoritative_refs,
        )
        if best is A02ControllabilityStatus.LOW_RELIABILITY:
            return (
                A02CapabilityGapEntry(
                    demand_id=demand.demand_id,
                    coverage_status=A02CoverageStatus.CONTESTED,
                    gap_kind=A02GapKind.LOW_RELIABILITY_AFFORDANCE,
                    matching_affordance_candidates=coverage_candidates,
                    blocked_by=(),
                    required_conditions=("reliability_upgrade_required",),
                    composition_status=A02CompositionStatus.NO_COMPOSITION_NEEDED,
                    composition_route_refs=(),
                    partial_coverage=None,
                    controllability_status=best,
                    ownership_boundary_status="within_owner_surface",
                    severity=demand.severity,
                    confidence=A02ConfidenceBand.LOW,
                    downstream_route_hint=A02DownstreamRouteHint.REVALIDATE_ONTOLOGY_OR_DEMAND,
                    coverage_evidence=evidence,
                    provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
                ),
                composition_routes,
            )
        if len(matching_entries) == 1:
            composition_status = A02CompositionStatus.NO_COMPOSITION_NEEDED
            route_refs: tuple[str, ...] = ()
        elif composition_enabled:
            route = A02CompositionRoute(
                route_id=f"a02:{tick_id}:{tick_index}:composition:{demand.demand_id}",
                steps=tuple(
                    A02CompositionStep(
                        step_id=f"a02:{tick_id}:{tick_index}:{demand.demand_id}:{index}",
                        affordance_id=item.affordance_id,
                        contributes_scope=item.effect_scope.primary_outcomes,
                    )
                    for index, item in enumerate(matching_entries, start=1)
                ),
                verified=True,
            )
            composition_routes.append(route)
            composition_status = A02CompositionStatus.COVERED_BY_COMPOSITION
            route_refs = (route.route_id,)
        else:
            composition_status = A02CompositionStatus.COMPOSITION_FORBIDDEN
            route_refs = ()
        gap_kind = A02GapKind.NO_GAP if composition_status is not A02CompositionStatus.COMPOSITION_FORBIDDEN else A02GapKind.COMPOSITION_GAP
        coverage = A02CoverageStatus.FULLY_COVERED if gap_kind is A02GapKind.NO_GAP else A02CoverageStatus.NOT_COVERED
        route_hint = (
            A02DownstreamRouteHint.PROCEED_WITH_COVERED_DEMAND
            if gap_kind is A02GapKind.NO_GAP
            else A02DownstreamRouteHint.SEARCH_COMPOSITION
        )
        confidence = A02ConfidenceBand.HIGH if gap_kind is A02GapKind.NO_GAP else A02ConfidenceBand.LOW
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=coverage,
                gap_kind=gap_kind,
                matching_affordance_candidates=coverage_candidates,
                blocked_by=(),
                required_conditions=(),
                composition_status=composition_status,
                composition_route_refs=route_refs,
                partial_coverage=None,
                controllability_status=best,
                ownership_boundary_status="within_owner_surface",
                severity=demand.severity,
                confidence=confidence,
                downstream_route_hint=route_hint,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    if composition_enabled and covered_scope.issuperset(set(required_scope)):
        route = A02CompositionRoute(
            route_id=f"a02:{tick_id}:{tick_index}:composition:{demand.demand_id}:unverified",
            steps=tuple(
                A02CompositionStep(
                    step_id=f"a02:{tick_id}:{tick_index}:{demand.demand_id}:u{index}",
                    affordance_id=item.affordance_id,
                    contributes_scope=item.effect_scope.primary_outcomes,
                )
                for index, item in enumerate(matching_entries, start=1)
            ),
            verified=False,
        )
        composition_routes.append(route)
        evidence = _build_evidence(
            demand_id=demand.demand_id,
            required_scope=required_scope,
            required_channels=required_channels,
            matching_entries=matching_entries,
            additional_basis_refs=non_authoritative_refs,
        )
        return (
            A02CapabilityGapEntry(
                demand_id=demand.demand_id,
                coverage_status=A02CoverageStatus.NO_CLEAN_COVERAGE_CLAIM,
                gap_kind=A02GapKind.COMPOSITION_GAP,
                matching_affordance_candidates=coverage_candidates,
                blocked_by=(),
                required_conditions=("composition_verification_required",),
                composition_status=A02CompositionStatus.COMPOSITION_POSSIBLE_BUT_UNVERIFIED,
                composition_route_refs=(route.route_id,),
                partial_coverage=None,
                controllability_status=_best_controllability(matching_entries),
                ownership_boundary_status="not_triggered",
                severity=demand.severity,
                confidence=A02ConfidenceBand.LOW,
                downstream_route_hint=A02DownstreamRouteHint.SEARCH_COMPOSITION,
                coverage_evidence=evidence,
                provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
            ),
            composition_routes,
        )

    partial = A02PartialCoverageRecord(
        demand_id=demand.demand_id,
        covered_scope=tuple(sorted(covered_scope.intersection(set(required_scope)))),
        residual_scope=missing_scope,
        covered_channels=tuple(sorted(covered_channels.intersection(set(required_channels)))),
        residual_channels=missing_channels,
    )
    evidence = _build_evidence(
        demand_id=demand.demand_id,
        required_scope=required_scope,
        required_channels=required_channels,
        matching_entries=matching_entries,
        additional_basis_refs=non_authoritative_refs,
    )
    return (
        A02CapabilityGapEntry(
            demand_id=demand.demand_id,
            coverage_status=A02CoverageStatus.PARTIALLY_COVERED,
            gap_kind=A02GapKind.INSUFFICIENT_EFFECT_SCOPE,
            matching_affordance_candidates=coverage_candidates,
            blocked_by=(),
            required_conditions=("residual_scope_uncovered",),
            composition_status=A02CompositionStatus.COMPOSITION_MISSING,
            composition_route_refs=(),
            partial_coverage=partial,
            controllability_status=_best_controllability(matching_entries),
            ownership_boundary_status="not_triggered",
            severity=demand.severity,
            confidence=A02ConfidenceBand.MEDIUM,
            downstream_route_hint=A02DownstreamRouteHint.DEFER_DEMAND,
            coverage_evidence=evidence,
            provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
        ),
        composition_routes,
    )


def _matching_entries(*, demanded_class, demanded_scope, demanded_channels, canonical_entries):
    expected_classes = _expected_affordance_classes(demanded_class)
    scope_set = set(demanded_scope)
    channel_set = set(demanded_channels)
    matching = []
    for entry in canonical_entries:
        if entry.affordance_class not in expected_classes:
            continue
        entry_scope = set(entry.effect_scope.primary_outcomes)
        if scope_set and scope_set.isdisjoint(entry_scope):
            continue
        if channel_set and channel_set.isdisjoint(set(entry.target_channels)):
            continue
        matching.append(entry)
    return tuple(matching)


def _expected_affordance_classes(demand_class: A02DemandClass) -> set[A01AffordanceClass]:
    mapping = {
        A02DemandClass.REGULATORY: {
            A01AffordanceClass.REGULATION_ADJUSTMENT,
            A01AffordanceClass.INHIBITION_SUPPRESSION,
        },
        A02DemandClass.CONTINUITY: {A01AffordanceClass.DEFER_REVISIT},
        A02DemandClass.SELF_REPAIR: {A01AffordanceClass.REPAIR_RECOVERY},
        A02DemandClass.WORLD_FACING: {
            A01AffordanceClass.WORLD_DIRECTED_ACTION,
            A01AffordanceClass.COMMUNICATION_OUTPUT,
        },
        A02DemandClass.COMMUNICATION: {A01AffordanceClass.COMMUNICATION_OUTPUT},
        A02DemandClass.INTERNAL_TOOL: {
            A01AffordanceClass.SENSING_MONITORING,
            A01AffordanceClass.INTERNAL_MODE_SHIFT,
            A01AffordanceClass.REGULATION_ADJUSTMENT,
        },
        A02DemandClass.EXPLORATORY: {A01AffordanceClass.EXPLORATION_DIVERSIFICATION},
        A02DemandClass.COMMITMENT_DRIVEN: {
            A01AffordanceClass.DEFER_REVISIT,
            A01AffordanceClass.COMMUNICATION_OUTPUT,
        },
    }
    return mapping.get(demand_class, set(A01AffordanceClass))


def _best_controllability(entries) -> A02ControllabilityStatus:
    if not entries:
        return A02ControllabilityStatus.UNKNOWN
    classes = {item.controllability.controllability_class for item in entries}
    if classes == {A01ControllabilityClass.SELF_CONTROLLED}:
        return A02ControllabilityStatus.CONTROLLABLE_CURRENTLY
    if classes.issubset(
        {
            A01ControllabilityClass.SELF_CONTROLLED,
            A01ControllabilityClass.SHARED_CONTROLLED,
        }
    ):
        return A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY
    if A01ControllabilityClass.WORLD_DEPENDENT in classes:
        return A02ControllabilityStatus.OUTSIDE_CURRENT_CONTROL
    if A01ControllabilityClass.OBSERVATIONAL in classes:
        return A02ControllabilityStatus.LOW_RELIABILITY
    if A01ControllabilityClass.UNKNOWN in classes:
        return A02ControllabilityStatus.UNKNOWN
    return A02ControllabilityStatus.MIXED_OR_CONTAMINATED


def _non_authoritative_signal_refs(demand) -> tuple[str, ...]:
    refs: list[str] = []
    if bool(getattr(demand, "planner_deadend_signal", False)):
        refs.append("planner_deadend_signal_non_authoritative")
    if bool(getattr(demand, "low_confidence_signal", False)):
        refs.append("low_confidence_signal_non_authoritative")
    return tuple(dict.fromkeys(refs))


def _build_evidence(
    *,
    demand_id,
    required_scope,
    required_channels,
    matching_entries,
    additional_basis_refs: tuple[str, ...] = (),
) -> A02CoverageEvidence:
    matched_scope = set()
    matched_channels = set()
    basis = []
    for item in matching_entries:
        matched_scope.update(set(item.effect_scope.primary_outcomes))
        matched_channels.update(set(item.target_channels))
        basis.append(item.affordance_id)
    unmatched_scope = tuple(sorted(set(required_scope).difference(matched_scope)))
    unmatched_channels = tuple(sorted(set(required_channels).difference(matched_channels)))
    return A02CoverageEvidence(
        demand_id=demand_id,
        matched_scope=tuple(sorted(set(required_scope).intersection(matched_scope))),
        unmatched_scope=unmatched_scope,
        matched_channels=tuple(sorted(set(required_channels).intersection(matched_channels))),
        unmatched_channels=unmatched_channels,
        basis_refs=tuple(dict.fromkeys((*basis, *additional_basis_refs))),
    )


def _build_telemetry(
    *,
    gap_entries: tuple[A02CapabilityGapEntry, ...],
    source_lineage_count: int,
    source_lineage_complete: bool,
    canonical_hint_used_count: int,
    canonical_generated_count: int,
    canonical_coverage_complete: bool,
) -> A02Telemetry:
    return A02Telemetry(
        demand_count=len(gap_entries),
        gap_entry_count=len(gap_entries),
        fully_covered_count=sum(
            int(item.coverage_status is A02CoverageStatus.FULLY_COVERED) for item in gap_entries
        ),
        partial_coverage_count=sum(
            int(item.coverage_status is A02CoverageStatus.PARTIALLY_COVERED)
            for item in gap_entries
        ),
        missing_gap_count=sum(int(item.gap_kind is A02GapKind.MISSING_AFFORDANCE) for item in gap_entries),
        blocked_gap_count=sum(int(item.coverage_status is A02CoverageStatus.BLOCKED) for item in gap_entries),
        composition_gap_count=sum(int(item.gap_kind is A02GapKind.COMPOSITION_GAP) for item in gap_entries),
        composition_unverified_count=sum(
            int(item.composition_status is A02CompositionStatus.COMPOSITION_POSSIBLE_BUT_UNVERIFIED)
            for item in gap_entries
        ),
        ownership_boundary_gap_count=sum(
            int(item.gap_kind is A02GapKind.OWNERSHIP_BOUNDARY_GAP) for item in gap_entries
        ),
        no_clean_coverage_count=sum(
            int(
                item.coverage_status
                in {A02CoverageStatus.NO_CLEAN_COVERAGE_CLAIM, A02CoverageStatus.CONTESTED}
            )
            for item in gap_entries
        ),
        source_lineage_count=source_lineage_count,
        source_lineage_complete=source_lineage_complete,
        canonical_id_hint_used_count=canonical_hint_used_count,
        canonical_id_generated_count=canonical_generated_count,
        canonical_id_coverage_complete=canonical_coverage_complete,
        downstream_consumer_ready=bool(gap_entries),
    )


def _build_gate(
    *,
    entries: tuple[A02CapabilityGapEntry, ...],
    telemetry: A02Telemetry,
    demand_count: int,
) -> A02CapabilityGapGateDecision:
    restrictions: list[str] = []
    status = A02DownstreamReadinessStatus.READY
    gap_ready = bool(entries) and demand_count > 0
    partial_ready = telemetry.partial_coverage_count > 0
    ownership_ready = telemetry.ownership_boundary_gap_count > 0
    composition_ready = (
        telemetry.composition_gap_count > 0 or telemetry.composition_unverified_count > 0
    )

    if not gap_ready:
        restrictions.append("a02_gap_packet_consumer_not_ready")
        status = A02DownstreamReadinessStatus.BLOCKED
    if telemetry.missing_gap_count > 0:
        restrictions.append("a02_missing_affordance_present")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if telemetry.blocked_gap_count > 0:
        restrictions.append("a02_blocked_affordance_present")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if telemetry.partial_coverage_count > 0:
        restrictions.append("a02_partial_coverage_present")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if telemetry.composition_gap_count > 0:
        restrictions.append("a02_composition_gap_present")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if telemetry.composition_unverified_count > 0:
        restrictions.append("a02_composition_unverified")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if telemetry.ownership_boundary_gap_count > 0:
        restrictions.append("a02_ownership_boundary_gap_present")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if telemetry.no_clean_coverage_count > 0:
        restrictions.append("a02_no_clean_coverage_claim")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if not telemetry.source_lineage_complete:
        restrictions.append("a02_source_lineage_partial")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED
    if gap_ready and not telemetry.canonical_id_coverage_complete:
        restrictions.append("a02_canonical_id_coverage_incomplete")
        if status is A02DownstreamReadinessStatus.READY:
            status = A02DownstreamReadinessStatus.DEGRADED

    return A02CapabilityGapGateDecision(
        gap_packet_consumer_ready=gap_ready,
        partial_coverage_consumer_ready=partial_ready,
        ownership_boundary_consumer_ready=ownership_ready,
        composition_consumer_ready=composition_ready,
        downstream_readiness_status=status,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="a02 gate exposes typed capability-gap readiness and bounded restrictions",
    )


def _build_minimal_result(
    *, demand_set_id: str, reason: str, restrictions: tuple[str, ...]
) -> A02CapabilityGapResult:
    telemetry = A02Telemetry(
        demand_count=0,
        gap_entry_count=0,
        fully_covered_count=0,
        partial_coverage_count=0,
        missing_gap_count=0,
        blocked_gap_count=0,
        composition_gap_count=0,
        composition_unverified_count=0,
        ownership_boundary_gap_count=0,
        no_clean_coverage_count=1 if "a02_no_clean_coverage_claim" in restrictions else 0,
        source_lineage_count=0,
        source_lineage_complete=False,
        canonical_id_hint_used_count=0,
        canonical_id_generated_count=0,
        canonical_id_coverage_complete=False,
        downstream_consumer_ready=False,
    )
    ledger = A02CapabilityGapLedger(
        ledger_id="a02:minimal:ledger",
        entries=(),
        source_lineage_refs=(),
        source_lineage_count=0,
        source_lineage_complete=False,
        canonical_id_hint_used_count=0,
        canonical_id_generated_count=0,
        canonical_id_coverage_complete=False,
        no_affordance_invention_observed=True,
        reason=reason,
    )
    gate = A02CapabilityGapGateDecision(
        gap_packet_consumer_ready=False,
        partial_coverage_consumer_ready=False,
        ownership_boundary_consumer_ready=False,
        composition_consumer_ready=False,
        downstream_readiness_status=A02DownstreamReadinessStatus.BLOCKED,
        restrictions=restrictions,
        reason=reason,
    )
    scope = A02ScopeMarker(
        scope="frontier_hosted_a02_capability_gap_detection_slice",
        frontier_only=True,
        narrow_slice_only=True,
        capability_gap_not_planner=True,
        depends_on_a01_canonical_ontology=True,
        no_map_wide_claim=True,
        no_affordance_discovery_claim=True,
        no_hidden_action_execution_claim=True,
        reason="a02 minimal fallback scope",
    )
    return A02CapabilityGapResult(
        demand_set_id=demand_set_id,
        gap_entries=(),
        ledger=ledger,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )


def _build_no_clean_result(
    *,
    tick_id: str,
    tick_index: int,
    demand_set,
    reason: str,
    restrictions: tuple[str, ...],
    capability_input: A02CapabilityGapInput,
    canonical_hint_used_count: int = 0,
    canonical_generated_count: int = 0,
    canonical_coverage_complete: bool = False,
) -> A02CapabilityGapResult:
    lineage_refs = tuple(dict.fromkeys((*capability_input.source_lineage, *demand_set.source_lineage)))
    source_lineage_complete = bool(capability_input.source_lineage and demand_set.source_lineage)
    entries = tuple(
        A02CapabilityGapEntry(
            demand_id=demand.demand_id,
            coverage_status=A02CoverageStatus.NO_CLEAN_COVERAGE_CLAIM,
            gap_kind=A02GapKind.UNKNOWN_CAPABILITY_STATUS,
            matching_affordance_candidates=(),
            blocked_by=(),
            required_conditions=("a01_canonical_ontology_required",),
            composition_status=A02CompositionStatus.COMPOSITION_UNKNOWN,
            composition_route_refs=(),
            partial_coverage=None,
            controllability_status=A02ControllabilityStatus.UNKNOWN,
            ownership_boundary_status="not_evaluated",
            severity=demand.severity,
            confidence=A02ConfidenceBand.INSUFFICIENT_BASIS,
            downstream_route_hint=A02DownstreamRouteHint.REVALIDATE_ONTOLOGY_OR_DEMAND,
            coverage_evidence=A02CoverageEvidence(
                demand_id=demand.demand_id,
                matched_scope=(),
                unmatched_scope=demand.demanded_scope,
                matched_channels=(),
                unmatched_channels=demand.target_channels,
                basis_refs=("a01_unavailable",),
            ),
            provenance=tuple(dict.fromkeys((*demand.provenance, demand.source_ref))),
        )
        for demand in demand_set.demands
    )
    telemetry = _build_telemetry(
        gap_entries=entries,
        source_lineage_count=len(lineage_refs),
        source_lineage_complete=source_lineage_complete,
        canonical_hint_used_count=canonical_hint_used_count,
        canonical_generated_count=canonical_generated_count,
        canonical_coverage_complete=canonical_coverage_complete,
    )
    ledger = A02CapabilityGapLedger(
        ledger_id=f"a02:{tick_id}:{tick_index}:ledger",
        entries=tuple(
            A02GapLedgerEntry(
                ledger_entry_id=f"a02:{tick_id}:{tick_index}:ledger:{item.demand_id}",
                demand_id=item.demand_id,
                coverage_status=item.coverage_status,
                gap_kind=item.gap_kind,
                reason=item.downstream_route_hint.value,
            )
            for item in entries
        ),
        source_lineage_refs=lineage_refs,
        source_lineage_count=len(lineage_refs),
        source_lineage_complete=source_lineage_complete,
        canonical_id_hint_used_count=canonical_hint_used_count,
        canonical_id_generated_count=canonical_generated_count,
        canonical_id_coverage_complete=canonical_coverage_complete,
        no_affordance_invention_observed=True,
        reason=reason,
    )
    gate = A02CapabilityGapGateDecision(
        gap_packet_consumer_ready=bool(entries),
        partial_coverage_consumer_ready=False,
        ownership_boundary_consumer_ready=False,
        composition_consumer_ready=False,
        downstream_readiness_status=A02DownstreamReadinessStatus.DEGRADED,
        restrictions=tuple(dict.fromkeys((*restrictions, "a02_no_clean_coverage_claim"))),
        reason=reason,
    )
    scope = A02ScopeMarker(
        scope="frontier_hosted_a02_capability_gap_detection_slice",
        frontier_only=True,
        narrow_slice_only=True,
        capability_gap_not_planner=True,
        depends_on_a01_canonical_ontology=True,
        no_map_wide_claim=True,
        no_affordance_discovery_claim=True,
        no_hidden_action_execution_claim=True,
        reason="a02 no-clean fallback scope",
    )
    return A02CapabilityGapResult(
        demand_set_id=demand_set.demand_set_id,
        gap_entries=entries,
        ledger=ledger,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )
