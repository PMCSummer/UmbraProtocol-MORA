from __future__ import annotations

from dataclasses import dataclass

from substrate.w02_regularity_extraction.models import (
    W02DownstreamRegularityPermissionPacket,
    W02ResultBundle,
)


@dataclass(frozen=True, slots=True)
class W02ContractView:
    regularity_record_count: int
    promotion_count: int
    blocked_count: int
    contested_count: int
    downgraded_count: int
    contradiction_count: int
    lineage_ambiguity_count: int
    must_abstain_count: int
    consumer_ready: bool
    clean_regularity_claim_allowed: bool
    no_mature_object_identity_claim: bool
    no_object_permanence_claim: bool
    no_scene_graph_truth_claim: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W02ConsumerPacket:
    regularity_id: str
    may_use_as_scaffold: bool
    may_use_as_instance_hypothesis: bool
    may_use_as_kind_hint: bool
    may_use_as_affordance_hint: bool
    may_use_as_scene_role_hint: bool
    may_claim_stable_identity: bool
    must_preserve_uncertainty: bool
    must_abstain: bool
    reason_codes: tuple[str, ...]


def derive_w02_contract_view(result: W02ResultBundle) -> W02ContractView:
    if not isinstance(result, W02ResultBundle):
        raise TypeError("derive_w02_contract_view requires W02ResultBundle")
    return W02ContractView(
        regularity_record_count=len(result.regularity_records),
        promotion_count=result.telemetry.promoted_count,
        blocked_count=result.telemetry.blocked_count,
        contested_count=result.telemetry.contested_count,
        downgraded_count=result.telemetry.downgraded_count,
        contradiction_count=result.telemetry.contradiction_count,
        lineage_ambiguity_count=result.telemetry.lineage_ambiguity_count,
        must_abstain_count=result.telemetry.must_abstain_count,
        consumer_ready=result.gate.consumer_ready,
        clean_regularity_claim_allowed=result.gate.clean_regularity_claim_allowed,
        no_mature_object_identity_claim=result.scope_marker.no_mature_object_identity_claim,
        no_object_permanence_claim=result.scope_marker.no_object_permanence_claim,
        no_scene_graph_truth_claim=result.scope_marker.no_scene_graph_truth_claim,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        reason=result.reason,
    )


def derive_w02_consumer_packets(result: W02ResultBundle) -> tuple[W02ConsumerPacket, ...]:
    if not isinstance(result, W02ResultBundle):
        raise TypeError("derive_w02_consumer_packets requires W02ResultBundle")
    return tuple(_packet_to_consumer(item) for item in result.downstream_permission_packets)


def require_w02_permission_packet_consumer(result_or_view: W02ResultBundle | W02ContractView) -> W02ContractView:
    view = derive_w02_contract_view(result_or_view) if isinstance(result_or_view, W02ResultBundle) else result_or_view
    if not isinstance(view, W02ContractView):
        raise TypeError("require_w02_permission_packet_consumer requires W02ResultBundle/W02ContractView")
    if not view.consumer_ready:
        raise PermissionError("w02 permission consumer requires consumer-ready staged regularity packets")
    return view


def require_w02_contradiction_review_consumer(result_or_view: W02ResultBundle | W02ContractView) -> W02ContractView:
    view = derive_w02_contract_view(result_or_view) if isinstance(result_or_view, W02ResultBundle) else result_or_view
    if not isinstance(view, W02ContractView):
        raise TypeError("require_w02_contradiction_review_consumer requires W02ResultBundle/W02ContractView")
    if view.contradiction_count <= 0:
        raise PermissionError("w02 contradiction review consumer requires contradiction-positive staged regularity state")
    return view


def _packet_to_consumer(packet: W02DownstreamRegularityPermissionPacket) -> W02ConsumerPacket:
    return W02ConsumerPacket(
        regularity_id=packet.regularity_id,
        may_use_as_scaffold=packet.may_use_as_scaffold,
        may_use_as_instance_hypothesis=packet.may_use_as_instance_hypothesis,
        may_use_as_kind_hint=packet.may_use_as_kind_hint,
        may_use_as_affordance_hint=packet.may_use_as_affordance_hint,
        may_use_as_scene_role_hint=packet.may_use_as_scene_role_hint,
        may_claim_stable_identity=packet.may_claim_stable_identity,
        must_preserve_uncertainty=packet.must_preserve_uncertainty,
        must_abstain=packet.must_abstain,
        reason_codes=packet.reason_codes,
    )
