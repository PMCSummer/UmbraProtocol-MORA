from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reviewer.config import ReviewerPipelineConfig


@dataclass(frozen=True, slots=True)
class TriageDecision:
    action: str  # close | escalate | freeze
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

    if overall in {"likely_problematic"} or priority == "high":
        if tier_name == "tier1" and next_tier is not None:
            return TriageDecision(
                action="escalate",
                reason="tier1 high-risk signal requires stronger model review",
                next_tier=next_tier,
            )
        if (
            tier_name == "tier2"
            and next_tier is not None
            and config.escalation.second_opinion_on_high_priority
        ):
            return TriageDecision(
                action="escalate",
                reason="high priority routed for second opinion",
                next_tier=next_tier,
            )
        return TriageDecision(action="freeze", reason="high-priority suspicious case")

    if overall == "suspicious_but_inconclusive":
        if (
            next_tier is not None
            and confidence <= (
                config.escalation.tier1_escalate_confidence_max
                if tier_name == "tier1"
                else config.escalation.tier2_second_opinion_confidence_max
            )
        ):
            return TriageDecision(
                action="escalate",
                reason="suspicious and low-confidence review requires escalation",
                next_tier=next_tier,
            )
        return TriageDecision(action="freeze", reason="suspicious case kept for human review")

    if overall == "insufficient_evidence":
        if next_tier is not None:
            return TriageDecision(
                action="escalate",
                reason="insufficient evidence routed upward",
                next_tier=next_tier,
            )
        return TriageDecision(action="freeze", reason="insufficient evidence at top tier")

    if overall == "mostly_coherent_with_questions" and priority in {"medium", "high"} and next_tier is not None:
        return TriageDecision(
            action="escalate",
            reason="questions with non-low priority escalated",
            next_tier=next_tier,
        )

    return TriageDecision(action="close", reason="coherent enough for compact closure")

