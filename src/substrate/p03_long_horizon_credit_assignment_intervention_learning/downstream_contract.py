from __future__ import annotations

from dataclasses import dataclass

from substrate.p03_long_horizon_credit_assignment_intervention_learning.models import (
    P03CreditAssignmentResult,
)


@dataclass(frozen=True, slots=True)
class P03CreditAssignmentContractView:
    evaluated_episode_count: int
    credit_record_count: int
    no_update_count: int
    positive_credit_count: int
    negative_credit_count: int
    mixed_credit_count: int
    unresolved_credit_count: int
    confounded_credit_count: int
    guarded_update_count: int
    side_effect_dominant_count: int
    outcome_window_open_count: int
    credit_record_consumer_ready: bool
    no_update_consumer_ready: bool
    update_recommendation_consumer_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    attribution_classes: tuple[str, ...]
    recommendation_classes: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_p03_frontier_slice_only: bool
    scope_no_policy_mutation_authority: bool
    scope_no_scalar_reward_shortcut: bool
    scope_no_raw_approval_shortcut: bool
    scope_no_full_causal_discovery_claim: bool
    scope_no_map_wide_rollout_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class P03CreditAssignmentConsumerView:
    credit_record_count: int
    no_update_count: int
    positive_credit_count: int
    negative_credit_count: int
    mixed_credit_count: int
    unresolved_credit_count: int
    confounded_credit_count: int
    guarded_update_count: int
    side_effect_dominant_count: int
    outcome_window_open_count: int
    credit_record_consumer_ready: bool
    no_update_consumer_ready: bool
    update_recommendation_consumer_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_p03_credit_assignment_contract_view(
    result: P03CreditAssignmentResult,
) -> P03CreditAssignmentContractView:
    if not isinstance(result, P03CreditAssignmentResult):
        raise TypeError("derive_p03_credit_assignment_contract_view requires P03CreditAssignmentResult")
    telemetry = result.telemetry
    classes = tuple(item.attribution_class.value for item in result.record_set.credit_records)
    recommendations = tuple(
        item.recommendation.recommendation.value
        for item in (*result.record_set.credit_records, *result.record_set.no_update_records)
    )
    return P03CreditAssignmentContractView(
        evaluated_episode_count=telemetry.evaluated_episode_count,
        credit_record_count=telemetry.credit_record_count,
        no_update_count=telemetry.no_update_count,
        positive_credit_count=telemetry.positive_credit_count,
        negative_credit_count=telemetry.negative_credit_count,
        mixed_credit_count=telemetry.mixed_credit_count,
        unresolved_credit_count=telemetry.unresolved_credit_count,
        confounded_credit_count=telemetry.confounded_credit_count,
        guarded_update_count=telemetry.guarded_update_count,
        side_effect_dominant_count=telemetry.side_effect_dominant_count,
        outcome_window_open_count=telemetry.outcome_window_open_count,
        credit_record_consumer_ready=result.gate.credit_record_consumer_ready,
        no_update_consumer_ready=result.gate.no_update_consumer_ready,
        update_recommendation_consumer_ready=result.gate.update_recommendation_consumer_ready,
        downstream_consumer_ready=telemetry.downstream_consumer_ready,
        restrictions=result.gate.restrictions,
        attribution_classes=classes,
        recommendation_classes=recommendations,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_p03_frontier_slice_only=result.scope_marker.p03_frontier_slice_only,
        scope_no_policy_mutation_authority=result.scope_marker.no_policy_mutation_authority,
        scope_no_scalar_reward_shortcut=result.scope_marker.no_scalar_reward_shortcut,
        scope_no_raw_approval_shortcut=result.scope_marker.no_raw_approval_shortcut,
        scope_no_full_causal_discovery_claim=result.scope_marker.no_full_causal_discovery_claim,
        scope_no_map_wide_rollout_claim=result.scope_marker.no_map_wide_rollout_claim,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_p03_credit_assignment_consumer_view(
    result_or_view: P03CreditAssignmentResult | P03CreditAssignmentContractView,
) -> P03CreditAssignmentConsumerView:
    view = (
        derive_p03_credit_assignment_contract_view(result_or_view)
        if isinstance(result_or_view, P03CreditAssignmentResult)
        else result_or_view
    )
    if not isinstance(view, P03CreditAssignmentContractView):
        raise TypeError(
            "derive_p03_credit_assignment_consumer_view requires P03CreditAssignmentResult/P03CreditAssignmentContractView"
        )
    return P03CreditAssignmentConsumerView(
        credit_record_count=view.credit_record_count,
        no_update_count=view.no_update_count,
        positive_credit_count=view.positive_credit_count,
        negative_credit_count=view.negative_credit_count,
        mixed_credit_count=view.mixed_credit_count,
        unresolved_credit_count=view.unresolved_credit_count,
        confounded_credit_count=view.confounded_credit_count,
        guarded_update_count=view.guarded_update_count,
        side_effect_dominant_count=view.side_effect_dominant_count,
        outcome_window_open_count=view.outcome_window_open_count,
        credit_record_consumer_ready=view.credit_record_consumer_ready,
        no_update_consumer_ready=view.no_update_consumer_ready,
        update_recommendation_consumer_ready=view.update_recommendation_consumer_ready,
        downstream_consumer_ready=view.downstream_consumer_ready,
        restrictions=view.restrictions,
        reason="p03 credit assignment consumer view",
    )


def require_p03_credit_record_consumer(
    result_or_view: P03CreditAssignmentResult | P03CreditAssignmentContractView,
) -> P03CreditAssignmentConsumerView:
    view = derive_p03_credit_assignment_consumer_view(result_or_view)
    if not view.credit_record_consumer_ready:
        raise PermissionError("p03 credit-record consumer requires explicit credit records")
    return view


def require_p03_no_update_consumer(
    result_or_view: P03CreditAssignmentResult | P03CreditAssignmentContractView,
) -> P03CreditAssignmentConsumerView:
    view = derive_p03_credit_assignment_consumer_view(result_or_view)
    if not view.no_update_consumer_ready:
        raise PermissionError("p03 no-update consumer requires explicit no-update records")
    return view


def require_p03_update_recommendation_consumer(
    result_or_view: P03CreditAssignmentResult | P03CreditAssignmentContractView,
) -> P03CreditAssignmentConsumerView:
    view = derive_p03_credit_assignment_consumer_view(result_or_view)
    if not view.update_recommendation_consumer_ready:
        raise PermissionError(
            "p03 update recommendation consumer requires explicit recommendation records"
        )
    return view
