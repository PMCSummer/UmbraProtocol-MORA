from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from substrate.a_line_normalization import build_a_line_normalization
from substrate.m_minimal import build_m_minimal
from substrate.affordances import (
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.affordances.policy import evaluate_affordance_landscape_for_downstream
from substrate.authority import issue_rt01_route_auth_nonce
from substrate.downstream_obedience import (
    ObedienceFallback,
    build_downstream_obedience_decision,
)
from substrate.contracts import (
    ContinuityDomainState,
    DomainWriteClaim,
    DomainWriteRoute,
    DomainWriterPhase,
    RegulationDomainState,
    RuntimeState,
    RuntimeDomainUpdate,
    RuntimeRouteAuthContext,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    ValidityDomainState,
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
from substrate.world_adapter import run_world_adapter_cycle
from substrate.self_contour import build_s_minimal_contour
from substrate.world_entry_contract import build_world_entry_contract


ATTEMPTED_SUBJECT_TICK_PATHS: tuple[str, ...] = (
    "subject_tick.run_regulation_stack",
    "subject_tick.run_c01_stream_kernel",
    "subject_tick.run_c02_tension_scheduler",
    "subject_tick.run_c03_stream_diversification",
    "subject_tick.run_c04_mode_arbitration",
    "subject_tick.run_c05_temporal_validity",
    "subject_tick.enforce_c04_c05_contract_obedience",
    "subject_tick.enforce_downstream_obedience_contract",
    "subject_tick.evaluate_world_entry_contract",
    "subject_tick.evaluate_s_minimal_contour",
    "subject_tick.evaluate_a_line_normalization",
    "subject_tick.evaluate_m_minimal_contour",
    "subject_tick.world_seam_enforcement",
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

    c05_state = temporal_validity.state
    obedience_source_of_truth_surface = "phase_local.upstream_surfaces"
    obedience_c04_mode_legitimacy = mode_view.gate_accepted
    obedience_c05_legality_reuse_allowed = not bool(
        c05_state.invalidated_item_ids
        or c05_state.expired_item_ids
        or c05_state.dependency_contaminated_item_ids
        or c05_state.no_safe_reuse_item_ids
    )
    obedience_c05_revalidation_required = bool(
        c05_state.revalidation_item_ids
        or c05_state.selective_scope_targets
        or c05_state.insufficient_basis_for_revalidation
        or c05_state.selective_scope_uncertain
        or c05_validity_action
        in {"run_selective_revalidation", "run_bounded_revalidation", "suspend_until_revalidation_basis"}
    )
    obedience_c05_no_safe_reuse = bool(c05_state.no_safe_reuse_item_ids)
    obedience_c05_surface_invalidated = bool(
        c05_state.invalidated_item_ids
        or c05_state.expired_item_ids
        or c05_state.dependency_contaminated_item_ids
    )
    obedience_r04_override_scope = viability.state.override_scope.value
    obedience_r04_no_strong_override_claim = viability.state.no_strong_override_claim

    prior_shared_runtime = (
        context.prior_runtime_state
        if isinstance(context.prior_runtime_state, RuntimeState)
        else None
    )
    if prior_shared_runtime is not None:
        shared_reasons: list[str] = []
        shared_validity = prior_shared_runtime.domains.validity
        shared_continuity = prior_shared_runtime.domains.continuity
        shared_regulation = prior_shared_runtime.domains.regulation
        obedience_source_of_truth_surface = "runtime_state.domains"
        obedience_c04_mode_legitimacy = shared_continuity.mode_legitimacy
        obedience_c05_legality_reuse_allowed = shared_validity.legality_reuse_allowed
        obedience_c05_revalidation_required = shared_validity.revalidation_required
        obedience_c05_no_safe_reuse = shared_validity.no_safe_reuse
        obedience_r04_override_scope = shared_regulation.override_scope
        obedience_r04_no_strong_override_claim = shared_regulation.no_strong_override_claim

        if shared_validity.no_safe_reuse and halt_reason is None:
            halt_reason = "shared_validity_no_safe_reuse"
            active_execution_mode = "halt_execution"
            shared_reasons.append("shared_validity.no_safe_reuse")
        elif shared_validity.revalidation_required and halt_reason is None:
            if active_execution_mode != "revalidate_scope":
                active_execution_mode = "revalidate_scope"
            revalidation_needed = True
            shared_reasons.append("shared_validity.revalidation_required")

        if (
            not shared_continuity.mode_legitimacy
            and halt_reason is None
            and active_execution_mode not in revalidation_modes
        ):
            repair_needed = True
            active_execution_mode = "repair_runtime_path"
            shared_reasons.append("shared_continuity.mode_legitimacy_false")

        if (
            shared_regulation.override_scope in {"broad", "emergency"}
            and not shared_regulation.no_strong_override_claim
            and halt_reason is None
            and active_execution_mode
            not in {
                "run_recovery",
                "repair_runtime_path",
                "revalidate_scope",
                "halt_execution",
            }
        ):
            repair_needed = True
            active_execution_mode = "repair_runtime_path"
            shared_reasons.append("shared_regulation.high_override_scope")

        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.shared_runtime_domain_checkpoint",
                source_contract="shared.runtime_domains",
                status=(
                    SubjectTickCheckpointStatus.BLOCKED
                    if halt_reason == "shared_validity_no_safe_reuse"
                    else SubjectTickCheckpointStatus.ENFORCED_DETOUR
                    if shared_reasons
                    else SubjectTickCheckpointStatus.ALLOWED
                ),
                required_action="consume_shared_regulation_continuity_validity_domains",
                applied_action=active_execution_mode,
                reason=(
                    "shared runtime domains influenced contour path: " + ",".join(shared_reasons)
                    if shared_reasons
                    else "shared runtime domains read with no additional detour"
                ),
            )
        )
    else:
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.shared_runtime_domain_checkpoint",
                source_contract="shared.runtime_domains",
                status=SubjectTickCheckpointStatus.ALLOWED,
                required_action="consume_shared_regulation_continuity_validity_domains",
                applied_action=active_execution_mode,
                reason="no prior shared runtime state supplied; contour followed phase-local contracts",
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

    obedience_decision = build_downstream_obedience_decision(
        source_of_truth_surface=obedience_source_of_truth_surface,
        c04_mode_legitimacy=obedience_c04_mode_legitimacy,
        c04_mode_claim=c04_execution_mode_claim,
        c04_authority_role=c04_authority_role,
        c04_computational_role=c04_computational_role,
        c05_legality_reuse_allowed=obedience_c05_legality_reuse_allowed,
        c05_revalidation_required=obedience_c05_revalidation_required,
        c05_no_safe_reuse=obedience_c05_no_safe_reuse,
        c05_action_claim=c05_execution_action_claim,
        c05_authority_role=c05_authority_role,
        c05_computational_role=c05_computational_role,
        r04_override_scope=obedience_r04_override_scope,
        r04_no_strong_override_claim=obedience_r04_no_strong_override_claim,
        r04_authority_role=r04_authority_role,
        r04_computational_role=r04_computational_role,
        c05_surface_invalidated=obedience_c05_surface_invalidated,
    )
    obedience_pre_enforcement_action = active_execution_mode
    obedience_checkpoint_status = (
        SubjectTickCheckpointStatus.BLOCKED
        if obedience_decision.fallback == ObedienceFallback.HALT
        else SubjectTickCheckpointStatus.ENFORCED_DETOUR
        if obedience_decision.fallback in {ObedienceFallback.REPAIR, ObedienceFallback.REVALIDATE}
        else SubjectTickCheckpointStatus.ALLOWED
    )
    if not context.disable_downstream_obedience_enforcement:
        if obedience_decision.fallback == ObedienceFallback.HALT:
            halt_reason = halt_reason or "downstream_obedience_halt"
            active_execution_mode = "halt_execution"
        elif obedience_decision.fallback == ObedienceFallback.REVALIDATE and halt_reason is None:
            revalidation_needed = True
            if active_execution_mode not in {"halt_execution"}:
                active_execution_mode = "revalidate_scope"
        elif obedience_decision.fallback == ObedienceFallback.REPAIR and halt_reason is None:
            repair_needed = True
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
    else:
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.downstream_obedience_ablation",
                source_contract="rt01.downstream_obedience",
                status=SubjectTickCheckpointStatus.ENFORCED_DETOUR,
                required_action=obedience_decision.status.value,
                applied_action=active_execution_mode,
                reason="downstream obedience enforcement disabled in ablation context",
            )
        )
    obedience_reason = obedience_decision.reason
    if obedience_pre_enforcement_action != active_execution_mode:
        obedience_reason = (
            f"{obedience_reason}; action_transition={obedience_pre_enforcement_action}->{active_execution_mode}"
        )
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.downstream_obedience_checkpoint",
            source_contract="rt01.downstream_obedience",
            status=obedience_checkpoint_status,
            required_action=obedience_decision.status.value,
            applied_action=active_execution_mode,
            reason=obedience_reason,
        )
    )

    world_adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode=active_execution_mode,
        adapter_input=context.world_adapter_input,
        request_action_candidate=(
            context.emit_world_action_candidate
            or context.require_world_effect_feedback_for_success_claim
        ),
        source_lineage=lineage,
    )
    world_entry_result = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=world_adapter_result,
        source_lineage=lineage,
    )
    world_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    world_checkpoint_reason = world_entry_result.reason
    if not context.disable_world_seam_enforcement:
        if (
            context.require_world_grounded_transition
            and not world_entry_result.world_grounded_transition_admissible
            and halt_reason is None
        ):
            repair_needed = True
            world_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            world_checkpoint_reason = (
                "world grounded transition required but lawful world-entry episode basis is unavailable"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"

        if (
            context.require_world_effect_feedback_for_success_claim
            and not world_entry_result.world_effect_success_admissible
            and halt_reason is None
            and not repair_needed
        ):
            revalidation_needed = True
            world_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            world_checkpoint_reason = (
                "world effect feedback required for success claim but lawful correlated success basis is unavailable"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        world_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        world_checkpoint_reason = "world seam enforcement disabled in ablation context"

    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.world_seam_checkpoint",
            source_contract="world_entry_contract.admission",
            status=world_checkpoint_status,
            required_action=(
                "require_world_effect_feedback_for_success_claim"
                if context.require_world_effect_feedback_for_success_claim
                else "require_world_grounded_transition"
                if context.require_world_grounded_transition
                else "world_entry_optional"
            ),
            applied_action=active_execution_mode,
            reason=world_checkpoint_reason,
        )
    )
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.world_entry_checkpoint",
            source_contract="world_entry_contract.admission",
            status=(
                SubjectTickCheckpointStatus.ALLOWED
                if world_entry_result.w01_admission.admission_ready
                else SubjectTickCheckpointStatus.ENFORCED_DETOUR
            ),
            required_action="forbidden_world_claims_must_be_machine_readable",
            applied_action=(
                "w_entry_admission_ready"
                if world_entry_result.w01_admission.admission_ready
                else "w_entry_admission_not_ready"
            ),
            reason=world_entry_result.w01_admission.reason,
        )
    )
    s_minimal_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        world_adapter_result=world_adapter_result,
        require_self_side_claim=context.require_self_side_claim,
        require_world_side_claim=context.require_world_side_claim,
        require_self_controlled_transition_claim=context.require_self_controlled_transition_claim,
        source_lineage=lineage,
    )
    s_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    s_checkpoint_reason = s_minimal_result.gate.reason
    if not context.disable_s_minimal_enforcement:
        if (
            context.require_self_controlled_transition_claim
            and not s_minimal_result.gate.self_controlled_transition_claim_allowed
            and halt_reason is None
        ):
            revalidation_needed = True
            s_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s_checkpoint_reason = (
                "self-controlled transition claim requested but s-minimal contour lacks controllability basis"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_self_side_claim
            and not s_minimal_result.gate.self_owned_state_claim_allowed
            and halt_reason is None
            and not revalidation_needed
        ):
            repair_needed = True
            s_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s_checkpoint_reason = (
                "self-side claim requested but s-minimal contour has no safe self attribution basis"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_world_side_claim
            and not (
                s_minimal_result.gate.externally_caused_change_claim_allowed
                or s_minimal_result.gate.world_caused_perturbation_claim_allowed
            )
            and halt_reason is None
            and not revalidation_needed
        ):
            repair_needed = True
            s_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s_checkpoint_reason = (
                "world-side claim requested but s-minimal contour has no safe world attribution basis"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.strict_mixed_attribution_guard
            and "mixed_attribution_without_uncertainty_marking"
            in s_minimal_result.gate.forbidden_shortcuts
            and (
                context.require_self_side_claim
                or context.require_world_side_claim
                or context.require_self_controlled_transition_claim
            )
            and halt_reason is None
        ):
            revalidation_needed = True
            s_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s_checkpoint_reason = (
                "mixed self/world attribution remains unstable under claim pressure; explicit uncertainty marking required"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        s_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        s_checkpoint_reason = "s-minimal contour enforcement disabled in ablation context"
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.s_minimal_contour_checkpoint",
            source_contract="s_minimal_contour.boundary",
            status=s_checkpoint_status,
            required_action=(
                "require_self_controlled_transition_claim"
                if context.require_self_controlled_transition_claim
                else "require_self_side_claim"
                if context.require_self_side_claim
                else "require_world_side_claim"
                if context.require_world_side_claim
                else "s_minimal_optional"
            ),
            applied_action=active_execution_mode,
            reason=s_checkpoint_reason,
        )
    )
    a_line_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        source_lineage=lineage,
    )
    a_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    a_checkpoint_reason = a_line_result.gate.reason
    if not context.disable_a_line_enforcement:
        if (
            context.require_a_line_capability_claim
            and not a_line_result.gate.available_capability_claim_allowed
            and halt_reason is None
        ):
            a_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            if (
                a_line_result.gate.underconstrained_capability
                or a_line_result.gate.policy_conditioned_capability_present
            ):
                revalidation_needed = True
                a_checkpoint_reason = (
                    "available capability claim requested but basis remains underconstrained or policy-conditioned"
                )
                if active_execution_mode != "halt_execution":
                    active_execution_mode = "revalidate_scope"
            else:
                repair_needed = True
                a_checkpoint_reason = (
                    "available capability claim requested but no safe capability basis is available"
                )
                if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                    active_execution_mode = "repair_runtime_path"
    else:
        a_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        a_checkpoint_reason = "a-line normalization enforcement disabled in ablation context"

    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.a_line_normalization_checkpoint",
            source_contract="a_line_normalization.a01_a03_substrate",
            status=a_checkpoint_status,
            required_action=(
                "require_a_line_capability_claim"
                if context.require_a_line_capability_claim
                else "a_line_optional"
            ),
            applied_action=active_execution_mode,
            reason=a_checkpoint_reason,
        )
    )
    m_minimal_result = build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        c05_validity_action=c05_validity_action,
        source_lineage=lineage,
    )
    m_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    m_checkpoint_reason = m_minimal_result.gate.reason
    if not context.disable_m_minimal_enforcement:
        if (
            context.require_memory_safe_claim
            and not m_minimal_result.gate.safe_memory_claim_allowed
            and halt_reason is None
        ):
            m_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            if (
                m_minimal_result.state.review_required
                or m_minimal_result.state.stale_risk.value in {"medium", "high"}
                or m_minimal_result.state.conflict_risk.value in {"medium", "high"}
            ):
                revalidation_needed = True
                m_checkpoint_reason = (
                    "safe memory claim requested but memory lifecycle is stale/conflict/review-bound"
                )
                if active_execution_mode != "halt_execution":
                    active_execution_mode = "revalidate_scope"
            else:
                repair_needed = True
                m_checkpoint_reason = (
                    "safe memory claim requested but no safe memory lifecycle basis is available"
                )
                if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                    active_execution_mode = "repair_runtime_path"
    else:
        m_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        m_checkpoint_reason = "m-minimal contour enforcement disabled in ablation context"
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.m_minimal_contour_checkpoint",
            source_contract="m_minimal.memory_lifecycle",
            status=m_checkpoint_status,
            required_action=(
                "require_memory_safe_claim"
                if context.require_memory_safe_claim
                else "m_minimal_optional"
            ),
            applied_action=active_execution_mode,
            reason=m_checkpoint_reason,
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
        downstream_obedience_status=obedience_decision.status.value,
        downstream_obedience_fallback=obedience_decision.fallback.value,
        downstream_obedience_source_of_truth_surface=obedience_decision.source_of_truth_surface,
        downstream_obedience_requires_restrictions_read=(
            obedience_decision.requires_restrictions_read
        ),
        downstream_obedience_reason=obedience_decision.reason,
        world_adapter_presence=world_adapter_result.state.adapter_presence,
        world_adapter_available=world_adapter_result.state.adapter_available,
        world_adapter_degraded=world_adapter_result.state.adapter_degraded,
        world_link_status=world_adapter_result.state.world_link_status.value,
        world_effect_status=world_adapter_result.state.effect_status.value,
        world_grounded_transition_allowed=world_adapter_result.gate.world_grounded_transition_allowed,
        world_externally_effected_change_claim_allowed=(
            world_adapter_result.gate.externally_effected_change_claim_allowed
        ),
        world_action_success_claim_allowed=world_adapter_result.gate.world_action_success_claim_allowed,
        world_effect_feedback_correlated=world_adapter_result.gate.effect_feedback_correlated,
        world_grounding_confidence=world_adapter_result.state.world_grounding_confidence,
        world_require_grounded_transition=context.require_world_grounded_transition,
        world_require_effect_feedback_for_success_claim=(
            context.require_world_effect_feedback_for_success_claim
        ),
        world_adapter_reason=world_adapter_result.gate.reason,
        world_entry_episode_id=world_entry_result.episode.world_episode_id,
        world_entry_presence_mode=world_entry_result.episode.world_presence_mode.value,
        world_entry_episode_scope=world_entry_result.episode.episode_scope,
        world_entry_observation_basis_present=world_entry_result.episode.observation_basis_present,
        world_entry_action_trace_present=world_entry_result.episode.action_trace_present,
        world_entry_effect_basis_present=world_entry_result.episode.effect_basis_present,
        world_entry_effect_feedback_correlated=world_entry_result.episode.effect_feedback_correlated,
        world_entry_confidence=world_entry_result.episode.confidence,
        world_entry_reliability=world_entry_result.episode.reliability,
        world_entry_degraded=world_entry_result.episode.degraded,
        world_entry_incomplete=world_entry_result.episode.incomplete,
        world_entry_forbidden_claim_classes=world_entry_result.forbidden_claim_classes,
        world_entry_world_grounded_transition_admissible=(
            world_entry_result.world_grounded_transition_admissible
        ),
        world_entry_world_effect_success_admissible=(
            world_entry_result.world_effect_success_admissible
        ),
        world_entry_w01_admission_ready=world_entry_result.w01_admission.admission_ready,
        world_entry_w01_admission_restrictions=world_entry_result.w01_admission.restrictions,
        world_entry_scope=world_entry_result.scope_marker.scope,
        world_entry_scope_admission_layer_only=world_entry_result.scope_marker.admission_layer_only,
        world_entry_scope_w01_implemented=world_entry_result.scope_marker.w01_implemented,
        world_entry_scope_w_line_implemented=world_entry_result.scope_marker.w_line_implemented,
        world_entry_scope_repo_wide_adoption=world_entry_result.scope_marker.repo_wide_adoption,
        world_entry_scope_reason=world_entry_result.scope_marker.reason,
        world_entry_reason=world_entry_result.w01_admission.reason,
        s_boundary_state_id=s_minimal_result.state.boundary_state_id,
        s_self_attribution_basis_present=s_minimal_result.state.self_attribution_basis_present,
        s_world_attribution_basis_present=s_minimal_result.state.world_attribution_basis_present,
        s_controllability_estimate=s_minimal_result.state.controllability_estimate,
        s_ownership_estimate=s_minimal_result.state.ownership_estimate,
        s_attribution_confidence=s_minimal_result.state.attribution_confidence,
        s_source_status=s_minimal_result.state.internal_vs_external_source_status.value,
        s_boundary_breach_risk=s_minimal_result.state.boundary_breach_risk.value,
        s_attribution_class=s_minimal_result.state.attribution_class.value,
        s_no_safe_self_claim=s_minimal_result.gate.no_safe_self_claim,
        s_no_safe_world_claim=s_minimal_result.gate.no_safe_world_claim,
        s_degraded=s_minimal_result.state.degraded,
        s_underconstrained=s_minimal_result.state.underconstrained,
        s_forbidden_shortcuts=s_minimal_result.gate.forbidden_shortcuts,
        s_restrictions=s_minimal_result.gate.restrictions,
        s_s01_admission_ready=s_minimal_result.admission.admission_ready_for_s01,
        s_self_attribution_basis_sufficient=s_minimal_result.admission.self_attribution_basis_sufficient,
        s_controllability_basis_sufficient=s_minimal_result.admission.controllability_basis_sufficient,
        s_ownership_basis_sufficient=s_minimal_result.admission.ownership_basis_sufficient,
        s_attribution_underconstrained=s_minimal_result.admission.attribution_underconstrained,
        s_mixed_boundary_instability=s_minimal_result.admission.mixed_boundary_instability,
        s_no_safe_self_basis=s_minimal_result.admission.no_safe_self_basis,
        s_no_safe_world_basis=s_minimal_result.admission.no_safe_world_basis,
        s_readiness_blockers=s_minimal_result.admission.readiness_blockers,
        s_future_s01_s05_remain_open=s_minimal_result.admission.future_s01_s05_remain_open,
        s_full_self_model_implemented=s_minimal_result.admission.full_self_model_implemented,
        s_scope=s_minimal_result.scope_marker.scope,
        s_scope_rt01_contour_only=s_minimal_result.scope_marker.rt01_contour_only,
        s_scope_s_minimal_only=s_minimal_result.scope_marker.s_minimal_only,
        s_scope_s01_implemented=s_minimal_result.scope_marker.s01_implemented,
        s_scope_s_line_implemented=s_minimal_result.scope_marker.s_line_implemented,
        s_scope_minimal_contour_only=s_minimal_result.scope_marker.minimal_contour_only,
        s_scope_s01_s05_implemented=s_minimal_result.scope_marker.s01_s05_implemented,
        s_scope_full_self_model_implemented=s_minimal_result.scope_marker.full_self_model_implemented,
        s_scope_repo_wide_adoption=s_minimal_result.scope_marker.repo_wide_adoption,
        s_scope_reason=s_minimal_result.scope_marker.reason,
        s_reason=s_minimal_result.reason,
        s_require_self_side_claim=context.require_self_side_claim,
        s_require_world_side_claim=context.require_world_side_claim,
        s_require_self_controlled_transition_claim=context.require_self_controlled_transition_claim,
        s_strict_mixed_attribution_guard=context.strict_mixed_attribution_guard,
        a_capability_id=a_line_result.state.capability_id,
        a_affordance_id=a_line_result.state.affordance_id,
        a_capability_class=a_line_result.state.capability_class.value,
        a_capability_status=a_line_result.state.capability_status.value,
        a_availability_basis_present=a_line_result.state.availability_basis_present,
        a_world_dependency_present=a_line_result.state.world_dependency_present,
        a_self_dependency_present=a_line_result.state.self_dependency_present,
        a_controllability_dependency_present=a_line_result.state.controllability_dependency_present,
        a_legitimacy_dependency_present=a_line_result.state.legitimacy_dependency_present,
        a_confidence=a_line_result.state.confidence,
        a_degraded=a_line_result.state.degraded,
        a_underconstrained=a_line_result.state.underconstrained,
        a_available_capability_claim_allowed=a_line_result.gate.available_capability_claim_allowed,
        a_world_conditioned_capability_claim_allowed=(
            a_line_result.gate.world_conditioned_capability_claim_allowed
        ),
        a_self_conditioned_capability_claim_allowed=(
            a_line_result.gate.self_conditioned_capability_claim_allowed
        ),
        a_policy_conditioned_capability_present=(
            a_line_result.gate.policy_conditioned_capability_present
        ),
        a_no_safe_capability_claim=a_line_result.gate.no_safe_capability_claim,
        a_forbidden_shortcuts=a_line_result.gate.forbidden_shortcuts,
        a_restrictions=a_line_result.gate.restrictions,
        a_a04_admission_ready=a_line_result.a04_readiness.admission_ready_for_a04,
        a_a04_blockers=a_line_result.a04_readiness.blockers,
        a_a04_structurally_present_but_not_ready=(
            a_line_result.a04_readiness.structurally_present_but_not_ready
        ),
        a_a04_capability_basis_missing=a_line_result.a04_readiness.capability_basis_missing,
        a_a04_world_dependency_unmet=a_line_result.a04_readiness.world_dependency_unmet,
        a_a04_self_dependency_unmet=a_line_result.a04_readiness.self_dependency_unmet,
        a_a04_policy_legitimacy_unmet=a_line_result.a04_readiness.policy_legitimacy_unmet,
        a_a04_underconstrained_capability_surface=(
            a_line_result.a04_readiness.underconstrained_capability_surface
        ),
        a_a04_external_means_not_justified=(
            a_line_result.a04_readiness.external_means_not_justified
        ),
        a_a04_implemented=a_line_result.a04_readiness.a04_implemented,
        a_a05_touched=a_line_result.a04_readiness.a05_touched,
        a_scope=a_line_result.scope_marker.scope,
        a_scope_rt01_contour_only=a_line_result.scope_marker.rt01_contour_only,
        a_scope_a_line_normalization_only=(
            a_line_result.scope_marker.a_line_normalization_only
        ),
        a_scope_readiness_gate_only=a_line_result.scope_marker.readiness_gate_only,
        a_scope_a04_implemented=a_line_result.scope_marker.a04_implemented,
        a_scope_a05_touched=a_line_result.scope_marker.a05_touched,
        a_scope_full_agency_stack_implemented=(
            a_line_result.scope_marker.full_agency_stack_implemented
        ),
        a_scope_repo_wide_adoption=a_line_result.scope_marker.repo_wide_adoption,
        a_scope_reason=a_line_result.scope_marker.reason,
        a_reason=a_line_result.reason,
        a_require_capability_claim=context.require_a_line_capability_claim,
        m_memory_item_id=m_minimal_result.state.memory_item_id,
        m_memory_packet_id=m_minimal_result.state.memory_packet_id,
        m_lifecycle_status=m_minimal_result.state.lifecycle_status.value,
        m_retention_class=m_minimal_result.state.retention_class.value,
        m_bounded_persistence_allowed=m_minimal_result.state.bounded_persistence_allowed,
        m_temporary_carry_allowed=m_minimal_result.state.temporary_carry_allowed,
        m_review_required=m_minimal_result.state.review_required,
        m_reactivation_eligible=m_minimal_result.state.reactivation_eligible,
        m_decay_eligible=m_minimal_result.state.decay_eligible,
        m_pruning_eligible=m_minimal_result.state.pruning_eligible,
        m_stale_risk=m_minimal_result.state.stale_risk.value,
        m_conflict_risk=m_minimal_result.state.conflict_risk.value,
        m_confidence=m_minimal_result.state.confidence,
        m_reliability=m_minimal_result.state.reliability,
        m_degraded=m_minimal_result.state.degraded,
        m_underconstrained=m_minimal_result.state.underconstrained,
        m_safe_memory_claim_allowed=m_minimal_result.gate.safe_memory_claim_allowed,
        m_bounded_retained_claim_allowed=(
            m_minimal_result.gate.bounded_retained_claim_allowed
        ),
        m_no_safe_memory_claim=m_minimal_result.gate.no_safe_memory_claim,
        m_forbidden_shortcuts=m_minimal_result.gate.forbidden_shortcuts,
        m_restrictions=m_minimal_result.gate.restrictions,
        m_m01_admission_ready=m_minimal_result.admission.admission_ready_for_m01,
        m_m01_blockers=m_minimal_result.admission.blockers,
        m_m01_structurally_present_but_not_ready=(
            m_minimal_result.admission.structurally_present_but_not_ready
        ),
        m_m01_stale_risk_unacceptable=(
            m_minimal_result.admission.stale_risk_unacceptable
        ),
        m_m01_conflict_risk_unacceptable=(
            m_minimal_result.admission.conflict_risk_unacceptable
        ),
        m_m01_reactivation_requires_review=(
            m_minimal_result.admission.reactivation_requires_review
        ),
        m_m01_temporary_carry_not_stable_enough=(
            m_minimal_result.admission.temporary_carry_not_stable_enough
        ),
        m_m01_no_safe_memory_basis=m_minimal_result.admission.no_safe_memory_basis,
        m_m01_provenance_insufficient=(
            m_minimal_result.admission.provenance_insufficient
        ),
        m_m01_lifecycle_underconstrained=(
            m_minimal_result.admission.lifecycle_underconstrained
        ),
        m_m01_implemented=m_minimal_result.admission.m01_implemented,
        m_m02_implemented=m_minimal_result.admission.m02_implemented,
        m_m03_implemented=m_minimal_result.admission.m03_implemented,
        m_scope=m_minimal_result.scope_marker.scope,
        m_scope_rt01_contour_only=m_minimal_result.scope_marker.rt01_contour_only,
        m_scope_m_minimal_only=m_minimal_result.scope_marker.m_minimal_only,
        m_scope_readiness_gate_only=m_minimal_result.scope_marker.readiness_gate_only,
        m_scope_m01_implemented=m_minimal_result.scope_marker.m01_implemented,
        m_scope_m02_implemented=m_minimal_result.scope_marker.m02_implemented,
        m_scope_m03_implemented=m_minimal_result.scope_marker.m03_implemented,
        m_scope_full_memory_stack_implemented=(
            m_minimal_result.scope_marker.full_memory_stack_implemented
        ),
        m_scope_repo_wide_adoption=m_minimal_result.scope_marker.repo_wide_adoption,
        m_scope_reason=m_minimal_result.scope_marker.reason,
        m_reason=m_minimal_result.reason,
        m_require_memory_safe_claim=context.require_memory_safe_claim,
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
            "bounded runtime execution spine enforces roadmap authority roles for C04/C05, consumes world-entry, s-minimal contour and a-line normalization gates, and keeps D01 observability-only over fixed R->C order"
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
        world_adapter_result=world_adapter_result,
        world_entry_result=world_entry_result,
        self_contour_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
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
    domain_update = build_subject_tick_runtime_domain_update(result)
    route_auth = build_subject_tick_runtime_route_auth_context(
        result=result,
        domain_update=domain_update,
    )
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
            "runtime_domain_update": domain_update,
            "runtime_route_auth": route_auth,
        },
    )
    return execute_transition(request, runtime_state)


def build_subject_tick_runtime_domain_update(result: SubjectTickResult) -> RuntimeDomainUpdate:
    if not isinstance(result, SubjectTickResult):
        raise TypeError("build_subject_tick_runtime_domain_update requires SubjectTickResult")

    viability_state = result.viability_result.state
    c04_state = result.c04_result.state
    c05_state = result.c05_result.state

    mode_legitimacy = any(
        checkpoint.checkpoint_id == "rt01.c04_mode_binding"
        and checkpoint.status in {SubjectTickCheckpointStatus.ALLOWED, SubjectTickCheckpointStatus.ENFORCED_DETOUR}
        for checkpoint in result.state.execution_checkpoints
    ) and result.state.c04_authority_role == SubjectTickAuthorityRole.ARBITRATION.value

    legality_reuse_allowed = not bool(
        c05_state.invalidated_item_ids
        or c05_state.expired_item_ids
        or c05_state.dependency_contaminated_item_ids
        or c05_state.no_safe_reuse_item_ids
    )
    revalidation_required = bool(
        c05_state.revalidation_item_ids
        or c05_state.selective_scope_targets
        or c05_state.insufficient_basis_for_revalidation
        or c05_state.selective_scope_uncertain
        or result.state.revalidation_needed
    )
    no_safe_reuse = bool(c05_state.no_safe_reuse_item_ids)

    return RuntimeDomainUpdate(
        regulation=RegulationDomainState(
            pressure_level=viability_state.pressure_level,
            escalation_stage=viability_state.escalation_stage.value,
            override_scope=viability_state.override_scope.value,
            no_strong_override_claim=viability_state.no_strong_override_claim,
            gate_accepted=result.viability_result.downstream_gate.accepted,
            source_state_ref=viability_state.input_regulation_snapshot_ref,
            updated_by_phase=DomainWriterPhase.R04.value,
            last_update_provenance=viability_state.provenance,
        ),
        continuity=ContinuityDomainState(
            c04_mode_claim=result.state.c04_execution_mode_claim,
            c04_selected_mode=result.state.c04_selected_mode,
            mode_legitimacy=mode_legitimacy,
            endogenous_tick_allowed=c04_state.endogenous_tick_allowed,
            arbitration_confidence=c04_state.arbitration_confidence,
            source_state_ref=result.state.source_c04_state_ref,
            updated_by_phase=DomainWriterPhase.C04.value,
            last_update_provenance=c04_state.last_update_provenance,
        ),
        validity=ValidityDomainState(
            c05_action_claim=result.state.c05_execution_action_claim,
            c05_validity_action=result.state.c05_validity_action,
            legality_reuse_allowed=legality_reuse_allowed,
            revalidation_required=revalidation_required,
            no_safe_reuse=no_safe_reuse,
            selective_scope_targets=c05_state.selective_scope_targets,
            source_state_ref=result.state.source_c05_state_ref,
            updated_by_phase=DomainWriterPhase.C05.value,
            last_update_provenance=c05_state.last_update_provenance,
        ),
        write_claims=(
            DomainWriteClaim(
                phase=DomainWriterPhase.R04,
                domain_path="domains.regulation",
                transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
                route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
                checkpoint_id="rt01.r04_regulation_surface",
                reason="r04 viability pressure must propagate to shared regulation runtime domain",
            ),
            DomainWriteClaim(
                phase=DomainWriterPhase.C04,
                domain_path="domains.continuity",
                transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
                route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
                checkpoint_id="rt01.c04_mode_binding",
                reason="c04 lawful mode arbitration must propagate to shared continuity runtime domain",
            ),
            DomainWriteClaim(
                phase=DomainWriterPhase.C05,
                domain_path="domains.validity",
                transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
                route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
                checkpoint_id="rt01.c05_legality_checkpoint",
                reason="c05 temporal legality/revalidation claims must propagate to shared validity runtime domain",
            ),
        ),
        reason="subject_tick runtime contour shared domain propagation",
    )


def build_subject_tick_runtime_route_auth_context(
    *,
    result: SubjectTickResult,
    domain_update: RuntimeDomainUpdate | None = None,
) -> RuntimeRouteAuthContext:
    if not isinstance(result, SubjectTickResult):
        raise TypeError("build_subject_tick_runtime_route_auth_context requires SubjectTickResult")
    domain_update = domain_update or build_subject_tick_runtime_domain_update(result)
    if not isinstance(domain_update, RuntimeDomainUpdate):
        raise TypeError("domain_update must be RuntimeDomainUpdate")

    claims = tuple(
        claim
        for claim in domain_update.write_claims
        if claim.route == DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR
    )
    authorized_paths = tuple(sorted({claim.domain_path for claim in claims}))
    claimed_checkpoint_ids = tuple(sorted({claim.checkpoint_id for claim in claims}))
    available_checkpoint_ids = tuple(
        checkpoint.checkpoint_id for checkpoint in result.state.execution_checkpoints
    )
    checkpoint_ids = _union_unique(claimed_checkpoint_ids, available_checkpoint_ids)

    nonce = issue_rt01_route_auth_nonce(
        route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
        origin_phase=DomainWriterPhase.RT01,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        tick_id=result.state.tick_id,
        authorized_domain_paths=authorized_paths,
        checkpoint_ids=checkpoint_ids,
        origin_contract="subject_tick.runtime_contour_from_r_to_c05",
    )
    return RuntimeRouteAuthContext(
        route=DomainWriteRoute.RT01_SUBJECT_TICK_CONTOUR,
        origin_phase=DomainWriterPhase.RT01,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        tick_id=result.state.tick_id,
        authorized_domain_paths=authorized_paths,
        checkpoint_ids=checkpoint_ids,
        origin_contract="subject_tick.runtime_contour_from_r_to_c05",
        auth_nonce=nonce,
    )


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


def _union_unique(*chunks: Iterable[str]) -> tuple[str, ...]:
    acc: list[str] = []
    for chunk in chunks:
        for item in chunk:
            token = str(item or "").strip()
            if token and token not in acc:
                acc.append(token)
    return tuple(acc)
