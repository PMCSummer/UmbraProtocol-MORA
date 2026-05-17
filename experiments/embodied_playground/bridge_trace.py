from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BridgeVerdict(str, Enum):
    NO_CANDIDATE_NO_EXECUTION = "no_candidate_no_execution"
    REQUEST_PUBLISHED_AND_SUBMITTED = "request_published_and_submitted"
    REQUEST_BLOCKED_NO_EXECUTION = "request_blocked_no_execution"
    REQUEST_REVALIDATION_NO_EXECUTION = "request_revalidation_no_execution"
    UNSAFE_CANDIDATE_REJECTED = "unsafe_candidate_rejected"
    MULTIPLE_REQUESTS_REJECTED = "multiple_requests_rejected"
    WORLD_EFFECT_OBSERVED = "world_effect_observed"
    BRIDGE_ERROR = "bridge_error"


@dataclass(frozen=True, slots=True)
class SubjectWorldBridgeConfig:
    subject_id: str
    max_ticks: int
    execute_world_actions: bool
    include_eval_only: bool = False
    allow_manual_candidate_provider: bool = True
    reject_multiple_published_requests: bool = True
    claim_boundary: str = (
        "p3_bridge_orchestration_only_no_planning_no_world_claim_no_autonomous_selection"
    )


@dataclass(frozen=True, slots=True)
class BridgeTickRecord:
    bridge_tick_index: int
    world_tick_before: int
    observation_id: str
    observation_previous_effect_refs: tuple[str, ...]
    subject_tick_surface_payload: dict[str, object]
    action_space_frame_id: str
    subject_tick_used: bool
    subject_tick_result_ref: str | None
    ap01_candidate_count: int
    ap01_published_request_count: int
    ap01_blocked_count: int
    ap01_revalidation_required_count: int
    ap01_unsafe_basis_count: int
    ap01_request_ref: str | None
    envelope_created: bool
    envelope_ref: str | None
    envelope_payload: dict[str, object] | None
    world_submission_attempted: bool
    world_effect_id: str | None
    world_effect_status: str | None
    correlation_status: str | None
    world_effect_payload: dict[str, object] | None
    world_tick_after: int
    next_observation_id: str | None
    subject_tick_error: str | None = None
    hidden_eval_excluded: bool = True
    direct_phase_calls_detected: bool = False
    bridge_chose_action: bool = False
    manual_candidate_input: bool = False
    autonomous_action_selection: bool = False
    verdict: BridgeVerdict = BridgeVerdict.NO_CANDIDATE_NO_EXECUTION
    claim_boundary: str = (
        "bridge_tick_record_request_boundary_preserved_no_direct_phase_calls"
    )


@dataclass(frozen=True, slots=True)
class SubjectWorldBridgeRun:
    run_id: str
    scenario_id: str
    subject_id: str
    bridge_stage: str
    steps: tuple[BridgeTickRecord, ...]
    final_observation_id: str
    subject_tick_used_any: bool
    world_submissions_count: int
    world_effect_count: int
    no_candidate_no_execution_count: int
    rejected_multiple_requests_count: int
    hidden_eval_excluded: bool = True
    autonomous_action_selection: bool = False
    claim_boundary: str = (
        "p3_subject_world_bridge_orchestration_only_request_not_success"
    )
    eval_only: dict[str, object] | None = field(default=None)
