from __future__ import annotations

from .recipe_precursor_learning import RecipePrecursorLearningRun

_OVERCLAIM_MARKERS: tuple[str, ...] = (
    "mature recipe",
    "automation",
    "minecraft crafting",
    "general tool use",
    "consciousness",
    "full causal learning",
)
_OVERCLAIM_GUARDS: tuple[str, ...] = (
    "provisional",
    "not mature",
    "no mature",
    "no automation",
    "no consciousness",
)


def hidden_recipe_leak(*, run: RecipePrecursorLearningRun) -> bool:
    if any(item.hidden_eval_used for item in run.lived_trace_records):
        return True
    return any(item.hidden_recipe_used or item.protected_eval_used for item in run.recipe_candidates)


def one_shot_recipe_maturity(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.one_shot_mature:
            return True
        if item.maturity_status == "mature_forbidden_or_not_reached" and len(item.supporting_trace_refs) <= 1:
            return True
    return False


def recipe_without_lived_trace(*, run: RecipePrecursorLearningRun) -> bool:
    return bool(run.recipe_candidates) and not run.lived_trace_records


def recipe_without_effect_refs(*, run: RecipePrecursorLearningRun) -> bool:
    return any(
        (not item.effect_refs) and item.maturity_status in {"weak_candidate", "provisional_candidate", "repeated_trace_supported"}
        for item in run.recipe_candidates
    )


def recipe_without_input_refs(*, run: RecipePrecursorLearningRun) -> bool:
    return any(
        (not item.input_refs) and item.maturity_status in {"weak_candidate", "provisional_candidate", "repeated_trace_supported"}
        for item in run.recipe_candidates
    )


def station_visible_as_recipe_basis(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        has_station_only = bool(item.station_ref) and not item.input_refs and not item.effect_refs
        if has_station_only and item.maturity_status in {"weak_candidate", "provisional_candidate", "repeated_trace_supported"}:
            return True
    return False


def station_affordance_as_recipe_truth(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.maturity_status in {"repeated_trace_supported", "mature_forbidden_or_not_reached"}:
            if not item.p13_schema_candidate_refs:
                return True
    return False


def confounder_bypasses_recipe_maturity(*, run: RecipePrecursorLearningRun) -> bool:
    active = {
        str(item.get("confounder_ref"))
        for item in run.confounder_records
        if str(item.get("status")) in {"active", "unresolved"}
    }
    if not active:
        return False
    for item in run.recipe_candidates:
        if item.maturity_status in {"repeated_trace_supported", "mature_forbidden_or_not_reached"}:
            if not set(item.confounder_refs).intersection(active):
                return True
    return False


def missing_evidence_erased(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.maturity_status in {"provisional_candidate", "repeated_trace_supported"} and not item.missing_evidence:
            if not item.input_refs or not item.effect_refs:
                return True
            active_confounder = {
                str(record.get("confounder_ref"))
                for record in run.confounder_records
                if str(record.get("status")) in {"active", "unresolved"}
            }
            if active_confounder and not set(item.confounder_refs).intersection(active_confounder):
                return True
    return False


def disconfirming_trace_ignored(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.disconfirming_trace_refs and item.maturity_status in {"provisional_candidate", "repeated_trace_supported"}:
            return True
    return False


def repeated_trace_without_public_refs(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.maturity_status == "repeated_trace_supported" and len(item.supporting_trace_refs) >= 2:
            supporting = {trace.trace_id: trace for trace in run.lived_trace_records}
            for trace_id in item.supporting_trace_refs:
                trace = supporting.get(trace_id)
                if trace is None or not trace.evidence_refs:
                    return True
    return False


def delayed_effect_as_immediate_recipe(*, run: RecipePrecursorLearningRun) -> bool:
    delayed_trace_ids = {
        trace.trace_id
        for trace in run.lived_trace_records
        if trace.timing_refs
    }
    if not delayed_trace_ids:
        return False
    for item in run.recipe_candidates:
        if delayed_trace_ids.intersection(set(item.supporting_trace_refs)) and item.maturity_score >= 0.7:
            return True
    return False


def output_as_truth_oracle(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.output_refs and not item.input_refs and item.maturity_status in {"provisional_candidate", "repeated_trace_supported"}:
            return True
    return False


def ab5_update_as_recipe_oracle(*, run: RecipePrecursorLearningRun) -> bool:
    for trace in run.lived_trace_records:
        has_ab5_only = any(ref.startswith("ab5:") for ref in trace.evidence_refs)
        has_public_station = any(ref.startswith("station:") for ref in trace.evidence_refs)
        if has_ab5_only and not has_public_station:
            return True
    return False


def ab6_attribution_as_recipe_oracle(*, run: RecipePrecursorLearningRun) -> bool:
    for trace in run.lived_trace_records:
        has_ab6 = any(ref.startswith("ab6:") for ref in trace.evidence_refs)
        has_effect = bool(trace.public_effect_refs)
        if has_ab6 and not has_effect:
            return True
    return False


def scenario_label_recipe_learning(*, run: RecipePrecursorLearningRun) -> bool:
    return any(item.scenario_label_used for item in run.lived_trace_records)


def protected_eval_output_used(*, run: RecipePrecursorLearningRun) -> bool:
    return any(item.protected_eval_used for item in run.recipe_candidates)


def recipe_candidate_emits_action_request(*, run: RecipePrecursorLearningRun) -> bool:
    if run.action_request_emitted:
        return True
    return any(item.action_request_emitted for item in run.recipe_candidates)


def recipe_candidate_executes_world(*, run: RecipePrecursorLearningRun) -> bool:
    if run.world_submission_emitted:
        return True
    return any(item.world_submission_emitted for item in run.recipe_candidates)


def mature_schema_without_p13_gate(*, run: RecipePrecursorLearningRun) -> bool:
    for item in run.recipe_candidates:
        if item.maturity_status in {"repeated_trace_supported", "mature_forbidden_or_not_reached"}:
            if not item.p13_schema_candidate_refs:
                return True
            if len(item.supporting_trace_refs) < 2:
                return True
            if item.disconfirming_trace_refs:
                return True
    return False


def p15_overclaims_recipe_learning(*, claim_boundary: str) -> bool:
    lowered = claim_boundary.lower()
    if any(guard in lowered for guard in _OVERCLAIM_GUARDS):
        return False
    return any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def evaluate_recipe_precursor_falsifiers(
    *,
    run: RecipePrecursorLearningRun,
    claim_boundary: str,
) -> dict[str, bool]:
    return {
        "hidden_recipe_leak": hidden_recipe_leak(run=run),
        "one_shot_recipe_maturity": one_shot_recipe_maturity(run=run),
        "recipe_without_lived_trace": recipe_without_lived_trace(run=run),
        "recipe_without_effect_refs": recipe_without_effect_refs(run=run),
        "recipe_without_input_refs": recipe_without_input_refs(run=run),
        "station_visible_as_recipe_basis": station_visible_as_recipe_basis(run=run),
        "station_affordance_as_recipe_truth": station_affordance_as_recipe_truth(run=run),
        "confounder_bypasses_recipe_maturity": confounder_bypasses_recipe_maturity(run=run),
        "missing_evidence_erased": missing_evidence_erased(run=run),
        "disconfirming_trace_ignored": disconfirming_trace_ignored(run=run),
        "repeated_trace_without_public_refs": repeated_trace_without_public_refs(run=run),
        "delayed_effect_as_immediate_recipe": delayed_effect_as_immediate_recipe(run=run),
        "output_as_truth_oracle": output_as_truth_oracle(run=run),
        "ab5_update_as_recipe_oracle": ab5_update_as_recipe_oracle(run=run),
        "ab6_attribution_as_recipe_oracle": ab6_attribution_as_recipe_oracle(run=run),
        "scenario_label_recipe_learning": scenario_label_recipe_learning(run=run),
        "protected_eval_output_used": protected_eval_output_used(run=run),
        "recipe_candidate_emits_action_request": recipe_candidate_emits_action_request(run=run),
        "recipe_candidate_executes_world": recipe_candidate_executes_world(run=run),
        "mature_schema_without_p13_gate": mature_schema_without_p13_gate(run=run),
        "P15_overclaims_recipe_learning": p15_overclaims_recipe_learning(claim_boundary=claim_boundary),
    }
