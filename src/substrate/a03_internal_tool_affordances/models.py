from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class A03ToolClass(str, Enum):
    RETRIEVAL = "retrieval"
    COMPARISON = "comparison"
    DECOMPOSITION = "decomposition"
    SIMULATION = "simulation"
    REVALIDATION = "revalidation"
    HYPOTHESIS_CHECKING = "hypothesis_checking"
    FACTORIZATION = "factorization"
    MONITORING = "monitoring"
    INSPECTION = "inspection"
    CONSTRAINT_CHECKING = "constraint_checking"
    COMPRESSION = "compression"
    ATTENTION_REDIRECTION = "attention_redirection"
    SELF_QUERY = "self_query"
    EVIDENCE_GATHERING = "evidence_gathering"
    SEARCH_ENABLING = "search_enabling"
    TRANSFORMATIVE = "transformative"
    DIAGNOSTIC = "diagnostic"
    ROUTE_BUILDING = "route_building"


class A03OperationBoundaryKind(str, Enum):
    REUSABLE_TOOL = "reusable_tool"
    INTERNAL_MODE = "internal_mode"
    HELPER_ROUTINE = "helper_routine"
    HIDDEN_PLUMBING = "hidden_plumbing"
    LATENT_STATE = "latent_state"
    STORED_CONTENT = "stored_content"
    STRATEGY = "strategy"
    PSEUDO_TOOL = "pseudo_tool"
    EXTERNAL_API_PROXY = "external_api_proxy"
    UNKNOWN_BOUNDARY = "unknown_boundary"


class A03ContractStatus(str, Enum):
    COMPLETE_CONTRACT = "complete_contract"
    PARTIAL_CONTRACT = "partial_contract"
    CONTRACT_INCOMPLETE = "contract_incomplete"
    CONTRACT_CONFLICTING = "contract_conflicting"
    OUTPUT_SCOPE_UNCERTAIN = "output_scope_uncertain"
    INPUT_SCOPE_UNCERTAIN = "input_scope_uncertain"
    NO_CLEAN_TOOL_CONTRACT_CLAIM = "no_clean_tool_contract_claim"


class A03AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    BLOCKED_BY_CONTEXT = "blocked_by_context"
    BLOCKED_BY_RESOURCE = "blocked_by_resource"
    BLOCKED_BY_MISSING_OBSERVATION = "blocked_by_missing_observation"
    INVALID_UNDER_CURRENT_MODE = "invalid_under_current_mode"
    AVAILABLE_BUT_UNVERIFIED = "available_but_unverified"
    CONTESTED_AVAILABILITY = "contested_availability"


class A03RejectionReason(str, Enum):
    MODE_NOT_TOOL = "mode_not_tool"
    HELPER_NOT_AFFORDANCE = "helper_not_affordance"
    STORED_CONTENT_NOT_TOOL = "stored_content_not_tool"
    NARRATIVE_SLOGAN_WITHOUT_CONTRACT = "narrative_slogan_without_contract"
    OVERBROAD_GENERIC_OPERATION = "overbroad_generic_operation"
    IMPLEMENTATION_PLUMBING = "implementation_plumbing"
    MISSING_INPUTS = "missing_inputs"
    MISSING_OUTPUTS = "missing_outputs"
    NO_OBSERVATION_HOOK = "no_observation_hook"
    NO_FAILURE_SIGNATURE = "no_failure_signature"
    NO_REUSABLE_OPERATION = "no_reusable_operation"


class A03NormalizationDecisionType(str, Enum):
    CANONICALIZED = "canonicalized"
    MERGED_AS_ALIAS = "merged_as_alias"
    SPLIT_BY_CONTRACT = "split_by_contract"
    SPLIT_BY_OUTPUT_SCOPE = "split_by_output_scope"
    RETAINED_CONTEXT_BOUND = "retained_context_bound"
    REJECTED_AS_NON_TOOL = "rejected_as_non_tool"
    CONTESTED_PENDING_CONTRACT = "contested_pending_contract"
    DECOMPOSED_FROM_OVERBROAD_GENERIC_OPERATION = (
        "decomposed_from_overbroad_generic_operation"
    )
    NO_CLEAN_CANONICALIZATION_CLAIM = "no_clean_canonicalization_claim"


class A03CapabilityGapLinkageKind(str, Enum):
    MISSING_INTERNAL_TOOL = "missing_internal_tool"
    BLOCKED_INTERNAL_TOOL = "blocked_internal_tool"
    DEGRADED_INTERNAL_TOOL = "degraded_internal_tool"
    CONTRACT_INCOMPLETE_TOOL = "contract_incomplete_tool"
    MISSING_WORLD_ACTION_NOT_TOOL = "missing_world_action_not_tool"
    NO_TOOL_GAP_CLAIM = "no_tool_gap_claim"
    GAP_LINKAGE_UNCERTAIN = "gap_linkage_uncertain"


class A03DownstreamReadinessStatus(str, Enum):
    READY = "ready"
    MISSING_CONTRACT_CONSUMER = "missing_contract_consumer"
    MISSING_TOOL_ID_CONSUMER = "missing_tool_id_consumer"
    LEGACY_DIRECT_CALL_DETECTED = "legacy_direct_call_detected"
    NO_SAFE_DOWNSTREAM_TOOL_CLAIM = "no_safe_downstream_tool_claim"


@dataclass(frozen=True, slots=True)
class A03ToolInputSpec:
    type_name: str
    required: bool = True
    shape_hint: str = ""


@dataclass(frozen=True, slots=True)
class A03ToolOutputSpec:
    type_name: str
    guaranteed: bool = False
    scope_hint: str = ""


@dataclass(frozen=True, slots=True)
class A03ObservationHook:
    hook_id: str
    signal_ref: str
    verification_required: bool


@dataclass(frozen=True, slots=True)
class A03ToolCostProfile:
    latency_class: str
    cost_band: str


@dataclass(frozen=True, slots=True)
class A03ToolSideEffectProfile:
    side_effect_refs: tuple[str, ...]
    risk_band: str


@dataclass(frozen=True, slots=True)
class A03ToolFailureSignature:
    signature_id: str
    failure_mode: str
    detectable: bool


@dataclass(frozen=True, slots=True)
class A03ToolAvailabilityProfile:
    status: A03AvailabilityStatus
    basis_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A03OperationSourceProfile:
    source_module: str
    source_surface: str
    provenance_refs: tuple[str, ...]
    source_lineage: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A03InvocationContract:
    accepted_input_types: tuple[A03ToolInputSpec, ...]
    produced_output_types: tuple[A03ToolOutputSpec, ...]
    required_context: tuple[str, ...]
    preconditions: tuple[str, ...]
    abort_conditions: tuple[str, ...]
    completion_criteria: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A03InternalOperationCandidate:
    operation_ref: str
    local_label: str
    tool_class: A03ToolClass
    source_profile: A03OperationSourceProfile
    boundary_kind: A03OperationBoundaryKind
    invocation_contract: A03InvocationContract
    observation_hooks: tuple[A03ObservationHook, ...]
    failure_signatures: tuple[A03ToolFailureSignature, ...]
    cost_profile: A03ToolCostProfile
    side_effect_profile: A03ToolSideEffectProfile
    controllability_hint: float
    reliability_hint: float
    reuse_scope: str
    required_context: tuple[str, ...] = ()
    canonical_tool_id_hint: str | None = None
    validity_hint: str = "valid"
    legacy_module_only: bool = False


@dataclass(frozen=True, slots=True)
class A03InternalOperationCandidateSet:
    candidate_set_id: str
    candidates: tuple[A03InternalOperationCandidate, ...]
    source_lineage: tuple[str, ...] = ()
    active_mode: str = "continue_stream"
    resource_pressure: bool = False
    available_observation_channels: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class A03CanonicalToolAffordance:
    tool_affordance_id: str
    canonical_label: str
    tool_class: A03ToolClass
    invocation_contract: A03InvocationContract
    observation_hooks: tuple[A03ObservationHook, ...]
    failure_signatures: tuple[A03ToolFailureSignature, ...]
    cost_profile: A03ToolCostProfile
    side_effect_profile: A03ToolSideEffectProfile
    availability_profile: A03ToolAvailabilityProfile
    contract_status: A03ContractStatus
    provenance_refs: tuple[str, ...]
    canonical_source_operation_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A03CanonicalToolRegistry:
    registry_id: str
    canonical_tools: tuple[A03CanonicalToolAffordance, ...]
    aliases: tuple["A03ToolAliasRecord", ...]
    composition_roles: tuple["A03ToolCompositionRole", ...]


@dataclass(frozen=True, slots=True)
class A03ToolAliasRecord:
    alias_id: str
    canonical_tool_id: str
    alias_label: str
    source_operation_ref: str


@dataclass(frozen=True, slots=True)
class A03ToolCompositionRole:
    role_id: str
    tool_affordance_id: str
    role_kind: str


@dataclass(frozen=True, slots=True)
class A03ToolNormalizationDecision:
    decision_id: str
    decision_type: A03NormalizationDecisionType
    source_operation_refs: tuple[str, ...]
    produced_tool_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A03RejectedInternalOperation:
    operation_ref: str
    local_label: str
    rejection_reason: A03RejectionReason
    reason: str


@dataclass(frozen=True, slots=True)
class A03ContestedToolRecord:
    contested_id: str
    operation_refs: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A03ToolBoundaryConflict:
    conflict_id: str
    operation_ref: str
    conflicting_boundary: A03OperationBoundaryKind
    reason: str


@dataclass(frozen=True, slots=True)
class A03MissingInternalToolRecord:
    demand_id: str
    required_tool_class: A03ToolClass
    reason: str


@dataclass(frozen=True, slots=True)
class A03BlockedInternalToolRecord:
    demand_id: str
    blocking_reason: str
    related_tool_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A03ToolInsufficiencyRecord:
    demand_id: str
    insufficiency_kind: str
    residual_scope: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A03CapabilityGapToolLinkage:
    linkage_kind: A03CapabilityGapLinkageKind
    missing_internal_tools: tuple[A03MissingInternalToolRecord, ...]
    blocked_internal_tools: tuple[A03BlockedInternalToolRecord, ...]
    tool_insufficiency: tuple[A03ToolInsufficiencyRecord, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A03ToolCleanupLedger:
    ledger_id: str
    normalization_decisions: tuple[A03ToolNormalizationDecision, ...]
    rejected_operations: tuple[A03RejectedInternalOperation, ...]
    contested_records: tuple[A03ContestedToolRecord, ...]
    boundary_conflicts: tuple[A03ToolBoundaryConflict, ...]
    canonical_tool_count: int
    rejected_operation_count: int
    contested_tool_count: int
    contract_incomplete_count: int
    degraded_tool_count: int
    blocked_tool_count: int
    missing_internal_tool_gap_count: int
    blocked_internal_tool_gap_count: int
    overbroad_generic_operation_rejected: bool
    legacy_direct_call_detected: bool
    canonical_tool_id_hint_used_count: int
    canonical_tool_id_generated_count: int
    canonical_tool_id_coverage_complete: bool
    source_lineage_count: int
    source_lineage_complete: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A03InternalToolGateDecision:
    internal_tool_consumer_ready: bool
    tool_contract_consumer_ready: bool
    tool_gap_linkage_consumer_ready: bool
    no_legacy_direct_call_consumer_ready: bool
    downstream_readiness_status: A03DownstreamReadinessStatus
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A03ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    internal_tool_ontology_not_executor: bool
    depends_on_a01_canonical_ontology: bool
    depends_on_a02_gap_packets: bool
    no_map_wide_claim: bool
    no_tool_invention_claim: bool
    no_truth_or_correctness_guarantee_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A03Telemetry:
    canonical_tool_count: int
    rejected_operation_count: int
    contested_tool_count: int
    contract_incomplete_count: int
    degraded_tool_count: int
    blocked_tool_count: int
    missing_internal_tool_gap_count: int
    blocked_internal_tool_gap_count: int
    overbroad_generic_operation_rejected: bool
    legacy_direct_call_detected: bool
    canonical_tool_id_coverage_complete: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class A03InternalToolAffordanceResult:
    candidate_set_id: str
    canonical_registry: A03CanonicalToolRegistry
    cleanup_ledger: A03ToolCleanupLedger
    gap_linkage: A03CapabilityGapToolLinkage
    gate: A03InternalToolGateDecision
    scope_marker: A03ScopeMarker
    telemetry: A03Telemetry
    reason: str

