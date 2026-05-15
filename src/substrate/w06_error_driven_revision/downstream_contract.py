from __future__ import annotations

from dataclasses import dataclass

from substrate.w06_error_driven_revision.models import (
    W06DownstreamRevisionPermissionPacket,
    W06ResultBundle,
)


@dataclass(frozen=True, slots=True)
class W06ContractView:
    revision_decision_count: int
    consequence_count: int
    revalidate_count: int
    downgrade_count: int
    invalidate_count: int
    split_identity_count: int
    block_claim_count: int
    quarantine_count: int
    retain_unresolved_count: int
    correction_candidate_count: int
    residual_uncertainty_count: int
    anti_paralysis_count: int
    global_scope_count: int
    local_scope_count: int
    confidence_drop_count: int
    must_not_execute_correction: bool
    claim_blocked: bool
    consumer_ready: bool
    no_clean_revision: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W06ConsumerPacket:
    may_continue_narrowly: bool
    may_use_with_residue: bool
    must_revalidate: bool
    must_block_claim: bool
    must_split_identity: bool
    must_not_execute_correction: bool
    must_escalate: bool
    must_quarantine: bool
    preserved_uncertainty_markers: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    correction_candidate_refs: tuple[str, ...]
    blocked_claim_packet_refs: tuple[str, ...]


def derive_w06_contract_view(result: W06ResultBundle) -> W06ContractView:
    if not isinstance(result, W06ResultBundle):
        raise TypeError("derive_w06_contract_view requires W06ResultBundle")
    return W06ContractView(
        revision_decision_count=1,
        consequence_count=1,
        revalidate_count=result.telemetry.revalidate_count,
        downgrade_count=result.telemetry.downgrade_count,
        invalidate_count=result.telemetry.invalidate_count,
        split_identity_count=result.telemetry.split_identity_count,
        block_claim_count=result.telemetry.block_claim_count,
        quarantine_count=result.telemetry.quarantine_count,
        retain_unresolved_count=result.telemetry.retain_unresolved_count,
        correction_candidate_count=result.telemetry.correction_candidate_count,
        residual_uncertainty_count=result.telemetry.residue_retention_count,
        anti_paralysis_count=result.telemetry.anti_paralysis_count,
        global_scope_count=result.telemetry.global_scope_count,
        local_scope_count=result.telemetry.local_scope_count,
        confidence_drop_count=result.telemetry.confidence_drop_count,
        must_not_execute_correction=result.gate.must_not_execute_correction,
        claim_blocked=result.gate.must_block_claim,
        consumer_ready=result.gate.consumer_ready,
        no_clean_revision=result.gate.no_clean_revision,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        reason=result.reason,
    )


def derive_w06_consumer_packets(result: W06ResultBundle) -> tuple[W06ConsumerPacket, ...]:
    if not isinstance(result, W06ResultBundle):
        raise TypeError("derive_w06_consumer_packets requires W06ResultBundle")
    return (_to_consumer(result.downstream_packet),)


def require_w06_revision_consumer(result_or_view: W06ResultBundle | W06ContractView) -> W06ContractView:
    view = derive_w06_contract_view(result_or_view) if isinstance(result_or_view, W06ResultBundle) else result_or_view
    if not isinstance(view, W06ContractView):
        raise TypeError("require_w06_revision_consumer requires W06ResultBundle/W06ContractView")
    if not view.consumer_ready:
        raise PermissionError("w06 revision consumer requires bounded continuation-ready revision route")
    return view


def require_w06_execution_seam_consumer(result_or_view: W06ResultBundle | W06ContractView) -> W06ContractView:
    view = derive_w06_contract_view(result_or_view) if isinstance(result_or_view, W06ResultBundle) else result_or_view
    if not isinstance(view, W06ContractView):
        raise TypeError("require_w06_execution_seam_consumer requires W06ResultBundle/W06ContractView")
    if not view.must_not_execute_correction:
        raise PermissionError("w06 execution seam consumer requires correction execution prohibition")
    return view


def _to_consumer(packet: W06DownstreamRevisionPermissionPacket) -> W06ConsumerPacket:
    return W06ConsumerPacket(
        may_continue_narrowly=packet.may_continue_narrowly,
        may_use_with_residue=packet.may_use_with_residue,
        must_revalidate=packet.must_revalidate,
        must_block_claim=packet.must_block_claim,
        must_split_identity=packet.must_split_identity,
        must_not_execute_correction=packet.must_not_execute_correction,
        must_escalate=packet.must_escalate,
        must_quarantine=packet.must_quarantine,
        preserved_uncertainty_markers=packet.preserved_uncertainty_markers,
        prohibited_claims=packet.prohibited_claims,
        correction_candidate_refs=packet.correction_candidate_refs,
        blocked_claim_packet_refs=packet.blocked_claim_packet_refs,
    )
