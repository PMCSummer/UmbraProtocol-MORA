from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01CanonicalOntologyResult,
    A01ValidityStatus,
)
from substrate.a02_capability_gap_detection import (
    A02CapabilityGapResult,
    A02GapKind,
)
from substrate.a03_internal_tool_affordances.models import (
    A03AvailabilityStatus,
    A03BlockedInternalToolRecord,
    A03CanonicalToolAffordance,
    A03CanonicalToolRegistry,
    A03CapabilityGapLinkageKind,
    A03CapabilityGapToolLinkage,
    A03ContractStatus,
    A03ContestedToolRecord,
    A03DownstreamReadinessStatus,
    A03InternalOperationCandidate,
    A03InternalOperationCandidateSet,
    A03InternalToolAffordanceResult,
    A03InternalToolGateDecision,
    A03MissingInternalToolRecord,
    A03NormalizationDecisionType,
    A03OperationBoundaryKind,
    A03RejectedInternalOperation,
    A03RejectionReason,
    A03ScopeMarker,
    A03Telemetry,
    A03ToolAliasRecord,
    A03ToolAvailabilityProfile,
    A03ToolBoundaryConflict,
    A03ToolClass,
    A03ToolCleanupLedger,
    A03ToolCompositionRole,
    A03ToolInsufficiencyRecord,
    A03ToolNormalizationDecision,
)

_PSEUDOTOOL_LABEL_TOKENS = {
    "reason_about_anything",
    "general_reasoning_tool",
    "fix_problem",
    "think_harder",
    "reflect_more",
    "understand_better",
}
_NARRATIVE_SLOGAN_TOKENS = {
    "think harder",
    "reflect more",
    "understand better",
}


def build_a03_internal_tool_affordances(
    *,
    tick_id: str,
    tick_index: int,
    operation_candidate_set: A03InternalOperationCandidateSet | None,
    a01_result: A01CanonicalOntologyResult | None,
    a02_result: A02CapabilityGapResult | None,
    tool_affordance_enabled: bool = True,
) -> A03InternalToolAffordanceResult:
    if not tool_affordance_enabled:
        return _build_minimal_result(
            candidate_set_id=f"a03:{tick_id}:candidate_set:none",
            reason="A03 gate disabled in test fixture",
            restrictions=("a03_disabled", "a03_no_safe_tool_claim"),
        )
    if not isinstance(operation_candidate_set, A03InternalOperationCandidateSet):
        return _build_minimal_result(
            candidate_set_id=f"a03:{tick_id}:candidate_set:none",
            reason="a03 requires typed operation candidates and will not infer tools from module names",
            restrictions=("insufficient_a03_basis", "a03_no_safe_tool_claim"),
        )
    if not operation_candidate_set.candidates:
        return _build_minimal_result(
            candidate_set_id=operation_candidate_set.candidate_set_id,
            reason="a03 received empty candidate set and cannot claim canonical internal tool affordances",
            restrictions=("insufficient_a03_basis", "a03_no_safe_tool_claim"),
        )

    if not isinstance(a01_result, A01CanonicalOntologyResult):
        return _build_minimal_result(
            candidate_set_id=operation_candidate_set.candidate_set_id,
            reason="a03 requires a01 canonical ontology and will not reconstruct tool affordances from raw labels",
            restrictions=("a03_requires_a01_canonical_ontology", "a03_no_safe_tool_claim"),
        )

    a01_entries = a01_result.ontology_snapshot.canonical_entries
    a01_by_id = {entry.affordance_id: entry for entry in a01_entries}
    source_lineage = tuple(dict.fromkeys(operation_candidate_set.source_lineage))

    canonical_tools: list[A03CanonicalToolAffordance] = []
    alias_records: list[A03ToolAliasRecord] = []
    composition_roles: list[A03ToolCompositionRole] = []
    normalization_decisions: list[A03ToolNormalizationDecision] = []
    rejected_operations: list[A03RejectedInternalOperation] = []
    contested_records: list[A03ContestedToolRecord] = []
    boundary_conflicts: list[A03ToolBoundaryConflict] = []

    canonical_hint_used_count = 0
    canonical_generated_count = 0

    tool_candidates: list[A03InternalOperationCandidate] = []

    for candidate in operation_candidate_set.candidates:
        rejection = _reject_non_tool_candidate(candidate)
        if rejection is not None:
            rejected_operations.append(rejection)
            normalization_decisions.append(
                A03ToolNormalizationDecision(
                    decision_id=f"a03:{tick_id}:{tick_index}:reject:{candidate.operation_ref}",
                    decision_type=A03NormalizationDecisionType.REJECTED_AS_NON_TOOL,
                    source_operation_refs=(candidate.operation_ref,),
                    produced_tool_ids=(),
                    reason=rejection.reason,
                )
            )
            if candidate.boundary_kind not in {
                A03OperationBoundaryKind.REUSABLE_TOOL,
                A03OperationBoundaryKind.PSEUDO_TOOL,
            }:
                boundary_conflicts.append(
                    A03ToolBoundaryConflict(
                        conflict_id=f"a03:{tick_id}:{tick_index}:boundary:{candidate.operation_ref}",
                        operation_ref=candidate.operation_ref,
                        conflicting_boundary=candidate.boundary_kind,
                        reason=rejection.rejection_reason.value,
                    )
                )
            continue
        tool_candidates.append(candidate)

    signature_groups: dict[tuple[str, ...], list[A03InternalOperationCandidate]] = {}
    for candidate in tool_candidates:
        signature_groups.setdefault(_contract_signature(candidate), []).append(candidate)

    label_contract_map: dict[str, set[tuple[str, ...]]] = {}
    for signature, candidates in signature_groups.items():
        for candidate in candidates:
            label_contract_map.setdefault(candidate.local_label.strip().lower(), set()).add(signature)

    for label, signatures in label_contract_map.items():
        if len(signatures) > 1:
            source_refs = tuple(
                item.operation_ref
                for signature in signatures
                for item in signature_groups[signature]
                if item.local_label.strip().lower() == label
            )
            contested_records.append(
                A03ContestedToolRecord(
                    contested_id=f"a03:{tick_id}:{tick_index}:contested:{label}",
                    operation_refs=source_refs,
                    reason="same label has materially different invocation contracts",
                )
            )
            normalization_decisions.append(
                A03ToolNormalizationDecision(
                    decision_id=f"a03:{tick_id}:{tick_index}:split:{label}",
                    decision_type=A03NormalizationDecisionType.SPLIT_BY_CONTRACT,
                    source_operation_refs=source_refs,
                    produced_tool_ids=(),
                    reason="same-label candidates were split by typed contract signature",
                )
            )

    for signature, candidates in signature_groups.items():
        primary = candidates[0]
        tool_id, hint_used = _resolve_tool_id(
            tick_id=tick_id,
            tick_index=tick_index,
            operation_ref=primary.operation_ref,
            canonical_tool_id_hint=primary.canonical_tool_id_hint,
            a01_ids=set(a01_by_id),
        )
        if hint_used:
            canonical_hint_used_count += 1
        else:
            canonical_generated_count += 1

        contract_status = _contract_status(primary)
        availability = _availability_profile(
            candidate=primary,
            candidate_set=operation_candidate_set,
            a01_entry=a01_by_id.get(primary.canonical_tool_id_hint or ""),
            contract_status=contract_status,
        )
        canonical_tools.append(
            A03CanonicalToolAffordance(
                tool_affordance_id=tool_id,
                canonical_label=primary.local_label,
                tool_class=primary.tool_class,
                invocation_contract=primary.invocation_contract,
                observation_hooks=primary.observation_hooks,
                failure_signatures=primary.failure_signatures,
                cost_profile=primary.cost_profile,
                side_effect_profile=primary.side_effect_profile,
                availability_profile=availability,
                contract_status=contract_status,
                provenance_refs=tuple(
                    dict.fromkeys(
                        (
                            *primary.source_profile.provenance_refs,
                            primary.operation_ref,
                            *primary.source_profile.source_lineage,
                        )
                    )
                ),
                canonical_source_operation_refs=tuple(item.operation_ref for item in candidates),
            )
        )

        decision_type = (
            A03NormalizationDecisionType.MERGED_AS_ALIAS
            if len(candidates) > 1
            else A03NormalizationDecisionType.CANONICALIZED
        )
        normalization_decisions.append(
            A03ToolNormalizationDecision(
                decision_id=f"a03:{tick_id}:{tick_index}:normalize:{tool_id}",
                decision_type=decision_type,
                source_operation_refs=tuple(item.operation_ref for item in candidates),
                produced_tool_ids=(tool_id,),
                reason=(
                    "true alias merge by equivalent typed invocation contract"
                    if len(candidates) > 1
                    else "typed reusable operation canonicalized as internal tool affordance"
                ),
            )
        )

        if len(candidates) > 1:
            for alias in candidates[1:]:
                alias_records.append(
                    A03ToolAliasRecord(
                        alias_id=f"a03:{tick_id}:{tick_index}:alias:{alias.operation_ref}",
                        canonical_tool_id=tool_id,
                        alias_label=alias.local_label,
                        source_operation_ref=alias.operation_ref,
                    )
                )

        composition_roles.append(
            A03ToolCompositionRole(
                role_id=f"a03:{tick_id}:{tick_index}:role:{tool_id}",
                tool_affordance_id=tool_id,
                role_kind=primary.tool_class.value,
            )
        )

    gap_linkage = _build_gap_linkage(
        a02_result=a02_result,
        canonical_tools=tuple(canonical_tools),
    )

    contract_incomplete_count = sum(
        int(tool.contract_status is A03ContractStatus.CONTRACT_INCOMPLETE)
        for tool in canonical_tools
    )
    degraded_tool_count = sum(
        int(tool.availability_profile.status is A03AvailabilityStatus.DEGRADED)
        for tool in canonical_tools
    )
    blocked_tool_count = sum(
        int(
            tool.availability_profile.status
            in {
                A03AvailabilityStatus.BLOCKED_BY_CONTEXT,
                A03AvailabilityStatus.BLOCKED_BY_RESOURCE,
                A03AvailabilityStatus.BLOCKED_BY_MISSING_OBSERVATION,
                A03AvailabilityStatus.INVALID_UNDER_CURRENT_MODE,
                A03AvailabilityStatus.CONTESTED_AVAILABILITY,
            }
        )
        for tool in canonical_tools
    )
    overbroad_generic_operation_rejected = any(
        item.rejection_reason is A03RejectionReason.OVERBROAD_GENERIC_OPERATION
        for item in rejected_operations
    )
    legacy_direct_call_path_detected = any(item.legacy_module_only for item in tool_candidates) or any(
        item.rejection_reason is A03RejectionReason.IMPLEMENTATION_PLUMBING
        for item in rejected_operations
    )

    canonical_tool_id_coverage_complete = (
        canonical_hint_used_count > 0 and canonical_generated_count == 0
    )

    ledger = A03ToolCleanupLedger(
        ledger_id=f"a03:{tick_id}:{tick_index}:ledger",
        normalization_decisions=tuple(normalization_decisions),
        rejected_operations=tuple(rejected_operations),
        contested_records=tuple(contested_records),
        boundary_conflicts=tuple(boundary_conflicts),
        canonical_tool_count=len(canonical_tools),
        rejected_operation_count=len(rejected_operations),
        contested_tool_count=len(contested_records),
        contract_incomplete_count=contract_incomplete_count,
        degraded_tool_count=degraded_tool_count,
        blocked_tool_count=blocked_tool_count,
        missing_internal_tool_gap_count=len(gap_linkage.missing_internal_tools),
        blocked_internal_tool_gap_count=len(gap_linkage.blocked_internal_tools),
        overbroad_generic_operation_rejected=overbroad_generic_operation_rejected,
        legacy_direct_call_detected=legacy_direct_call_path_detected,
        canonical_tool_id_hint_used_count=canonical_hint_used_count,
        canonical_tool_id_generated_count=canonical_generated_count,
        canonical_tool_id_coverage_complete=canonical_tool_id_coverage_complete,
        source_lineage_count=len(source_lineage),
        source_lineage_complete=bool(source_lineage),
        reason="a03 cleanup ledger captures typed canonicalization/rejection/linkage decisions for internal tools",
    )

    telemetry = A03Telemetry(
        canonical_tool_count=ledger.canonical_tool_count,
        rejected_operation_count=ledger.rejected_operation_count,
        contested_tool_count=ledger.contested_tool_count,
        contract_incomplete_count=ledger.contract_incomplete_count,
        degraded_tool_count=ledger.degraded_tool_count,
        blocked_tool_count=ledger.blocked_tool_count,
        missing_internal_tool_gap_count=ledger.missing_internal_tool_gap_count,
        blocked_internal_tool_gap_count=ledger.blocked_internal_tool_gap_count,
        overbroad_generic_operation_rejected=ledger.overbroad_generic_operation_rejected,
        legacy_direct_call_detected=ledger.legacy_direct_call_detected,
        canonical_tool_id_coverage_complete=ledger.canonical_tool_id_coverage_complete,
        downstream_consumer_ready=ledger.canonical_tool_count > 0,
    )

    gate = _build_gate(
        ledger=ledger,
        telemetry=telemetry,
        a02_present=isinstance(a02_result, A02CapabilityGapResult),
    )

    registry = A03CanonicalToolRegistry(
        registry_id=f"a03:{tick_id}:{tick_index}:registry",
        canonical_tools=tuple(canonical_tools),
        aliases=tuple(alias_records),
        composition_roles=tuple(composition_roles),
    )

    return A03InternalToolAffordanceResult(
        candidate_set_id=operation_candidate_set.candidate_set_id,
        canonical_registry=registry,
        cleanup_ledger=ledger,
        gap_linkage=gap_linkage,
        gate=gate,
        scope_marker=A03ScopeMarker(
            scope="frontier_hosted_a03_internal_tool_affordance_slice",
            frontier_only=True,
            narrow_slice_only=True,
            internal_tool_ontology_not_executor=True,
            depends_on_a01_canonical_ontology=True,
            depends_on_a02_gap_packets=True,
            no_map_wide_claim=True,
            no_tool_invention_claim=True,
            no_truth_or_correctness_guarantee_claim=True,
            reason="a03 normalizes typed internal operation contracts into canonical tool affordances without execution authority",
        ),
        telemetry=telemetry,
        reason="a03 produced typed internal tool registry, rejection ledger, and a02 gap linkage without tool execution",
    )


def _reject_non_tool_candidate(
    candidate: A03InternalOperationCandidate,
) -> A03RejectedInternalOperation | None:
    label_norm = candidate.local_label.strip().lower()
    if candidate.boundary_kind is A03OperationBoundaryKind.INTERNAL_MODE:
        return A03RejectedInternalOperation(
            operation_ref=candidate.operation_ref,
            local_label=candidate.local_label,
            rejection_reason=A03RejectionReason.MODE_NOT_TOOL,
            reason="internal mode/state marker is not a reusable internal tool affordance",
        )
    if candidate.boundary_kind is A03OperationBoundaryKind.HELPER_ROUTINE:
        return A03RejectedInternalOperation(
            operation_ref=candidate.operation_ref,
            local_label=candidate.local_label,
            rejection_reason=A03RejectionReason.HELPER_NOT_AFFORDANCE,
            reason="helper routine does not expose agency-level invocation contract",
        )
    if candidate.boundary_kind in {
        A03OperationBoundaryKind.HIDDEN_PLUMBING,
        A03OperationBoundaryKind.EXTERNAL_API_PROXY,
    } or candidate.legacy_module_only:
        return A03RejectedInternalOperation(
            operation_ref=candidate.operation_ref,
            local_label=candidate.local_label,
            rejection_reason=A03RejectionReason.IMPLEMENTATION_PLUMBING,
            reason="implementation/module plumbing is not canonical internal tool affordance",
        )
    if candidate.boundary_kind is A03OperationBoundaryKind.STORED_CONTENT:
        return A03RejectedInternalOperation(
            operation_ref=candidate.operation_ref,
            local_label=candidate.local_label,
            rejection_reason=A03RejectionReason.STORED_CONTENT_NOT_TOOL,
            reason="stored content/state is not an invocable internal operation",
        )
    if candidate.boundary_kind is A03OperationBoundaryKind.PSEUDO_TOOL or label_norm in _PSEUDOTOOL_LABEL_TOKENS:
        return A03RejectedInternalOperation(
            operation_ref=candidate.operation_ref,
            local_label=candidate.local_label,
            rejection_reason=A03RejectionReason.OVERBROAD_GENERIC_OPERATION,
            reason="overbroad generic operation cannot be canonicalized without bounded typed decomposition",
        )
    if label_norm in _NARRATIVE_SLOGAN_TOKENS:
        return A03RejectedInternalOperation(
            operation_ref=candidate.operation_ref,
            local_label=candidate.local_label,
            rejection_reason=A03RejectionReason.NARRATIVE_SLOGAN_WITHOUT_CONTRACT,
            reason="narrative slogan without typed invocation contract is not a tool affordance",
        )
    return None


def _contract_signature(candidate: A03InternalOperationCandidate) -> tuple[str, ...]:
    contract = candidate.invocation_contract
    return (
        candidate.tool_class.value,
        ",".join(sorted(f"{item.type_name}:{int(item.required)}" for item in contract.accepted_input_types)),
        ",".join(sorted(f"{item.type_name}:{int(item.guaranteed)}" for item in contract.produced_output_types)),
        ",".join(sorted(contract.required_context)),
        ",".join(sorted(contract.preconditions)),
        ",".join(sorted(contract.abort_conditions)),
        ",".join(sorted(contract.completion_criteria)),
        ",".join(sorted(item.signal_ref for item in candidate.observation_hooks)),
        ",".join(sorted(item.failure_mode for item in candidate.failure_signatures)),
    )


def _resolve_tool_id(
    *,
    tick_id: str,
    tick_index: int,
    operation_ref: str,
    canonical_tool_id_hint: str | None,
    a01_ids: set[str],
) -> tuple[str, bool]:
    if canonical_tool_id_hint and canonical_tool_id_hint in a01_ids:
        return canonical_tool_id_hint, True
    return f"a03:{tick_id}:{tick_index}:tool:{operation_ref}", False


def _contract_status(candidate: A03InternalOperationCandidate) -> A03ContractStatus:
    contract = candidate.invocation_contract
    if not contract.accepted_input_types:
        return A03ContractStatus.CONTRACT_INCOMPLETE
    if not contract.produced_output_types:
        return A03ContractStatus.CONTRACT_INCOMPLETE
    if not contract.completion_criteria:
        return A03ContractStatus.CONTRACT_INCOMPLETE
    if not candidate.observation_hooks:
        return A03ContractStatus.CONTRACT_INCOMPLETE
    if not candidate.failure_signatures:
        return A03ContractStatus.CONTRACT_INCOMPLETE
    if not contract.abort_conditions:
        return A03ContractStatus.PARTIAL_CONTRACT
    return A03ContractStatus.COMPLETE_CONTRACT


def _availability_profile(
    *,
    candidate: A03InternalOperationCandidate,
    candidate_set: A03InternalOperationCandidateSet,
    a01_entry,
    contract_status: A03ContractStatus,
) -> A03ToolAvailabilityProfile:
    basis: list[str] = []
    if contract_status is A03ContractStatus.CONTRACT_INCOMPLETE:
        basis.append("contract_incomplete")
        return A03ToolAvailabilityProfile(
            status=A03AvailabilityStatus.AVAILABLE_BUT_UNVERIFIED,
            basis_refs=tuple(dict.fromkeys(basis)),
        )

    mode_requirements = [
        req.split(":", 1)[1]
        for req in (*candidate.required_context, *candidate.invocation_contract.required_context)
        if req.startswith("mode:")
    ]
    if mode_requirements and candidate_set.active_mode not in mode_requirements:
        basis.append("invalid_mode")
        return A03ToolAvailabilityProfile(
            status=A03AvailabilityStatus.INVALID_UNDER_CURRENT_MODE,
            basis_refs=tuple(dict.fromkeys(basis)),
        )

    observation_requirements = [
        req.split(":", 1)[1]
        for req in candidate.invocation_contract.preconditions
        if req.startswith("requires_observation:")
    ]
    if observation_requirements:
        missing = [
            ref for ref in observation_requirements if ref not in set(candidate_set.available_observation_channels)
        ]
        if missing:
            basis.append("missing_observation_channel")
            return A03ToolAvailabilityProfile(
                status=A03AvailabilityStatus.BLOCKED_BY_MISSING_OBSERVATION,
                basis_refs=tuple(dict.fromkeys((*basis, *missing))),
            )

    if candidate_set.resource_pressure and any(
        req in {"resource_available", "resource_budget_available"}
        for req in candidate.invocation_contract.preconditions
    ):
        basis.append("resource_pressure")
        return A03ToolAvailabilityProfile(
            status=A03AvailabilityStatus.BLOCKED_BY_RESOURCE,
            basis_refs=tuple(dict.fromkeys(basis)),
        )

    if a01_entry is not None and a01_entry.validity_status in {
        A01ValidityStatus.DEPRECATED,
        A01ValidityStatus.UNAVAILABLE,
    }:
        basis.append(f"a01_validity:{a01_entry.validity_status.value}")
        return A03ToolAvailabilityProfile(
            status=A03AvailabilityStatus.BLOCKED_BY_CONTEXT,
            basis_refs=tuple(dict.fromkeys(basis)),
        )

    if str(candidate.validity_hint).strip().lower() == "contested":
        basis.append("candidate_validity_contested")
        return A03ToolAvailabilityProfile(
            status=A03AvailabilityStatus.CONTESTED_AVAILABILITY,
            basis_refs=tuple(dict.fromkeys(basis)),
        )

    if candidate.reliability_hint < 0.5 or candidate.controllability_hint < 0.5:
        basis.append("low_reliability_or_controllability")
        return A03ToolAvailabilityProfile(
            status=A03AvailabilityStatus.DEGRADED,
            basis_refs=tuple(dict.fromkeys(basis)),
        )

    return A03ToolAvailabilityProfile(
        status=A03AvailabilityStatus.AVAILABLE,
        basis_refs=("availability_ok",),
    )


def _build_gap_linkage(
    *,
    a02_result: A02CapabilityGapResult | None,
    canonical_tools: tuple[A03CanonicalToolAffordance, ...],
) -> A03CapabilityGapToolLinkage:
    if not isinstance(a02_result, A02CapabilityGapResult):
        return A03CapabilityGapToolLinkage(
            linkage_kind=A03CapabilityGapLinkageKind.NO_TOOL_GAP_CLAIM,
            missing_internal_tools=(),
            blocked_internal_tools=(),
            tool_insufficiency=(),
            reason="a03 received no typed a02 gap packet and does not fabricate tool-gap linkage",
        )

    missing_internal: list[A03MissingInternalToolRecord] = []
    blocked_internal: list[A03BlockedInternalToolRecord] = []
    insufficiency: list[A03ToolInsufficiencyRecord] = []
    world_missing_count = 0

    for entry in a02_result.gap_entries:
        is_internal = _is_internal_tool_gap(entry)
        if entry.gap_kind is A02GapKind.MISSING_AFFORDANCE:
            if is_internal:
                missing_internal.append(
                    A03MissingInternalToolRecord(
                        demand_id=entry.demand_id,
                        required_tool_class=_infer_required_tool_class(entry),
                        reason="a02 gap scope implies missing internal diagnostic/revalidation/comparison means",
                    )
                )
            else:
                world_missing_count += 1
        elif entry.gap_kind in {
            A02GapKind.RESOURCE_BLOCKED_GAP,
            A02GapKind.PRECONDITION_UNSATISFIED_GAP,
            A02GapKind.UNAVAILABLE_AFFORDANCE,
            A02GapKind.INVALIDATED_AFFORDANCE_GAP,
        } and is_internal:
            blocked_internal.append(
                A03BlockedInternalToolRecord(
                    demand_id=entry.demand_id,
                    blocking_reason=entry.gap_kind.value,
                    related_tool_ids=tuple(tool.tool_affordance_id for tool in canonical_tools),
                )
            )
        elif entry.gap_kind in {
            A02GapKind.LOW_RELIABILITY_AFFORDANCE,
            A02GapKind.INSUFFICIENT_EFFECT_SCOPE,
            A02GapKind.COMPOSITION_GAP,
            A02GapKind.UNKNOWN_CAPABILITY_STATUS,
        } and is_internal:
            insufficiency.append(
                A03ToolInsufficiencyRecord(
                    demand_id=entry.demand_id,
                    insufficiency_kind=entry.gap_kind.value,
                    residual_scope=entry.coverage_evidence.unmatched_scope,
                )
            )

    if missing_internal:
        kind = A03CapabilityGapLinkageKind.MISSING_INTERNAL_TOOL
        reason = "a03 localized a02 uncovered demand to missing internal tool means"
    elif blocked_internal:
        kind = A03CapabilityGapLinkageKind.BLOCKED_INTERNAL_TOOL
        reason = "a03 localized a02 blockage to blocked internal tool means"
    elif insufficiency:
        kind = A03CapabilityGapLinkageKind.DEGRADED_INTERNAL_TOOL
        reason = "a03 localized a02 insufficiency to degraded/internal-tool contract weakness"
    elif world_missing_count > 0:
        kind = A03CapabilityGapLinkageKind.MISSING_WORLD_ACTION_NOT_TOOL
        reason = "a02 missing gap points to world-action means and is not re-labeled as internal tool gap"
    elif a02_result.telemetry.no_clean_coverage_count > 0:
        kind = A03CapabilityGapLinkageKind.GAP_LINKAGE_UNCERTAIN
        reason = "a02 no-clean coverage keeps tool-gap linkage explicitly uncertain"
    else:
        kind = A03CapabilityGapLinkageKind.NO_TOOL_GAP_CLAIM
        reason = "a02 gap packet provides no internal-tool insufficiency localization"

    return A03CapabilityGapToolLinkage(
        linkage_kind=kind,
        missing_internal_tools=tuple(missing_internal),
        blocked_internal_tools=tuple(blocked_internal),
        tool_insufficiency=tuple(insufficiency),
        reason=reason,
    )


def _is_internal_tool_gap(entry) -> bool:
    unmatched_scope = {token.lower() for token in entry.coverage_evidence.unmatched_scope}
    unmatched_channels = {token.lower() for token in entry.coverage_evidence.unmatched_channels}
    if "world" in unmatched_channels:
        return False
    internal_markers = {
        "diagnostic",
        "diagnostics",
        "revalidate",
        "revalidation",
        "compare",
        "comparison",
        "simulate",
        "simulation",
        "inspect",
        "inspection",
        "monitor",
        "monitoring",
        "check",
        "constraint",
    }
    return bool(unmatched_scope.intersection(internal_markers))


def _infer_required_tool_class(entry) -> A03ToolClass:
    unmatched_scope = {token.lower() for token in entry.coverage_evidence.unmatched_scope}
    if {"diagnostic", "diagnostics"}.intersection(unmatched_scope):
        return A03ToolClass.DIAGNOSTIC
    if {"revalidate", "revalidation", "check"}.intersection(unmatched_scope):
        return A03ToolClass.REVALIDATION
    if {"compare", "comparison"}.intersection(unmatched_scope):
        return A03ToolClass.COMPARISON
    if {"simulate", "simulation"}.intersection(unmatched_scope):
        return A03ToolClass.SIMULATION
    if {"inspect", "inspection"}.intersection(unmatched_scope):
        return A03ToolClass.INSPECTION
    return A03ToolClass.SEARCH_ENABLING


def _build_gate(
    *,
    ledger: A03ToolCleanupLedger,
    telemetry: A03Telemetry,
    a02_present: bool,
) -> A03InternalToolGateDecision:
    restrictions: list[str] = []
    internal_tool_ready = ledger.canonical_tool_count > 0
    tool_contract_ready = ledger.contract_incomplete_count == 0 and internal_tool_ready
    gap_linkage_ready = a02_present
    no_legacy_direct_call_ready = not ledger.legacy_direct_call_detected

    status = A03DownstreamReadinessStatus.READY

    if not internal_tool_ready:
        restrictions.append("a03_internal_tool_consumer_not_ready")
        status = A03DownstreamReadinessStatus.NO_SAFE_DOWNSTREAM_TOOL_CLAIM
    if not tool_contract_ready:
        restrictions.append("a03_tool_contract_incomplete")
        if status is A03DownstreamReadinessStatus.READY:
            status = A03DownstreamReadinessStatus.MISSING_CONTRACT_CONSUMER
    if telemetry.degraded_tool_count > 0 or telemetry.blocked_tool_count > 0:
        restrictions.append("a03_tool_degraded_or_blocked")
    if telemetry.missing_internal_tool_gap_count > 0:
        restrictions.append("a03_missing_internal_tool_gap")
    if telemetry.overbroad_generic_operation_rejected:
        restrictions.append("a03_overbroad_generic_operation_rejected")
    if not gap_linkage_ready:
        restrictions.append("a03_tool_gap_linkage_unavailable")
    if not no_legacy_direct_call_ready:
        restrictions.append("a03_legacy_direct_call_detected")
        status = A03DownstreamReadinessStatus.LEGACY_DIRECT_CALL_DETECTED
    if not ledger.canonical_tool_id_coverage_complete:
        restrictions.append("a03_canonical_tool_id_coverage_incomplete")
        if status is A03DownstreamReadinessStatus.READY:
            status = A03DownstreamReadinessStatus.MISSING_TOOL_ID_CONSUMER

    return A03InternalToolGateDecision(
        internal_tool_consumer_ready=internal_tool_ready,
        tool_contract_consumer_ready=tool_contract_ready,
        tool_gap_linkage_consumer_ready=gap_linkage_ready,
        no_legacy_direct_call_consumer_ready=no_legacy_direct_call_ready,
        downstream_readiness_status=status,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="a03 gate exposes canonical internal-tool readiness, contract completeness, and legacy direct-call path restrictions",
    )


def _build_minimal_result(
    *,
    candidate_set_id: str,
    reason: str,
    restrictions: tuple[str, ...],
) -> A03InternalToolAffordanceResult:
    registry = A03CanonicalToolRegistry(
        registry_id="a03:minimal:registry",
        canonical_tools=(),
        aliases=(),
        composition_roles=(),
    )
    gap_linkage = A03CapabilityGapToolLinkage(
        linkage_kind=A03CapabilityGapLinkageKind.NO_TOOL_GAP_CLAIM,
        missing_internal_tools=(),
        blocked_internal_tools=(),
        tool_insufficiency=(),
        reason=reason,
    )
    ledger = A03ToolCleanupLedger(
        ledger_id="a03:minimal:ledger",
        normalization_decisions=(),
        rejected_operations=(),
        contested_records=(),
        boundary_conflicts=(),
        canonical_tool_count=0,
        rejected_operation_count=0,
        contested_tool_count=0,
        contract_incomplete_count=0,
        degraded_tool_count=0,
        blocked_tool_count=0,
        missing_internal_tool_gap_count=0,
        blocked_internal_tool_gap_count=0,
        overbroad_generic_operation_rejected=False,
        legacy_direct_call_detected=False,
        canonical_tool_id_hint_used_count=0,
        canonical_tool_id_generated_count=0,
        canonical_tool_id_coverage_complete=False,
        source_lineage_count=0,
        source_lineage_complete=False,
        reason=reason,
    )
    telemetry = A03Telemetry(
        canonical_tool_count=0,
        rejected_operation_count=0,
        contested_tool_count=0,
        contract_incomplete_count=0,
        degraded_tool_count=0,
        blocked_tool_count=0,
        missing_internal_tool_gap_count=0,
        blocked_internal_tool_gap_count=0,
        overbroad_generic_operation_rejected=False,
        legacy_direct_call_detected=False,
        canonical_tool_id_coverage_complete=False,
        downstream_consumer_ready=False,
    )
    gate = A03InternalToolGateDecision(
        internal_tool_consumer_ready=False,
        tool_contract_consumer_ready=False,
        tool_gap_linkage_consumer_ready=False,
        no_legacy_direct_call_consumer_ready=True,
        downstream_readiness_status=A03DownstreamReadinessStatus.NO_SAFE_DOWNSTREAM_TOOL_CLAIM,
        restrictions=restrictions,
        reason=reason,
    )
    return A03InternalToolAffordanceResult(
        candidate_set_id=candidate_set_id,
        canonical_registry=registry,
        cleanup_ledger=ledger,
        gap_linkage=gap_linkage,
        gate=gate,
        scope_marker=A03ScopeMarker(
            scope="frontier_hosted_a03_internal_tool_affordance_slice",
            frontier_only=True,
            narrow_slice_only=True,
            internal_tool_ontology_not_executor=True,
            depends_on_a01_canonical_ontology=True,
            depends_on_a02_gap_packets=True,
            no_map_wide_claim=True,
            no_tool_invention_claim=True,
            no_truth_or_correctness_guarantee_claim=True,
            reason="a03 minimal fallback scope",
        ),
        telemetry=telemetry,
        reason=reason,
    )

