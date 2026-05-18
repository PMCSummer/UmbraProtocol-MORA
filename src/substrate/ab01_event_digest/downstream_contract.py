from __future__ import annotations

from dataclasses import dataclass

from .models import AB1EventDigest, AB1EventDigestResult


@dataclass(frozen=True, slots=True)
class AB1DownstreamContract:
    digest_refs: tuple[str, ...]
    digest_count: int
    may_be_consumed_as_hypothesis: bool
    may_be_consumed_as_action_candidate: bool
    may_be_consumed_as_ap01_request: bool
    explicit_non_causal_closure: bool
    reason: str


def build_ab1_downstream_contract(result: AB1EventDigestResult) -> AB1DownstreamContract:
    digest_refs = tuple(item.event_id for item in result.digests)
    non_causal = all(item.explicit_non_causal_closure for item in result.digests) if result.digests else True
    return AB1DownstreamContract(
        digest_refs=digest_refs,
        digest_count=len(result.digests),
        may_be_consumed_as_hypothesis=False,
        may_be_consumed_as_action_candidate=False,
        may_be_consumed_as_ap01_request=False,
        explicit_non_causal_closure=non_causal,
        reason="ab1_digest_is_signal_compression_only_not_hypothesis_not_action_not_request",
    )
