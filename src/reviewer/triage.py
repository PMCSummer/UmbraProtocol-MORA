from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reviewer.config import ReviewerPipelineConfig


@dataclass(frozen=True, slots=True)
class TriageDecision:
    action: str  # close | behavioral_review | infra_review | escalate
    reason: str
    next_tier: str | None = None


def decide_triage(
    *,
    review_json: dict[str, Any],
    tier_name: str,
    config: ReviewerPipelineConfig,
) -> TriageDecision:
    overall = str(review_json.get("overall_reading", "insufficient_evidence"))
    priority = str(review_json.get("human_review_priority", "high"))
    confidence = float(review_json.get("confidence", 0.0))

    enabled_tiers = [
        name
        for name in ("tier1", "tier2", "tier3")
        if config.tiers.get(name) is not None and config.tiers[name].enabled
    ]
    current_idx = enabled_tiers.index(tier_name) if tier_name in enabled_tiers else -1
    next_tier = enabled_tiers[current_idx + 1] if 0 <= current_idx < len(enabled_tiers) - 1 else None

    if overall in {"coherent_bounded_caution", "coherent_abstention_or_revalidation"}:
        return TriageDecision(action="close", reason="coherent bounded behavior")

    if overall == "plausible_but_needs_review":
        if priority in {"medium", "high"}:
            return TriageDecision(
                action="behavioral_review",
                reason="plausible but requires behavioral inspection",
            )
        return TriageDecision(action="close", reason="plausible low-priority case")

    if overall == "likely_behavioral_problem":
        if next_tier is not None and confidence <= config.escalation.tier1_escalate_confidence_max:
            return TriageDecision(
                action="escalate",
                reason="likely behavioral problem with low confidence",
                next_tier=next_tier,
            )
        return TriageDecision(
            action="behavioral_review",
            reason="likely behavioral problem",
        )

    if overall == "insufficient_evidence":
        if priority == "low":
            return TriageDecision(
                action="close",
                reason="insufficient evidence but low priority",
            )
        return TriageDecision(
            action="infra_review",
            reason="insufficient evidence requires infra-level review",
        )

    return TriageDecision(action="close", reason="default close")
