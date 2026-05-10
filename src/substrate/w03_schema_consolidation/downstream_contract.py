from __future__ import annotations

from dataclasses import dataclass

from substrate.w03_schema_consolidation.models import (
    W03DownstreamSchemaPermissionPacket,
    W03ResultBundle,
    W03SchemaChannel,
)


@dataclass(frozen=True, slots=True)
class W03ContractView:
    schema_candidate_count: int
    everyday_prior_count: int
    operational_default_count: int
    contested_count: int
    stale_count: int
    must_revalidate_count: int
    must_abstain_count: int
    contradiction_count: int
    version_update_count: int
    consumer_ready: bool
    no_clean_schema: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W03ConsumerPacket:
    schema_id: str
    channel: W03SchemaChannel
    may_use_as_bounded_prior: bool
    may_use_as_schema_hint: bool
    may_use_as_operational_default: bool
    must_revalidate_before_use: bool
    must_preserve_contradiction: bool
    must_abstain: bool
    prohibited_claims: tuple[str, ...]
    reason_codes: tuple[str, ...]


def derive_w03_contract_view(result: W03ResultBundle) -> W03ContractView:
    if not isinstance(result, W03ResultBundle):
        raise TypeError("derive_w03_contract_view requires W03ResultBundle")
    return W03ContractView(
        schema_candidate_count=result.telemetry.schema_candidate_count,
        everyday_prior_count=result.telemetry.everyday_prior_count,
        operational_default_count=result.telemetry.operational_default_count,
        contested_count=result.telemetry.contested_count,
        stale_count=result.telemetry.stale_count,
        must_revalidate_count=result.telemetry.must_revalidate_count,
        must_abstain_count=result.telemetry.must_abstain_count,
        contradiction_count=result.telemetry.contradiction_count,
        version_update_count=result.telemetry.version_update_count,
        consumer_ready=result.gate.consumer_ready,
        no_clean_schema=result.gate.no_clean_schema,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        reason=result.reason,
    )


def derive_w03_consumer_packets(result: W03ResultBundle) -> tuple[W03ConsumerPacket, ...]:
    if not isinstance(result, W03ResultBundle):
        raise TypeError("derive_w03_consumer_packets requires W03ResultBundle")
    return tuple(_to_consumer(item) for item in result.downstream_permission_packets)


def require_w03_schema_consumer_ready(result_or_view: W03ResultBundle | W03ContractView) -> W03ContractView:
    view = derive_w03_contract_view(result_or_view) if isinstance(result_or_view, W03ResultBundle) else result_or_view
    if not isinstance(view, W03ContractView):
        raise TypeError("require_w03_schema_consumer_ready requires W03ResultBundle/W03ContractView")
    if not view.consumer_ready:
        raise PermissionError("w03 schema consumer requires consumer-ready bounded priors")
    return view


def require_w03_revalidation_consumer(result_or_view: W03ResultBundle | W03ContractView) -> W03ContractView:
    view = derive_w03_contract_view(result_or_view) if isinstance(result_or_view, W03ResultBundle) else result_or_view
    if not isinstance(view, W03ContractView):
        raise TypeError("require_w03_revalidation_consumer requires W03ResultBundle/W03ContractView")
    if view.must_revalidate_count <= 0:
        raise PermissionError("w03 revalidation consumer requires revalidation-bearing schema state")
    return view


def _to_consumer(packet: W03DownstreamSchemaPermissionPacket) -> W03ConsumerPacket:
    return W03ConsumerPacket(
        schema_id=packet.schema_id,
        channel=packet.channel,
        may_use_as_bounded_prior=packet.may_use_as_bounded_prior,
        may_use_as_schema_hint=packet.may_use_as_schema_hint,
        may_use_as_operational_default=packet.may_use_as_operational_default,
        must_revalidate_before_use=packet.must_revalidate_before_use,
        must_preserve_contradiction=packet.must_preserve_contradiction,
        must_abstain=packet.must_abstain,
        prohibited_claims=packet.prohibited_claims,
        reason_codes=packet.reason_codes,
    )
