from __future__ import annotations

from .instrumental_value import InstrumentalValueRun

_OVERCLAIM_MARKERS: tuple[str, ...] = (
    "mature automation",
    "intrinsic value learning",
    "general planning",
    "minecraft crafting",
    "consciousness",
    "general intelligence",
)
_OVERCLAIM_GUARDS: tuple[str, ...] = (
    "bounded instrumental value",
    "no automation",
    "no intrinsic value",
    "no consciousness",
)


def iron_magic_value(*, run: InstrumentalValueRun) -> bool:
    return any(
        frame.resource_ref.endswith("iron")
        and frame.value_status not in {"no_value", "blocked"}
        and not frame.need_refs
        for frame in run.instrumental_value_frames
    )


def filter_without_water_problem(*, run: InstrumentalValueRun) -> bool:
    return any(
        frame.resource_ref.endswith("filter")
        and frame.value_status not in {"no_value", "blocked"}
        and not frame.need_refs
        and not frame.effect_refs
        for frame in run.instrumental_value_frames
    )


def resource_value_without_need(*, run: InstrumentalValueRun) -> bool:
    return any(
        frame.value_status in {"weak_instrumental", "provisional_instrumental", "repeated_trace_supported"}
        and not frame.need_refs
        for frame in run.instrumental_value_frames
    )


def value_without_effect_chain(*, run: InstrumentalValueRun) -> bool:
    return any(
        frame.value_status in {"weak_instrumental", "provisional_instrumental", "repeated_trace_supported"}
        and not frame.effect_refs
        for frame in run.instrumental_value_frames
    )


def instrumental_value_becomes_intrinsic_goal(*, run: InstrumentalValueRun) -> bool:
    if run.intrinsic_value_claimed:
        return True
    return any(frame.intrinsic_value_claimed for frame in run.instrumental_value_frames)


def recipe_candidate_as_automation_value(*, run: InstrumentalValueRun) -> bool:
    return any(item.readiness_status == "automation_forbidden_in_P16" for item in run.means_candidates)


def ab7_constraint_ignored(*, run: InstrumentalValueRun) -> bool:
    if not run.ab7_constraint_refs:
        return any(frame.value_status in {"provisional_instrumental", "repeated_trace_supported"} for frame in run.instrumental_value_frames)
    return False


def p13_confounder_ignored_for_value(*, run: InstrumentalValueRun) -> bool:
    if not run.confounder_refs:
        return False
    return any(frame.value_status in {"provisional_instrumental", "repeated_trace_supported"} for frame in run.instrumental_value_frames)


def p14_affordance_ignored_for_value(*, run: InstrumentalValueRun) -> bool:
    station_linked = any(chain.chain_kind == "resource_to_station_input" for chain in run.value_chains)
    if not station_linked:
        return False
    if run.p14_affordance_refs:
        return False
    return any(frame.value_status in {"weak_instrumental", "provisional_instrumental", "repeated_trace_supported"} for frame in run.instrumental_value_frames)


def ab5_support_as_value_oracle(*, run: InstrumentalValueRun) -> bool:
    has_ab5_only = any(ref.startswith("ab5_update:") for ref in run.effect_chain_refs)
    has_public_effect = any(ref.startswith("effect:") for ref in run.effect_chain_refs)
    return has_ab5_only and not has_public_effect


def ab6_attribution_as_value_oracle(*, run: InstrumentalValueRun) -> bool:
    has_ab6_only = any(ref.startswith("ab6_attribution:") for ref in run.effect_chain_refs)
    has_public_effect = any(ref.startswith("effect:") for ref in run.effect_chain_refs)
    return has_ab6_only and not has_public_effect


def hidden_eval_value_rule_used(*, run: InstrumentalValueRun) -> bool:
    if run.hidden_eval_used:
        return True
    return any(frame.hidden_eval_used for frame in run.instrumental_value_frames)


def scenario_label_value_assignment(*, run: InstrumentalValueRun) -> bool:
    if run.scenario_label_used:
        return True
    return any(frame.scenario_label_used for frame in run.instrumental_value_frames)


def value_without_resource_refs(*, run: InstrumentalValueRun) -> bool:
    return bool(run.instrumental_value_frames) and not run.resource_refs


def value_without_evidence_refs(*, run: InstrumentalValueRun) -> bool:
    return any(not frame.evidence_refs for frame in run.instrumental_value_frames)


def missing_evidence_erased(*, run: InstrumentalValueRun) -> bool:
    expected_missing = any(
        key in run.blocked_reasons
        for key in ("need_refs_required", "effect_chain_refs_required", "p14_station_affordance_refs_required", "ab7_constraint_refs_required")
    )
    if not expected_missing:
        return False
    return any(not frame.missing_evidence for frame in run.instrumental_value_frames)


def disconfirmation_ignored(*, run: InstrumentalValueRun) -> bool:
    if not run.disconfirmation_refs:
        return False
    return any(frame.value_status in {"weak_instrumental", "provisional_instrumental", "repeated_trace_supported"} for frame in run.instrumental_value_frames)


def value_emits_action_request(*, run: InstrumentalValueRun) -> bool:
    if run.action_request_emitted:
        return True
    return any(frame.action_request_emitted for frame in run.instrumental_value_frames) or any(item.action_request_emitted for item in run.means_candidates)


def value_executes_world(*, run: InstrumentalValueRun) -> bool:
    if run.world_submission_emitted:
        return True
    return any(frame.world_submission_emitted for frame in run.instrumental_value_frames) or any(item.world_submission_emitted for item in run.means_candidates)


def p16_overclaims_automation_or_value_learning(*, claim_boundary: str) -> bool:
    lowered = claim_boundary.lower()
    if any(guard in lowered for guard in _OVERCLAIM_GUARDS):
        return False
    return any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def evaluate_instrumental_value_falsifiers(
    *,
    run: InstrumentalValueRun,
    claim_boundary: str,
) -> dict[str, bool]:
    return {
        "iron_magic_value": iron_magic_value(run=run),
        "filter_without_water_problem": filter_without_water_problem(run=run),
        "resource_value_without_need": resource_value_without_need(run=run),
        "value_without_effect_chain": value_without_effect_chain(run=run),
        "instrumental_value_becomes_intrinsic_goal": instrumental_value_becomes_intrinsic_goal(run=run),
        "recipe_candidate_as_automation_value": recipe_candidate_as_automation_value(run=run),
        "ab7_constraint_ignored": ab7_constraint_ignored(run=run),
        "p13_confounder_ignored_for_value": p13_confounder_ignored_for_value(run=run),
        "p14_affordance_ignored_for_value": p14_affordance_ignored_for_value(run=run),
        "ab5_support_as_value_oracle": ab5_support_as_value_oracle(run=run),
        "ab6_attribution_as_value_oracle": ab6_attribution_as_value_oracle(run=run),
        "hidden_eval_value_rule_used": hidden_eval_value_rule_used(run=run),
        "scenario_label_value_assignment": scenario_label_value_assignment(run=run),
        "value_without_resource_refs": value_without_resource_refs(run=run),
        "value_without_evidence_refs": value_without_evidence_refs(run=run),
        "missing_evidence_erased": missing_evidence_erased(run=run),
        "disconfirmation_ignored": disconfirmation_ignored(run=run),
        "value_emits_action_request": value_emits_action_request(run=run),
        "value_executes_world": value_executes_world(run=run),
        "P16_overclaims_automation_or_value_learning": p16_overclaims_automation_or_value_learning(claim_boundary=claim_boundary),
    }
