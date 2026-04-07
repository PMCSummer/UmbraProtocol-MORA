from __future__ import annotations

from dataclasses import replace

from substrate.affordances import (
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.affordances.policy import evaluate_affordance_landscape_for_downstream
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.mode_arbitration import (
    ModeArbitrationContext,
    ModeArbitrationState,
    build_mode_arbitration,
    choose_subject_execution_mode,
    derive_mode_arbitration_contract_view,
)
from substrate.regulation import (
    NeedAxis,
    NeedSignal,
    RegulationContext,
    RegulationGateDecision,
    RegulationState,
    evaluate_downstream_regulation_gate,
    update_regulation_state,
)
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    PreferenceState,
    evaluate_preference_downstream_gate,
    update_regulatory_preferences,
)
from substrate.stream_diversification import (
    StreamDiversificationContext,
    StreamDiversificationState,
    build_stream_diversification,
    choose_diversification_execution_mode,
    derive_stream_diversification_contract_view,
)
from substrate.stream_kernel import (
    StreamKernelContext,
    StreamKernelState,
    build_stream_kernel,
    choose_stream_execution_mode,
    derive_stream_kernel_contract_view,
)
from substrate.subject_tick.models import (
    SubjectTickAuthorityRole,
    SubjectTickCheckpointResult,
    SubjectTickCheckpointStatus,
    SubjectTickComputationalRole,
    SubjectTickContext,
    SubjectTickExecutionStance,
    SubjectTickInput,
    SubjectTickOutcome,
    SubjectTickRoleMapSource,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickStepResult,
    SubjectTickStepStatus,
)
from substrate.subject_tick.policy import evaluate_subject_tick_downstream_gate
from substrate.subject_tick.telemetry import (
    build_subject_tick_telemetry,
    subject_tick_result_snapshot,
)
from substrate.temporal_validity import (
    TemporalValidityContext,
    TemporalValidityState,
    build_temporal_validity,
    can_continue_mode_hold,
    can_open_branch_access,
    can_revisit_with_basis,
    choose_temporal_reuse_execution_mode,
    derive_temporal_validity_contract_view,
)
from substrate.tension_scheduler import (
    TensionSchedulerContext,
    TensionSchedulerState,
    build_tension_scheduler,
    choose_tension_execution_mode,
    derive_tension_scheduler_contract_view,
)
from substrate.transition import execute_transition
from substrate.viability_control import (
    ViabilityContext,
    ViabilityControlState,
    compute_viability_control_state,
    evaluate_viability_downstream_gate,
)


ATTEMPTED_SUBJECT_TICK_PATHS: tuple[str, ...] = (
    "subject_tick.run_regulation_stack",
    "subject_tick.run_c01_stream_kernel",
    "subject_tick.run_c02_tension_scheduler",
    "subject_tick.run_c03_stream_diversification",
    "subject_tick.run_c04_mode_arbitration",
    "subject_tick.run_c05_temporal_validity",
    "subject_tick.enforce_c04_c05_contract_obedience",
    "subject_tick.resolve_bounded_runtime_outcome",
    "subject_tick.downstream_gate",
)

DEFAULT_PHASE_AUTHORITY_ROLES: dict[str, SubjectTickAuthorityRole] = {
    "F01": SubjectTickAuthorityRole.OBSERVABILITY_ONLY,
    "R04": SubjectTickAuthorityRole.GATING,
    "C04": SubjectTickAuthorityRole.ARBITRATION,
    "C05": SubjectTickAuthorityRole.INVALIDATION,
    "D01": SubjectTickAuthorityRole.OBSERVABILITY_ONLY,
    "RT01": SubjectTickAuthorityRole.GATING,
}

DEFAULT_PHASE_COMPUTATIONAL_ROLES: dict[str, SubjectTickComputationalRole] = {
    "F01": SubjectTickComputationalRole.BRIDGE_CONTRACT,
    "R04": SubjectTickComputationalRole.EVALUATOR,
    "C04": SubjectTickComputationalRole.SCHEDULER,
    "C05": SubjectTickComputationalRole.EVALUATOR,
    "D01": SubjectTickComputationalRole.OBSERVABILITY,
    "RT01": SubjectTickComputationalRole.EXECUTION_SPINE,
}

ROLE_FRONTIER_CODES: tuple[str, ...] = tuple(DEFAULT_PHASE_AUTHORITY_ROLES.keys())
ROLE_FALLBACK_AUTHORITY = SubjectTickAuthorityRole.COMPUTATIONAL.value
ROLE_FALLBACK_COMPUTATIONAL = SubjectTickComputationalRole.UNKNOWN.value


def execute_subject_tick(
    tick_input: SubjectTickInput,
    context: SubjectTickContext | None = None,
) -> SubjectTickResult:
    if not isinstance(tick_input, SubjectTickInput):
        raise TypeError("execute_subject_tick requires SubjectTickInput")
    context = context or SubjectTickContext()
    if not isinstance(context, SubjectTickContext):
        raise TypeError("context must be SubjectTickContext")

    prior_state = context.prior_subject_tick_state
    tick_index = 1 if prior_state is None else prior_state.tick_index + 1
    tick_id = f"subject-tick-{tick_input.case_id}-{tick_index}"
    lineage = tuple(dict.fromkeys((*context.source_lineage, f"subject-tick:{tick_input.case_id}")))
    (
        authority_roles,
        computational_roles,
        role_source_ref,
        role_frontier_only,
        role_map_ready,
        role_frontier_typed,
    ) = _resolve_phase_role_contract(context)
    f01_authority_role = authority_roles["F01"].value
    r04_authority_role = authority_roles["R04"].value
    c04_authority_role = authority_roles["C04"].value
    c05_authority_role = authority_roles["C05"].value
    d01_authority_role = authority_roles["D01"].value
    rt01_authority_role = authority_roles["RT01"].value
    f01_computational_role = computational_roles["F01"].value
    r04_computational_role = computational_roles["R04"].value
    c04_computational_role = computational_roles["C04"].value
    c05_computational_role = computational_roles["C05"].value
    d01_computational_role = computational_roles["D01"].value
    rt01_computational_role = computational_roles["RT01"].value

    regulation = update_regulation_state(
        (
            NeedSignal(
                axis=NeedAxis.ENERGY,
                value=tick_input.energy,
                source_ref=f"{tick_id}-energy",
            ),
            NeedSignal(
                axis=NeedAxis.COGNITIVE_LOAD,
                value=tick_input.cognitive,
                source_ref=f"{tick_id}-cognitive",
            ),
            NeedSignal(
                axis=NeedAxis.SAFETY,
                value=tick_input.safety,
                source_ref=f"{tick_id}-safety",
            ),
        ),
        prior_state=(
            context.prior_regulation_state
            if isinstance(context.prior_regulation_state, RegulationState)
            else None
        ),
        context=RegulationContext(
            source_lineage=lineage,
            require_strong_claim=context.require_strong_regulation_claim,
        ),
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation.state,
        capability_state=create_default_capability_state(),
    )
    candidate = next(
        (
            item
            for item in affordances.candidates
            if item.status.value == "available"
        ),
        affordances.candidates[0],
    )
    if tick_input.unresolved_preference:
        short_delta = 0.35
        long_delta = None
        delayed_complete = False
    else:
        short_delta = 0.55
        long_delta = 0.3
        delayed_complete = True
    preferences = update_regulatory_preferences(
        regulation_state=regulation.state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id=f"ep-{tick_id}",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("subject_tick", tick_input.case_id),
                observed_short_term_delta=short_delta,
                observed_long_term_delta=long_delta,
                attribution_confidence=regulation.state.confidence,
                delayed_window_complete=delayed_complete,
                observed_at_step=tick_index,
            ),
        ),
        context=PreferenceContext(source_lineage=lineage),
    )
    viability = compute_viability_control_state(
        regulation,
        affordances,
        preferences,
        context=ViabilityContext(
            source_lineage=lineage,
            prior_regulation_state=context.prior_regulation_state,
            prior_viability_state=(
                context.prior_viability_state
                if isinstance(context.prior_viability_state, ViabilityControlState)
                else None
            ),
        ),
    )

    regulation_gate = evaluate_downstream_regulation_gate(
        regulation.bias,
        require_strong_claim=context.require_strong_regulation_claim,
    )
    affordance_gate = evaluate_affordance_landscape_for_downstream(
        affordances.candidates,
        require_available=context.require_available_affordance,
    )
    preference_gate = evaluate_preference_downstream_gate(preferences)
    viability_gate = evaluate_viability_downstream_gate(viability)
    r_gate_accepted = (
        regulation_gate.allowed
        and bool(affordance_gate.accepted_candidate_ids)
        and preference_gate.accepted
    )

    stream = build_stream_kernel(
        regulation,
        affordances,
        preferences,
        viability,
        context=StreamKernelContext(
            prior_stream_state=(
                context.prior_stream_state
                if isinstance(context.prior_stream_state, StreamKernelState)
                else None
            ),
            source_lineage=lineage,
        ),
    )
    stream_view = derive_stream_kernel_contract_view(stream)
    stream_mode = choose_stream_execution_mode(stream)

    scheduler = build_tension_scheduler(
        stream,
        regulation,
        affordances,
        preferences,
        viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=(
                context.prior_scheduler_state
                if isinstance(context.prior_scheduler_state, TensionSchedulerState)
                else None
            ),
            source_lineage=lineage,
        ),
    )
    scheduler_view = derive_tension_scheduler_contract_view(scheduler)
    scheduler_mode = choose_tension_execution_mode(scheduler)

    diversification = build_stream_diversification(
        stream,
        scheduler,
        regulation,
        affordances,
        preferences,
        viability,
        context=StreamDiversificationContext(
            prior_diversification_state=(
                context.prior_diversification_state
                if isinstance(context.prior_diversification_state, StreamDiversificationState)
                else None
            ),
            source_lineage=lineage,
        ),
    )
    diversification_view = derive_stream_diversification_contract_view(diversification)
    diversification_mode = choose_diversification_execution_mode(diversification)

    mode_arbitration = build_mode_arbitration(
        stream,
        scheduler,
        diversification,
        regulation,
        affordances,
        preferences,
        viability,
        context=ModeArbitrationContext(
            prior_mode_arbitration_state=(
                context.prior_mode_state
                if isinstance(context.prior_mode_state, ModeArbitrationState)
                else None
            ),
            external_turn_present=context.external_turn_present,
            allow_endogenous_tick=context.allow_endogenous_tick,
            resource_budget=context.mode_resource_budget,
            cooldown_active=context.mode_cooldown_active,
            source_lineage=lineage,
        ),
    )
    mode_view = derive_mode_arbitration_contract_view(mode_arbitration)
    c04_execution_mode = choose_subject_execution_mode(mode_arbitration)

    temporal_validity = build_temporal_validity(
        stream,
        scheduler,
        diversification,
        mode_arbitration,
        regulation,
        affordances,
        preferences,
        viability,
        context=TemporalValidityContext(
            prior_temporal_validity_state=(
                context.prior_temporal_validity_state
                if isinstance(context.prior_temporal_validity_state, TemporalValidityState)
                else None
            ),
            dependency_trigger_hits=context.dependency_trigger_hits,
            context_shift_markers=context.context_shift_markers,
            contradicted_source_refs=context.contradicted_source_refs,
            withdrawn_source_refs=context.withdrawn_source_refs,
            allow_provisional_carry=context.allow_provisional_carry,
            source_lineage=lineage,
        ),
    )
    temporal_view = derive_temporal_validity_contract_view(temporal_validity)
    c05_validity_action = choose_temporal_reuse_execution_mode(temporal_validity)

    c04_execution_mode_claim = c04_execution_mode
    c05_execution_action_claim = c05_validity_action
    active_execution_mode = c04_execution_mode_claim
    repair_needed = False
    revalidation_needed = False
    halt_reason: str | None = None
    checkpoints: list[SubjectTickCheckpointResult] = []
    c05_enforcement_authority = c05_authority_role in {
        SubjectTickAuthorityRole.GATING.value,
        SubjectTickAuthorityRole.INVALIDATION.value,
    }

    if c04_authority_role != SubjectTickAuthorityRole.ARBITRATION.value:
        active_execution_mode = "repair_runtime_path"
        repair_needed = True
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c04_mode_binding",
                source_contract="c04.mode_arbitration",
                status=SubjectTickCheckpointStatus.BLOCKED,
                required_action=SubjectTickAuthorityRole.ARBITRATION.value,
                applied_action=c04_authority_role,
                reason="rt01 rejected c04 mode claim because roadmap authority_role is not arbitration",
            )
        )
    elif not context.disable_c04_mode_execution_binding:
        active_execution_mode = c04_execution_mode_claim
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c04_mode_binding",
                source_contract="c04.mode_arbitration",
                status=SubjectTickCheckpointStatus.ALLOWED,
                required_action=c04_execution_mode_claim,
                applied_action=active_execution_mode,
                reason="rt01 consumed c04 execution mode claim without reinterpretation",
            )
        )
    else:
        active_execution_mode = stream_mode
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c04_mode_binding",
                source_contract="c04.mode_arbitration",
                status=SubjectTickCheckpointStatus.ENFORCED_DETOUR,
                required_action=c04_execution_mode_claim,
                applied_action=active_execution_mode,
                reason="c04 mode binding disabled in ablation context",
            )
        )

    if not c05_enforcement_authority:
        repair_needed = True
        active_execution_mode = "repair_runtime_path"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c05_legality_checkpoint",
                source_contract="c05.temporal_validity",
                status=SubjectTickCheckpointStatus.BLOCKED,
                required_action="gating_or_invalidation",
                applied_action=c05_authority_role,
                reason="rt01 refused applying c05 legality as authority because roadmap authority_role is non-enforcement",
            )
        )
    elif not context.disable_c05_validity_enforcement:
        c05_status = SubjectTickCheckpointStatus.ALLOWED
        c05_reason = "c05 legality allows bounded reuse path"
        prior_mode = active_execution_mode
        if active_execution_mode == "continue_stream" and not can_continue_mode_hold(temporal_validity):
            active_execution_mode = "revalidate_mode_hold"
            revalidation_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 blocked mode hold reuse; revalidation detour enforced"
        if active_execution_mode == "run_revisit" and not can_revisit_with_basis(temporal_validity):
            active_execution_mode = "revalidate_revisit_basis"
            revalidation_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 blocked revisit basis reuse; revalidation detour enforced"
        if active_execution_mode == "probe_alternatives" and not can_open_branch_access(temporal_validity):
            active_execution_mode = "repair_branch_access"
            repair_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 blocked branch access; repair detour enforced"
        if c05_validity_action in {
            "run_selective_revalidation",
            "run_bounded_revalidation",
            "suspend_until_revalidation_basis",
        }:
            active_execution_mode = "revalidate_scope"
            revalidation_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 requested revalidation scope before runtime continuation"
        if c05_validity_action == "halt_reuse_and_rebuild_scope":
            active_execution_mode = "halt_execution"
            halt_reason = "c05_halt_reuse_and_rebuild_scope"
            c05_status = SubjectTickCheckpointStatus.BLOCKED
            c05_reason = "c05 halted reuse legality; runtime continuation blocked"
        if c05_status == SubjectTickCheckpointStatus.ALLOWED and prior_mode != active_execution_mode:
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 enforcement changed runtime execution path"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c05_legality_checkpoint",
                source_contract="c05.temporal_validity",
                status=c05_status,
                required_action=c05_execution_action_claim,
                applied_action=active_execution_mode,
                reason=c05_reason,
            )
        )
    else:
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c05_legality_checkpoint",
                source_contract="c05.temporal_validity",
                status=SubjectTickCheckpointStatus.ENFORCED_DETOUR,
                required_action=c05_execution_action_claim,
                applied_action=active_execution_mode,
                reason="c05 legality enforcement disabled in ablation context",
            )
        )

    revalidation_modes = {"revalidate_mode_hold", "revalidate_revisit_basis", "revalidate_scope"}
    if d01_authority_role != SubjectTickAuthorityRole.OBSERVABILITY_ONLY.value:
        repair_needed = True
        if halt_reason is None and active_execution_mode not in revalidation_modes:
            active_execution_mode = "repair_runtime_path"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.d01_observability_guard",
                source_contract="d01.observability_boundary",
                status=SubjectTickCheckpointStatus.ENFORCED_DETOUR,
                required_action=SubjectTickAuthorityRole.OBSERVABILITY_ONLY.value,
                applied_action=d01_authority_role,
                reason="rt01 kept D01 out of enforcement authority and downgraded runtime stance to repair",
            )
        )
    else:
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.d01_observability_guard",
                source_contract="d01.observability_boundary",
                status=SubjectTickCheckpointStatus.ALLOWED,
                required_action=SubjectTickAuthorityRole.OBSERVABILITY_ONLY.value,
                applied_action=d01_authority_role,
                reason="d01 remains observability-only and is not used as enforcement authority",
            )
        )

    role_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    role_checkpoint_reason = "rt01 consumed phase authority roles under bounded frontier contract"
    if rt01_authority_role != SubjectTickAuthorityRole.GATING.value:
        repair_needed = True
        role_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        role_checkpoint_reason = "rt01 authority_role mismatch: execution spine must remain gating authority surface"
    if f01_authority_role != SubjectTickAuthorityRole.OBSERVABILITY_ONLY.value:
        repair_needed = True
        role_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        role_checkpoint_reason = "f01 authority_role mismatch: f01 must remain observability/transition spine surface"
    if role_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        if halt_reason is None and active_execution_mode not in revalidation_modes:
            active_execution_mode = "repair_runtime_path"
        role_checkpoint_reason = (
            f"{role_checkpoint_reason}; runtime detoured to bounded repair stance"
        )
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.authority_role_checkpoint",
            source_contract="roadmap.phase_role_contract",
            status=role_checkpoint_status,
            required_action="f01=observability_only; c04=arbitration; c05=gating|invalidation; d01=observability_only; rt01=gating",
            applied_action=(
                f"f01={f01_authority_role}; c04={c04_authority_role}; "
                f"c05={c05_authority_role}; d01={d01_authority_role}; "
                f"rt01={rt01_authority_role}; runtime_mode={active_execution_mode}"
            ),
            reason=role_checkpoint_reason,
        )
    )
    if not role_frontier_typed:
        repair_needed = True
        if halt_reason is None and active_execution_mode not in revalidation_modes:
            active_execution_mode = "repair_runtime_path"
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.role_coverage_checkpoint",
            source_contract="roadmap.role_readiness_contract",
            status=(
                SubjectTickCheckpointStatus.ALLOWED
                if role_frontier_typed
                else SubjectTickCheckpointStatus.ENFORCED_DETOUR
            ),
            required_action="frontier_role_typed_required_for_honest_runtime_authority_enforcement",
            applied_action=(
                f"source={role_source_ref}; frontier_only={role_frontier_only}; "
                f"map_ready={role_map_ready}; frontier_typed={role_frontier_typed}"
            ),
            reason=(
                "rt01 consumed explicit role-readiness envelope and kept frontier-only claim bounded"
                if role_frontier_typed
                else "frontier role typing incomplete; runtime detoured to repair stance instead of overclaiming authority readiness"
            ),
        )
    )

    if not context.disable_gate_application:
        gate_reasons: list[str] = []
        if c05_enforcement_authority and c05_validity_action == "halt_reuse_and_rebuild_scope" and halt_reason is None:
            halt_reason = "c05_halt_reuse_and_rebuild_scope"
            gate_reasons.append("c05_halt_reuse_action")
        if c05_enforcement_authority and c05_validity_action in {
            "run_selective_revalidation",
            "run_bounded_revalidation",
            "suspend_until_revalidation_basis",
        }:
            revalidation_needed = True
            gate_reasons.append("c05_revalidation_action")
        if not r_gate_accepted or not stream_view.gate_accepted:
            repair_needed = True
            gate_reasons.append("r_or_c01_gate_degraded")
        if not scheduler_view.gate_accepted or not diversification_view.gate_accepted:
            repair_needed = True
            gate_reasons.append("c02_or_c03_gate_degraded")
        if not mode_view.gate_accepted and halt_reason is None:
            repair_needed = True
            gate_reasons.append("c04_gate_degraded")
        if (
            active_execution_mode in {"hold_safe_idle", "idle"}
            and stream_mode in {"continue_existing_stream", "continue_with_limits", "resume_or_hold"}
            and halt_reason is None
            and not revalidation_needed
        ):
            repair_needed = True
            gate_reasons.append("stream_continuity_requires_non_idle_path")
        gate_status = (
            SubjectTickCheckpointStatus.ALLOWED
            if not gate_reasons
            else SubjectTickCheckpointStatus.ENFORCED_DETOUR
        )
        gate_reason = (
            "all runtime contour gates passed without critical detour"
            if not gate_reasons
            else f"critical gate checkpoint enforced detour: {','.join(gate_reasons)}"
        )
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.critical_gate_checkpoint",
                source_contract="rt01.phase_contract_gates",
                status=gate_status,
                required_action="enforce_runtime_gate_restrictions",
                applied_action=active_execution_mode,
                reason=gate_reason,
            )
        )
    else:
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.critical_gate_checkpoint",
                source_contract="rt01.phase_contract_gates",
                status=SubjectTickCheckpointStatus.ENFORCED_DETOUR,
                required_action="enforce_runtime_gate_restrictions",
                applied_action=active_execution_mode,
                reason="runtime gate application disabled in ablation context",
            )
        )

    if halt_reason is not None:
        final_outcome = SubjectTickOutcome.HALT
        execution_stance = SubjectTickExecutionStance.HALT_PATH
    elif revalidation_needed:
        final_outcome = SubjectTickOutcome.REVALIDATE
        execution_stance = SubjectTickExecutionStance.REVALIDATE_PATH
    elif repair_needed:
        final_outcome = SubjectTickOutcome.REPAIR
        execution_stance = SubjectTickExecutionStance.REPAIR_PATH
        if active_execution_mode not in {"repair_branch_access", "repair_runtime_path"}:
            active_execution_mode = "repair_runtime_path"
    else:
        final_outcome = SubjectTickOutcome.CONTINUE
        execution_stance = SubjectTickExecutionStance.CONTINUE_PATH

    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.outcome_resolution_checkpoint",
            source_contract="rt01.runtime_outcome",
            status=(
                SubjectTickCheckpointStatus.BLOCKED
                if final_outcome == SubjectTickOutcome.HALT
                else SubjectTickCheckpointStatus.ENFORCED_DETOUR
                if final_outcome != SubjectTickOutcome.CONTINUE
                else SubjectTickCheckpointStatus.ALLOWED
            ),
            required_action="bounded_outcome_must_be_resolved",
            applied_action=f"{execution_stance.value}:{active_execution_mode}",
            reason="runtime contour resolved bounded outcome from enforced contracts",
        )
    )

    r_restrictions = tuple(
        dict.fromkeys(
            (
                *regulation_gate.applied_restrictions,
                *affordance_gate.restrictions,
                *preference_gate.restrictions,
                *viability_gate.restrictions,
            )
        )
    )
    step_results = (
        SubjectTickStepResult(
            phase_id="R",
            status=SubjectTickStepStatus.EXECUTED if r_gate_accepted else SubjectTickStepStatus.BLOCKED,
            gate_accepted=r_gate_accepted,
            usability_class="usable_bounded" if r_gate_accepted else "degraded_bounded",
            execution_mode="r_update_ready",
            restrictions=r_restrictions,
            reason=(
                "regulation/affordance/preference/viability stack produced typed upstream basis"
                if r_gate_accepted
                else "r-stack gate degraded; downstream continuation must be repaired"
            ),
        ),
        _phase_step(
            phase_id="C01",
            gate_accepted=stream_view.gate_accepted,
            usability_class=stream_view.usability_class.value,
            execution_mode=stream_mode,
            restrictions=tuple(code.value for code in stream_view.restrictions),
            reason=stream_view.reason,
        ),
        _phase_step(
            phase_id="C02",
            gate_accepted=scheduler_view.gate_accepted,
            usability_class=scheduler_view.usability_class.value,
            execution_mode=scheduler_mode,
            restrictions=tuple(code.value for code in scheduler_view.restrictions),
            reason=scheduler_view.reason,
        ),
        _phase_step(
            phase_id="C03",
            gate_accepted=diversification_view.gate_accepted,
            usability_class=diversification_view.usability_class.value,
            execution_mode=diversification_mode,
            restrictions=tuple(code.value for code in diversification_view.restrictions),
            reason=diversification_view.reason,
        ),
        _phase_step(
            phase_id="C04",
            gate_accepted=mode_view.gate_accepted,
            usability_class=mode_view.usability_class.value,
            execution_mode=c04_execution_mode,
            restrictions=tuple(code.value for code in mode_view.restrictions),
            reason=mode_view.reason,
        ),
        _phase_step(
            phase_id="C05",
            gate_accepted=temporal_view.gate_accepted,
            usability_class=temporal_view.usability_class.value,
            execution_mode=c05_validity_action,
            restrictions=tuple(code.value for code in temporal_view.restrictions),
            reason=temporal_view.reason,
        ),
    )

    state = SubjectTickState(
        tick_id=tick_id,
        tick_index=tick_index,
        prior_runtime_status=None if prior_state is None else prior_state.final_execution_outcome,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_execution_action_claim=c05_execution_action_claim,
        f01_authority_role=f01_authority_role,
        r04_authority_role=r04_authority_role,
        c04_authority_role=c04_authority_role,
        c05_authority_role=c05_authority_role,
        d01_authority_role=d01_authority_role,
        rt01_authority_role=rt01_authority_role,
        f01_computational_role=f01_computational_role,
        r04_computational_role=r04_computational_role,
        c04_computational_role=c04_computational_role,
        c05_computational_role=c05_computational_role,
        d01_computational_role=d01_computational_role,
        rt01_computational_role=rt01_computational_role,
        role_source_ref=role_source_ref,
        role_frontier_only=role_frontier_only,
        role_map_ready=role_map_ready,
        role_frontier_typed=role_frontier_typed,
        active_execution_mode=active_execution_mode,
        c04_selected_mode=mode_arbitration.state.active_mode.value,
        c05_validity_action=c05_validity_action,
        execution_stance=execution_stance,
        execution_checkpoints=tuple(checkpoints),
        downstream_step_results=step_results,
        final_execution_outcome=final_outcome,
        repair_needed=repair_needed,
        revalidation_needed=revalidation_needed,
        halt_reason=halt_reason,
        source_stream_id=stream.state.stream_id,
        source_stream_sequence_index=stream.state.sequence_index,
        source_c01_state_ref=f"{stream.state.stream_id}@{stream.state.sequence_index}",
        source_c02_state_ref=(
            f"{scheduler.state.scheduler_id}@{scheduler.state.source_stream_sequence_index}"
        ),
        source_c03_state_ref=(
            f"{diversification.state.diversification_id}@{diversification.state.source_stream_sequence_index}"
        ),
        source_c04_state_ref=(
            f"{mode_arbitration.state.arbitration_id}@{mode_arbitration.state.source_stream_sequence_index}"
        ),
        source_c05_state_ref=(
            f"{temporal_validity.state.validity_id}@{temporal_validity.state.source_stream_sequence_index}"
        ),
        source_lineage=tuple(dict.fromkeys((*lineage, *stream.state.source_lineage))),
        last_update_provenance="subject_tick.runtime_contour_from_r_to_c05",
    )
    gate = evaluate_subject_tick_downstream_gate(state)
    telemetry = build_subject_tick_telemetry(
        state=state,
        attempted_paths=ATTEMPTED_SUBJECT_TICK_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "bounded runtime execution spine enforces roadmap authority roles for C04/C05 and keeps D01 observability-only over fixed R->C order"
        ),
    )
    abstain = final_outcome in {SubjectTickOutcome.REPAIR, SubjectTickOutcome.REVALIDATE}
    abstain_reason = (
        "halt_required_by_c05"
        if final_outcome == SubjectTickOutcome.HALT
        else "revalidation_required"
        if final_outcome == SubjectTickOutcome.REVALIDATE
        else "repair_required"
        if final_outcome == SubjectTickOutcome.REPAIR
        else None
    )
    return SubjectTickResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        regulation_result=regulation,
        affordance_result=affordances,
        preference_result=preferences,
        viability_result=viability,
        c01_result=stream,
        c02_result=scheduler,
        c03_result=diversification,
        c04_result=mode_arbitration,
        c05_result=temporal_validity,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_planner_orchestrator_dependency=True,
        no_phase_semantics_override_dependency=True,
    )


def subject_tick_result_to_payload(result: SubjectTickResult) -> dict[str, object]:
    return subject_tick_result_snapshot(result)


def persist_subject_tick_result_via_f01(
    *,
    result: SubjectTickResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("subject-tick-runtime-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"subject-tick-{result.state.tick_index}",
            "subject_tick_snapshot": subject_tick_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _normalize_authority_role(value: str | None) -> SubjectTickAuthorityRole:
    token = str(value or "").strip()
    try:
        return SubjectTickAuthorityRole(token)
    except ValueError:
        return SubjectTickAuthorityRole.COMPUTATIONAL


def _normalize_computational_role(value: str | None) -> SubjectTickComputationalRole:
    token = str(value or "").strip()
    try:
        return SubjectTickComputationalRole(token)
    except ValueError:
        return SubjectTickComputationalRole.UNKNOWN


def _resolve_phase_role_contract(
    context: SubjectTickContext,
) -> tuple[
    dict[str, SubjectTickAuthorityRole],
    dict[str, SubjectTickComputationalRole],
    str,
    bool,
    bool,
    bool,
]:
    authority_roles = dict(DEFAULT_PHASE_AUTHORITY_ROLES)
    computational_roles = dict(DEFAULT_PHASE_COMPUTATIONAL_ROLES)
    role_source_ref = "rt01.default_frontier_role_map"
    role_map_ready = False
    role_frontier_only = True

    # Backward-compatible local overrides remain supported.
    if context.phase_authority_roles or context.phase_computational_roles:
        role_source_ref = "rt01.context_role_overrides"
    for code, value in (context.phase_authority_roles or {}).items():
        normalized_code = str(code or "").strip().upper()
        if normalized_code in authority_roles:
            authority_roles[normalized_code] = _normalize_authority_role(value)
    for code, value in (context.phase_computational_roles or {}).items():
        normalized_code = str(code or "").strip().upper()
        if normalized_code in computational_roles:
            computational_roles[normalized_code] = _normalize_computational_role(value)

    # Explicit source-driven injection path has highest priority on frontier.
    injected = context.role_map_source
    if isinstance(injected, SubjectTickRoleMapSource):
        role_source_ref = str(injected.source_ref or "").strip() or "rt01.injected_role_map_source"
        role_map_ready = bool(injected.map_wide_role_ready)
        role_frontier_only = bool(injected.role_frontier_only)
        for code, value in (injected.phase_authority_roles or {}).items():
            normalized_code = str(code or "").strip().upper()
            if normalized_code in authority_roles:
                authority_roles[normalized_code] = _normalize_authority_role(value)
        for code, value in (injected.phase_computational_roles or {}).items():
            normalized_code = str(code or "").strip().upper()
            if normalized_code in computational_roles:
                computational_roles[normalized_code] = _normalize_computational_role(value)

    role_frontier_typed = _is_frontier_role_typed(authority_roles, computational_roles)
    if role_map_ready:
        role_frontier_only = False
    elif not role_frontier_typed:
        role_frontier_only = False

    return (
        authority_roles,
        computational_roles,
        role_source_ref,
        role_frontier_only,
        role_map_ready,
        role_frontier_typed,
    )


def _is_frontier_role_typed(
    authority_roles: dict[str, SubjectTickAuthorityRole],
    computational_roles: dict[str, SubjectTickComputationalRole],
) -> bool:
    for code in ROLE_FRONTIER_CODES:
        authority = authority_roles[code].value
        computational = computational_roles[code].value
        if authority == ROLE_FALLBACK_AUTHORITY and computational == ROLE_FALLBACK_COMPUTATIONAL:
            return False
    return True


def _phase_step(
    *,
    phase_id: str,
    gate_accepted: bool,
    usability_class: str,
    execution_mode: str | None,
    restrictions: tuple[str, ...],
    reason: str,
) -> SubjectTickStepResult:
    return SubjectTickStepResult(
        phase_id=phase_id,
        status=SubjectTickStepStatus.EXECUTED if gate_accepted else SubjectTickStepStatus.BLOCKED,
        gate_accepted=gate_accepted,
        usability_class=usability_class,
        execution_mode=execution_mode,
        restrictions=restrictions,
        reason=reason,
    )
