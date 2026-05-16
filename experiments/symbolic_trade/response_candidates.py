from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class AResponseKind(str, Enum):
    OBSERVE_ONLY = "observe_only"
    ACKNOWLEDGE_PRESENCE = "acknowledge_presence"
    REQUEST_STATUS = "request_status"
    REQUEST_CLARIFICATION = "request_clarification"
    OFFER_CANDIDATE = "offer_candidate"
    TRANSFER_ATTEMPT_CANDIDATE = "transfer_attempt_candidate"
    ABSTAIN = "abstain"
    REVALIDATE_BEFORE_RESPONSE = "revalidate_before_response"
    BLOCK_DUE_CONSTRAINT = "block_due_constraint"
    NO_RESPONSE = "no_response"


class ResponseVerdict(str, Enum):
    NO_CANDIDATE = "no_candidate"
    OBSERVE_ONLY = "observe_only"
    CLARIFICATION_NEEDED = "clarification_needed"
    REVALIDATION_NEEDED = "revalidation_needed"
    BLOCKED = "blocked"
    BOUNDED_OFFER_CANDIDATE = "bounded_offer_candidate"
    BOUNDED_TRANSFER_ATTEMPT_CANDIDATE = "bounded_transfer_attempt_candidate"
    INVALID_SHORTCUT_DETECTED = "invalid_shortcut_detected"
    TRACE_INCOMPLETE = "trace_incomplete"


_FORBIDDEN_RESPONSE_KIND_TERMS = (
    "trade_intent",
    "should_trade",
    "mutual_benefit_detected",
    "economic_agency",
    "deal",
    "barter",
    "contract",
    "wants_trade",
)


@dataclass(frozen=True, slots=True)
class AResponseCandidate:
    response_id: str
    scenario_name: str
    source_step_id: str
    source_step_ids: tuple[str, ...]
    response_kind: AResponseKind
    target_ref: str | None
    object_ref: str | None
    requested_effect: str
    confidence: float
    permitted_status: str
    evidence_refs: tuple[str, ...]
    phase_evidence_refs: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    reason_codes: tuple[str, ...]
    boundary_markers: tuple[str, ...]
    execution_prohibited: bool
    claim_boundary: tuple[str, ...]
    hidden_truth_used: bool
    eval_only_used: bool
    trade_shortcut_used: bool
    derived_from_real_subject_tick: bool
    extraction_method: str
    source_phase_coverage: tuple[str, ...]
    residual_uncertainty_refs: tuple[str, ...]
    response_basis_summary: tuple[str, ...]
    forbidden_basis_markers: tuple[str, ...]
    transfer_executed: bool = False
    action_executed: bool = False
    correction_executed: bool = False

    def __post_init__(self) -> None:
        if any(token in self.response_kind.value for token in _FORBIDDEN_RESPONSE_KIND_TERMS):
            raise ValueError(f"Forbidden response kind: {self.response_kind.value}")
        if self.response_kind in {AResponseKind.OFFER_CANDIDATE, AResponseKind.TRANSFER_ATTEMPT_CANDIDATE}:
            if not self.claim_boundary:
                raise ValueError("offer/transfer candidates require explicit claim_boundary")
            if not self.execution_prohibited:
                raise ValueError("offer/transfer candidates must keep execution_prohibited=true")
            if self.hidden_truth_used:
                raise ValueError("offer/transfer candidates cannot use hidden truth")
            if self.eval_only_used:
                raise ValueError("offer/transfer candidates cannot use eval-only data")
            if self.trade_shortcut_used:
                raise ValueError("offer/transfer candidates cannot use trade shortcut markers")
            if self.transfer_executed or self.action_executed or self.correction_executed:
                raise ValueError("offer/transfer candidates cannot be marked as executed")
            if not self.evidence_refs:
                raise ValueError("offer/transfer candidates require non-empty evidence_refs")
            if not self.phase_evidence_refs:
                raise ValueError("offer/transfer candidates require non-empty phase_evidence_refs")
            required_claim_tokens = {
                "no_autonomous_trade_claim",
                "no_negotiation_claim",
                "no_hidden_truth_claim",
                "no_executed_transfer_claim",
                "no_economic_agency_claim",
            }
            if not required_claim_tokens.issubset(set(self.prohibited_claims)):
                raise ValueError("offer/transfer candidates must preserve prohibited-claim boundary tokens")
            # Require phase-specific evidence, not just run-level summary marker.
            phase_tokens = {item.split(":", 1)[0] for item in self.phase_evidence_refs if ":" in item}
            if len(phase_tokens) < 2:
                raise ValueError("offer/transfer candidates require candidate-specific phase evidence chain")


@dataclass(frozen=True, slots=True)
class AResponseCandidateRun:
    run_id: str
    scenario_name: str
    execution_level: str
    subject_tick_used: bool
    owner_surface_used: bool
    adapter_projection_used: bool
    fallback_reasons: tuple[str, ...]
    phase_coverage_verified: bool
    phase_coverage_evidence: tuple[str, ...]
    response_candidates: tuple[AResponseCandidate, ...]
    selected_response_kind: AResponseKind
    selected_response_id: str | None
    response_verdict: ResponseVerdict
    claim_boundary: tuple[str, ...]
    falsifier_summary: tuple[dict[str, object], ...] = ()
    eval_only: dict[str, object] = field(default_factory=dict)


def response_candidate_run_to_dict(
    run: AResponseCandidateRun,
    *,
    include_eval_only: bool = False,
    include_response_candidates: bool = True,
) -> dict[str, object]:
    payload = {
        "run_id": run.run_id,
        "scenario_name": run.scenario_name,
        "stage": "stage3_response_candidate_probe",
        "execution_level": run.execution_level,
        "subject_tick_used": run.subject_tick_used,
        "owner_surface_used": run.owner_surface_used,
        "adapter_projection_used": run.adapter_projection_used,
        "fallback_reasons": list(run.fallback_reasons),
        "phase_coverage_verified": run.phase_coverage_verified,
        "phase_coverage_evidence": list(run.phase_coverage_evidence),
        "selected_response_kind": run.selected_response_kind.value,
        "selected_response_id": run.selected_response_id,
        "response_verdict": run.response_verdict.value,
        "claim_boundary": list(run.claim_boundary),
        "falsifier_summary": list(run.falsifier_summary),
    }
    if include_response_candidates:
        payload["response_candidates"] = [asdict(item) for item in run.response_candidates]
    if include_eval_only:
        payload["eval_only"] = run.eval_only
    return payload
