from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ResourceKind


class InternalResourceStatus(str, Enum):
    DEFICIT = "deficit"
    ADEQUATE = "adequate"
    SURPLUS = "surplus"
    UNKNOWN = "unknown"


class InternalMagnitudeBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class InternalStateAuthority(str, Enum):
    SUBJECT_INTERNAL_PROBE = "subject_internal_probe"
    HARNESS_INJECTED_INTERNAL_STATE = "harness_injected_internal_state"


@dataclass(frozen=True, slots=True)
class AResourceState:
    subject_id: str
    resource_id: ResourceKind
    resource_status: InternalResourceStatus
    magnitude_band: InternalMagnitudeBand
    source_authority: InternalStateAuthority
    provenance_ref: tuple[str, ...]
    visible_to_subject: bool
    may_generate_desired_signal: bool
    may_count_as_world_evidence: bool
    may_authorize_action: bool
    claim_boundary: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SelfStateProbeRecord:
    self_state_id: str
    profile_id: str
    resource_states: tuple[AResourceState, ...]
    deficit_markers: tuple[str, ...]
    surplus_markers: tuple[str, ...]
    desired_signal_candidates: tuple[str, ...]
    prohibited_interpretations: tuple[str, ...]
    evidence_boundary: str
    action_authorization_granted: bool
    claim_boundary: tuple[str, ...]


def _resource_state(
    *,
    profile_id: str,
    subject_id: str,
    resource: ResourceKind,
    status: InternalResourceStatus,
    magnitude: InternalMagnitudeBand,
) -> AResourceState:
    return AResourceState(
        subject_id=subject_id,
        resource_id=resource,
        resource_status=status,
        magnitude_band=magnitude,
        source_authority=InternalStateAuthority.HARNESS_INJECTED_INTERNAL_STATE,
        provenance_ref=("experiments.symbolic_trade.stage25", profile_id),
        visible_to_subject=True,
        may_generate_desired_signal=status is InternalResourceStatus.DEFICIT,
        may_count_as_world_evidence=False,
        may_authorize_action=False,
        claim_boundary=(
            "computational_internal_resource_state_only",
            "not_world_evidence",
            "not_action_permission",
        ),
    )


def build_self_state_probe_for_scenario(scenario_id: str, *, subject_id: str = "subject_a") -> SelfStateProbeRecord:
    # Stage 2.5 keeps B scripted and varies only bounded self-side computational state profiles.
    profile_id = {
        "presence_only": "a_deficit_only",
        "a_deficit_only": "a_deficit_only",
        "b_surplus_claim_only": "a_surplus_only",
        "b_surplus_only": "mirrored_deficit_surplus",
        "b_need_only": "mirrored_deficit_surplus",
        "clarification_resolves_missing_need": "mirrored_deficit_surplus",
        "clarification_loop_guard": "a_deficit_only",
        "resource_claim_contact": "a_deficit_only",
        "mirrored_resource_asymmetry": "mirrored_deficit_surplus",
        "false_counterpart_claim": "false_mirrored_claim",
        "blocked_aperture": "blocked_aperture_with_complementarity",
        "noisy_signal": "noisy_mirrored_claim",
        "transfer_seen_without_trade_token": "object_seen_without_claim",
        "claim_then_confirmed_transfer": "mirrored_deficit_surplus",
        "claim_then_failed_transfer": "mirrored_deficit_surplus",
        "transfer_affordance_failure": "mirrored_deficit_surplus",
        "successful_scripted_exchange_cycle": "mirrored_deficit_surplus",
        "eval_label_leak_attack": "eval_label_attack_with_self_state",
    }.get(scenario_id, "a_deficit_only")

    if profile_id == "a_surplus_only":
        states = (
            _resource_state(
                profile_id=profile_id,
                subject_id=subject_id,
                resource=ResourceKind.FOOD,
                status=InternalResourceStatus.SURPLUS,
                magnitude=InternalMagnitudeBand.MEDIUM,
            ),
            _resource_state(
                profile_id=profile_id,
                subject_id=subject_id,
                resource=ResourceKind.WATER,
                status=InternalResourceStatus.ADEQUATE,
                magnitude=InternalMagnitudeBand.LOW,
            ),
        )
    elif profile_id == "a_deficit_only":
        states = (
            _resource_state(
                profile_id=profile_id,
                subject_id=subject_id,
                resource=ResourceKind.WATER,
                status=InternalResourceStatus.DEFICIT,
                magnitude=InternalMagnitudeBand.HIGH,
            ),
            _resource_state(
                profile_id=profile_id,
                subject_id=subject_id,
                resource=ResourceKind.FOOD,
                status=InternalResourceStatus.ADEQUATE,
                magnitude=InternalMagnitudeBand.LOW,
            ),
        )
    else:
        states = (
            _resource_state(
                profile_id=profile_id,
                subject_id=subject_id,
                resource=ResourceKind.WATER,
                status=InternalResourceStatus.DEFICIT,
                magnitude=InternalMagnitudeBand.HIGH,
            ),
            _resource_state(
                profile_id=profile_id,
                subject_id=subject_id,
                resource=ResourceKind.FOOD,
                status=InternalResourceStatus.SURPLUS,
                magnitude=InternalMagnitudeBand.MEDIUM,
            ),
        )

    deficits = tuple(f"{item.resource_id.value}:{item.resource_status.value}" for item in states if item.resource_status is InternalResourceStatus.DEFICIT)
    surpluses = tuple(f"{item.resource_id.value}:{item.resource_status.value}" for item in states if item.resource_status is InternalResourceStatus.SURPLUS)
    desired_candidates = tuple(f"desired:{item.resource_id.value}:stabilize" for item in states if item.resource_status is InternalResourceStatus.DEFICIT)

    return SelfStateProbeRecord(
        self_state_id=f"stage25:{scenario_id}:self_state",
        profile_id=profile_id,
        resource_states=states,
        deficit_markers=deficits,
        surplus_markers=surpluses,
        desired_signal_candidates=desired_candidates,
        prohibited_interpretations=(
            "self_state_not_world_evidence",
            "self_state_not_counterpart_truth",
            "self_state_not_action_permission",
            "self_state_not_trade_command",
        ),
        evidence_boundary="self_state_may_inform_desired_signal_only",
        action_authorization_granted=False,
        claim_boundary=(
            "no_subjective_need_claim",
            "no_autonomous_exchange_claim",
        ),
    )


def summarize_self_state_probe(probe: SelfStateProbeRecord) -> dict[str, object]:
    return {
        "self_state_id": probe.self_state_id,
        "profile_id": probe.profile_id,
        "deficit_markers": list(probe.deficit_markers),
        "surplus_markers": list(probe.surplus_markers),
        "desired_signal_candidates": list(probe.desired_signal_candidates),
        "evidence_boundary": probe.evidence_boundary,
        "action_authorization_granted": probe.action_authorization_granted,
    }
