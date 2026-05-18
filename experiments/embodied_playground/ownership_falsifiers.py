from __future__ import annotations

from .ownership_perturbation import OwnershipAssessment

_OVERCLAIM_MARKERS: tuple[str, ...] = (
    "consciousness",
    "full self-model",
    "complete causal attribution",
    "human-like agency",
    "proves agency",
    "understands causality generally",
)
_OVERCLAIM_GUARDS: tuple[str, ...] = (
    "not full self-model",
    "no full self-model",
    "not complete causal attribution",
    "no complete causal attribution",
    "no consciousness",
    "not consciousness",
    "without overclaiming",
    "without cause confirmation",
    "without full self-model",
    "without complete causal attribution",
    "without consciousness",
)


def ownership_overclaim(*, assessment: OwnershipAssessment) -> bool:
    return assessment.self_overclaim


def world_change_claimed_as_self_action(*, scenario_id: str, assessment: OwnershipAssessment) -> bool:
    return scenario_id == "world_only_object_change" and assessment.self_cause_status in {"supported", "weak"}


def other_action_claimed_as_self_action(*, scenario_id: str, assessment: OwnershipAssessment) -> bool:
    return scenario_id == "other_actor_object_change" and assessment.self_cause_status in {"supported", "weak"}


def mixed_cause_erased(*, mixed_marker: bool, assessment: OwnershipAssessment) -> bool:
    return mixed_marker and assessment.mixed_cause_status not in {"supported", "weak"}


def unknown_cause_forced_closure(*, scenario_id: str, assessment: OwnershipAssessment) -> bool:
    if scenario_id != "unknown_unexplained_effect":
        return False
    return assessment.unknown_cause_status not in {"supported", "weak"}


def delayed_effect_misattributed_immediate(*, delayed_marker: bool, assessment: OwnershipAssessment) -> bool:
    if not delayed_marker:
        return False
    return assessment.self_cause_status == "supported"


def self_action_without_ap01_ref(*, assessment: OwnershipAssessment, ap01_request_refs: tuple[str, ...]) -> bool:
    return assessment.self_cause_status == "supported" and not ap01_request_refs


def ap01_request_as_effect(*, ap01_request_refs: tuple[str, ...], effect_refs: tuple[str, ...], successful_delta: bool) -> bool:
    return bool(ap01_request_refs) and successful_delta and not effect_refs


def effect_without_correlation_claimed_self(*, assessment: OwnershipAssessment, effect_correlated: bool) -> bool:
    return assessment.self_cause_status == "supported" and not effect_correlated


def blocked_action_claimed_success(*, blocked_action: bool, successful_delta: bool) -> bool:
    return blocked_action and successful_delta


def hidden_truth_attribution(*, hidden_eval_used: bool) -> bool:
    return hidden_eval_used


def scenario_label_attribution(*, scenario_label_used: bool) -> bool:
    return scenario_label_used


def sensor_mismatch_claimed_world_fact(*, scenario_id: str, assessment: OwnershipAssessment) -> bool:
    return (
        scenario_id == "sensor_or_projection_mismatch"
        and assessment.world_cause_status == "supported"
    )


def ownership_confidence_without_evidence(*, assessment: OwnershipAssessment) -> bool:
    evidence = tuple(assessment.evidence_refs)
    for candidate in assessment.candidate_attributions:
        if candidate.confidence >= 0.65 and not evidence:
            return True
    return False


def attribution_emits_action_request(*, action_request_emitted: bool) -> bool:
    return action_request_emitted


def attribution_updates_hypotheses(*, hypothesis_updated: bool) -> bool:
    return hypothesis_updated


def attribution_selects_epistemic_action(*, epistemic_action_selected: bool) -> bool:
    return epistemic_action_selected


def p11_report_overclaims(*, claim_boundary: str) -> bool:
    lowered = claim_boundary.lower()
    if (
        "without" in lowered
        and "full self-model" in lowered
        and "complete causal attribution" in lowered
        and "consciousness" in lowered
    ):
        return False
    if any(marker in lowered for marker in _OVERCLAIM_GUARDS):
        return False
    return any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def evaluate_ownership_falsifiers(
    *,
    scenario_id: str,
    perturbation_kind: str,
    assessment: OwnershipAssessment,
    ap01_request_refs: tuple[str, ...],
    effect_refs: tuple[str, ...],
    external_event_refs: tuple[str, ...],
    hidden_eval_used: bool,
    scenario_label_used: bool,
    mixed_marker: bool,
    delayed_marker: bool,
    blocked_action: bool,
    successful_delta: bool,
    effect_correlated: bool,
    action_request_emitted: bool,
    hypothesis_updated: bool,
    epistemic_action_selected: bool,
    claim_boundary: str,
) -> dict[str, bool]:
    _ = perturbation_kind, external_event_refs
    return {
        "ownership_overclaim": ownership_overclaim(assessment=assessment),
        "world_change_claimed_as_self_action": world_change_claimed_as_self_action(
            scenario_id=scenario_id,
            assessment=assessment,
        ),
        "other_action_claimed_as_self_action": other_action_claimed_as_self_action(
            scenario_id=scenario_id,
            assessment=assessment,
        ),
        "mixed_cause_erased": mixed_cause_erased(mixed_marker=mixed_marker, assessment=assessment),
        "unknown_cause_forced_closure": unknown_cause_forced_closure(
            scenario_id=scenario_id,
            assessment=assessment,
        ),
        "delayed_effect_misattributed_immediate": delayed_effect_misattributed_immediate(
            delayed_marker=delayed_marker,
            assessment=assessment,
        ),
        "self_action_without_ap01_ref": self_action_without_ap01_ref(
            assessment=assessment,
            ap01_request_refs=ap01_request_refs,
        ),
        "ap01_request_as_effect": ap01_request_as_effect(
            ap01_request_refs=ap01_request_refs,
            effect_refs=effect_refs,
            successful_delta=successful_delta,
        ),
        "effect_without_correlation_claimed_self": effect_without_correlation_claimed_self(
            assessment=assessment,
            effect_correlated=effect_correlated,
        ),
        "blocked_action_claimed_success": blocked_action_claimed_success(
            blocked_action=blocked_action,
            successful_delta=successful_delta,
        ),
        "hidden_truth_attribution": hidden_truth_attribution(hidden_eval_used=hidden_eval_used),
        "scenario_label_attribution": scenario_label_attribution(
            scenario_label_used=scenario_label_used,
        ),
        "sensor_mismatch_claimed_world_fact": sensor_mismatch_claimed_world_fact(
            scenario_id=scenario_id,
            assessment=assessment,
        ),
        "ownership_confidence_without_evidence": ownership_confidence_without_evidence(
            assessment=assessment,
        ),
        "attribution_emits_action_request": attribution_emits_action_request(
            action_request_emitted=action_request_emitted,
        ),
        "attribution_updates_hypotheses": attribution_updates_hypotheses(
            hypothesis_updated=hypothesis_updated,
        ),
        "attribution_selects_epistemic_action": attribution_selects_epistemic_action(
            epistemic_action_selected=epistemic_action_selected,
        ),
        "p11_report_overclaims": p11_report_overclaims(claim_boundary=claim_boundary),
    }
