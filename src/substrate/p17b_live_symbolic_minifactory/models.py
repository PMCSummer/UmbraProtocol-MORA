from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class P17BRunStatus(str, Enum):
    COMPLETED_BOUNDED_FIXTURE = "completed_bounded_fixture"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    NOOP = "noop"
    HALTED = "halted"
    MAX_TICK_REACHED = "max_tick_reached"


class P17BStepStatus(str, Enum):
    PROPOSED = "proposed"
    CANDIDATE_READY = "candidate_ready"
    AP01_REQUESTED = "ap01_requested"
    EXECUTED = "executed"
    EFFECT_OBSERVED = "effect_observed"
    INTERMEDIATE_VERIFIED = "intermediate_verified"
    BLOCKED = "blocked"
    FAILED = "failed"
    UNRESOLVED = "unresolved"
    RESIDUE_OPEN = "residue_open"
    SKIPPED = "skipped"


class P17BStepKind(str, Enum):
    INSPECT_RESOURCE = "inspect_resource"
    GATHER_RESOURCE = "gather_resource"
    MOVE_OR_REACH = "move_or_reach"
    USE_STATION = "use_station"
    TRANSFORM_RESOURCE = "transform_resource"
    STORE_INTERMEDIATE = "store_intermediate"
    VERIFY_INTERMEDIATE = "verify_intermediate"
    WAIT = "wait"
    SCAN = "scan"
    REPAIR_CHECK = "repair_check"


class P17BBlockedReason(str, Enum):
    MISSING_PUBLIC_NEED = "missing_public_need"
    MISSING_WORLD0_LINEAGE = "missing_world0_lineage"
    MISSING_PUBLIC_RESOURCE = "missing_public_resource"
    MISSING_STATION_AFFORDANCE = "missing_station_affordance"
    MISSING_MICRO_OPERATION_BASIS = "missing_micro_operation_basis"
    MISSING_AP01_REQUEST = "missing_ap01_request"
    INVALID_AP01_LINEAGE = "invalid_ap01_lineage"
    EXECUTION_WITHOUT_AP01 = "execution_without_ap01"
    MISSING_WORLD_EFFECT = "missing_world_effect"
    EXPECTED_EFFECT_NOT_OBSERVED = "expected_effect_not_observed"
    UNVERIFIED_INTERMEDIATE = "unverified_intermediate"
    DOWNSTREAM_WITHOUT_VERIFIED_INTERMEDIATE = "downstream_without_verified_intermediate"
    FAILED_STEP_RESIDUE_OPEN = "failed_step_residue_open"
    RESIDUE_NOT_PRESERVED = "residue_not_preserved"
    HIDDEN_RECIPE_DETECTED = "hidden_recipe_detected"
    BACKEND_WORLDSTATE_DETECTED = "backend_worldstate_detected"
    SCENARIO_LABEL_DETECTED = "scenario_label_detected"
    CONTACTSPEC_FACTORY_SCRIPT_DETECTED = "contactspec_factory_script_detected"
    ADAPTER_SOLUTION_SEQUENCE_DETECTED = "adapter_solution_sequence_detected"
    COST_WINNER_AS_PERMISSION_DETECTED = "cost_winner_as_permission_detected"
    PROVIDER_HINT_AS_TRUTH_DETECTED = "provider_hint_as_truth_detected"
    RECIPE_CANDIDATE_AS_SKILL_DETECTED = "recipe_candidate_as_skill_detected"
    P17_PROOF_AS_LIVE_EXECUTION_DETECTED = "p17_proof_as_live_execution_detected"
    TRACE_OMITS_FAILED_STEP = "trace_omits_failed_step"
    COUNTERS_MISMATCH = "counters_mismatch"
    COMPLETION_WITHOUT_TRACE = "completion_without_trace"
    NOOP_OR_BLOCKED_CLAIMED_COMPLETED = "noop_or_blocked_claimed_completed"


class P17BResourceState(str, Enum):
    ABSENT = "absent"
    PUBLIC_CANDIDATE = "public_candidate"
    AVAILABLE_PUBLIC = "available_public"
    CONSUMED = "consumed"
    PRODUCED_CANDIDATE = "produced_candidate"
    PRODUCED_VERIFIED = "produced_verified"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class P17BAuthorityFlags:
    can_select_action: bool = False
    can_create_ap01: bool = False
    can_execute_without_world0: bool = False
    can_execute_without_ap01: bool = False
    can_use_hidden_recipe: bool = False
    can_use_backend_worldstate: bool = False
    can_use_scenario_label: bool = False
    can_treat_provider_hint_as_truth: bool = False
    can_treat_cost_winner_as_permission: bool = False
    can_mature_recipe: bool = False
    can_mature_skill: bool = False
    can_claim_automation: bool = False
    can_claim_general_autonomy: bool = False


@dataclass(frozen=True, slots=True)
class P17BFactoryNeed:
    need_id: str
    target_ref: str
    pressure_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    urgency: str | None = None
    public_basis_refs: tuple[str, ...] = ()
    hidden_goal_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class P17BFactoryStepSpec:
    step_id: str
    step_kind: P17BStepKind
    required_input_refs: tuple[str, ...]
    required_station_refs: tuple[str, ...]
    expected_output_refs: tuple[str, ...]
    required_micro_operation_kinds: tuple[str, ...]
    allowed_action_surface_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    no_hidden_recipe: bool = True
    no_selected_action: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class P17BFactoryStepTrace:
    step_id: str
    cycle_refs: tuple[str, ...]
    world0_run_ref: str | None
    micro_operation_refs: tuple[str, ...]
    cost_comparison_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    backend_execution_refs: tuple[str, ...]
    world_effect_feedback_refs: tuple[str, ...]
    observed_effect_refs: tuple[str, ...]
    expected_effect_refs: tuple[str, ...]
    verified_intermediate_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    blocked_reasons: tuple[P17BBlockedReason, ...]
    status: P17BStepStatus
    downstream_unlocked: bool = False
    effect_verified: bool = False
    no_action_selected_by_p17b: bool = True
    no_ap01_created_by_p17b: bool = True


@dataclass(frozen=True, slots=True)
class P17BIntermediateVerification:
    verification_id: str
    intermediate_ref: str
    required_effect_refs: tuple[str, ...]
    observed_effect_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    correlation_refs: tuple[str, ...]
    verified: bool
    partial: bool
    blocked: bool
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    verification_basis: tuple[str, ...]
    no_backend_truth: bool = True


@dataclass(frozen=True, slots=True)
class P17BChainAdvanceDecision:
    decision_id: str
    current_step_ref: str
    next_step_ref: str | None
    advance_allowed: bool
    required_verified_intermediate_refs: tuple[str, ...]
    missing_intermediate_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    blocked_reasons: tuple[P17BBlockedReason, ...]
    source_refs: tuple[str, ...]
    no_hidden_plan: bool = True


@dataclass(frozen=True, slots=True)
class P17BResidueStopFrame:
    stop_id: str
    failed_step_ref: str
    residue_refs: tuple[str, ...]
    unresolved_refs: tuple[str, ...]
    blocked_downstream_step_refs: tuple[str, ...]
    next_pressure_refs: tuple[str, ...]
    stop_reason: P17BBlockedReason
    continuation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class P17BCounters:
    step_count: int = 0
    completed_step_count: int = 0
    blocked_step_count: int = 0
    failed_step_count: int = 0
    verified_intermediate_count: int = 0
    unverified_intermediate_count: int = 0
    ap01_request_count: int = 0
    world0_cycle_count: int = 0
    backend_execution_count: int = 0
    residue_count: int = 0
    chain_advance_count: int = 0
    chain_block_count: int = 0
    shortcut_block_count: int = 0
    hidden_recipe_block_count: int = 0
    adapter_script_block_count: int = 0
    cost_permission_block_count: int = 0
    provider_truth_block_count: int = 0


@dataclass(frozen=True, slots=True)
class P17BLiveMiniFactoryRun:
    run_id: str
    need: P17BFactoryNeed
    step_specs: tuple[P17BFactoryStepSpec, ...]
    step_traces: tuple[P17BFactoryStepTrace, ...]
    verification_records: tuple[P17BIntermediateVerification, ...]
    advance_decisions: tuple[P17BChainAdvanceDecision, ...]
    residue_stop_frames: tuple[P17BResidueStopFrame, ...]
    world0_run_refs: tuple[str, ...]
    final_target_refs: tuple[str, ...]
    final_status: P17BRunStatus
    counters: P17BCounters
    replay_trace_ref: str | None
    source_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    blocked_reasons: tuple[P17BBlockedReason, ...]
    no_factory_script: bool = True
    no_hidden_recipe: bool = True
    no_general_automation_claim: bool = True
    no_mature_skill_claim: bool = True
    no_general_autonomy_claim: bool = True
    authority_flags: P17BAuthorityFlags = field(default_factory=P17BAuthorityFlags)


@dataclass(frozen=True, slots=True)
class P17BStepInput:
    step_spec: P17BFactoryStepSpec
    cycle_refs: tuple[str, ...] = ()
    world0_run_ref: str | None = None
    micro_operation_refs: tuple[str, ...] = ()
    cost_comparison_refs: tuple[str, ...] = ()
    ap01_request_refs: tuple[str, ...] = ()
    backend_execution_refs: tuple[str, ...] = ()
    world_effect_feedback_refs: tuple[str, ...] = ()
    observed_effect_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    provider_hint_refs: tuple[str, ...] = ()
    metadata_refs: tuple[str, ...] = ()
