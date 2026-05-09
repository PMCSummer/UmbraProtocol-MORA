from __future__ import annotations

from dataclasses import dataclass

from substrate.w01_bounded_world_loop.models import W01Result


@dataclass(frozen=True, slots=True)
class W01ContractView:
    packet_count: int
    admitted_count: int
    contested_count: int
    blocked_count: int
    revoked_count: int
    contradiction_count: int
    linked_effect_count: int
    no_link_count: int
    source_authority_missing_count: int
    non_mature_object_claim_count: int
    consumer_ready: bool
    admission_required: bool
    clean_world_claim_allowed: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    scope: str
    staged_world_scaffold_only: bool
    no_mature_object_claim: bool
    no_object_permanence_claim: bool
    no_scene_graph_maturity_claim: bool
    no_policy_selection_claim: bool
    no_world_truth_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W01ConsumerView:
    consumer_ready: bool
    admitted_count: int
    contested_count: int
    blocked_count: int
    revoked_count: int
    linked_effect_count: int
    no_link_count: int
    source_authority_missing_count: int
    non_mature_object_claim_count: int
    required_restrictions: tuple[str, ...]
    reason: str


def derive_w01_contract_view(result: W01Result) -> W01ContractView:
    if not isinstance(result, W01Result):
        raise TypeError("derive_w01_contract_view requires W01Result")
    gate = result.gate
    telemetry = result.telemetry
    scope = result.scope_marker
    return W01ContractView(
        packet_count=telemetry.packet_count,
        admitted_count=telemetry.admitted_count,
        contested_count=telemetry.contested_count,
        blocked_count=telemetry.rejected_count + telemetry.absent_count,
        revoked_count=telemetry.revoked_count,
        contradiction_count=telemetry.contradiction_count,
        linked_effect_count=telemetry.linked_effect_count,
        no_link_count=telemetry.no_link_count,
        source_authority_missing_count=telemetry.source_authority_missing_count,
        non_mature_object_claim_count=telemetry.non_mature_object_claim_count,
        consumer_ready=gate.consumer_ready,
        admission_required=gate.admission_required,
        clean_world_claim_allowed=gate.clean_world_claim_allowed,
        required_restrictions=gate.required_restrictions,
        reason_codes=gate.reason_codes,
        scope=scope.scope,
        staged_world_scaffold_only=scope.staged_world_scaffold_only,
        no_mature_object_claim=scope.no_mature_object_claim,
        no_object_permanence_claim=scope.no_object_permanence_claim,
        no_scene_graph_maturity_claim=scope.no_scene_graph_maturity_claim,
        no_policy_selection_claim=scope.no_policy_selection_claim,
        no_world_truth_claim=scope.no_world_truth_claim,
        reason=result.reason,
    )


def derive_w01_consumer_view(result_or_view: W01Result | W01ContractView) -> W01ConsumerView:
    view = derive_w01_contract_view(result_or_view) if isinstance(result_or_view, W01Result) else result_or_view
    if not isinstance(view, W01ContractView):
        raise TypeError("derive_w01_consumer_view requires W01Result/W01ContractView")
    return W01ConsumerView(
        consumer_ready=view.consumer_ready,
        admitted_count=view.admitted_count,
        contested_count=view.contested_count,
        blocked_count=view.blocked_count,
        revoked_count=view.revoked_count,
        linked_effect_count=view.linked_effect_count,
        no_link_count=view.no_link_count,
        source_authority_missing_count=view.source_authority_missing_count,
        non_mature_object_claim_count=view.non_mature_object_claim_count,
        required_restrictions=view.required_restrictions,
        reason="w01 bounded world-loop consumer view",
    )


def require_w01_permission_packet_consumer(result_or_view: W01Result | W01ContractView) -> W01ConsumerView:
    view = derive_w01_consumer_view(result_or_view)
    if not view.consumer_ready:
        raise PermissionError("w01 permission-packet consumer requires consumer_ready world admission")
    return view


def require_w01_action_effect_linkage_consumer(result_or_view: W01Result | W01ContractView) -> W01ConsumerView:
    view = derive_w01_consumer_view(result_or_view)
    if view.linked_effect_count == 0:
        raise PermissionError("w01 action-effect linkage consumer requires at least one linked effect")
    return view
