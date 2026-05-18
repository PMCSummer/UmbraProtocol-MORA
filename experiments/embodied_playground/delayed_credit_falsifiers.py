from __future__ import annotations

from .delayed_credit_learning import DelayedCreditLearningRun

_OVERCLAIM_MARKERS: tuple[str, ...] = (
    "mature recipe",
    "true cause learned",
    "stable world model learned",
    "scientific reasoning",
    "consciousness",
    "general intelligence",
)
_OVERCLAIM_GUARDS: tuple[str, ...] = (
    "not recipe learning",
    "no mature recipe learning",
    "without mature schema",
    "without true cause",
    "no consciousness",
)


def one_shot_mature_schema(*, run: DelayedCreditLearningRun) -> bool:
    return any(
        item.one_shot_mature or item.maturity_status == "mature_forbidden_in_P13"
        for item in run.provisional_schema_candidates
    )


def confounder_credit_leak(*, run: DelayedCreditLearningRun) -> bool:
    active = {
        item.confounder_ref
        for item in run.confounder_records
        if item.status in {"active", "unresolved"} and item.could_explain_effect
    }
    if not active:
        return False
    for link in run.candidate_credit_links:
        if link.maturity_status in {"provisional_candidate", "repeated_trace_supported"} and not link.missing_evidence:
            overlaps = set(link.missing_evidence).intersection(active)
            if not overlaps:
                return True
    return False


def delayed_effect_misattribution(*, run: DelayedCreditLearningRun) -> bool:
    for record in run.delayed_effect_records:
        if not record["timing_refs"]:
            return True
        linked = [item for item in run.candidate_credit_links if item.effect_ref == record["effect_ref"]]
        if record.get("status") == "window_mismatch":
            if any(item.correlation_status not in {"insufficient_evidence", "disconfirmed"} for item in linked):
                return True
            continue
        if any(item.correlation_status not in {"delayed_possible", "ambiguous"} for item in linked):
            return True
    return False


def correlation_as_cause(*, run: DelayedCreditLearningRun) -> bool:
    for link in run.candidate_credit_links:
        if link.fact_claimed or link.cause_confirmed:
            return True
    for schema in run.provisional_schema_candidates:
        if schema.fact_claimed or schema.cause_confirmed:
            return True
    return False


def hidden_recipe_leak(*, run: DelayedCreditLearningRun) -> bool:
    if any(item.hidden_eval_used for item in run.episode_traces):
        return True
    return any(item.hidden_recipe_used for item in run.provisional_schema_candidates)


def scenario_label_learning(*, run: DelayedCreditLearningRun) -> bool:
    return any(item.scenario_label_used for item in run.episode_traces)


def schema_without_effect_refs(*, run: DelayedCreditLearningRun) -> bool:
    return any(not item.effect_refs for item in run.provisional_schema_candidates)


def schema_without_precursor_refs(*, run: DelayedCreditLearningRun) -> bool:
    return any(not item.precursor_refs for item in run.provisional_schema_candidates)


def mature_schema_without_repetition(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.provisional_schema_candidates:
        if item.maturity_status == "mature_forbidden_in_P13" and len(item.supporting_episode_refs) < 2:
            return True
    return False


def disconfirming_trace_ignored(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.provisional_schema_candidates:
        if item.disconfirming_episode_refs and item.maturity_status in {"provisional", "repeated_trace_supported"}:
            return True
    return False


def confounder_erased(*, run: DelayedCreditLearningRun) -> bool:
    if any("confounded" in item.correlation_status for item in run.candidate_credit_links):
        return not run.confounder_records
    return False


def delayed_window_without_timing_refs(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.candidate_credit_links:
        if item.correlation_status == "delayed_possible" and not item.delay_window:
            return True
    return False


def support_precision_without_evidence(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.candidate_credit_links:
        if item.confidence >= 0.8 and not item.evidence_refs:
            return True
    return False


def request_as_learning_confirmation(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.candidate_credit_links:
        has_ap01 = any("ap01:" in ref for ref in item.evidence_refs)
        has_effect = bool(item.effect_ref)
        if has_ap01 and not has_effect and item.maturity_status in {"provisional_candidate", "repeated_trace_supported"}:
            return True
    return False


def effect_as_learning_oracle(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.candidate_credit_links:
        if item.effect_ref and not item.precursor_ref and item.maturity_status in {"provisional_candidate", "repeated_trace_supported"}:
            return True
    return False


def attribution_as_learning_oracle(*, run: DelayedCreditLearningRun) -> bool:
    for item in run.candidate_credit_links:
        if item.attribution_kind_refs and not item.evidence_refs and item.confidence >= 0.6:
            return True
    return False


def credit_learning_emits_action_request(*, run: DelayedCreditLearningRun) -> bool:
    return run.action_request_emitted


def p13_overclaims_learning(*, claim_boundary: str) -> bool:
    lowered = claim_boundary.lower()
    if any(guard in lowered for guard in _OVERCLAIM_GUARDS):
        return False
    return any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def evaluate_delayed_credit_falsifiers(
    *,
    run: DelayedCreditLearningRun,
    claim_boundary: str,
) -> dict[str, bool]:
    return {
        "one_shot_mature_schema": one_shot_mature_schema(run=run),
        "confounder_credit_leak": confounder_credit_leak(run=run),
        "delayed_effect_misattribution": delayed_effect_misattribution(run=run),
        "correlation_as_cause": correlation_as_cause(run=run),
        "hidden_recipe_leak": hidden_recipe_leak(run=run),
        "scenario_label_learning": scenario_label_learning(run=run),
        "schema_without_effect_refs": schema_without_effect_refs(run=run),
        "schema_without_precursor_refs": schema_without_precursor_refs(run=run),
        "mature_schema_without_repetition": mature_schema_without_repetition(run=run),
        "disconfirming_trace_ignored": disconfirming_trace_ignored(run=run),
        "confounder_erased": confounder_erased(run=run),
        "delayed_window_without_timing_refs": delayed_window_without_timing_refs(run=run),
        "support_precision_without_evidence": support_precision_without_evidence(run=run),
        "request_as_learning_confirmation": request_as_learning_confirmation(run=run),
        "effect_as_learning_oracle": effect_as_learning_oracle(run=run),
        "attribution_as_learning_oracle": attribution_as_learning_oracle(run=run),
        "credit_learning_emits_action_request": credit_learning_emits_action_request(run=run),
        "P13_overclaims_learning": p13_overclaims_learning(claim_boundary=claim_boundary),
    }
