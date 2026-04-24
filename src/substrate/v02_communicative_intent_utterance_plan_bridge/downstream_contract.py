from __future__ import annotations

from dataclasses import dataclass

from substrate.v02_communicative_intent_utterance_plan_bridge.models import (
    V02UtterancePlanResult,
)


@dataclass(frozen=True, slots=True)
class V02UtterancePlanContractView:
    plan_id: str
    plan_status: str
    segment_count: int
    branch_count: int
    ordering_edge_count: int
    mandatory_qualifier_attachment_count: int
    mandatory_qualifier_ids: tuple[str, ...]
    blocked_expansion_count: int
    protected_omission_count: int
    clarification_first_required: bool
    refusal_dominant: bool
    protective_boundary_first: bool
    partial_plan_only: bool
    unresolved_branching: bool
    realization_contract_ready: bool
    discourse_history_sensitive: bool
    downstream_consumer_ready: bool
    plan_consumer_ready: bool
    ordering_consumer_ready: bool
    realization_contract_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_v02_first_slice_only: bool
    scope_v03_not_implemented: bool
    scope_p02_not_implemented: bool
    scope_p04_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class V02UtterancePlanConsumerView:
    plan_id: str
    plan_status: str
    partial_plan_only: bool
    clarification_first_required: bool
    protective_boundary_first: bool
    unresolved_branching: bool
    blocked_expansion_count: int
    protected_omission_count: int
    mandatory_qualifier_ids: tuple[str, ...]
    plan_consumer_ready: bool
    ordering_consumer_ready: bool
    realization_contract_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_v02_utterance_plan_contract_view(
    result: V02UtterancePlanResult,
) -> V02UtterancePlanContractView:
    if not isinstance(result, V02UtterancePlanResult):
        raise TypeError("derive_v02_utterance_plan_contract_view requires V02UtterancePlanResult")
    return V02UtterancePlanContractView(
        plan_id=result.state.plan_id,
        plan_status=result.state.plan_status.value,
        segment_count=result.state.segment_count,
        branch_count=result.state.branch_count,
        ordering_edge_count=result.state.ordering_edge_count,
        mandatory_qualifier_attachment_count=result.state.mandatory_qualifier_attachment_count,
        mandatory_qualifier_ids=result.state.mandatory_qualifier_ids,
        blocked_expansion_count=result.state.blocked_expansion_count,
        protected_omission_count=result.state.protected_omission_count,
        clarification_first_required=result.state.clarification_first_required,
        refusal_dominant=result.state.refusal_dominant,
        protective_boundary_first=result.state.protective_boundary_first,
        partial_plan_only=result.state.partial_plan_only,
        unresolved_branching=result.state.unresolved_branching,
        realization_contract_ready=result.state.realization_contract_ready,
        discourse_history_sensitive=result.state.discourse_history_sensitive,
        downstream_consumer_ready=result.state.downstream_consumer_ready,
        plan_consumer_ready=result.gate.plan_consumer_ready,
        ordering_consumer_ready=result.gate.ordering_consumer_ready,
        realization_contract_consumer_ready=result.gate.realization_contract_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_v02_first_slice_only=result.scope_marker.v02_first_slice_only,
        scope_v03_not_implemented=result.scope_marker.v03_not_implemented,
        scope_p02_not_implemented=result.scope_marker.p02_not_implemented,
        scope_p04_not_implemented=result.scope_marker.p04_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_v02_utterance_plan_consumer_view(
    result_or_view: V02UtterancePlanResult | V02UtterancePlanContractView,
) -> V02UtterancePlanConsumerView:
    view = (
        derive_v02_utterance_plan_contract_view(result_or_view)
        if isinstance(result_or_view, V02UtterancePlanResult)
        else result_or_view
    )
    if not isinstance(view, V02UtterancePlanContractView):
        raise TypeError(
            "derive_v02_utterance_plan_consumer_view requires V02UtterancePlanResult/V02UtterancePlanContractView"
        )
    return V02UtterancePlanConsumerView(
        plan_id=view.plan_id,
        plan_status=view.plan_status,
        partial_plan_only=view.partial_plan_only,
        clarification_first_required=view.clarification_first_required,
        protective_boundary_first=view.protective_boundary_first,
        unresolved_branching=view.unresolved_branching,
        blocked_expansion_count=view.blocked_expansion_count,
        protected_omission_count=view.protected_omission_count,
        mandatory_qualifier_ids=view.mandatory_qualifier_ids,
        plan_consumer_ready=view.plan_consumer_ready,
        ordering_consumer_ready=view.ordering_consumer_ready,
        realization_contract_consumer_ready=view.realization_contract_consumer_ready,
        restrictions=view.restrictions,
        reason="v02 utterance-plan consumer view",
    )


def require_v02_plan_consumer_ready(
    result_or_view: V02UtterancePlanResult | V02UtterancePlanContractView,
) -> V02UtterancePlanConsumerView:
    view = derive_v02_utterance_plan_consumer_view(result_or_view)
    if not view.plan_consumer_ready:
        raise PermissionError("v02 plan consumer requires typed utterance-plan state readiness")
    return view


def require_v02_ordering_consumer_ready(
    result_or_view: V02UtterancePlanResult | V02UtterancePlanContractView,
) -> V02UtterancePlanConsumerView:
    view = derive_v02_utterance_plan_consumer_view(result_or_view)
    if not view.ordering_consumer_ready:
        raise PermissionError("v02 ordering consumer requires typed segment ordering surface")
    return view


def require_v02_realization_contract_consumer_ready(
    result_or_view: V02UtterancePlanResult | V02UtterancePlanContractView,
) -> V02UtterancePlanConsumerView:
    view = derive_v02_utterance_plan_consumer_view(result_or_view)
    if not view.realization_contract_consumer_ready:
        raise PermissionError("v02 realization consumer requires ready bounded realization contract")
    return view
