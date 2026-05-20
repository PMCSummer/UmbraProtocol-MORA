from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from substrate.ap01_subject_action_publication import (
    AP01SubjectActionPublicationResult,
    AP01SubjectActionRequestPacket,
)
from substrate.contact_projection_gate import ProjectedSubjectTickInputs
from substrate.subject_tick import SubjectTickInput, SubjectTickResult
from substrate.umwelt0_phenomenal_contact import ContactAuthorityFlags, ContactConformanceResult
from substrate.umwelts_symbolic_contact import ContactSpec


class WorldRunnerCycleStatus(str, Enum):
    COMPLETED = "completed"
    NOOP = "noop"
    BLOCKED = "blocked"
    PARTIAL = "partial"
    FAILED = "failed"
    HALTED = "halted"
    TIMEOUT = "timeout"


class WorldRunnerExecutionStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    SKIPPED_NO_AP01 = "skipped_no_ap01"
    EXECUTED_FROM_AP01 = "executed_from_ap01"
    BLOCKED = "blocked"
    FAILED = "failed"
    PASSIVE_EVENT_ONLY = "passive_event_only"


class WorldRunnerBlockReason(str, Enum):
    MISSING_ADAPTER_SPEC = "missing_adapter_spec"
    INVALID_CONTACT_SPEC = "invalid_contact_spec"
    CONTACT_BLOCKED = "contact_blocked"
    PROJECTION_BLOCKED = "projection_blocked"
    SUBJECT_TICK_FAILED = "subject_tick_failed"
    NO_AP01_REQUEST = "no_ap01_request"
    RUNNER_AP01_CREATION_ATTEMPT = "runner_ap01_creation_attempt"
    ADAPTER_ACTION_SELECTION_ATTEMPT = "adapter_action_selection_attempt"
    BACKEND_WORLDSTATE_DETECTED = "backend_worldstate_detected"
    SCENARIO_LABEL_DECISION_DETECTED = "scenario_label_decision_detected"
    CONTACT_SPEC_PLAN_DETECTED = "contact_spec_plan_detected"
    EXECUTION_WITHOUT_AP01 = "execution_without_ap01"
    EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER = "effect_without_request_or_passive_marker"
    RESIDUE_MISSING_AFTER_FAILURE = "residue_missing_after_failure"
    MAX_TICKS_REACHED = "max_ticks_reached"
    TIMEOUT_REACHED = "timeout_reached"
    FACTORY_SOLUTION_DETECTED = "factory_solution_detected"
    BACKEND_SPECIFIC_SUBJECT_LOGIC_DETECTED = "backend_specific_subject_logic_detected"


class WorldAdapterCapability(str, Enum):
    OBSERVE = "observe"
    EXECUTE_AP01_ENVELOPE = "execute_ap01_envelope"
    PRODUCE_EFFECT_DELTA = "produce_effect_delta"
    PASSIVE_EVENTS = "passive_events"
    PUBLIC_STATUS = "public_status"
    PUBLIC_INVENTORY = "public_inventory"
    PUBLIC_MAP = "public_map"
    PUBLIC_ENTITIES = "public_entities"
    PUBLIC_STATIONS = "public_stations"
    PUBLIC_KNOWLEDGE = "public_knowledge"


@dataclass(frozen=True, slots=True)
class WorldRunnerAuthorityFlags:
    can_select_action: bool = False
    can_select_goal: bool = False
    can_rank_candidates: bool = False
    can_create_ap01_request: bool = False
    can_bypass_ap01: bool = False
    can_execute_without_ap01: bool = False
    can_claim_fact: bool = False
    can_confirm_cause: bool = False
    can_assign_value: bool = False
    can_mature_recipe: bool = False
    can_mature_skill: bool = False
    can_claim_automation: bool = False
    can_claim_autonomous_progression: bool = False
    can_expose_worldstate_to_subject: bool = False
    can_use_scenario_label: bool = False
    can_hardcode_factory_solution: bool = False


@dataclass(frozen=True, slots=True)
class WorldAdapterSpec:
    adapter_id: str
    backend_family: str
    capabilities: tuple[WorldAdapterCapability, ...]
    public_surface_refs: tuple[str, ...]
    contact_spec_ref: str
    source_refs: tuple[str, ...]
    allowed_action_kinds: tuple[str, ...]
    forbidden_payload_markers: tuple[str, ...] = ()
    exposes_worldstate_to_subject: bool = False
    adapter_can_select_action: bool = False
    adapter_can_select_goal: bool = False
    scenario_label_available: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorldObservationPacket:
    observation_id: str
    adapter_id: str
    cycle_id: str
    public_observation_refs: tuple[str, ...]
    public_effect_refs: tuple[str, ...]
    passive_public_event_refs: tuple[str, ...]
    action_surface_refs: tuple[str, ...]
    effect_surface_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    contact_spec_ref: str
    metadata: dict[str, str] = field(default_factory=dict)
    no_backend_worldstate: bool = True


@dataclass(frozen=True, slots=True)
class WorldRunnerConfig:
    max_ticks: int = 1
    timeout_seconds: float | None = None
    allow_noop_cycles: bool = True
    allow_passive_events: bool = True
    require_ap01_for_execution: bool = True
    trace_enabled: bool = True
    replay_enabled: bool = True
    fail_on_backend_worldstate: bool = True
    fail_on_scenario_label: bool = True


@dataclass(frozen=True, slots=True)
class WorldBackendExecutionRequest:
    execution_request_id: str
    cycle_id: str
    ap01_request_ref: str
    adapter_ref: str
    action_kind_ref: str | None
    source_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    created_by_runner: bool = False
    created_from_ap01: bool = True
    runner_selected_action: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorldBackendExecutionResult:
    backend_execution_ref: str
    execution_request_ref: str
    ap01_request_ref: str
    adapter_ref: str
    public_effect_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    failed: bool
    blocked: bool
    passive_event: bool
    source_refs: tuple[str, ...]
    metadata: dict[str, str] = field(default_factory=dict)
    no_truth_claim: bool = True
    no_cause_claim: bool = True


@dataclass(frozen=True, slots=True)
class WorldEffectFeedback:
    feedback_id: str
    cycle_id: str
    request_ref: str | None
    passive_event_ref: str | None
    backend_execution_ref: str | None
    public_effect_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    correlation_status: str
    effect_frame_ref: str | None = None
    no_fact_claim: bool = True
    no_cause_confirmed: bool = True


@dataclass(frozen=True, slots=True)
class WorldRunnerCycleTrace:
    cycle_id: str
    adapter_ref: str
    contact_spec_ref: str
    observation_packet_ref: str | None
    contact_frame_refs: tuple[str, ...]
    projection_refs: tuple[str, ...]
    subject_tick_ref: str | None
    ap01_request_refs: tuple[str, ...]
    backend_execution_refs: tuple[str, ...]
    world_effect_frame_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    blocked_reasons: tuple[WorldRunnerBlockReason, ...]
    cycle_status: WorldRunnerCycleStatus
    execution_status: WorldRunnerExecutionStatus
    no_runner_action_selection: bool = True
    no_runner_ap01_creation: bool = True
    no_backend_worldstate_to_subject: bool = True
    no_factory_solution: bool = True


@dataclass(frozen=True, slots=True)
class WorldRunnerCounters:
    cycle_count: int = 0
    noop_count: int = 0
    blocked_count: int = 0
    failed_count: int = 0
    completed_count: int = 0
    contact_blocked_count: int = 0
    projection_blocked_count: int = 0
    subject_tick_failed_count: int = 0
    ap01_request_count: int = 0
    backend_execution_count: int = 0
    skipped_no_ap01_count: int = 0
    passive_event_count: int = 0
    effect_frame_count: int = 0
    residue_count: int = 0
    uncertainty_count: int = 0
    backend_worldstate_block_count: int = 0
    scenario_label_block_count: int = 0
    adapter_action_selection_block_count: int = 0
    runner_ap01_creation_block_count: int = 0
    execution_without_ap01_block_count: int = 0
    contact_spec_plan_block_count: int = 0
    factory_solution_block_count: int = 0
    timeout_count: int = 0
    max_tick_stop_count: int = 0


@dataclass(frozen=True, slots=True)
class WorldRunnerCycleResult:
    cycle_trace: WorldRunnerCycleTrace
    cycle_status: WorldRunnerCycleStatus
    execution_status: WorldRunnerExecutionStatus
    contact_result: ContactConformanceResult | None
    projection_result: ProjectedSubjectTickInputs | None
    subject_tick_result: SubjectTickResult | None
    ap01_requests: tuple[AP01SubjectActionRequestPacket, ...]
    backend_requests: tuple[WorldBackendExecutionRequest, ...]
    backend_results: tuple[WorldBackendExecutionResult, ...]
    effect_feedback: tuple[WorldEffectFeedback, ...]
    blocked_reasons: tuple[WorldRunnerBlockReason, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    counters: WorldRunnerCounters
    authority_flags: WorldRunnerAuthorityFlags


@dataclass(frozen=True, slots=True)
class WorldRunnerLoopResult:
    run_id: str
    cycle_traces: tuple[WorldRunnerCycleTrace, ...]
    final_status: WorldRunnerCycleStatus
    counters: WorldRunnerCounters
    replay_trace_ref: str | None
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    blocked_reasons: tuple[WorldRunnerBlockReason, ...]
    no_action_selected_by_runner: bool = True
    no_ap01_created_by_runner: bool = True
    no_world_submission_without_ap01: bool = True
    fact_claimed: bool = False
    cause_confirmed: bool = False
    value_assigned: bool = False
    recipe_matured: bool = False
    skill_matured: bool = False
    automation_claimed: bool = False
    factory_solution_hardcoded: bool = False


@dataclass(frozen=True, slots=True)
class WorldRunnerCycleInput:
    cycle_id: str
    adapter_spec: WorldAdapterSpec
    observation_packet: WorldObservationPacket | None = None
    contact_spec: ContactSpec | None = None
    subject_tick_input: SubjectTickInput | None = None
    external_ap01_result: AP01SubjectActionPublicationResult | None = None
    external_ap01_requests: tuple[AP01SubjectActionRequestPacket, ...] = ()
    prior_world_effect_frames: tuple[str, ...] = ()
    metadata_refs: tuple[str, ...] = ()
    runner_created_ap01_refs: tuple[str, ...] = ()
    execution_without_ap01_attempt: bool = False
    skip_subject_tick: bool = False


@dataclass(frozen=True, slots=True)
class WorldRunnerLoopInput:
    run_id: str
    adapter_spec: WorldAdapterSpec
    cycle_inputs: tuple[WorldRunnerCycleInput, ...]
    config: WorldRunnerConfig = field(default_factory=WorldRunnerConfig)


class WorldAdapterRuntime(Protocol):
    adapter_id: str

    def observe(self, cycle_id: str) -> WorldObservationPacket: ...

    def execute_ap01_envelope(self, request: WorldBackendExecutionRequest) -> WorldBackendExecutionResult: ...


@dataclass(frozen=True, slots=True)
class WorldRunnerConformanceSummary:
    run_id: str
    final_status: WorldRunnerCycleStatus
    blocked_reasons: tuple[str, ...]
    counters: WorldRunnerCounters
    authority_flags: WorldRunnerAuthorityFlags
