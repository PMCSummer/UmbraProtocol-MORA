from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class W05SignalChannel(str, Enum):
    DESIRED = "desired"
    PREDICTED = "predicted"
    OBSERVED = "observed"
    PERMITTED = "permitted"


class W05InjectionTarget(str, Enum):
    INTERPRETATION_INTERFACE = "interpretation_interface"
    POLICY_INTERFACE = "policy_interface"
    MEMORY_INTERFACE = "memory_interface"
    WORLD_MODEL_INTERFACE = "world_model_interface"
    ACTION_EFFECT_MODEL = "action_effect_model"
    AFFORDANCE_MODEL = "affordance_model"
    OWNERSHIP_MODEL = "ownership_model"
    GOAL_SATISFACTION_MODEL = "goal_satisfaction_model"
    VALIDITY_MODEL = "validity_model"
    PROTECTED_CONSTITUTIONAL_LAYER = "protected_constitutional_layer"


class W05MismatchClass(str, Enum):
    NO_MISMATCH = "no_mismatch"
    WORLD_MODEL = "world_model"
    ACTION_EFFECT = "action_effect"
    AFFORDANCE = "affordance"
    OWNERSHIP = "ownership"
    GOAL_SATISFACTION = "goal_satisfaction"
    VALIDITY = "validity"
    AUTHORITY_SCOPE = "authority_scope"
    TEMPORAL_SCOPE = "temporal_scope"
    CONSTITUTIONAL_BOUNDARY = "constitutional_boundary"
    DESIRED_VS_PREDICTED = "desired_vs_predicted"
    PREDICTED_VS_OBSERVED = "predicted_vs_observed"
    OBSERVED_VS_PERMITTED = "observed_vs_permitted"
    DESIRED_VS_PERMITTED = "desired_vs_permitted"
    PRIOR_VS_CURRENT_EVIDENCE = "prior_vs_current_evidence"
    AMBIGUOUS_MULTI_CLASS = "ambiguous_multi_class"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    MALFORMED_SIGNAL_STACK = "malformed_signal_stack"


class W05MismatchDirection(str, Enum):
    DESIRED_VS_PREDICTED = "desired_vs_predicted"
    PREDICTED_VS_OBSERVED = "predicted_vs_observed"
    OBSERVED_VS_PERMITTED = "observed_vs_permitted"
    DESIRED_VS_PERMITTED = "desired_vs_permitted"
    PRIOR_VS_CURRENT_EVIDENCE = "prior_vs_current_evidence"
    PREDICTED_VS_PERMITTED = "predicted_vs_permitted"
    DESIRED_VS_OBSERVED = "desired_vs_observed"


@dataclass(frozen=True, slots=True)
class W05DesiredSignal:
    signal_id: str
    desired_state_id: str
    requested_outcome: str
    actor_id: str
    perspective_id: str
    priority: str
    source_authority: str
    provenance: tuple[str, ...]
    allowed_relaxation_fields: tuple[str, ...]
    non_negotiable_constraints: tuple[str, ...]
    forbidden_update_targets: tuple[str, ...]
    malformed_markers: tuple[str, ...] = ()
    target_scope: tuple[str, ...] = ()
    confidence: float = 0.5
    precision: float = 0.5
    uncertainty_markers: tuple[str, ...] = ()
    prohibited_promotions: tuple[str, ...] = ("desired_not_evidence",)
    channel: W05SignalChannel = W05SignalChannel.DESIRED


@dataclass(frozen=True, slots=True)
class W05PredictedSignal:
    signal_id: str
    prediction_id: str
    prior_id: str
    expected_observation: str
    expected_action_effect: str
    expected_affordance: str
    expected_goal_satisfaction: str
    expected_validity_window: tuple[int, int] | None
    prior_strength: float
    prediction_confidence: float
    source_reliability: float
    source_authority: str
    provenance: tuple[str, ...]
    target_scope: tuple[str, ...] = ()
    confidence: float = 0.5
    precision: float = 0.5
    timestamp_or_sequence: int = 0
    uncertainty_markers: tuple[str, ...] = ()
    prohibited_promotions: tuple[str, ...] = ("predicted_utility_not_permission",)
    channel: W05SignalChannel = W05SignalChannel.PREDICTED


@dataclass(frozen=True, slots=True)
class W05ObservedSignal:
    signal_id: str
    observation_id: str
    observation_refs: tuple[str, ...]
    observed_outcome: str
    observed_action_effect: str
    observed_affordance: str
    evidence_precision: float
    source_reliability: float
    source_authority: str
    presence_mode: str
    timestamp_or_sequence: int
    contradiction_markers: tuple[str, ...]
    provenance: tuple[str, ...]
    target_scope: tuple[str, ...] = ()
    confidence: float = 0.5
    precision: float = 0.5
    uncertainty_markers: tuple[str, ...] = ()
    prohibited_promotions: tuple[str, ...] = ("observation_without_provenance_not_clean",)
    channel: W05SignalChannel = W05SignalChannel.OBSERVED


@dataclass(frozen=True, slots=True)
class W05PermittedSignal:
    signal_id: str
    permitted_signal_id: str
    w04_decision_ref: str
    permitted_status: str
    may_deploy_candidate: bool
    may_use_as_hint_only: bool
    may_use_after_revalidation: bool
    may_use_with_relaxation: bool
    must_abstain: bool
    must_block: bool
    must_revalidate: bool
    prohibited_uses: tuple[str, ...]
    protected_targets: tuple[W05InjectionTarget, ...]
    non_learnable_layer_flags: tuple[str, ...]
    allowed_update_targets: tuple[W05InjectionTarget, ...]
    prohibited_update_targets: tuple[W05InjectionTarget, ...]
    constitutional_guard_flags: tuple[str, ...]
    source_authority: str
    provenance: tuple[str, ...]
    target_scope: tuple[str, ...] = ()
    confidence: float = 1.0
    precision: float = 1.0
    timestamp_or_sequence: int = 0
    uncertainty_markers: tuple[str, ...] = ()
    prohibited_promotions: tuple[str, ...] = ("permission_not_execution",)
    channel: W05SignalChannel = W05SignalChannel.PERMITTED


@dataclass(frozen=True, slots=True)
class W05TypedSignalStackRecord:
    stack_id: str
    desired_signal: W05DesiredSignal
    predicted_signal: W05PredictedSignal
    observed_signal: W05ObservedSignal
    permitted_signal: W05PermittedSignal
    per_channel_provenance: tuple[tuple[W05SignalChannel, tuple[str, ...]], ...]
    per_channel_authority: tuple[tuple[W05SignalChannel, str], ...]
    per_channel_confidence: tuple[tuple[W05SignalChannel, float], ...]
    per_channel_precision: tuple[tuple[W05SignalChannel, float], ...]
    mismatch_readiness: bool
    channel_integrity_status: str
    missing_channel_markers: tuple[str, ...]
    collapsed_channel_guard: bool


@dataclass(frozen=True, slots=True)
class W05PriorGainControlConfig:
    prior_strength_policy: str
    evidence_precision_policy: str
    source_reliability_interaction_matrix: tuple[str, ...]
    suppress_conditions: tuple[str, ...]
    amplify_conditions: tuple[str, ...]
    maximum_gain: float
    minimum_gain: float
    high_precision_contradiction_threshold: float
    low_precision_noise_threshold: float
    protected_target_gain_cap: float
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W05PriorGainDecision:
    prior_strength: float
    evidence_precision: float
    source_reliability_score: float
    effective_gain: float
    gain_bounds: tuple[float, float]
    suppressed: bool
    amplified: bool
    unchanged: bool
    suppression_reason: str
    amplification_reason: str
    reason_codes: tuple[str, ...]
    residual_uncertainty: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W05PredictionUseRecord:
    prediction_use_id: str
    prior_id: str
    w04_decision_ref: str
    injection_target: W05InjectionTarget
    allowed_scope: tuple[str, ...]
    prior_strength: float
    effective_prior_gain: float
    evidence_precision: float
    source_reliability_interaction: str
    suppress_or_amplify_reason: str
    constitutional_guard_status: str
    permitted_boundary: str
    gain_bounds: tuple[float, float]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W05MismatchClassificationRecord:
    mismatch_id: str
    compared_channels: tuple[W05SignalChannel, ...]
    mismatch_class: W05MismatchClass
    mismatch_direction: W05MismatchDirection
    severity: str
    confidence: float
    evidence_refs: tuple[str, ...]
    ambiguity_markers: tuple[str, ...]
    competing_class_candidates: tuple[W05MismatchClass, ...]
    target_scope_candidate: W05InjectionTarget
    reason_codes: tuple[str, ...]
    execution_prohibited: bool


@dataclass(frozen=True, slots=True)
class W05UpdateRoutingPacket:
    routing_id: str
    mismatch_class: W05MismatchClass
    target_scope: tuple[str, ...]
    target_layer: W05InjectionTarget
    update_candidate_type: str
    severity: str
    confidence: float
    evidence_refs: tuple[str, ...]
    recommended_route: str
    required_revalidation: bool
    execution_prohibited: bool
    constitutional_guard_flags: tuple[str, ...]
    protected_target_blocked: bool
    permitted_channel_status: str
    downstream_must_not_execute_update: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W05ConstitutionalGuardCheck:
    protected_targets: tuple[W05InjectionTarget, ...]
    attempted_update_targets: tuple[W05InjectionTarget, ...]
    blocked_targets: tuple[W05InjectionTarget, ...]
    allowed_routing_targets: tuple[W05InjectionTarget, ...]
    non_learnable_layer_flags: tuple[str, ...]
    violation_reason: str
    guard_status: str
    escalation_required: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W05PermittedChannelEnforcementRecord:
    permitted_status: str
    prohibited_uses: tuple[str, ...]
    utility_not_permission: bool
    desired_not_permission: bool
    prediction_not_permission: bool
    blocked_by_w04: bool
    downstream_permission_delta: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W05RevalidationOrEscalationRequest:
    request_id: str
    target_scope: tuple[str, ...]
    required_upstream_layer: str
    missing_evidence: tuple[str, ...]
    ambiguous_mismatch_reason: str
    constitutional_concern: bool
    route_priority: str
    blocked_until_revalidated: bool


@dataclass(frozen=True, slots=True)
class W05DownstreamRoutingPermissionPacket:
    routing_id: str
    may_consider_update: bool
    may_request_learning: bool
    may_adjust_interpretation: bool
    may_adjust_policy_hint: bool
    must_revalidate: bool
    must_escalate: bool
    must_abstain: bool
    must_not_execute_update: bool
    must_preserve_desired_predicted_observed_permitted_separation: bool
    must_preserve_guardrails: bool
    protected_target_blocked: bool
    prohibited_uses: tuple[str, ...]
    preserved_guardrails: tuple[str, ...]
    execution_authorization_granted: bool


@dataclass(frozen=True, slots=True)
class W05Telemetry:
    signal_stack_count: int
    prediction_use_count: int
    prior_gain_suppressed_count: int
    prior_gain_amplified_count: int
    prior_gain_unchanged_count: int
    mismatch_count: int
    ambiguous_mismatch_count: int
    revalidate_route_count: int
    escalate_route_count: int
    abstain_count: int
    constitutional_guard_count: int
    protected_target_block_count: int
    must_not_execute_update_count: int
    permitted_channel_block_count: int
    channel_collapse_block_count: int
    consumer_ready: bool
    no_clean_routing: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class W05GateDecision:
    consumer_ready: bool
    no_clean_routing: bool
    must_not_execute_update_count: int
    revalidate_route_count: int
    escalate_route_count: int
    abstain_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W05ScopeMarker:
    scope: str
    prior_injection_only: bool
    no_w06_revision_claim: bool
    no_planner_claim: bool
    no_action_selector_claim: bool
    no_execution_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W05InputBundle:
    bundle_id: str
    source_lineage: tuple[str, ...]
    w04_decision_ref: str
    w03_prior_ref: str
    desired_signal: W05DesiredSignal | None
    predicted_signal: W05PredictedSignal | None
    observed_signal: W05ObservedSignal | None
    permitted_signal: W05PermittedSignal | None
    prior_gain_config: W05PriorGainControlConfig | None
    protected_target_registry: tuple[W05InjectionTarget, ...]
    reason: str = ""


@dataclass(frozen=True, slots=True)
class W05ResultBundle:
    bundle_id: str
    signal_stacks: tuple[W05TypedSignalStackRecord, ...]
    prediction_use_records: tuple[W05PredictionUseRecord, ...]
    prior_gain_decisions: tuple[W05PriorGainDecision, ...]
    mismatch_classifications: tuple[W05MismatchClassificationRecord, ...]
    update_routing_packets: tuple[W05UpdateRoutingPacket, ...]
    constitutional_guard_checks: tuple[W05ConstitutionalGuardCheck, ...]
    permitted_channel_enforcement_records: tuple[W05PermittedChannelEnforcementRecord, ...]
    revalidation_or_escalation_requests: tuple[W05RevalidationOrEscalationRequest, ...]
    downstream_routing_packets: tuple[W05DownstreamRoutingPermissionPacket, ...]
    telemetry: W05Telemetry
    gate: W05GateDecision
    scope_marker: W05ScopeMarker
    no_claim_markers: tuple[str, ...]
    reason: str
