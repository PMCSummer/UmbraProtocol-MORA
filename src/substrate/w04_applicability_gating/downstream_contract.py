from __future__ import annotations

from dataclasses import dataclass

from substrate.w04_applicability_gating.models import (
    W04DownstreamApplicabilityPermissionPacket,
    W04ResultBundle,
)


@dataclass(frozen=True, slots=True)
class W04ContractView:
    applicability_decision_count: int
    allowed_count: int
    blocked_count: int
    narrowed_count: int
    hint_only_count: int
    revalidate_required_count: int
    abstain_count: int
    relaxation_count: int
    hard_constraint_failure_count: int
    unknown_hard_count: int
    malformed_desired_state_count: int
    perspective_block_count: int
    authority_block_count: int
    stale_block_count: int
    consumer_ready: bool
    no_clean_applicability: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W04ConsumerPacket:
    decision_id: str
    candidate_id: str
    may_deploy_candidate: bool
    may_use_as_hint_only: bool
    may_use_after_revalidation: bool
    may_use_with_relaxation: bool
    must_abstain: bool
    must_block: bool
    must_revalidate: bool
    must_preserve_hard_constraints: bool
    must_preserve_perspective_scope: bool
    must_preserve_authority_scope: bool
    action_authorization_granted: bool
    prohibited_uses: tuple[str, ...]
    required_preserved_markers: tuple[str, ...]
    blocked_reason: str
    decision_reason_codes: tuple[str, ...]


def derive_w04_contract_view(result: W04ResultBundle) -> W04ContractView:
    if not isinstance(result, W04ResultBundle):
        raise TypeError("derive_w04_contract_view requires W04ResultBundle")
    return W04ContractView(
        applicability_decision_count=result.telemetry.applicability_decision_count,
        allowed_count=result.telemetry.allowed_count,
        blocked_count=result.telemetry.blocked_count,
        narrowed_count=result.telemetry.narrowed_count,
        hint_only_count=result.telemetry.hint_only_count,
        revalidate_required_count=result.telemetry.revalidate_required_count,
        abstain_count=result.telemetry.abstain_count,
        relaxation_count=result.telemetry.relaxation_count,
        hard_constraint_failure_count=result.telemetry.hard_constraint_failure_count,
        unknown_hard_count=result.telemetry.unknown_hard_count,
        malformed_desired_state_count=result.telemetry.malformed_desired_state_count,
        perspective_block_count=result.telemetry.perspective_block_count,
        authority_block_count=result.telemetry.authority_block_count,
        stale_block_count=result.telemetry.stale_block_count,
        consumer_ready=result.gate.consumer_ready,
        no_clean_applicability=result.gate.no_clean_applicability,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        reason=result.reason,
    )


def derive_w04_consumer_packets(result: W04ResultBundle) -> tuple[W04ConsumerPacket, ...]:
    if not isinstance(result, W04ResultBundle):
        raise TypeError("derive_w04_consumer_packets requires W04ResultBundle")
    return tuple(_to_consumer(item) for item in result.downstream_permission_packets)


def require_w04_applicability_consumer(result_or_view: W04ResultBundle | W04ContractView) -> W04ContractView:
    view = derive_w04_contract_view(result_or_view) if isinstance(result_or_view, W04ResultBundle) else result_or_view
    if not isinstance(view, W04ContractView):
        raise TypeError("require_w04_applicability_consumer requires W04ResultBundle/W04ContractView")
    if not view.consumer_ready:
        raise PermissionError("w04 applicability consumer requires clean applicability packet")
    return view


def require_w04_revalidation_consumer(result_or_view: W04ResultBundle | W04ContractView) -> W04ContractView:
    view = derive_w04_contract_view(result_or_view) if isinstance(result_or_view, W04ResultBundle) else result_or_view
    if not isinstance(view, W04ContractView):
        raise TypeError("require_w04_revalidation_consumer requires W04ResultBundle/W04ContractView")
    if view.revalidate_required_count <= 0:
        raise PermissionError("w04 revalidation consumer requires revalidation-bearing applicability state")
    return view


def _to_consumer(packet: W04DownstreamApplicabilityPermissionPacket) -> W04ConsumerPacket:
    return W04ConsumerPacket(
        decision_id=packet.decision_id,
        candidate_id=packet.candidate_id,
        may_deploy_candidate=packet.may_deploy_candidate,
        may_use_as_hint_only=packet.may_use_as_hint_only,
        may_use_after_revalidation=packet.may_use_after_revalidation,
        may_use_with_relaxation=packet.may_use_with_relaxation,
        must_abstain=packet.must_abstain,
        must_block=packet.must_block,
        must_revalidate=packet.must_revalidate,
        must_preserve_hard_constraints=packet.must_preserve_hard_constraints,
        must_preserve_perspective_scope=packet.must_preserve_perspective_scope,
        must_preserve_authority_scope=packet.must_preserve_authority_scope,
        action_authorization_granted=packet.action_authorization_granted,
        prohibited_uses=packet.prohibited_uses,
        required_preserved_markers=packet.required_preserved_markers,
        blocked_reason=packet.blocked_reason,
        decision_reason_codes=packet.decision_reason_codes,
    )
