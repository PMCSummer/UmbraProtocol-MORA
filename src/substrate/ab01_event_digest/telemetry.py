from __future__ import annotations

from .models import AB1DigestStatus, AB1EventDigest, AB1EventDigestInput, AB1Telemetry


def build_ab1_telemetry(
    *,
    candidate_input: AB1EventDigestInput,
    digests: tuple[AB1EventDigest, ...],
    unsafe_basis_count: int,
) -> AB1Telemetry:
    strong_count = sum(1 for item in digests if item.digest_status is AB1DigestStatus.STRONG)
    weak_count = sum(1 for item in digests if item.digest_status is AB1DigestStatus.WEAK)
    blocked_count = sum(1 for item in digests if item.digest_status is AB1DigestStatus.BLOCKED)
    return AB1Telemetry(
        tick_ref=candidate_input.tick_ref,
        digest_count=len(digests),
        strong_count=strong_count,
        weak_count=weak_count,
        blocked_count=blocked_count,
        unsafe_basis_count=unsafe_basis_count,
        no_digest_count=1 if not digests else 0,
        hidden_eval_excluded=candidate_input.hidden_eval_excluded,
        scenario_label_excluded=candidate_input.scenario_label_excluded,
    )
