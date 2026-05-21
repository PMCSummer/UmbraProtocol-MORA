from __future__ import annotations

from dataclasses import asdict

from .models import (
    P17BAuthorityFlags,
    P17BBlockedReason,
    P17BChainAdvanceDecision,
    P17BCounters,
    P17BFactoryNeed,
    P17BFactoryStepSpec,
    P17BFactoryStepTrace,
    P17BIntermediateVerification,
    P17BLiveMiniFactoryRun,
    P17BResidueStopFrame,
    P17BResourceState,
    P17BRunStatus,
    P17BStepInput,
    P17BStepStatus,
)

_HIDDEN_RECIPE_TOKENS: tuple[str, ...] = (
    "hidden_recipe",
    "true_recipe",
    "recipe_table",
    "authoritative_transformation",
    "recipe_oracle",
)
_WORLDSTATE_TOKENS: tuple[str, ...] = (
    "worldstate",
    "full_map",
    "backend_object_id",
    "hidden_label",
    "hidden_identity",
    "raw_state",
)
_SCENARIO_TOKENS: tuple[str, ...] = ("scenario_label", "eval_label", "scenario:")
_FACTORY_SCRIPT_TOKENS: tuple[str, ...] = (
    "factory_steps",
    "ordered_plan",
    "solution_sequence",
    "route_plan",
    "planner_policy",
)
_SELECTION_TOKENS: tuple[str, ...] = (
    "selected_action",
    "selected_goal",
    "choose_candidate",
    "best_action",
    "selected_micro_operation",
)
_COST_PERMISSION_TOKENS: tuple[str, ...] = ("cost_winner", "cheapest_candidate", "lowest_cost_permission")
_PROVIDER_TRUTH_TOKENS: tuple[str, ...] = ("provider_truth", "truth_authority", "fact_claimed", "recipe_truth")
_PROOF_ONLY_TOKENS: tuple[str, ...] = ("p17_proof_only", "proof_trace_only", "non_live_chain")
_INVALID_AP01_TOKENS: tuple[str, ...] = (
    "fake_ap01",
    "local_ap01",
    "created_by_p17b",
    "p17b_created_ap01",
    "runner_created_ap01",
)


def build_p17b_factory_need(
    *,
    need_id: str,
    target_ref: str,
    pressure_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
    public_basis_refs: tuple[str, ...],
    urgency: str | None = None,
) -> P17BFactoryNeed:
    return P17BFactoryNeed(
        need_id=need_id,
        target_ref=target_ref,
        pressure_refs=pressure_refs,
        source_refs=source_refs,
        urgency=urgency,
        public_basis_refs=public_basis_refs,
        hidden_goal_used=False,
        scenario_label_used=False,
    )


def build_p17b_step_spec(
    *,
    step_id: str,
    step_kind,
    required_input_refs: tuple[str, ...],
    required_station_refs: tuple[str, ...],
    expected_output_refs: tuple[str, ...],
    required_micro_operation_kinds: tuple[str, ...],
    allowed_action_surface_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...] = (),
    lossiness_refs: tuple[str, ...] = (),
    metadata: dict[str, object] | None = None,
) -> P17BFactoryStepSpec:
    return P17BFactoryStepSpec(
        step_id=step_id,
        step_kind=step_kind,
        required_input_refs=required_input_refs,
        required_station_refs=required_station_refs,
        expected_output_refs=expected_output_refs,
        required_micro_operation_kinds=required_micro_operation_kinds,
        allowed_action_surface_refs=allowed_action_surface_refs,
        source_refs=source_refs,
        uncertainty_refs=uncertainty_refs,
        lossiness_refs=lossiness_refs,
        no_hidden_recipe=True,
        no_selected_action=True,
        metadata=metadata or {},
    )


def validate_p17b_step_spec(step_spec: P17BFactoryStepSpec) -> tuple[P17BBlockedReason, ...]:
    blocked: list[P17BBlockedReason] = []
    tokens = _joined(step_spec.step_id, *step_spec.source_refs, step_spec.metadata)
    if not step_spec.source_refs:
        blocked.append(P17BBlockedReason.MISSING_MICRO_OPERATION_BASIS)
    if _contains_any(tokens, _HIDDEN_RECIPE_TOKENS):
        blocked.append(P17BBlockedReason.HIDDEN_RECIPE_DETECTED)
    if _contains_any(tokens, _SELECTION_TOKENS):
        blocked.append(P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED)
    if _contains_any(tokens, _FACTORY_SCRIPT_TOKENS):
        blocked.append(P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED)
    return tuple(dict.fromkeys(blocked))


def verify_p17b_intermediate(
    *,
    verification_id: str,
    intermediate_ref: str,
    required_effect_refs: tuple[str, ...],
    observed_effect_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
    correlation_refs: tuple[str, ...],
    residue_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...],
) -> P17BIntermediateVerification:
    required = set(required_effect_refs)
    observed = set(observed_effect_refs)
    verified = bool(required) and required.issubset(observed)
    partial = bool(required & observed) and not verified
    blocked = not verified and not partial
    return P17BIntermediateVerification(
        verification_id=verification_id,
        intermediate_ref=intermediate_ref,
        required_effect_refs=required_effect_refs,
        observed_effect_refs=observed_effect_refs,
        source_refs=source_refs,
        correlation_refs=correlation_refs,
        verified=verified,
        partial=partial,
        blocked=blocked,
        residue_refs=residue_refs,
        uncertainty_refs=uncertainty_refs,
        verification_basis=tuple(dict.fromkeys((*required_effect_refs, *observed_effect_refs))),
        no_backend_truth=True,
    )


def decide_p17b_chain_advance(
    *,
    decision_id: str,
    current_step_ref: str,
    next_step_ref: str | None,
    required_verified_intermediate_refs: tuple[str, ...],
    verified_intermediate_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
    residue_refs: tuple[str, ...],
) -> P17BChainAdvanceDecision:
    verified = set(verified_intermediate_refs)
    missing = tuple(ref for ref in required_verified_intermediate_refs if ref not in verified)
    blocked_reasons: list[P17BBlockedReason] = []
    if missing:
        blocked_reasons.append(P17BBlockedReason.DOWNSTREAM_WITHOUT_VERIFIED_INTERMEDIATE)
    return P17BChainAdvanceDecision(
        decision_id=decision_id,
        current_step_ref=current_step_ref,
        next_step_ref=next_step_ref,
        advance_allowed=not missing,
        required_verified_intermediate_refs=required_verified_intermediate_refs,
        missing_intermediate_refs=missing,
        residue_refs=residue_refs,
        blocked_reasons=tuple(blocked_reasons),
        source_refs=source_refs,
        no_hidden_plan=True,
    )


def build_p17b_residue_stop(
    *,
    stop_id: str,
    failed_step_ref: str,
    residue_refs: tuple[str, ...],
    unresolved_refs: tuple[str, ...],
    blocked_downstream_step_refs: tuple[str, ...],
    next_pressure_refs: tuple[str, ...],
    stop_reason: P17BBlockedReason,
    continuation_allowed: bool = False,
) -> P17BResidueStopFrame:
    return P17BResidueStopFrame(
        stop_id=stop_id,
        failed_step_ref=failed_step_ref,
        residue_refs=residue_refs,
        unresolved_refs=unresolved_refs,
        blocked_downstream_step_refs=blocked_downstream_step_refs,
        next_pressure_refs=next_pressure_refs,
        stop_reason=stop_reason,
        continuation_allowed=continuation_allowed,
    )


def build_p17b_step_trace(
    *,
    step_input: P17BStepInput,
    available_resources: set[str],
    station_affordances: set[str],
    allow_safe_partial_continuation: bool,
) -> tuple[P17BFactoryStepTrace, tuple[P17BIntermediateVerification, ...], tuple[P17BBlockedReason, ...]]:
    spec = step_input.step_spec
    blocked: list[P17BBlockedReason] = list(validate_p17b_step_spec(spec))
    combined_tokens = _joined(
        step_input.metadata_refs,
        step_input.provider_hint_refs,
        step_input.ap01_request_refs,
        step_input.backend_execution_refs,
        step_input.world_effect_feedback_refs,
        spec.metadata,
    )

    if _contains_any(combined_tokens, _PROVIDER_TRUTH_TOKENS):
        blocked.append(P17BBlockedReason.PROVIDER_HINT_AS_TRUTH_DETECTED)
    if _contains_any(combined_tokens, _SELECTION_TOKENS):
        blocked.append(P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED)
    if _contains_any(combined_tokens, _COST_PERMISSION_TOKENS):
        blocked.append(P17BBlockedReason.COST_WINNER_AS_PERMISSION_DETECTED)
    if _contains_any(combined_tokens, _FACTORY_SCRIPT_TOKENS):
        blocked.append(P17BBlockedReason.ADAPTER_SOLUTION_SEQUENCE_DETECTED)
    if _contains_any(combined_tokens, _WORLDSTATE_TOKENS):
        blocked.append(P17BBlockedReason.BACKEND_WORLDSTATE_DETECTED)
    if _contains_any(combined_tokens, _SCENARIO_TOKENS):
        blocked.append(P17BBlockedReason.SCENARIO_LABEL_DETECTED)
    if _contains_any(combined_tokens, _PROOF_ONLY_TOKENS):
        blocked.append(P17BBlockedReason.P17_PROOF_AS_LIVE_EXECUTION_DETECTED)
    if _contains_any(combined_tokens, _INVALID_AP01_TOKENS):
        blocked.append(P17BBlockedReason.INVALID_AP01_LINEAGE)
    if "recipe_candidate_as_skill" in combined_tokens:
        blocked.append(P17BBlockedReason.RECIPE_CANDIDATE_AS_SKILL_DETECTED)

    live_lineage_claimed = bool(
        step_input.ap01_request_refs
        or step_input.backend_execution_refs
        or step_input.world_effect_feedback_refs
        or step_input.observed_effect_refs
    )
    if live_lineage_claimed and (not step_input.cycle_refs or not step_input.world0_run_ref):
        blocked.append(P17BBlockedReason.MISSING_WORLD0_LINEAGE)
    if step_input.ap01_request_refs and any(not ref.lower().startswith("ap01:") for ref in step_input.ap01_request_refs):
        blocked.append(P17BBlockedReason.INVALID_AP01_LINEAGE)
    if step_input.world_effect_feedback_refs and any(
        not ref.lower().startswith("world_effect:") for ref in step_input.world_effect_feedback_refs
    ):
        blocked.append(P17BBlockedReason.MISSING_WORLD0_LINEAGE)

    for ref in spec.required_input_refs:
        if ref not in available_resources:
            blocked.append(P17BBlockedReason.MISSING_PUBLIC_RESOURCE)
            break
    for station_ref in spec.required_station_refs:
        if station_ref not in station_affordances:
            blocked.append(P17BBlockedReason.MISSING_STATION_AFFORDANCE)
            break
    if spec.required_micro_operation_kinds and not step_input.micro_operation_refs:
        blocked.append(P17BBlockedReason.MISSING_MICRO_OPERATION_BASIS)
    if not step_input.ap01_request_refs:
        blocked.append(P17BBlockedReason.MISSING_AP01_REQUEST)
    if step_input.backend_execution_refs and not step_input.ap01_request_refs:
        blocked.append(P17BBlockedReason.EXECUTION_WITHOUT_AP01)
    if step_input.ap01_request_refs and (not step_input.world_effect_feedback_refs or not step_input.observed_effect_refs):
        blocked.append(P17BBlockedReason.MISSING_WORLD_EFFECT)

    verification_observed_refs = step_input.observed_effect_refs
    if P17BBlockedReason.MISSING_AP01_REQUEST in blocked or P17BBlockedReason.MISSING_WORLD_EFFECT in blocked:
        verification_observed_refs = ()

    verifications: list[P17BIntermediateVerification] = []
    verified_outputs: list[str] = []
    for output_ref in spec.expected_output_refs:
        v = verify_p17b_intermediate(
            verification_id=f"verify:{spec.step_id}:{output_ref}",
            intermediate_ref=output_ref,
            required_effect_refs=(output_ref,),
            observed_effect_refs=verification_observed_refs,
            source_refs=spec.source_refs,
            correlation_refs=step_input.ap01_request_refs,
            residue_refs=step_input.residue_refs,
            uncertainty_refs=step_input.uncertainty_refs,
        )
        verifications.append(v)
        if v.verified:
            verified_outputs.append(output_ref)

    if spec.expected_output_refs and len(verified_outputs) != len(spec.expected_output_refs):
        blocked.append(P17BBlockedReason.EXPECTED_EFFECT_NOT_OBSERVED)

    if blocked:
        if P17BBlockedReason.EXPECTED_EFFECT_NOT_OBSERVED in blocked:
            status = P17BStepStatus.UNRESOLVED
        elif P17BBlockedReason.MISSING_AP01_REQUEST in blocked:
            status = P17BStepStatus.BLOCKED
        elif P17BBlockedReason.MISSING_WORLD_EFFECT in blocked:
            status = P17BStepStatus.BLOCKED
        elif step_input.ap01_request_refs and step_input.backend_execution_refs:
            status = P17BStepStatus.FAILED
        else:
            status = P17BStepStatus.BLOCKED
    else:
        status = P17BStepStatus.INTERMEDIATE_VERIFIED

    trace = P17BFactoryStepTrace(
        step_id=spec.step_id,
        cycle_refs=step_input.cycle_refs,
        world0_run_ref=step_input.world0_run_ref,
        micro_operation_refs=step_input.micro_operation_refs,
        cost_comparison_refs=step_input.cost_comparison_refs,
        ap01_request_refs=step_input.ap01_request_refs,
        backend_execution_refs=step_input.backend_execution_refs,
        world_effect_feedback_refs=step_input.world_effect_feedback_refs,
        observed_effect_refs=step_input.observed_effect_refs,
        expected_effect_refs=spec.expected_output_refs,
        verified_intermediate_refs=tuple(verified_outputs),
        residue_refs=step_input.residue_refs,
        uncertainty_refs=step_input.uncertainty_refs,
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        status=status,
        downstream_unlocked=(status is P17BStepStatus.INTERMEDIATE_VERIFIED),
        effect_verified=(status is P17BStepStatus.INTERMEDIATE_VERIFIED),
        no_action_selected_by_p17b=True,
        no_ap01_created_by_p17b=True,
    )
    return trace, tuple(verifications), tuple(dict.fromkeys(blocked))


def validate_p17b_step_trace(step_trace: P17BFactoryStepTrace) -> tuple[P17BBlockedReason, ...]:
    blocked: list[P17BBlockedReason] = []
    if step_trace.backend_execution_refs and not step_trace.ap01_request_refs:
        blocked.append(P17BBlockedReason.EXECUTION_WITHOUT_AP01)
    if (
        step_trace.ap01_request_refs
        or step_trace.backend_execution_refs
        or step_trace.world_effect_feedback_refs
        or step_trace.observed_effect_refs
    ) and (not step_trace.cycle_refs or not step_trace.world0_run_ref):
        blocked.append(P17BBlockedReason.MISSING_WORLD0_LINEAGE)
    if step_trace.ap01_request_refs and any(not ref.lower().startswith("ap01:") for ref in step_trace.ap01_request_refs):
        blocked.append(P17BBlockedReason.INVALID_AP01_LINEAGE)
    if step_trace.status is P17BStepStatus.INTERMEDIATE_VERIFIED and not step_trace.verified_intermediate_refs:
        blocked.append(P17BBlockedReason.EXPECTED_EFFECT_NOT_OBSERVED)
    if step_trace.status in {P17BStepStatus.FAILED, P17BStepStatus.UNRESOLVED, P17BStepStatus.BLOCKED} and not step_trace.residue_refs:
        blocked.append(P17BBlockedReason.RESIDUE_NOT_PRESERVED)
    return tuple(dict.fromkeys(blocked))


def build_p17b_live_run(
    *,
    run_id: str,
    need: P17BFactoryNeed,
    step_inputs: tuple[P17BStepInput, ...],
    final_target_refs: tuple[str, ...],
    world0_run_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
    available_resources: tuple[str, ...],
    station_affordances: tuple[str, ...],
    allow_safe_partial_continuation: bool = False,
    replay_trace_ref: str | None = None,
    metadata: dict[str, object] | None = None,
) -> P17BLiveMiniFactoryRun:
    metadata = metadata or {}
    blocked_run: list[P17BBlockedReason] = []
    if not need.pressure_refs or not need.public_basis_refs:
        blocked_run.append(P17BBlockedReason.MISSING_PUBLIC_NEED)
    if need.hidden_goal_used:
        blocked_run.append(P17BBlockedReason.MISSING_PUBLIC_NEED)
    if need.scenario_label_used:
        blocked_run.append(P17BBlockedReason.SCENARIO_LABEL_DETECTED)

    joined = _joined(metadata, source_refs, need.target_ref, need.pressure_refs, need.source_refs, need.public_basis_refs)
    if _contains_any(joined, _HIDDEN_RECIPE_TOKENS):
        blocked_run.append(P17BBlockedReason.HIDDEN_RECIPE_DETECTED)
    if _contains_any(joined, _WORLDSTATE_TOKENS):
        blocked_run.append(P17BBlockedReason.BACKEND_WORLDSTATE_DETECTED)
    if _contains_any(joined, _SCENARIO_TOKENS):
        blocked_run.append(P17BBlockedReason.SCENARIO_LABEL_DETECTED)
    if _contains_any(joined, _FACTORY_SCRIPT_TOKENS):
        blocked_run.append(P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED)
    if _contains_any(joined, _PROOF_ONLY_TOKENS):
        blocked_run.append(P17BBlockedReason.P17_PROOF_AS_LIVE_EXECUTION_DETECTED)
    if any(
        item.ap01_request_refs or item.backend_execution_refs or item.world_effect_feedback_refs or item.observed_effect_refs
        for item in step_inputs
    ) and not world0_run_refs:
        blocked_run.append(P17BBlockedReason.MISSING_WORLD0_LINEAGE)

    resource_set = set(available_resources)
    station_set = set(station_affordances)

    step_traces: list[P17BFactoryStepTrace] = []
    verifications: list[P17BIntermediateVerification] = []
    decisions: list[P17BChainAdvanceDecision] = []
    stops: list[P17BResidueStopFrame] = []
    run_residue: list[str] = []
    run_uncertainty: list[str] = []
    all_blocked: list[P17BBlockedReason] = list(blocked_run)

    for idx, step_input in enumerate(step_inputs):
        step_trace, step_verifications, step_blocked = build_p17b_step_trace(
            step_input=step_input,
            available_resources=resource_set,
            station_affordances=station_set,
            allow_safe_partial_continuation=allow_safe_partial_continuation,
        )
        step_traces.append(step_trace)
        verifications.extend(step_verifications)
        all_blocked.extend(step_blocked)
        run_residue.extend(step_trace.residue_refs)
        run_uncertainty.extend(step_trace.uncertainty_refs)

        trace_issues = validate_p17b_step_trace(step_trace)
        all_blocked.extend(trace_issues)

        for verified_ref in step_trace.verified_intermediate_refs:
            resource_set.add(verified_ref)

        next_step_ref = step_inputs[idx + 1].step_spec.step_id if idx + 1 < len(step_inputs) else None
        decision = decide_p17b_chain_advance(
            decision_id=f"advance:{step_trace.step_id}",
            current_step_ref=step_trace.step_id,
            next_step_ref=next_step_ref,
            required_verified_intermediate_refs=step_trace.expected_effect_refs,
            verified_intermediate_refs=step_trace.verified_intermediate_refs,
            source_refs=step_input.step_spec.source_refs,
            residue_refs=step_trace.residue_refs,
        )
        decisions.append(decision)
        all_blocked.extend(decision.blocked_reasons)

        if step_trace.status in {P17BStepStatus.FAILED, P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED}:
            if step_trace.residue_refs:
                stops.append(
                    build_p17b_residue_stop(
                        stop_id=f"stop:{step_trace.step_id}",
                        failed_step_ref=step_trace.step_id,
                        residue_refs=step_trace.residue_refs,
                        unresolved_refs=tuple(step_trace.expected_effect_refs),
                        blocked_downstream_step_refs=tuple(
                            item.step_spec.step_id for item in step_inputs[idx + 1 :]
                        ),
                        next_pressure_refs=(f"pressure:recover:{step_trace.step_id}",),
                        stop_reason=P17BBlockedReason.FAILED_STEP_RESIDUE_OPEN,
                        continuation_allowed=allow_safe_partial_continuation,
                    )
                )
                all_blocked.append(P17BBlockedReason.FAILED_STEP_RESIDUE_OPEN)
            if not allow_safe_partial_continuation:
                break

    verified_refs = {ref for trace in step_traces for ref in trace.verified_intermediate_refs}
    final_verified = bool(final_target_refs) and all(ref in verified_refs for ref in final_target_refs)

    if not step_traces:
        final_status = P17BRunStatus.NOOP
        all_blocked.append(P17BBlockedReason.COMPLETION_WITHOUT_TRACE)
    elif final_verified and not any(
        trace.status in {P17BStepStatus.BLOCKED, P17BStepStatus.FAILED, P17BStepStatus.UNRESOLVED}
        for trace in step_traces
    ):
        final_status = P17BRunStatus.COMPLETED_BOUNDED_FIXTURE
    elif any(trace.status is P17BStepStatus.FAILED for trace in step_traces):
        final_status = P17BRunStatus.FAILED
    elif any(trace.status in {P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED} for trace in step_traces):
        final_status = P17BRunStatus.BLOCKED
    elif any(trace.status is P17BStepStatus.INTERMEDIATE_VERIFIED for trace in step_traces):
        final_status = P17BRunStatus.PARTIAL
    else:
        final_status = P17BRunStatus.NOOP

    if final_status is P17BRunStatus.COMPLETED_BOUNDED_FIXTURE and any(
        reason in all_blocked for reason in (P17BBlockedReason.NOOP_OR_BLOCKED_CLAIMED_COMPLETED, P17BBlockedReason.COMPLETION_WITHOUT_TRACE)
    ):
        final_status = P17BRunStatus.BLOCKED
    if final_status is P17BRunStatus.COMPLETED_BOUNDED_FIXTURE and (
        not step_traces or any(trace.status in {P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED, P17BStepStatus.FAILED} for trace in step_traces)
    ):
        all_blocked.append(P17BBlockedReason.NOOP_OR_BLOCKED_CLAIMED_COMPLETED)
        final_status = P17BRunStatus.BLOCKED

    counters = _build_counters(step_traces=tuple(step_traces), verification_records=tuple(verifications), blocked_reasons=tuple(all_blocked))

    run = P17BLiveMiniFactoryRun(
        run_id=run_id,
        need=need,
        step_specs=tuple(item.step_spec for item in step_inputs),
        step_traces=tuple(step_traces),
        verification_records=tuple(verifications),
        advance_decisions=tuple(decisions),
        residue_stop_frames=tuple(stops),
        world0_run_refs=world0_run_refs,
        final_target_refs=final_target_refs,
        final_status=final_status,
        counters=counters,
        replay_trace_ref=replay_trace_ref or f"p17b:replay:{run_id}",
        source_refs=source_refs,
        residue_refs=tuple(dict.fromkeys(run_residue)),
        uncertainty_refs=tuple(dict.fromkeys(run_uncertainty)),
        blocked_reasons=tuple(dict.fromkeys(all_blocked)),
        no_factory_script=True,
        no_hidden_recipe=True,
        no_general_automation_claim=True,
        no_mature_skill_claim=True,
        no_general_autonomy_claim=True,
        authority_flags=P17BAuthorityFlags(),
    )
    return run


def validate_p17b_live_run(run: P17BLiveMiniFactoryRun) -> tuple[P17BBlockedReason, ...]:
    blocked: list[P17BBlockedReason] = []
    joined = _joined(
        run.run_id,
        run.source_refs,
        run.final_target_refs,
        *(trace.step_id for trace in run.step_traces),
        *(reason.value for reason in run.blocked_reasons),
    )
    if _contains_any(joined, _HIDDEN_RECIPE_TOKENS):
        blocked.append(P17BBlockedReason.HIDDEN_RECIPE_DETECTED)
    if _contains_any(joined, _WORLDSTATE_TOKENS):
        blocked.append(P17BBlockedReason.BACKEND_WORLDSTATE_DETECTED)
    if _contains_any(joined, _SCENARIO_TOKENS):
        blocked.append(P17BBlockedReason.SCENARIO_LABEL_DETECTED)
    if _contains_any(joined, _PROOF_ONLY_TOKENS):
        blocked.append(P17BBlockedReason.P17_PROOF_AS_LIVE_EXECUTION_DETECTED)
    if run.final_status is P17BRunStatus.COMPLETED_BOUNDED_FIXTURE and not run.step_traces:
        blocked.append(P17BBlockedReason.COMPLETION_WITHOUT_TRACE)
    if run.final_status is P17BRunStatus.COMPLETED_BOUNDED_FIXTURE and any(
        trace.status in {P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED, P17BStepStatus.FAILED}
        for trace in run.step_traces
    ):
        blocked.append(P17BBlockedReason.NOOP_OR_BLOCKED_CLAIMED_COMPLETED)
    if run.final_status is P17BRunStatus.COMPLETED_BOUNDED_FIXTURE and not run.world0_run_refs:
        blocked.append(P17BBlockedReason.MISSING_WORLD0_LINEAGE)
    if any(trace.backend_execution_refs and not trace.ap01_request_refs for trace in run.step_traces):
        blocked.append(P17BBlockedReason.EXECUTION_WITHOUT_AP01)
    if any(
        (
            trace.ap01_request_refs
            or trace.backend_execution_refs
            or trace.world_effect_feedback_refs
            or trace.observed_effect_refs
        ) and (not trace.cycle_refs or not trace.world0_run_ref)
        for trace in run.step_traces
    ):
        blocked.append(P17BBlockedReason.MISSING_WORLD0_LINEAGE)
    if any(
        trace.ap01_request_refs and any(not ref.lower().startswith("ap01:") for ref in trace.ap01_request_refs)
        for trace in run.step_traces
    ):
        blocked.append(P17BBlockedReason.INVALID_AP01_LINEAGE)
    failed_or_blocked_ids = {
        trace.step_id
        for trace in run.step_traces
        if trace.status in {P17BStepStatus.FAILED, P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED}
    }
    if failed_or_blocked_ids and not run.residue_stop_frames:
        blocked.append(P17BBlockedReason.TRACE_OMITS_FAILED_STEP)
    if any(stop.failed_step_ref not in {trace.step_id for trace in run.step_traces} for stop in run.residue_stop_frames):
        blocked.append(P17BBlockedReason.TRACE_OMITS_FAILED_STEP)
    if failed_or_blocked_ids and not run.residue_refs:
        blocked.append(P17BBlockedReason.RESIDUE_NOT_PRESERVED)

    expected_counters = _build_counters(
        step_traces=run.step_traces,
        verification_records=run.verification_records,
        blocked_reasons=run.blocked_reasons,
    )
    if expected_counters != run.counters:
        blocked.append(P17BBlockedReason.COUNTERS_MISMATCH)
    return tuple(dict.fromkeys(blocked))


def validate_step_requires_ap01_and_effect(step_trace: P17BFactoryStepTrace) -> tuple[P17BBlockedReason, ...]:
    blocked: list[P17BBlockedReason] = []
    if not step_trace.ap01_request_refs:
        blocked.append(P17BBlockedReason.MISSING_AP01_REQUEST)
    if step_trace.ap01_request_refs and not step_trace.world_effect_feedback_refs:
        blocked.append(P17BBlockedReason.MISSING_WORLD_EFFECT)
    return tuple(blocked)


def validate_downstream_requires_verified_intermediate(
    step_trace: P17BFactoryStepTrace,
    decision: P17BChainAdvanceDecision,
) -> tuple[P17BBlockedReason, ...]:
    blocked: list[P17BBlockedReason] = []
    if not step_trace.verified_intermediate_refs and decision.next_step_ref is not None:
        blocked.append(P17BBlockedReason.DOWNSTREAM_WITHOUT_VERIFIED_INTERMEDIATE)
    return tuple(blocked)


def validate_failed_step_preserves_residue(step_trace: P17BFactoryStepTrace) -> tuple[P17BBlockedReason, ...]:
    if step_trace.status in {P17BStepStatus.FAILED, P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED} and not step_trace.residue_refs:
        return (P17BBlockedReason.RESIDUE_NOT_PRESERVED,)
    return ()


def summarize_p17b_run(run: P17BLiveMiniFactoryRun) -> dict[str, object]:
    return {
        "run_id": run.run_id,
        "final_status": run.final_status.value,
        "step_statuses": tuple(trace.status.value for trace in run.step_traces),
        "blocked_reasons": tuple(reason.value for reason in run.blocked_reasons),
        "world0_run_refs": run.world0_run_refs,
        "counters": asdict(run.counters),
        "authority_flags": asdict(run.authority_flags),
        "no_factory_script": run.no_factory_script,
        "no_hidden_recipe": run.no_hidden_recipe,
        "no_general_automation_claim": run.no_general_automation_claim,
        "no_mature_skill_claim": run.no_mature_skill_claim,
        "no_general_autonomy_claim": run.no_general_autonomy_claim,
    }


def _build_counters(
    *,
    step_traces: tuple[P17BFactoryStepTrace, ...],
    verification_records: tuple[P17BIntermediateVerification, ...],
    blocked_reasons: tuple[P17BBlockedReason, ...],
) -> P17BCounters:
    return P17BCounters(
        step_count=len(step_traces),
        completed_step_count=sum(1 for step in step_traces if step.status is P17BStepStatus.INTERMEDIATE_VERIFIED),
        blocked_step_count=sum(1 for step in step_traces if step.status is P17BStepStatus.BLOCKED),
        failed_step_count=sum(1 for step in step_traces if step.status is P17BStepStatus.FAILED),
        verified_intermediate_count=sum(1 for rec in verification_records if rec.verified),
        unverified_intermediate_count=sum(1 for rec in verification_records if not rec.verified),
        ap01_request_count=sum(len(step.ap01_request_refs) for step in step_traces),
        world0_cycle_count=sum(len(step.cycle_refs) for step in step_traces),
        backend_execution_count=sum(len(step.backend_execution_refs) for step in step_traces),
        residue_count=sum(len(step.residue_refs) for step in step_traces),
        chain_advance_count=sum(1 for _ in step_traces),
        chain_block_count=sum(1 for reason in blocked_reasons if reason is P17BBlockedReason.DOWNSTREAM_WITHOUT_VERIFIED_INTERMEDIATE),
        shortcut_block_count=sum(
            1
            for reason in blocked_reasons
            if reason
            in {
                P17BBlockedReason.COST_WINNER_AS_PERMISSION_DETECTED,
                P17BBlockedReason.PROVIDER_HINT_AS_TRUTH_DETECTED,
                P17BBlockedReason.ADAPTER_SOLUTION_SEQUENCE_DETECTED,
                P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED,
            }
        ),
        hidden_recipe_block_count=sum(1 for reason in blocked_reasons if reason is P17BBlockedReason.HIDDEN_RECIPE_DETECTED),
        adapter_script_block_count=sum(1 for reason in blocked_reasons if reason is P17BBlockedReason.ADAPTER_SOLUTION_SEQUENCE_DETECTED),
        cost_permission_block_count=sum(1 for reason in blocked_reasons if reason is P17BBlockedReason.COST_WINNER_AS_PERMISSION_DETECTED),
        provider_truth_block_count=sum(1 for reason in blocked_reasons if reason is P17BBlockedReason.PROVIDER_HINT_AS_TRUTH_DETECTED),
    )


def _contains_any(haystack: str, tokens: tuple[str, ...]) -> bool:
    return any(token in haystack for token in tokens)


def _joined(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        parts.extend(_flatten_tokens(value))
    return " ".join(parts).lower()


def _flatten_tokens(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        parts: list[str] = []
        for key, nested in value.items():
            parts.extend(_flatten_tokens(key))
            parts.extend(_flatten_tokens(nested))
        return tuple(parts)
    if isinstance(value, (tuple, list, set, frozenset)):
        parts: list[str] = []
        for item in value:
            parts.extend(_flatten_tokens(item))
        return tuple(parts)
    if hasattr(value, "__dict__"):
        return _flatten_tokens(vars(value))
    return (str(value),)
