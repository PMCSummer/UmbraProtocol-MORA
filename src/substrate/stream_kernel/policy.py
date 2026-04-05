from __future__ import annotations

from substrate.stream_kernel.models import (
    C01RestrictionCode,
    StreamKernelGateDecision,
    StreamKernelState,
    StreamKernelUsabilityClass,
    StreamLinkDecision,
)


def evaluate_stream_kernel_downstream_gate(
    stream_state_or_result: StreamKernelState | object,
) -> StreamKernelGateDecision:
    state = getattr(stream_state_or_result, "state", stream_state_or_result)
    if not isinstance(state, StreamKernelState):
        raise TypeError(
            "evaluate_stream_kernel_downstream_gate requires StreamKernelState/StreamKernelResult"
        )

    restrictions: list[C01RestrictionCode] = [
        C01RestrictionCode.STREAM_STATE_MUST_BE_READ,
        C01RestrictionCode.CARRYOVER_ITEMS_MUST_BE_READ,
        C01RestrictionCode.UNRESOLVED_ANCHORS_MUST_BE_READ,
        C01RestrictionCode.PENDING_OPERATIONS_MUST_BE_READ,
        C01RestrictionCode.INTERRUPTION_STATUS_MUST_BE_READ,
        C01RestrictionCode.BRANCH_STATUS_MUST_BE_READ,
        C01RestrictionCode.DECAY_STATE_MUST_BE_READ,
        C01RestrictionCode.STALE_MARKERS_MUST_BE_READ,
        C01RestrictionCode.CONTINUITY_NOT_TRANSCRIPT_REPLAY,
        C01RestrictionCode.CONTINUITY_NOT_MEMORY_RETRIEVAL,
        C01RestrictionCode.CONTINUITY_NOT_PLANNER_HIDDEN_FLAG,
        C01RestrictionCode.STREAM_OBJECT_PRESENCE_NOT_CONTINUITY,
    ]
    usability = StreamKernelUsabilityClass.USABLE_BOUNDED
    accepted = True
    reason = "typed stream kernel state available for bounded continuity carry-over"

    if state.link_decision == StreamLinkDecision.AMBIGUOUS_LINK:
        restrictions.append(C01RestrictionCode.AMBIGUOUS_LINK_MUST_NOT_BE_LAUNDERED)
        usability = StreamKernelUsabilityClass.DEGRADED_BOUNDED
        reason = "ambiguous continuity link forces degraded downstream interpretation"
    elif state.link_decision == StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION:
        restrictions.append(
            C01RestrictionCode.LOW_CONFIDENCE_CONTINUATION_MUST_BE_READ
        )
        usability = StreamKernelUsabilityClass.DEGRADED_BOUNDED
        reason = "low-confidence continuation requires caution-aware downstream reading"
    elif state.link_decision == StreamLinkDecision.FORCED_NEW_STREAM:
        restrictions.append(C01RestrictionCode.FORCED_NEW_STREAM_MUST_BE_READ)
        usability = StreamKernelUsabilityClass.DEGRADED_BOUNDED
        reason = "forced new stream prevents silent continuity carry-over"
    elif state.link_decision == StreamLinkDecision.FORCED_RELEASE:
        restrictions.append(C01RestrictionCode.FORCED_RELEASE_MUST_BE_READ)
        usability = StreamKernelUsabilityClass.DEGRADED_BOUNDED
        reason = "forced release ends prior stream authority for carry-over"

    if state.branch_status.value == "branch_conflict":
        restrictions.append(C01RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        accepted = False
        usability = StreamKernelUsabilityClass.BLOCKED
        reason = "branch conflict blocks strong downstream continuity claim"

    return StreamKernelGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.stream_id}@{state.sequence_index}",
    )
