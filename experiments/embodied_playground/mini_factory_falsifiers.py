from __future__ import annotations

from .mini_factory_chain import MiniFactoryChainRun

_OVERCLAIM_MARKERS: tuple[str, ...] = (
    "general automation",
    "mature factory skill",
    "minecraft crafting",
    "consciousness",
    "general intelligence",
    "long-horizon planning",
)
_OVERCLAIM_GUARDS: tuple[str, ...] = (
    "bounded mini-factory chain",
    "no general automation",
    "no mature factory skill",
    "no consciousness",
)


def completion_without_full_chain(*, run: MiniFactoryChainRun) -> bool:
    return bool(run.completion_assessment.chain_complete and run.completion_assessment.verified_step_count < run.completion_assessment.required_step_count)


def failed_intermediate_erased(*, run: MiniFactoryChainRun) -> bool:
    failed_steps = [step for step in run.chain_step_traces if step.step_status in {"failed", "blocked", "skipped_due_residue"} and step.step_index <= 3]
    if not failed_steps:
        return False
    residue_step_ids = {item.step_id for item in run.chain_residue_records}
    return any(step.step_id not in residue_step_ids and not step.residue_refs for step in failed_steps)


def downstream_step_without_verified_input(*, run: MiniFactoryChainRun) -> bool:
    verify_map = {item.step_id: item.verification_status for item in run.intermediate_verification_records}
    steps = sorted((item for item in run.chain_step_traces if item.step_index <= 3), key=lambda x: x.step_index)
    output_verified: dict[str, bool] = {}
    for step in steps:
        status = verify_map.get(step.step_id, "insufficient_evidence")
        if step.step_status in {"succeeded", "partial", "attempted"} and step.step_index > 1:
            required = step.input_resource_refs[0] if step.input_resource_refs else None
            if required is not None and not output_verified.get(required, False):
                return True
        if step.output_resource_refs:
            output_verified[step.output_resource_refs[0]] = status == "verified"
    return False


def clean_water_without_filter_chain(*, run: MiniFactoryChainRun) -> bool:
    clean_step = next((s for s in run.chain_step_traces if s.step_index == 3), None)
    if clean_step is None:
        return False
    filter_step = next((s for s in run.chain_step_traces if s.step_index == 2), None)
    filter_verified = any(v.step_id == filter_step.step_id and v.verification_status == "verified" for v in run.intermediate_verification_records) if filter_step else False
    clean_verified = any(v.step_id == clean_step.step_id and v.verification_status == "verified" for v in run.intermediate_verification_records)
    return bool(clean_verified and not filter_verified)


def factory_chain_bypasses_AP01(*, run: MiniFactoryChainRun) -> bool:
    for step in run.chain_step_traces:
        if step.step_index > 3:
            continue
        if step.step_status in {"succeeded", "partial", "attempted"}:
            if not step.ap01_request_ref or not step.world_effect_ref:
                return True
    return False


def chain_uses_hidden_transformation_rule(*, run: MiniFactoryChainRun) -> bool:
    if run.hidden_eval_used:
        return True
    return any(step.hidden_eval_used for step in run.chain_step_traces)


def scenario_label_chain_completion(*, run: MiniFactoryChainRun) -> bool:
    if run.scenario_label_used:
        return True
    return any(step.scenario_label_used for step in run.chain_step_traces)


def resource_name_implies_intermediate(*, run: MiniFactoryChainRun) -> bool:
    for verify in run.intermediate_verification_records:
        if verify.verification_status == "verified" and not verify.public_evidence_refs:
            return True
    return False


def recipe_candidate_as_executable_skill(*, run: MiniFactoryChainRun) -> bool:
    if run.readiness.automation_forbidden:
        return False
    return any(step.step_status == "succeeded" for step in run.chain_step_traces if step.step_index <= 3)


def AB7_constraint_ignored_in_chain(*, run: MiniFactoryChainRun) -> bool:
    if run.ab7_constraint_refs:
        return False
    return any(step.step_status in {"succeeded", "attempted", "partial"} for step in run.chain_step_traces if step.step_index <= 3)


def P16_value_as_action_permission(*, run: MiniFactoryChainRun) -> bool:
    return bool(not run.value_chain_refs and any(step.step_status in {"attempted", "succeeded", "partial"} for step in run.chain_step_traces if step.step_index <= 3))


def P14_affordance_ignored_in_station_step(*, run: MiniFactoryChainRun) -> bool:
    if run.station_affordance_refs:
        return False
    return any(step.step_status in {"attempted", "succeeded", "partial"} for step in run.chain_step_traces if step.step_index <= 3)


def P13_confounder_erased_in_chain(*, run: MiniFactoryChainRun) -> bool:
    has_confounder_residue = any(item.residue_kind == "confounder_active" for item in run.chain_residue_records)
    confounded_completion = run.completion_assessment.chain_complete and bool(run.chain_residue_records)
    return confounded_completion or (any("confounder" in ref for ref in run.recipe_candidate_refs) and not has_confounder_residue)


def disconfirming_trace_ignored_in_chain(*, run: MiniFactoryChainRun) -> bool:
    has_disconfirm = any(item.residue_kind == "disconfirmed_step" for item in run.chain_residue_records)
    return bool(has_disconfirm and run.completion_assessment.chain_complete)


def request_as_step_success(*, run: MiniFactoryChainRun) -> bool:
    for step in run.chain_step_traces:
        if step.step_index > 3:
            continue
        if step.ap01_request_ref and not step.world_effect_ref and step.step_status in {"succeeded", "partial"}:
            return True
    return False


def effect_as_completion_oracle(*, run: MiniFactoryChainRun) -> bool:
    if not run.action_effect_refs:
        return False
    return bool(run.completion_assessment.chain_complete and run.completion_assessment.verified_step_count < run.completion_assessment.required_step_count)


def missing_input_erased(*, run: MiniFactoryChainRun) -> bool:
    for step in run.chain_step_traces:
        if step.step_status == "blocked" and "resource:ore" in step.required_precondition_refs and not step.missing_precondition_refs and step.step_index == 1:
            return True
    return False


def residue_not_propagated_downstream(*, run: MiniFactoryChainRun) -> bool:
    residues = [item for item in run.chain_residue_records if item.step_id.endswith("step_ore_to_plate") or item.step_id.endswith("step_plate_to_filter")]
    if not residues:
        return False
    return any(not item.downstream_blocked_steps for item in residues)


def chain_emits_unbounded_automation(*, run: MiniFactoryChainRun) -> bool:
    return bool(run.completion_assessment.automation_claimed or run.completion_assessment.mature_factory_skill_claimed)


def chain_emits_action_request_directly(*, run: MiniFactoryChainRun) -> bool:
    if run.action_request_emitted:
        return True
    return any(step.action_request_emitted_by_p17 for step in run.chain_step_traces)


def chain_executes_world_directly(*, run: MiniFactoryChainRun) -> bool:
    if run.world_submission_emitted:
        return True
    return any(step.world_submission_emitted_by_p17 for step in run.chain_step_traces)


def P17_overclaims_factory_intelligence(*, claim_boundary: str) -> bool:
    lowered = claim_boundary.lower()
    if any(guard in lowered for guard in _OVERCLAIM_GUARDS):
        return False
    return any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def evaluate_mini_factory_falsifiers(*, run: MiniFactoryChainRun, claim_boundary: str) -> dict[str, bool]:
    return {
        "completion_without_full_chain": completion_without_full_chain(run=run),
        "failed_intermediate_erased": failed_intermediate_erased(run=run),
        "downstream_step_without_verified_input": downstream_step_without_verified_input(run=run),
        "clean_water_without_filter_chain": clean_water_without_filter_chain(run=run),
        "factory_chain_bypasses_AP01": factory_chain_bypasses_AP01(run=run),
        "chain_uses_hidden_transformation_rule": chain_uses_hidden_transformation_rule(run=run),
        "scenario_label_chain_completion": scenario_label_chain_completion(run=run),
        "resource_name_implies_intermediate": resource_name_implies_intermediate(run=run),
        "recipe_candidate_as_executable_skill": recipe_candidate_as_executable_skill(run=run),
        "AB7_constraint_ignored_in_chain": AB7_constraint_ignored_in_chain(run=run),
        "P16_value_as_action_permission": P16_value_as_action_permission(run=run),
        "P14_affordance_ignored_in_station_step": P14_affordance_ignored_in_station_step(run=run),
        "P13_confounder_erased_in_chain": P13_confounder_erased_in_chain(run=run),
        "disconfirming_trace_ignored_in_chain": disconfirming_trace_ignored_in_chain(run=run),
        "request_as_step_success": request_as_step_success(run=run),
        "effect_as_completion_oracle": effect_as_completion_oracle(run=run),
        "missing_input_erased": missing_input_erased(run=run),
        "residue_not_propagated_downstream": residue_not_propagated_downstream(run=run),
        "chain_emits_unbounded_automation": chain_emits_unbounded_automation(run=run),
        "chain_emits_action_request_directly": chain_emits_action_request_directly(run=run),
        "chain_executes_world_directly": chain_executes_world_directly(run=run),
        "P17_overclaims_factory_intelligence": P17_overclaims_factory_intelligence(claim_boundary=claim_boundary),
    }
