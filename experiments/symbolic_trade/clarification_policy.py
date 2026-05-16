from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .internal_state import SelfStateProbeRecord
from .models import ApertureState, CounterpartSignalKind, ResourceKind, SubjectVisiblePacket


class MissingInformationKind(str, Enum):
    COUNTERPART_RESOURCE_STATUS = "counterpart_resource_status"
    COUNTERPART_NEED_STATUS = "counterpart_need_status"
    COUNTERPART_ACCEPTANCE = "counterpart_acceptance"
    APERTURE_STATUS = "aperture_status"
    TRANSFER_AFFORDANCE_STATUS = "transfer_affordance_status"
    RESOURCE_IDENTITY = "resource_identity"
    CLAIM_AUTHORITY = "claim_authority"
    SELF_SURPLUS = "self_surplus"
    SELF_DEFICIT = "self_deficit"


class ClarificationRoute(str, Enum):
    TARGETED_QUERY = "targeted_query"
    REVALIDATE = "revalidate"
    ABSTAIN = "abstain"
    OBSERVE_ONLY = "observe_only"
    NO_CLARIFICATION = "no_clarification"


class ResponseReadinessStatus(str, Enum):
    SUFFICIENT_FOR_BOUNDED_OFFER = "sufficient_for_bounded_offer"
    CLARIFICATION_REQUIRED = "clarification_required"
    REVALIDATION_REQUIRED = "revalidation_required"
    BLOCKED = "blocked"
    OBSERVE_ONLY = "observe_only"
    ABSTAIN = "abstain"


@dataclass(frozen=True, slots=True)
class ClarificationBudget:
    max_total_queries: int = 2
    max_queries_per_field: int = 1
    consumed_total: int = 0
    consumed_by_field: tuple[tuple[MissingInformationKind, int], ...] = ()

    def consumed_for(self, field: MissingInformationKind) -> int:
        for current_field, count in self.consumed_by_field:
            if current_field is field:
                return count
        return 0

    def can_query(self, field: MissingInformationKind) -> bool:
        if self.consumed_total >= self.max_total_queries:
            return False
        return self.consumed_for(field) < self.max_queries_per_field

    def consume(self, field: MissingInformationKind) -> "ClarificationBudget":
        updated = dict(self.consumed_by_field)
        updated[field] = updated.get(field, 0) + 1
        return ClarificationBudget(
            max_total_queries=self.max_total_queries,
            max_queries_per_field=self.max_queries_per_field,
            consumed_total=self.consumed_total + 1,
            consumed_by_field=tuple((item, updated[item]) for item in sorted(updated, key=lambda x: x.value)),
        )


@dataclass(frozen=True, slots=True)
class ClarificationDecisionRecord:
    scenario_name: str
    route: ClarificationRoute
    target_field: MissingInformationKind | None
    decision_critical: bool
    progress_made: bool
    budget_before: ClarificationBudget
    budget_after: ClarificationBudget
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResponseReadinessDecision:
    scenario_name: str
    status: ResponseReadinessStatus
    critical_missing_fields: tuple[MissingInformationKind, ...]
    clarification_route: ClarificationRoute
    clarification_target: MissingInformationKind | None
    clarification_budget_exhausted: bool
    counterpart_claim_refs: tuple[str, ...]
    self_state_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    claim_boundary: tuple[str, ...]


def _self_sets(self_state: SelfStateProbeRecord) -> tuple[set[str], set[str]]:
    deficits = {item.split(":", 1)[0] for item in self_state.deficit_markers}
    surpluses = {item.split(":", 1)[0] for item in self_state.surplus_markers}
    return deficits, surpluses


def _counterpart_claim_sets(packets: tuple[SubjectVisiblePacket, ...]) -> tuple[set[str], set[str], tuple[str, ...]]:
    counterpart_surplus: set[str] = set()
    counterpart_deficit: set[str] = set()
    refs: list[str] = []
    for packet in packets:
        if packet.signal_kind is not CounterpartSignalKind.RESOURCE_STATUS_CLAIM:
            continue
        if packet.resource_kind is None or packet.reported_level is None:
            continue
        refs.append(f"counterpart_claim:{packet.packet_id}")
        if packet.reported_level.value == "surplus":
            counterpart_surplus.add(packet.resource_kind.value)
        elif packet.reported_level.value == "deficit":
            counterpart_deficit.add(packet.resource_kind.value)
    return counterpart_surplus, counterpart_deficit, tuple(refs)


def evaluate_response_readiness(
    *,
    scenario_name: str,
    self_state: SelfStateProbeRecord,
    subject_visible_packets: tuple[SubjectVisiblePacket, ...],
    transfer_affordance_status: str,
    budget: ClarificationBudget,
) -> ResponseReadinessDecision:
    deficits, surpluses = _self_sets(self_state)
    counterpart_surplus, counterpart_deficit, claim_refs = _counterpart_claim_sets(subject_visible_packets)
    evidence_refs = tuple(f"packet:{item.packet_id}" for item in subject_visible_packets) + claim_refs

    aperture_blocked = any(
        packet.signal_kind is CounterpartSignalKind.BLOCKED
        or packet.aperture_state in {ApertureState.BLOCKED, ApertureState.CLOSED}
        for packet in subject_visible_packets
    )
    contradiction_seen = any(packet.signal_kind is CounterpartSignalKind.CONTRADICTION for packet in subject_visible_packets)

    missing: list[MissingInformationKind] = []
    if not deficits:
        missing.append(MissingInformationKind.SELF_DEFICIT)
    if not surpluses:
        missing.append(MissingInformationKind.SELF_SURPLUS)
    if deficits and not deficits.intersection(counterpart_surplus):
        missing.append(MissingInformationKind.COUNTERPART_RESOURCE_STATUS)
    if surpluses and not surpluses.intersection(counterpart_deficit):
        missing.append(MissingInformationKind.COUNTERPART_NEED_STATUS)
    if transfer_affordance_status != "available":
        missing.append(MissingInformationKind.TRANSFER_AFFORDANCE_STATUS)
    if aperture_blocked:
        missing.append(MissingInformationKind.APERTURE_STATUS)

    claim_boundary = (
        "readiness_from_visible_signals_only",
        "counterpart_claim_not_fact",
        "self_state_not_world_evidence",
        "clarification_not_resolution",
        "no_trade_oracle",
    )

    if contradiction_seen:
        return ResponseReadinessDecision(
            scenario_name=scenario_name,
            status=ResponseReadinessStatus.REVALIDATION_REQUIRED,
            critical_missing_fields=tuple(dict.fromkeys(missing)),
            clarification_route=ClarificationRoute.REVALIDATE,
            clarification_target=None,
            clarification_budget_exhausted=budget.consumed_total >= budget.max_total_queries,
            counterpart_claim_refs=claim_refs,
            self_state_refs=(self_state.self_state_id,),
            evidence_refs=evidence_refs,
            reason_codes=("contradiction_visible", "revalidation_required_before_offer"),
            claim_boundary=claim_boundary,
        )

    if aperture_blocked or transfer_affordance_status in {"blocked", "revoked", "missing"}:
        return ResponseReadinessDecision(
            scenario_name=scenario_name,
            status=ResponseReadinessStatus.BLOCKED,
            critical_missing_fields=tuple(dict.fromkeys(missing)),
            clarification_route=ClarificationRoute.NO_CLARIFICATION,
            clarification_target=None,
            clarification_budget_exhausted=False,
            counterpart_claim_refs=claim_refs,
            self_state_refs=(self_state.self_state_id,),
            evidence_refs=evidence_refs,
            reason_codes=("blocked_or_missing_transfer_affordance",),
            claim_boundary=claim_boundary,
        )

    if deficits and surpluses and deficits.intersection(counterpart_surplus) and surpluses.intersection(counterpart_deficit):
        return ResponseReadinessDecision(
            scenario_name=scenario_name,
            status=ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER,
            critical_missing_fields=(),
            clarification_route=ClarificationRoute.NO_CLARIFICATION,
            clarification_target=None,
            clarification_budget_exhausted=False,
            counterpart_claim_refs=claim_refs,
            self_state_refs=(self_state.self_state_id,),
            evidence_refs=evidence_refs,
            reason_codes=(
                "visible_claim_relation_present",
                "self_state_asymmetry_present_without_permission_upgrade",
                "bounded_offer_readiness_only",
            ),
            claim_boundary=claim_boundary,
        )

    if not missing:
        return ResponseReadinessDecision(
            scenario_name=scenario_name,
            status=ResponseReadinessStatus.OBSERVE_ONLY,
            critical_missing_fields=(),
            clarification_route=ClarificationRoute.OBSERVE_ONLY,
            clarification_target=None,
            clarification_budget_exhausted=False,
            counterpart_claim_refs=claim_refs,
            self_state_refs=(self_state.self_state_id,),
            evidence_refs=evidence_refs,
            reason_codes=("no_decision_critical_missing_field",),
            claim_boundary=claim_boundary,
        )

    target = next(
        (
            item
            for item in missing
            if item in {
                MissingInformationKind.COUNTERPART_RESOURCE_STATUS,
                MissingInformationKind.COUNTERPART_NEED_STATUS,
                MissingInformationKind.APERTURE_STATUS,
                MissingInformationKind.TRANSFER_AFFORDANCE_STATUS,
            }
        ),
        missing[0],
    )

    if budget.can_query(target):
        return ResponseReadinessDecision(
            scenario_name=scenario_name,
            status=ResponseReadinessStatus.CLARIFICATION_REQUIRED,
            critical_missing_fields=tuple(dict.fromkeys(missing)),
            clarification_route=ClarificationRoute.TARGETED_QUERY,
            clarification_target=target,
            clarification_budget_exhausted=False,
            counterpart_claim_refs=claim_refs,
            self_state_refs=(self_state.self_state_id,),
            evidence_refs=evidence_refs,
            reason_codes=("decision_critical_missing_information", f"clarification_target:{target.value}"),
            claim_boundary=claim_boundary,
        )

    return ResponseReadinessDecision(
        scenario_name=scenario_name,
        status=ResponseReadinessStatus.REVALIDATION_REQUIRED,
        critical_missing_fields=tuple(dict.fromkeys(missing)),
        clarification_route=ClarificationRoute.REVALIDATE,
        clarification_target=target,
        clarification_budget_exhausted=True,
        counterpart_claim_refs=claim_refs,
        self_state_refs=(self_state.self_state_id,),
        evidence_refs=evidence_refs,
        reason_codes=("clarification_budget_exhausted", f"revalidate_target:{target.value}"),
        claim_boundary=claim_boundary,
    )
