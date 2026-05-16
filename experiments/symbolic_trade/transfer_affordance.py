from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .clarification_policy import ResponseReadinessDecision, ResponseReadinessStatus
from .internal_state import SelfStateProbeRecord
from .models import ApertureState, CounterpartSignalKind, ResourceKind, SubjectVisiblePacket, TransferOutcome


class TransferAffordanceKind(str, Enum):
    APERTURE_TRANSFER = "aperture_transfer"


class TransferAffordanceStatus(str, Enum):
    AVAILABLE = "available"
    BLOCKED = "blocked"
    CONTESTED = "contested"
    REVOKED = "revoked"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class TransferAffordanceRecord:
    affordance_id: str
    affordance_kind: TransferAffordanceKind
    status: TransferAffordanceStatus
    source_actor_id: str
    target_actor_id: str
    resource_kind: ResourceKind | None
    aperture_state: ApertureState
    authority_ref: str
    provenance_ref: tuple[str, ...]
    a04_binding_authority_present: bool
    a02_gap_markers: tuple[str, ...]
    claim_boundary: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransferAffordanceInvocationCandidate:
    invocation_id: str
    affordance_id: str
    eligible: bool
    execution_requested: bool
    execution_prohibited: bool
    source_offer_candidate_id: str | None
    resource_kind: ResourceKind | None
    reason_codes: tuple[str, ...]
    claim_boundary: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransferAttemptRecord:
    attempt_id: str
    invocation_id: str
    attempted: bool
    world_executed_by_harness: bool
    execution_prohibited: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransferResultRecord:
    result_id: str
    attempt_id: str
    observed: bool
    outcome: TransferOutcome
    verified: bool
    residue_required: bool
    revalidate_required: bool
    result_used_as_success_authority: bool
    prohibited_claims: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransferEpisodeRecord:
    episode_id: str
    candidate_emitted: bool
    attempted: bool
    world_executed: bool
    observed_result: bool
    verified: bool
    reciprocal_transfer_observed: bool
    exchange_completion_claim: bool
    completion_basis: tuple[str, ...]
    episode_completion_status: str
    residue_present: bool
    claim_boundary: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransferAffordancePolicy:
    execute_transfer_affordance: bool = False
    require_offer_candidate: bool = True


def infer_transfer_affordance_status(packets: tuple[SubjectVisiblePacket, ...]) -> TransferAffordanceStatus:
    if any(
        packet.signal_kind is CounterpartSignalKind.BLOCKED
        or packet.aperture_state in {ApertureState.BLOCKED, ApertureState.CLOSED}
        for packet in packets
    ):
        return TransferAffordanceStatus.BLOCKED
    if any(packet.signal_kind is CounterpartSignalKind.CONTRADICTION for packet in packets):
        return TransferAffordanceStatus.CONTESTED
    return TransferAffordanceStatus.AVAILABLE


def _self_surplus_resource(self_state: SelfStateProbeRecord) -> ResourceKind | None:
    for marker in self_state.surplus_markers:
        if marker.startswith("food:"):
            return ResourceKind.FOOD
        if marker.startswith("water:"):
            return ResourceKind.WATER
    return None


def build_transfer_affordance_record(
    *,
    scenario_name: str,
    packets: tuple[SubjectVisiblePacket, ...],
    self_state: SelfStateProbeRecord,
) -> TransferAffordanceRecord:
    status = infer_transfer_affordance_status(packets)
    aperture_state = ApertureState.OPEN
    for packet in packets:
        if packet.aperture_state in {ApertureState.BLOCKED, ApertureState.CLOSED, ApertureState.NOISY}:
            aperture_state = packet.aperture_state
            break

    a02_markers: list[str] = []
    if status is TransferAffordanceStatus.BLOCKED:
        a02_markers.append("a02_gap:blocked_transfer_resource")
    if status is TransferAffordanceStatus.MISSING:
        a02_markers.append("a02_gap:missing_transfer_affordance")
    if status is TransferAffordanceStatus.CONTESTED:
        a02_markers.append("a02_gap:low_reliability_affordance")

    return TransferAffordanceRecord(
        affordance_id=f"{scenario_name}:affordance:aperture_transfer",
        affordance_kind=TransferAffordanceKind.APERTURE_TRANSFER,
        status=status,
        source_actor_id="subject_a",
        target_actor_id="counterpart_b",
        resource_kind=_self_surplus_resource(self_state),
        aperture_state=aperture_state,
        authority_ref="harness_a04_binding",
        provenance_ref=("experiments.symbolic_trade", "stage4", "a04-compatible"),
        a04_binding_authority_present=True,
        a02_gap_markers=tuple(a02_markers),
        claim_boundary=(
            "external_transfer_affordance_only",
            "no_core_a04_mutation",
            "candidate_not_execution",
            "counterpart_claim_not_fact",
        ),
    )


def build_invocation_candidate(
    *,
    scenario_name: str,
    readiness: ResponseReadinessDecision,
    affordance: TransferAffordanceRecord,
    offer_candidate_id: str | None,
    policy: TransferAffordancePolicy,
) -> TransferAffordanceInvocationCandidate:
    eligible = True
    reasons: list[str] = []

    if policy.require_offer_candidate and offer_candidate_id is None:
        eligible = False
        reasons.append("no_offer_candidate_reference")
    if readiness.status is not ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER:
        eligible = False
        reasons.append(f"readiness_not_sufficient:{readiness.status.value}")
    if affordance.status is not TransferAffordanceStatus.AVAILABLE:
        eligible = False
        reasons.append(f"affordance_not_available:{affordance.status.value}")
    if affordance.resource_kind is None:
        eligible = False
        reasons.append("no_self_surplus_resource_for_transfer")

    execution_requested = policy.execute_transfer_affordance
    execution_prohibited = not (execution_requested and eligible)
    if execution_requested and not eligible:
        reasons.append("execution_requested_but_not_eligible")
    if not execution_requested:
        reasons.append("candidate_only_mode_no_execution_flag")

    return TransferAffordanceInvocationCandidate(
        invocation_id=f"{scenario_name}:invocation:aperture_transfer",
        affordance_id=affordance.affordance_id,
        eligible=eligible,
        execution_requested=execution_requested,
        execution_prohibited=execution_prohibited,
        source_offer_candidate_id=offer_candidate_id,
        resource_kind=affordance.resource_kind,
        reason_codes=tuple(dict.fromkeys(reasons)),
        claim_boundary=(
            "invocation_candidate_not_execution",
            "requires_explicit_execution_flag",
            "no_hidden_truth_dependency",
        ),
    )


def execute_transfer_invocation(
    *,
    scenario_name: str,
    invocation: TransferAffordanceInvocationCandidate,
    packets: tuple[SubjectVisiblePacket, ...],
) -> tuple[TransferAttemptRecord, TransferResultRecord, TransferEpisodeRecord]:
    attempted = invocation.execution_requested and invocation.eligible and not invocation.execution_prohibited
    attempt = TransferAttemptRecord(
        attempt_id=f"{scenario_name}:transfer_attempt:1",
        invocation_id=invocation.invocation_id,
        attempted=attempted,
        world_executed_by_harness=attempted,
        execution_prohibited=invocation.execution_prohibited,
        reason_codes=(
            "p02_attempt_recorded",
            "world_execution_harness_only" if attempted else "no_world_execution",
        ),
    )

    observed_outcomes = [
        packet.transfer_outcome
        for packet in packets
        if packet.signal_kind is CounterpartSignalKind.TRANSFER_RESULT and packet.transfer_outcome is not TransferOutcome.NOT_ATTEMPTED
    ]
    succeeded_transfer_result_count = sum(1 for outcome in observed_outcomes if outcome is TransferOutcome.SUCCEEDED)
    if not attempted:
        outcome = TransferOutcome.NOT_ATTEMPTED
    elif observed_outcomes:
        outcome = observed_outcomes[-1]
    else:
        outcome = TransferOutcome.FAILED_UNKNOWN

    observed = attempted and outcome is not TransferOutcome.NOT_ATTEMPTED
    reciprocal_transfer_observed = succeeded_transfer_result_count >= 2
    verified = outcome is TransferOutcome.SUCCEEDED and observed and reciprocal_transfer_observed
    result_used_as_success_authority = False
    residue = attempted and outcome is not TransferOutcome.SUCCEEDED

    prohibited_claims = (
        "transfer_result_not_trade_success_oracle",
        "single_result_not_exchange_completion_authority",
    )
    result = TransferResultRecord(
        result_id=f"{scenario_name}:transfer_result:1",
        attempt_id=attempt.attempt_id,
        observed=observed,
        outcome=outcome,
        verified=verified,
        residue_required=residue,
        revalidate_required=residue,
        result_used_as_success_authority=result_used_as_success_authority,
        prohibited_claims=prohibited_claims,
        reason_codes=(
            "p02_result_recorded",
            "w06_residue_required" if residue else "no_residue",
        ),
    )
    completion_basis: list[str] = []
    if attempted:
        completion_basis.append("a_to_b_attempt_visible")
    if observed:
        completion_basis.append("a_to_b_transfer_result_visible")
    if reciprocal_transfer_observed:
        completion_basis.append("b_to_a_reciprocal_transfer_result_visible")
    if verified:
        completion_basis.append("bounded_symbolic_exchange_episode_verified")

    if not attempted:
        completion_status = "not_attempted"
    elif outcome is not TransferOutcome.SUCCEEDED:
        completion_status = "attempt_failed_or_unverified"
    elif verified:
        completion_status = "exchange_cycle_completed_symbolically"
    else:
        completion_status = "single_transfer_only_not_verified"

    episode = TransferEpisodeRecord(
        episode_id=f"{scenario_name}:transfer_episode:1",
        candidate_emitted=True,
        attempted=attempt.attempted,
        world_executed=attempt.world_executed_by_harness,
        observed_result=result.observed,
        verified=result.verified,
        reciprocal_transfer_observed=reciprocal_transfer_observed,
        exchange_completion_claim=verified,
        completion_basis=tuple(completion_basis),
        episode_completion_status=completion_status,
        residue_present=result.residue_required,
        claim_boundary=(
            "p02_candidate_not_equal_attempt",
            "p02_attempt_not_equal_verified_success",
            "transfer_result_not_trade_success_oracle",
        ),
    )
    return attempt, result, episode
