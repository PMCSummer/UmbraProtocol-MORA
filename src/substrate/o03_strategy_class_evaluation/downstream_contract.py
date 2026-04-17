from __future__ import annotations

from dataclasses import dataclass

from substrate.o03_strategy_class_evaluation.models import (
    O03HiddenDivergenceBand,
    O03StrategyClass,
    O03StrategyEvaluationResult,
)


@dataclass(frozen=True, slots=True)
class O03StrategyContractView:
    strategy_id: str
    candidate_move_id: str
    strategy_class: O03StrategyClass
    hidden_divergence_band: O03HiddenDivergenceBand
    no_safe_classification: bool
    strategy_underconstrained: bool
    concealed_state_divergence_required: bool
    high_local_gain_but_high_entropy: bool
    strategy_contract_consumer_ready: bool
    cooperative_selection_consumer_ready: bool
    transparency_preserving_consumer_ready: bool
    exploitative_move_block_required: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_o03_first_slice_only: bool
    scope_o04_not_implemented: bool
    scope_r05_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class O03StrategyConsumerView:
    strategy_id: str
    cooperative_default_preferred: bool
    transparency_increase_required: bool
    clarification_required: bool
    block_exploitative_move_required: bool
    strategy_contract_consumer_ready: bool
    cooperative_selection_consumer_ready: bool
    transparency_preserving_consumer_ready: bool
    do_not_collapse_to_politeness: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_o03_strategy_contract_view(
    result: O03StrategyEvaluationResult,
) -> O03StrategyContractView:
    if not isinstance(result, O03StrategyEvaluationResult):
        raise TypeError(
            "derive_o03_strategy_contract_view requires O03StrategyEvaluationResult"
        )
    return O03StrategyContractView(
        strategy_id=result.state.strategy_id,
        candidate_move_id=result.state.candidate_move_id,
        strategy_class=result.state.strategy_class,
        hidden_divergence_band=result.state.hidden_divergence_band,
        no_safe_classification=result.state.no_safe_classification,
        strategy_underconstrained=result.state.strategy_underconstrained,
        concealed_state_divergence_required=result.state.concealed_state_divergence_required,
        high_local_gain_but_high_entropy=result.state.high_local_gain_but_high_entropy,
        strategy_contract_consumer_ready=result.gate.strategy_contract_consumer_ready,
        cooperative_selection_consumer_ready=result.gate.cooperative_selection_consumer_ready,
        transparency_preserving_consumer_ready=result.gate.transparency_preserving_consumer_ready,
        exploitative_move_block_required=result.gate.exploitative_move_block_required,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_o03_first_slice_only=result.scope_marker.o03_first_slice_only,
        scope_o04_not_implemented=result.scope_marker.o04_not_implemented,
        scope_r05_not_implemented=result.scope_marker.r05_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_o03_strategy_consumer_view(
    result_or_view: O03StrategyEvaluationResult | O03StrategyContractView,
) -> O03StrategyConsumerView:
    view = (
        derive_o03_strategy_contract_view(result_or_view)
        if isinstance(result_or_view, O03StrategyEvaluationResult)
        else result_or_view
    )
    if not isinstance(view, O03StrategyContractView):
        raise TypeError(
            "derive_o03_strategy_consumer_view requires O03StrategyEvaluationResult/O03StrategyContractView"
        )
    cooperative_default_preferred = bool(
        view.strategy_class
        in {
            O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED,
            O03StrategyClass.NO_SAFE_CLASSIFICATION,
            O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY,
        }
        or view.strategy_underconstrained
    )
    transparency_increase_required = bool(
        view.hidden_divergence_band is O03HiddenDivergenceBand.HIGH
        or view.concealed_state_divergence_required
        or view.no_safe_classification
        or view.strategy_underconstrained
        or not view.transparency_preserving_consumer_ready
    )
    clarification_required = bool(
        cooperative_default_preferred
        or view.no_safe_classification
        or view.strategy_underconstrained
        or "strategy_underconstrained" in view.restrictions
    )
    do_not_collapse_to_politeness = bool(
        transparency_increase_required
        or view.concealed_state_divergence_required
        or view.high_local_gain_but_high_entropy
    )
    return O03StrategyConsumerView(
        strategy_id=view.strategy_id,
        cooperative_default_preferred=cooperative_default_preferred,
        transparency_increase_required=transparency_increase_required,
        clarification_required=clarification_required,
        block_exploitative_move_required=view.exploitative_move_block_required,
        strategy_contract_consumer_ready=view.strategy_contract_consumer_ready,
        cooperative_selection_consumer_ready=view.cooperative_selection_consumer_ready,
        transparency_preserving_consumer_ready=view.transparency_preserving_consumer_ready,
        do_not_collapse_to_politeness=do_not_collapse_to_politeness,
        restrictions=view.restrictions,
        reason="o03 strategy consumer view",
    )


def require_o03_strategy_contract_consumer_ready(
    result_or_view: O03StrategyEvaluationResult | O03StrategyContractView,
) -> O03StrategyConsumerView:
    view = derive_o03_strategy_consumer_view(result_or_view)
    if not view.strategy_contract_consumer_ready:
        raise PermissionError(
            "o03 strategy consumer requires bounded strategy classification with lawful confidence"
        )
    return view


def require_o03_cooperative_selection_consumer_ready(
    result_or_view: O03StrategyEvaluationResult | O03StrategyContractView,
) -> O03StrategyConsumerView:
    view = derive_o03_strategy_consumer_view(result_or_view)
    if not view.cooperative_selection_consumer_ready:
        raise PermissionError(
            "o03 cooperative selection consumer requires non-exploitative strategy class readiness"
        )
    return view


def require_o03_transparency_preserving_consumer_ready(
    result_or_view: O03StrategyEvaluationResult | O03StrategyContractView,
) -> O03StrategyConsumerView:
    view = derive_o03_strategy_consumer_view(result_or_view)
    if not view.transparency_preserving_consumer_ready:
        raise PermissionError(
            "o03 transparency-preserving consumer requires explicit bounded disclosure posture"
        )
    return view
