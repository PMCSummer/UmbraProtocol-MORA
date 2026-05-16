from __future__ import annotations

from experiments.symbolic_trade.clarification_policy import (
    ClarificationBudget,
    MissingInformationKind,
    ResponseReadinessStatus,
    evaluate_response_readiness,
)
from experiments.symbolic_trade.internal_state import build_self_state_probe_for_scenario
from experiments.symbolic_trade.runner import run_stage1_scenario
from experiments.symbolic_trade.transfer_affordance import infer_transfer_affordance_status


def _decision(scenario: str, *, budget: ClarificationBudget | None = None):
    stage1 = run_stage1_scenario(scenario, include_falsifiers=False)
    self_state = build_self_state_probe_for_scenario(scenario)
    affordance_status = infer_transfer_affordance_status(stage1.emitted_packets).value
    return evaluate_response_readiness(
        scenario_name=scenario,
        self_state=self_state,
        subject_visible_packets=stage1.emitted_packets,
        transfer_affordance_status=affordance_status,
        budget=budget or ClarificationBudget(),
    )


def test_stage4_readiness_mirrored_is_sufficient_without_clarification() -> None:
    decision = _decision("mirrored_resource_asymmetry")
    assert decision.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
    assert decision.clarification_target is None


def test_stage4_readiness_b_surplus_only_requires_targeted_need_clarification() -> None:
    decision = _decision("b_surplus_only")
    assert decision.status is ResponseReadinessStatus.CLARIFICATION_REQUIRED
    assert decision.clarification_target is MissingInformationKind.COUNTERPART_NEED_STATUS


def test_stage4_readiness_b_need_only_requires_targeted_resource_clarification() -> None:
    decision = _decision("b_need_only")
    assert decision.status is ResponseReadinessStatus.CLARIFICATION_REQUIRED
    assert decision.clarification_target is MissingInformationKind.COUNTERPART_RESOURCE_STATUS


def test_stage4_readiness_budget_exhaustion_routes_to_revalidation() -> None:
    exhausted = ClarificationBudget(
        max_total_queries=1,
        max_queries_per_field=1,
        consumed_total=1,
        consumed_by_field=((MissingInformationKind.COUNTERPART_NEED_STATUS, 1),),
    )
    decision = _decision("b_surplus_only", budget=exhausted)
    assert decision.status is ResponseReadinessStatus.REVALIDATION_REQUIRED
    assert decision.clarification_budget_exhausted is True


def test_stage4_readiness_blocked_aperture_is_blocked() -> None:
    decision = _decision("blocked_aperture")
    assert decision.status is ResponseReadinessStatus.BLOCKED


def test_stage4_readiness_noisy_signal_routes_to_revalidation() -> None:
    decision = _decision("noisy_signal")
    assert decision.status is ResponseReadinessStatus.REVALIDATION_REQUIRED
