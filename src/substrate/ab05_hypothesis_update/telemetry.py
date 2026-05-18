from __future__ import annotations

from .models import (
    AB5DeltaKind,
    AB5HypothesisSupportDelta,
    AB5HypothesisUpdateInput,
    AB5Telemetry,
)


def build_ab5_telemetry(
    *,
    candidate_input: AB5HypothesisUpdateInput,
    support_deltas: tuple[AB5HypothesisSupportDelta, ...],
    unsafe_basis_count: int,
    closure_allowed: bool,
) -> AB5Telemetry:
    return AB5Telemetry(
        tick_ref=candidate_input.tick_ref,
        hypothesis_count=len(support_deltas),
        support_delta_count=len(support_deltas),
        strengthened_count=sum(1 for item in support_deltas if item.delta_kind is AB5DeltaKind.INCREASE),
        weakened_count=sum(1 for item in support_deltas if item.delta_kind is AB5DeltaKind.DECREASE),
        disconfirmed_count=sum(1 for item in support_deltas if item.delta_kind is AB5DeltaKind.DISCONFIRM),
        unresolved_count=sum(1 for item in support_deltas if item.delta_kind is AB5DeltaKind.UNRESOLVED),
        blocked_count=sum(1 for item in support_deltas if item.delta_kind is AB5DeltaKind.BLOCKED),
        unchanged_count=sum(1 for item in support_deltas if item.delta_kind is AB5DeltaKind.UNCHANGED),
        unsafe_basis_count=unsafe_basis_count,
        no_update_count=1 if not support_deltas else 0,
        closure_allowed_count=1 if closure_allowed else 0,
    )
