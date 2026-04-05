from __future__ import annotations

from dataclasses import dataclass

from substrate.stream_kernel.models import (
    C01RestrictionCode,
    StreamKernelResult,
    StreamKernelState,
    StreamKernelUsabilityClass,
    StreamLinkDecision,
)
from substrate.stream_kernel.policy import evaluate_stream_kernel_downstream_gate


@dataclass(frozen=True, slots=True)
class StreamKernelContractView:
    stream_id: str
    sequence_index: int
    link_decision: StreamLinkDecision
    active_carryover_present: bool
    unresolved_anchor_present: bool
    pending_operation_present: bool
    interruption_present: bool
    stale_markers_present: bool
    continuation_expected: bool
    new_stream_expected: bool
    forced_release_present: bool
    continuity_confidence: float
    gate_accepted: bool
    restrictions: tuple[C01RestrictionCode, ...]
    usability_class: StreamKernelUsabilityClass
    requires_restrictions_read: bool
    reason: str


def derive_stream_kernel_contract_view(
    stream_kernel_result_or_state: StreamKernelResult | StreamKernelState,
) -> StreamKernelContractView:
    if isinstance(stream_kernel_result_or_state, StreamKernelResult):
        state = stream_kernel_result_or_state.state
    elif isinstance(stream_kernel_result_or_state, StreamKernelState):
        state = stream_kernel_result_or_state
    else:
        raise TypeError(
            "derive_stream_kernel_contract_view requires StreamKernelResult/StreamKernelState"
        )
    gate = evaluate_stream_kernel_downstream_gate(state)
    continuation_expected = state.link_decision in {
        StreamLinkDecision.CONTINUED_EXISTING_STREAM,
        StreamLinkDecision.RESUMED_INTERRUPTED_STREAM,
        StreamLinkDecision.OPENED_BRANCH,
        StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
    }
    new_stream_expected = state.link_decision in {
        StreamLinkDecision.STARTED_NEW_STREAM,
        StreamLinkDecision.FORCED_NEW_STREAM,
        StreamLinkDecision.AMBIGUOUS_LINK,
    }
    return StreamKernelContractView(
        stream_id=state.stream_id,
        sequence_index=state.sequence_index,
        link_decision=state.link_decision,
        active_carryover_present=bool(state.carryover_items),
        unresolved_anchor_present=bool(state.unresolved_anchors),
        pending_operation_present=bool(state.pending_operations),
        interruption_present=state.interruption_status.value != "none",
        stale_markers_present=bool(state.stale_markers),
        continuation_expected=continuation_expected,
        new_stream_expected=new_stream_expected,
        forced_release_present=state.link_decision == StreamLinkDecision.FORCED_RELEASE,
        continuity_confidence=state.continuity_confidence,
        gate_accepted=gate.accepted,
        restrictions=gate.restrictions,
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason="contract view requires typed continuity topology read, not narrative reconstruction",
    )


def choose_stream_execution_mode(
    stream_kernel_result_or_state: StreamKernelResult | StreamKernelState,
) -> str:
    view = derive_stream_kernel_contract_view(stream_kernel_result_or_state)
    if not view.gate_accepted or view.usability_class == StreamKernelUsabilityClass.BLOCKED:
        return "hold_or_repair"
    if view.forced_release_present:
        return "start_new_stream"
    if view.interruption_present and view.link_decision != StreamLinkDecision.RESUMED_INTERRUPTED_STREAM:
        return "resume_or_hold"
    if view.stale_markers_present and view.continuity_confidence < 0.75:
        return "resume_or_hold"
    if view.new_stream_expected:
        return "start_new_stream"
    if view.continuation_expected and view.active_carryover_present and view.continuity_confidence >= 0.75:
        return "continue_existing_stream"
    if view.continuation_expected and view.active_carryover_present:
        return "continue_with_limits"
    if view.interruption_present:
        return "resume_or_hold"
    return "idle"
