from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reviewer.config import ReviewerPipelineConfig


@dataclass(frozen=True, slots=True)
class TriageDecision:
    action: str  # close | behavioral_review | infra_review | escalate
    reason: str
    normalized_priority: str
    next_tier: str | None = None


_MISMATCH_SIGNAL_CODES = {
    "causal_transition_mismatch",
    "unexpected_mode_shift",
}
_BENIGN_BOUNDED_SIGNAL_CODES = {
    "t03_honest_nonconvergence",
    "t04_not_reportable",
    "bounded_revalidation_required",
    "subject_idle_continuation",
    "world_basis_missing",
    "ownership_confidence_low",
    "memory_claim_denied",
    "narrative_claim_denied",
    "mode_safe_idle_selected",
    "validity_reuse_only",
    "bounded_repair_required",
    "subject_abstention_revalidation",
}
_DEFAULT_UNCLEAR_MODULES = {
    "t03_hypothesis_competition",
    "bounded_outcome_resolution",
    "subject_tick",
}


def _severity_score(value: str) -> int:
    if value == "high":
        return 3
    if value == "medium":
        return 2
    return 1


def _evidence(review_json: dict[str, Any]) -> dict[str, int]:
    suspicious = review_json.get("suspicious_segments")
    gaps = review_json.get("likely_observability_gaps")
    suspicious_list = suspicious if isinstance(suspicious, list) else []
    gaps_list = gaps if isinstance(gaps, list) else []

    mismatch_count = 0
    benign_only_count = 0
    high_count = 0
    weighted_score = 0

    for item in suspicious_list:
        if not isinstance(item, dict):
            continue
        signal_code = str(item.get("signal_code", ""))
        severity = str(item.get("severity", "low"))
        sev_score = _severity_score(severity)
        weighted_score += sev_score
        if severity == "high":
            high_count += 1
        if signal_code in _MISMATCH_SIGNAL_CODES:
            mismatch_count += 1
            weighted_score += 2
        elif signal_code in _BENIGN_BOUNDED_SIGNAL_CODES:
            benign_only_count += 1
        else:
            weighted_score += 1

    non_default_gap_count = 0
    unclear_default_count = 0
    for item in gaps_list:
        if not isinstance(item, dict):
            continue
        gap_code = str(item.get("gap_code", ""))
        module_or_transition = str(item.get("module_or_transition", ""))
        if gap_code == "unclear_resolution_step" and module_or_transition in _DEFAULT_UNCLEAR_MODULES:
            unclear_default_count += 1
            continue
        if gap_code:
            non_default_gap_count += 1
            weighted_score += 1

    non_benign_signal_count = max(0, len(suspicious_list) - benign_only_count)
    return {
        "mismatch_count": mismatch_count,
        "benign_only_count": benign_only_count,
        "high_count": high_count,
        "weighted_score": weighted_score,
        "non_default_gap_count": non_default_gap_count,
        "unclear_default_count": unclear_default_count,
        "total_signals": len(suspicious_list),
        "non_benign_signal_count": non_benign_signal_count,
    }


def normalize_human_review_priority(review_json: dict[str, Any]) -> str:
    overall = str(review_json.get("overall_reading", "insufficient_evidence"))
    evidence = _evidence(review_json)
    mismatch = evidence["mismatch_count"]
    score = evidence["weighted_score"]
    non_benign = evidence["non_benign_signal_count"]
    high_count = evidence["high_count"]
    non_default_gaps = evidence["non_default_gap_count"]

    if overall == "coherent_bounded_caution":
        if mismatch >= 2 and score >= 8:
            return "high"
        if mismatch >= 1 or (non_benign >= 1 and non_default_gaps >= 1):
            return "medium"
        return "low"

    if overall == "coherent_abstention_or_revalidation":
        if mismatch >= 2 and score >= 8:
            return "high"
        if mismatch >= 1 or non_benign >= 1 or non_default_gaps >= 2:
            return "medium"
        return "low"

    if overall == "plausible_but_needs_review":
        if mismatch >= 2 or (mismatch >= 1 and (high_count >= 1 or score >= 7)):
            return "high"
        if mismatch >= 1 or non_benign >= 2 or non_default_gaps >= 2:
            return "medium"
        if score <= 2 and non_default_gaps == 0:
            return "low"
        return "medium"

    if overall == "likely_behavioral_problem":
        if mismatch >= 1 and (high_count >= 1 or score >= 7):
            return "high"
        return "medium"

    if overall == "insufficient_evidence":
        if mismatch >= 1 and non_default_gaps >= 2:
            return "medium"
        return "low"

    return "medium"


def _plausible_requires_behavioral_review(review_json: dict[str, Any]) -> bool:
    evidence = _evidence(review_json)
    mismatch = evidence["mismatch_count"]
    non_benign = evidence["non_benign_signal_count"]
    non_default_gaps = evidence["non_default_gap_count"]
    score = evidence["weighted_score"]
    total_signals = evidence["total_signals"]
    benign_only = evidence["benign_only_count"]

    if mismatch >= 1:
        return True
    if non_benign >= 2 and score >= 5:
        return True
    if non_default_gaps >= 2 and score >= 4:
        return True
    # One mild bounded signal under weak basis is not enough for behavioral routing.
    if total_signals == 1 and benign_only == 1 and non_default_gaps == 0:
        return False
    return score >= 6 and (non_benign >= 1 or non_default_gaps >= 1)


def decide_triage(
    *,
    review_json: dict[str, Any],
    tier_name: str,
    config: ReviewerPipelineConfig,
) -> TriageDecision:
    overall = str(review_json.get("overall_reading", "insufficient_evidence"))
    normalized_priority = normalize_human_review_priority(review_json)
    confidence = float(review_json.get("confidence", 0.0))

    enabled_tiers = [
        name
        for name in ("tier1", "tier2", "tier3")
        if config.tiers.get(name) is not None and config.tiers[name].enabled
    ]
    current_idx = enabled_tiers.index(tier_name) if tier_name in enabled_tiers else -1
    next_tier = enabled_tiers[current_idx + 1] if 0 <= current_idx < len(enabled_tiers) - 1 else None

    if overall in {"coherent_bounded_caution", "coherent_abstention_or_revalidation"}:
        return TriageDecision(
            action="close",
            reason="coherent bounded behavior",
            normalized_priority=normalized_priority,
        )

    if overall == "plausible_but_needs_review":
        if _plausible_requires_behavioral_review(review_json):
            return TriageDecision(
                action="behavioral_review",
                reason="plausible but requires behavioral inspection",
                normalized_priority=normalized_priority,
            )
        return TriageDecision(
            action="close",
            reason="plausible but weak-basis bounded pattern",
            normalized_priority=normalized_priority,
        )

    if overall == "likely_behavioral_problem":
        if (
            next_tier is not None
            and confidence <= config.escalation.tier1_escalate_confidence_max
            and normalized_priority == "high"
        ):
            return TriageDecision(
                action="escalate",
                reason="likely behavioral problem with low confidence",
                normalized_priority=normalized_priority,
                next_tier=next_tier,
            )
        return TriageDecision(
            action="behavioral_review",
            reason="likely behavioral problem",
            normalized_priority=normalized_priority,
        )

    if overall == "insufficient_evidence":
        if normalized_priority == "low":
            return TriageDecision(
                action="close",
                reason="insufficient evidence but low priority",
                normalized_priority=normalized_priority,
            )
        return TriageDecision(
            action="infra_review",
            reason="insufficient evidence requires infra-level review",
            normalized_priority=normalized_priority,
        )

    return TriageDecision(
        action="close",
        reason="default close",
        normalized_priority=normalized_priority,
    )
