from __future__ import annotations

from dataclasses import dataclass

from substrate.stream_diversification.models import (
    AlternativePathClass,
    C03RestrictionCode,
    DiversificationDecisionStatus,
    StreamDiversificationResult,
    StreamDiversificationState,
    StreamDiversificationUsabilityClass,
)
from substrate.stream_diversification.policy import (
    evaluate_stream_diversification_downstream_gate,
)


@dataclass(frozen=True, slots=True)
class StreamDiversificationContractView:
    diversification_id: str
    stream_id: str
    decision_status: DiversificationDecisionStatus
    diversification_pressure: float
    stagnation_signature_present: bool
    repeat_justification_required: bool
    protected_recurrence_present: bool
    no_safe_diversification: bool
    diversification_conflict_with_survival: bool
    low_confidence_stagnation: bool
    allowed_alternative_classes: tuple[AlternativePathClass, ...]
    actionable_alternative_classes: tuple[AlternativePathClass, ...]
    gate_accepted: bool
    restrictions: tuple[C03RestrictionCode, ...]
    usability_class: StreamDiversificationUsabilityClass
    requires_restrictions_read: bool
    reason: str


def derive_stream_diversification_contract_view(
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
) -> StreamDiversificationContractView:
    if isinstance(diversification_state_or_result, StreamDiversificationResult):
        state = diversification_state_or_result.state
    elif isinstance(diversification_state_or_result, StreamDiversificationState):
        state = diversification_state_or_result
    else:
        raise TypeError(
            "derive_stream_diversification_contract_view requires StreamDiversificationState/StreamDiversificationResult"
        )
    gate = evaluate_stream_diversification_downstream_gate(state)
    return StreamDiversificationContractView(
        diversification_id=state.diversification_id,
        stream_id=state.stream_id,
        decision_status=state.decision_status,
        diversification_pressure=state.diversification_pressure,
        stagnation_signature_present=bool(state.stagnation_signatures),
        repeat_justification_required=bool(state.repeat_requires_justification_for),
        protected_recurrence_present=bool(state.protected_recurrence_classes),
        no_safe_diversification=state.no_safe_diversification,
        diversification_conflict_with_survival=state.diversification_conflict_with_survival,
        low_confidence_stagnation=state.low_confidence_stagnation,
        allowed_alternative_classes=state.allowed_alternative_classes,
        actionable_alternative_classes=state.actionable_alternative_classes,
        gate_accepted=gate.accepted,
        restrictions=gate.restrictions,
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason="contract requires structural stagnation and repeat-justification surfaces to be read",
    )


def choose_diversification_execution_mode(
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
) -> str:
    view = derive_stream_diversification_contract_view(diversification_state_or_result)
    if not view.gate_accepted or view.usability_class == StreamDiversificationUsabilityClass.BLOCKED:
        return "hold_current_route"
    if view.diversification_conflict_with_survival:
        return "continue_with_protection"
    if view.no_safe_diversification:
        return "request_additional_basis"
    if (
        view.decision_status == DiversificationDecisionStatus.ALTERNATIVE_PATH_OPENING
        and view.actionable_alternative_classes
        and view.diversification_pressure >= 0.55
    ):
        return "open_alternative_paths"
    if view.repeat_justification_required and not view.allowed_alternative_classes:
        return "request_additional_basis"
    if (
        view.stagnation_signature_present
        and view.diversification_pressure >= 0.4
        and not view.actionable_alternative_classes
    ):
        return "monitor_for_stagnation"
    return "continue_current_route"


def select_alternative_path_candidates(
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
) -> tuple[str, ...]:
    if isinstance(diversification_state_or_result, StreamDiversificationResult):
        state = diversification_state_or_result.state
    elif isinstance(diversification_state_or_result, StreamDiversificationState):
        state = diversification_state_or_result
    else:
        raise TypeError(
            "select_alternative_path_candidates requires StreamDiversificationState/StreamDiversificationResult"
        )
    gate = evaluate_stream_diversification_downstream_gate(state)
    if not gate.accepted:
        return ()
    if state.no_safe_diversification or state.diversification_conflict_with_survival:
        return ()
    return tuple(path_class.value for path_class in state.actionable_alternative_classes)
