from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .models import TransferOutcome


class AffordanceProvenanceMode(str, Enum):
    REAL_SUBJECT_TICK_SURFACE = "real_subject_tick_surface"
    HARNESS_COMPATIBLE_PROJECTION = "harness_compatible_projection"
    EXTERNAL_WORLD_ACTUATOR = "external_world_actuator"
    EVALUATION_ONLY = "evaluation_only"


class AffordanceSelectionStatus(str, Enum):
    SELECTED_FOR_INVOCATION_REQUEST = "selected_for_invocation_request"
    NOT_SELECTED_INSUFFICIENT_INFORMATION = "not_selected_insufficient_information"
    NOT_SELECTED_BLOCKED = "not_selected_blocked"
    NOT_SELECTED_CONTESTED = "not_selected_contested"
    NOT_SELECTED_NO_OFFER_CANDIDATE = "not_selected_no_offer_candidate"
    NOT_SELECTED_NO_RELEVANT_AFFORDANCE = "not_selected_no_relevant_affordance"


class ResponsibilityVerdict(str, Enum):
    READY_FOR_BOUNDED_AFFORDANCE_REQUEST = "ready_for_bounded_affordance_request"
    CANDIDATE_ONLY_NO_REQUEST = "candidate_only_no_request"
    BLOCKED_OR_REVALIDATE = "blocked_or_revalidate"
    TRACE_INCOMPLETE = "trace_incomplete"


@dataclass(frozen=True, slots=True)
class AffordanceSelectionRecord:
    selection_id: str
    response_candidate_ref: str | None
    selected_affordance_id: str | None
    selected_affordance_kind: str | None
    selected_affordance_source: str
    selected_affordance_status: str
    why_this_affordance: tuple[str, ...]
    rejected_alternatives: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    missing_preconditions: tuple[str, ...]
    permission_status: str
    selection_status: AffordanceSelectionStatus
    source_phase_refs: tuple[str, ...]
    provenance_mode: AffordanceProvenanceMode


@dataclass(frozen=True, slots=True)
class AffordanceUseRequest:
    request_id: str
    selected_affordance_ref: str | None
    give_resource: str | None
    requested_or_expected_receive_resource: str | None
    target_counterpart_ref: str
    intended_effect: str
    required_permissions: tuple[str, ...]
    prohibited_interpretations: tuple[str, ...]
    execution_requested: bool
    request_valid: bool
    execution_prohibited_until_world_actuator: bool
    may_be_sent_to_world_actuator: bool
    must_not_execute_inside_subject: bool
    source_phase_refs: tuple[str, ...]
    claim_boundary: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.execution_prohibited_until_world_actuator:
            raise ValueError("affordance use request must remain non-executing inside subject")
        if not self.must_not_execute_inside_subject:
            raise ValueError("affordance use request cannot execute inside subject")
        if self.may_be_sent_to_world_actuator and self.selected_affordance_ref is None:
            raise ValueError("request sent to world actuator requires selected affordance reference")


@dataclass(frozen=True, slots=True)
class WorldActuatorEnvelope:
    actuator_id: str
    actuator_kind: str
    invocation_request_ref: str | None
    explicit_execution_flag: bool
    invocation_id: str | None
    precondition_check_result: str
    invoked: bool
    invocation_reason: tuple[str, ...]
    blocked_reason: tuple[str, ...]
    attempt_id: str | None
    observed_result_ref: str | None
    actuator_authority: str
    subject_motor_control_claim: str

    def __post_init__(self) -> None:
        if self.subject_motor_control_claim not in {"not_claimed", "false"}:
            raise ValueError("world actuator envelope cannot claim subject motor control")
        if self.invoked and not self.explicit_execution_flag:
            raise ValueError("world actuator invocation requires explicit execution flag")


@dataclass(frozen=True, slots=True)
class AffordanceEpisodeResponsibilityRecord:
    episode_id: str
    offer_candidate_ref: str | None
    selection_ref: str
    invocation_request_ref: str | None
    actuator_envelope_ref: str
    observed_result_ref: str | None
    causing_invocation_id: str | None
    causing_attempt_id: str | None
    verification_status: str
    completion_claim: bool
    completion_basis: tuple[str, ...]
    completion_basis_chain_verified: bool
    completion_basis_missing: tuple[str, ...]
    completion_authority: str
    used_transfer_result_as_sole_authority: bool
    used_eval_only_for_completion: bool
    used_hidden_truth_for_completion: bool
    used_scenario_label_for_completion: bool
    used_w06_correction_execution_for_completion: bool
    residue_status: str
    failed_or_blocked_reason: tuple[str, ...]
    passive_packet_refs: tuple[str, ...]
    causal_post_invocation_refs: tuple[str, ...]
    claim_boundary: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.completion_claim and self.verification_status != "verified":
            raise ValueError("completion claim requires verified episode")


@dataclass(frozen=True, slots=True)
class ModuleResponsibilityLedger:
    W01_responsibility: str
    W02_responsibility: str
    W03_responsibility: str
    W04_responsibility: str
    W05_responsibility: str
    W06_responsibility: str
    A02_gap_responsibility: str
    A04_affordance_binding_responsibility: str
    P02_episode_responsibility: str
    V_communication_responsibility: str
    world_actuator_responsibility: str
    out_of_scope_modules: tuple[str, ...]
    unresolved_gaps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AffordanceResponsibilityTrace:
    trace_id: str
    scenario_id: str
    stage4_run_id: str
    execution_level: str
    subject_tick_used: bool
    phase_coverage_verified: bool
    phase_coverage_evidence: tuple[str, ...]
    phase_evidence_source_run_id: str
    stage4_phase_coverage_evidence: tuple[str, ...]
    responsibility_verdict: ResponsibilityVerdict
    claim_boundary: tuple[str, ...]
    evidence_visibility_boundary: tuple[str, ...]
    selection_record: AffordanceSelectionRecord
    affordance_use_request: AffordanceUseRequest
    world_actuator_envelope: WorldActuatorEnvelope
    episode_record: AffordanceEpisodeResponsibilityRecord
    module_responsibility_ledger: ModuleResponsibilityLedger
    transfer_result: TransferOutcome
    visible_packets: tuple[dict[str, object], ...]
    passive_response_records: tuple[dict[str, object], ...]
    causal_response_records: tuple[dict[str, object], ...]
    records: tuple[dict[str, object], ...]
    falsifier_summary: tuple[dict[str, object], ...] = ()
    eval_only: dict[str, object] | None = None


def affordance_trace_to_dict(
    trace: AffordanceResponsibilityTrace,
    *,
    include_eval_only: bool = False,
    include_affordance_records: bool = True,
    include_affordance_ledger: bool = False,
) -> dict[str, object]:
    payload = {
        "trace_id": trace.trace_id,
        "scenario_id": trace.scenario_id,
        "stage": "stage5_affordance_responsibility_trace",
        "stage4_run_id": trace.stage4_run_id,
        "execution_level": trace.execution_level,
        "subject_tick_used": trace.subject_tick_used,
        "phase_coverage_verified": trace.phase_coverage_verified,
        "phase_coverage_evidence": list(trace.phase_coverage_evidence),
        "phase_evidence_source_run_id": trace.phase_evidence_source_run_id,
        "stage4_phase_coverage_evidence": list(trace.stage4_phase_coverage_evidence),
        "responsibility_verdict": trace.responsibility_verdict.value,
        "claim_boundary": list(trace.claim_boundary),
        "evidence_visibility_boundary": list(trace.evidence_visibility_boundary),
        "falsifier_summary": list(trace.falsifier_summary),
        "transfer_result": trace.transfer_result.value,
        "visible_packets": list(trace.visible_packets),
        "passive_response_records": list(trace.passive_response_records),
        "causal_response_records": list(trace.causal_response_records),
    }
    if include_affordance_records:
        payload["selection_record"] = asdict(trace.selection_record)
        payload["affordance_use_request"] = asdict(trace.affordance_use_request)
        payload["world_actuator_envelope"] = asdict(trace.world_actuator_envelope)
        payload["episode_record"] = asdict(trace.episode_record)
        payload["records"] = list(trace.records)
    if include_affordance_ledger:
        payload["module_responsibility_ledger"] = asdict(trace.module_responsibility_ledger)
    if include_eval_only and trace.eval_only is not None:
        payload["eval_only"] = trace.eval_only
    return payload
