from __future__ import annotations

from .models import AB6CausalAttributionFrame, AB6CausalAttributionInput, AB6SupportStatus, AB6Telemetry


def build_ab6_telemetry(
    *,
    candidate_input: AB6CausalAttributionInput,
    frame: AB6CausalAttributionFrame | None,
    unsafe_basis_count: int,
) -> AB6Telemetry:
    candidates = frame.attribution_candidates if frame is not None else ()
    return AB6Telemetry(
        tick_ref=candidate_input.tick_ref,
        candidate_count=len(candidates),
        supported_count=sum(1 for item in candidates if item.support_status is AB6SupportStatus.SUPPORTED),
        weak_count=sum(1 for item in candidates if item.support_status is AB6SupportStatus.WEAK),
        blocked_count=sum(1 for item in candidates if item.support_status is AB6SupportStatus.BLOCKED),
        unresolved_count=sum(1 for item in candidates if item.support_status is AB6SupportStatus.UNRESOLVED),
        unsafe_basis_count=unsafe_basis_count,
        no_frame_count=1 if frame is None else 0,
        mixed_preserved_count=1 if frame is not None and frame.mixed_cause_preserved else 0,
        unknown_preserved_count=1 if frame is not None and frame.unknown_preserved else 0,
    )
