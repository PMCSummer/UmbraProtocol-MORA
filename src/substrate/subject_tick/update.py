from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from substrate.a_line_normalization import build_a_line_normalization
from substrate.epistemics import (
    ClaimPolarity,
    ConfidenceLevel,
    EpistemicUnit,
    GroundingContext,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    evaluate_downstream_allowance,
    ground_epistemic_input,
)
from substrate.m_minimal import build_m_minimal
from substrate.n_minimal import build_n_minimal
from substrate.t01_semantic_field import (
    build_t01_active_semantic_field,
    derive_t01_preverbal_consumer_view,
)
from substrate.t02_relation_binding import (
    T02AssemblyMode,
    build_t02_constrained_scene,
    derive_t02_preverbal_constraint_consumer_view,
)
from substrate.t03_hypothesis_competition import (
    T03CompetitionMode,
    build_t03_hypothesis_competition,
    derive_t03_preverbal_competition_consumer_view,
)
from substrate.t04_attention_schema import (
    build_t04_attention_schema,
    derive_t04_preverbal_focus_consumer_view,
)
from substrate.affordances import (
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.affordances.policy import evaluate_affordance_landscape_for_downstream
from substrate.authority import issue_rt01_route_auth_nonce
from substrate.downstream_obedience import (
    ObedienceFallback,
    ObedienceStatus,
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
from substrate.runtime_tap_trace import trace_emit_active
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
from substrate.s02_prediction_boundary import (
    build_s02_prediction_boundary,
    derive_s02_boundary_consumer_view,
)
from substrate.s03_ownership_weighted_learning import (
    build_s03_ownership_weighted_learning,
    derive_s03_update_packet_consumer_view,
)
from substrate.s04_interoceptive_self_binding import (
    build_s04_interoceptive_self_binding,
    derive_s04_interoceptive_self_binding_consumer_view,
)
from substrate.s05_multi_cause_attribution_factorization import (
    S05CauseClass,
    S05DownstreamRouteClass,
    build_s05_multi_cause_attribution_factorization,
    derive_s05_multi_cause_attribution_consumer_view,
)
from substrate.o01_other_entity_model import (
    build_o01_other_entity_model,
    derive_o01_other_entity_model_consumer_view,
)
from substrate.o02_intersubjective_allostasis import (
    O02InteractionDiagnosticsInput,
    build_o02_intersubjective_allostasis,
    derive_o02_intersubjective_allostasis_consumer_view,
)
from substrate.s01_efference_copy import (
    S01EfferenceCopyState,
    build_s01_efference_copy,
)
from substrate.world_entry_contract import build_world_entry_contract


ATTEMPTED_SUBJECT_TICK_PATHS: tuple[str, ...] = (
    "subject_tick.evaluate_epistemic_admission",
    "subject_tick.run_regulation_stack",
    "subject_tick.run_c01_stream_kernel",
    "subject_tick.run_c02_tension_scheduler",
    "subject_tick.run_c03_stream_diversification",
    "subject_tick.run_c04_mode_arbitration",
    "subject_tick.run_c05_temporal_validity",
    "subject_tick.enforce_c04_c05_contract_obedience",
    "subject_tick.enforce_downstream_obedience_contract",
    "subject_tick.evaluate_world_entry_contract",
    "subject_tick.evaluate_s01_efference_copy",
    "subject_tick.evaluate_s02_prediction_boundary",
    "subject_tick.evaluate_s03_ownership_weighted_learning",
    "subject_tick.evaluate_s04_interoceptive_self_binding",
    "subject_tick.evaluate_s05_multi_cause_attribution_factorization",
    "subject_tick.evaluate_s_minimal_contour",
    "subject_tick.evaluate_a_line_normalization",
    "subject_tick.evaluate_m_minimal_contour",
    "subject_tick.evaluate_n_minimal_contour",
    "subject_tick.evaluate_t01_semantic_field",
    "subject_tick.evaluate_t02_relation_binding",
    "subject_tick.evaluate_t03_hypothesis_competition",
    "subject_tick.evaluate_t04_attention_schema",
    "subject_tick.evaluate_o01_other_entity_model",
    "subject_tick.evaluate_o02_intersubjective_allostasis",
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

    epistemic = ground_epistemic_input(
        InputMaterial(
            material_id=f"{tick_id}-epistemic-material",
            content=tick_input.epistemic_content or f"runtime_tick:{tick_input.case_id}",
        ),
        SourceMetadata(
            source_id=tick_input.epistemic_source_id or f"subject_tick:{tick_input.case_id}",
            source_class=_resolve_epistemic_source_class(tick_input.epistemic_source_class),
            modality=_resolve_epistemic_modality_class(tick_input.epistemic_modality),
            confidence_hint=_resolve_epistemic_confidence_level(
                tick_input.epistemic_confidence_hint
            ),
            support_note=tick_input.epistemic_support_note,
            contestation_note=tick_input.epistemic_contestation_note,
            claim_key=tick_input.epistemic_claim_key,
            claim_polarity=_resolve_epistemic_claim_polarity(
                tick_input.epistemic_claim_polarity
            ),
        ),
        context=GroundingContext(
            existing_units=_coerce_epistemic_units(context.prior_epistemic_units),
            require_observation=context.require_epistemic_observation,
        ),
    )
    trace_emit_active(
        "epistemics",
        "enter",
        {
            "epistemic_status": epistemic.unit.status,
        },
    )
    epistemic_allowance = evaluate_downstream_allowance(
        epistemic.unit,
        require_observation=context.require_epistemic_observation,
    )
    epistemic_admission_allowed = (
        context.disable_epistemic_admission_enforcement
        or not epistemic_allowance.should_abstain
    )
    epistemic_trace_values = {
        "epistemic_status": epistemic.unit.status,
        "claim_strength": epistemic_allowance.claim_strength,
        "should_abstain": epistemic_allowance.should_abstain,
        "can_treat_as_observation": epistemic_allowance.can_treat_as_observation,
    }
    trace_emit_active("epistemics", "decision", epistemic_trace_values)
    if epistemic_allowance.should_abstain:
        trace_emit_active(
            "epistemics",
            "blocked",
            epistemic_trace_values,
            note=epistemic_allowance.reason,
        )
    trace_emit_active("epistemics", "exit", epistemic_trace_values)

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
    regulation_enter_values = {
        "dominant_axis": regulation.tradeoff.dominant_axis,
        "claim_strength": regulation.bias.claim_strength,
    }
    trace_emit_active("regulation", "enter", regulation_enter_values)
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
        epistemic_admission_allowed
        and regulation_gate.allowed
        and bool(affordance_gate.accepted_candidate_ids)
        and preference_gate.accepted
    )
    regulation_trace_values = {
        "pressure_level": viability.state.pressure_level,
        "escalation_stage": viability.state.escalation_stage,
        "override_scope": viability.state.override_scope,
        "gate_accepted": regulation_gate.allowed,
        "dominant_axis": regulation.tradeoff.dominant_axis,
        "claim_strength": regulation.bias.claim_strength,
    }
    trace_emit_active("regulation", "decision", regulation_trace_values)
    if not regulation_gate.allowed:
        trace_emit_active(
            "regulation",
            "blocked",
            regulation_trace_values,
            note=regulation_gate.reason,
        )
    trace_emit_active("regulation", "exit", regulation_trace_values)

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
    c01_enter_values = {
        "stream_state": stream.state.link_decision.value,
        "kernel_ready": stream_view.gate_accepted,
        "stream_load": _c01_stream_load(stream),
        "kernel_blocked": not stream_view.gate_accepted,
        "active_stream_count": len(stream.state.carryover_items),
    }
    trace_emit_active("c01_stream_kernel", "enter", c01_enter_values)
    c01_trace_values = {
        "stream_state": stream.state.link_decision.value,
        "kernel_ready": stream_view.gate_accepted,
        "stream_load": _c01_stream_load(stream),
        "kernel_blocked": not stream_view.gate_accepted,
        "active_stream_count": len(stream.state.carryover_items),
    }
    trace_emit_active("c01_stream_kernel", "decision", c01_trace_values)
    if c01_trace_values["kernel_blocked"]:
        trace_emit_active(
            "c01_stream_kernel",
            "blocked",
            c01_trace_values,
            note="kernel_gate_blocked",
        )
    trace_emit_active("c01_stream_kernel", "exit", c01_trace_values)

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
    c02_enter_values = {
        "tension_level": len(scheduler.state.active_tension_ids),
        "scheduler_state": scheduler_mode,
        "pressure_binding": scheduler_view.usability_class.value,
        "tension_blocked": not scheduler_view.gate_accepted,
        "schedule_ready": scheduler_view.gate_accepted,
    }
    trace_emit_active("c02_tension_scheduler", "enter", c02_enter_values)
    c02_trace_values = {
        "tension_level": len(scheduler.state.active_tension_ids),
        "scheduler_state": scheduler_mode,
        "pressure_binding": scheduler_view.usability_class.value,
        "tension_blocked": not scheduler_view.gate_accepted,
        "schedule_ready": scheduler_view.gate_accepted,
    }
    trace_emit_active("c02_tension_scheduler", "decision", c02_trace_values)
    if c02_trace_values["tension_blocked"]:
        trace_emit_active(
            "c02_tension_scheduler",
            "blocked",
            c02_trace_values,
            note="scheduler_gate_blocked",
        )
    trace_emit_active("c02_tension_scheduler", "exit", c02_trace_values)

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
    c03_enter_values = {
        "diversification_state": diversification.state.decision_status.value,
        "active_branches": len(diversification.state.actionable_alternative_classes),
        "branch_pressure": diversification.state.diversification_pressure,
        "diversification_blocked": not diversification_view.gate_accepted,
        "diversification_ready": diversification_view.gate_accepted,
    }
    trace_emit_active("c03_stream_diversification", "enter", c03_enter_values)
    c03_trace_values = {
        "diversification_state": diversification.state.decision_status.value,
        "active_branches": len(diversification.state.actionable_alternative_classes),
        "branch_pressure": diversification.state.diversification_pressure,
        "diversification_blocked": not diversification_view.gate_accepted,
        "diversification_ready": diversification_view.gate_accepted,
    }
    trace_emit_active("c03_stream_diversification", "decision", c03_trace_values)
    if c03_trace_values["diversification_blocked"]:
        trace_emit_active(
            "c03_stream_diversification",
            "blocked",
            c03_trace_values,
            note="diversification_gate_blocked",
        )
    trace_emit_active("c03_stream_diversification", "exit", c03_trace_values)

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
    c04_enter_values = {
        "selected_mode": mode_arbitration.state.active_mode.value,
        "mode_source": mode_arbitration.state.endogenous_tick_kind.value,
        "mode_conflict_present": _c04_mode_conflict_present(mode_arbitration, mode_view),
        "arbitration_stable": _c04_arbitration_stable(mode_arbitration, mode_view),
        "handoff_ready": mode_view.gate_accepted,
    }
    trace_emit_active("c04_mode_arbitration", "enter", c04_enter_values)
    active_execution_mode = c04_execution_mode_claim
    trace_emit_active(
        "subject_tick",
        "enter",
        {
            "active_execution_mode": active_execution_mode,
        },
    )
    repair_needed = False
    revalidation_needed = False
    halt_reason: str | None = None
    checkpoints: list[SubjectTickCheckpointResult] = []
    c05_enforcement_authority = c05_authority_role in {
        SubjectTickAuthorityRole.GATING.value,
        SubjectTickAuthorityRole.INVALIDATION.value,
    }
    c04_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    c04_checkpoint_reason = "rt01 consumed c04 execution mode claim without reinterpretation"
    c04_block_reason: str | None = None

    if c04_authority_role != SubjectTickAuthorityRole.ARBITRATION.value:
        active_execution_mode = "repair_runtime_path"
        repair_needed = True
        c04_checkpoint_status = SubjectTickCheckpointStatus.BLOCKED
        c04_checkpoint_reason = (
            "rt01 rejected c04 mode claim because roadmap authority_role is not arbitration"
        )
        c04_block_reason = "authority_role_mismatch"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c04_mode_binding",
                source_contract="c04.mode_arbitration",
                status=c04_checkpoint_status,
                required_action=SubjectTickAuthorityRole.ARBITRATION.value,
                applied_action=c04_authority_role,
                reason=c04_checkpoint_reason,
            )
        )
    elif not context.disable_c04_mode_execution_binding:
        active_execution_mode = c04_execution_mode_claim
        c04_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
        c04_checkpoint_reason = "rt01 consumed c04 execution mode claim without reinterpretation"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c04_mode_binding",
                source_contract="c04.mode_arbitration",
                status=c04_checkpoint_status,
                required_action=c04_execution_mode_claim,
                applied_action=active_execution_mode,
                reason=c04_checkpoint_reason,
            )
        )
    else:
        active_execution_mode = stream_mode
        c04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        c04_checkpoint_reason = "c04 mode binding disabled in ablation context"
        c04_block_reason = "binding_disabled"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c04_mode_binding",
                source_contract="c04.mode_arbitration",
                status=c04_checkpoint_status,
                required_action=c04_execution_mode_claim,
                applied_action=active_execution_mode,
                reason=c04_checkpoint_reason,
            )
        )
    c04_trace_values = {
        "selected_mode": mode_arbitration.state.active_mode.value,
        "mode_source": mode_arbitration.state.endogenous_tick_kind.value,
        "mode_conflict_present": _c04_mode_conflict_present(mode_arbitration, mode_view),
        "arbitration_stable": _c04_arbitration_stable(mode_arbitration, mode_view),
        "handoff_ready": c04_checkpoint_status == SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("c04_mode_arbitration", "decision", c04_trace_values)
    if c04_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "c04_mode_arbitration",
            "blocked",
            c04_trace_values,
            note=c04_block_reason or "mode_arbitration_detour",
        )
    trace_emit_active("c04_mode_arbitration", "exit", c04_trace_values)

    c05_enter_values = {
        "validity_status": c05_validity_action,
        "legality_class": temporal_view.usability_class.value,
        "revalidation_required": _c05_revalidation_required(temporal_validity, c05_validity_action),
        "temporal_blocked": not temporal_view.gate_accepted,
        "validity_ready": temporal_view.gate_accepted,
    }
    trace_emit_active("c05_temporal_validity", "enter", c05_enter_values)
    c05_status = SubjectTickCheckpointStatus.ALLOWED
    c05_reason = "c05 legality allows bounded reuse path"
    c05_block_reason: str | None = None

    if not c05_enforcement_authority:
        repair_needed = True
        active_execution_mode = "repair_runtime_path"
        c05_status = SubjectTickCheckpointStatus.BLOCKED
        c05_reason = (
            "rt01 refused applying c05 legality as authority because roadmap authority_role is non-enforcement"
        )
        c05_block_reason = "authority_role_mismatch"
        checkpoints.append(
            SubjectTickCheckpointResult(
                checkpoint_id="rt01.c05_legality_checkpoint",
                source_contract="c05.temporal_validity",
                status=c05_status,
                required_action="gating_or_invalidation",
                applied_action=c05_authority_role,
                reason=c05_reason,
            )
        )
    elif not context.disable_c05_validity_enforcement:
        prior_mode = active_execution_mode
        if active_execution_mode == "continue_stream" and not can_continue_mode_hold(temporal_validity):
            active_execution_mode = "revalidate_mode_hold"
            revalidation_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 blocked mode hold reuse; revalidation detour enforced"
            c05_block_reason = "mode_hold_revalidation_required"
        if active_execution_mode == "run_revisit" and not can_revisit_with_basis(temporal_validity):
            active_execution_mode = "revalidate_revisit_basis"
            revalidation_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 blocked revisit basis reuse; revalidation detour enforced"
            c05_block_reason = "revisit_basis_revalidation_required"
        if active_execution_mode == "probe_alternatives" and not can_open_branch_access(temporal_validity):
            active_execution_mode = "repair_branch_access"
            repair_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 blocked branch access; repair detour enforced"
            c05_block_reason = "branch_access_repair_required"
        if c05_validity_action in {
            "run_selective_revalidation",
            "run_bounded_revalidation",
            "suspend_until_revalidation_basis",
        }:
            active_execution_mode = "revalidate_scope"
            revalidation_needed = True
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 requested revalidation scope before runtime continuation"
            c05_block_reason = "revalidation_scope_required"
        if c05_validity_action == "halt_reuse_and_rebuild_scope":
            active_execution_mode = "halt_execution"
            halt_reason = "c05_halt_reuse_and_rebuild_scope"
            c05_status = SubjectTickCheckpointStatus.BLOCKED
            c05_reason = "c05 halted reuse legality; runtime continuation blocked"
            c05_block_reason = "halt_reuse_rebuild_scope"
        if c05_status == SubjectTickCheckpointStatus.ALLOWED and prior_mode != active_execution_mode:
            c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            c05_reason = "c05 enforcement changed runtime execution path"
            c05_block_reason = "runtime_path_changed_by_c05"
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
        c05_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        c05_reason = "c05 legality enforcement disabled in ablation context"
        c05_block_reason = "enforcement_disabled"
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
    c05_trace_values = {
        "validity_status": c05_validity_action,
        "legality_class": temporal_view.usability_class.value,
        "revalidation_required": (
            _c05_revalidation_required(temporal_validity, c05_validity_action)
            or active_execution_mode in {"revalidate_mode_hold", "revalidate_revisit_basis", "revalidate_scope"}
        ),
        "temporal_blocked": c05_status == SubjectTickCheckpointStatus.BLOCKED,
        "validity_ready": (
            c05_status == SubjectTickCheckpointStatus.ALLOWED and temporal_view.gate_accepted
        ),
    }
    trace_emit_active("c05_temporal_validity", "decision", c05_trace_values)
    if c05_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "c05_temporal_validity",
            "blocked",
            c05_trace_values,
            note=c05_block_reason or "temporal_validity_detour",
        )
    trace_emit_active("c05_temporal_validity", "exit", c05_trace_values)

    revalidation_modes = {"revalidate_mode_hold", "revalidate_revisit_basis", "revalidate_scope"}
    epistemic_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    epistemic_checkpoint_reason = epistemic_allowance.reason
    if not context.disable_epistemic_admission_enforcement:
        if epistemic_allowance.should_abstain:
            epistemic_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            if halt_reason is None and active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
            epistemic_checkpoint_reason = (
                "epistemic admission marked abstain/unknown/conflict; revalidation detour enforced"
            )
    else:
        epistemic_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        epistemic_checkpoint_reason = (
            "epistemic admission enforcement disabled in ablation context"
        )
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.epistemic_admission_checkpoint",
            source_contract="epistemics.downstream_allowance",
            status=epistemic_checkpoint_status,
            required_action=(
                "consume_epistemic_allowance_and_preserve_abstain_unknown_conflict_markers"
            ),
            applied_action=f"{epistemic_allowance.claim_strength}:{active_execution_mode}",
            reason=epistemic_checkpoint_reason,
        )
    )
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
        if not epistemic_admission_allowed:
            gate_reasons.append("epistemic_admission_blocked")
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
    top_restrictions = _top_restrictions(
        tuple(item.restriction_code for item in obedience_decision.restrictions)
    )
    obedience_usability_class = _downstream_usability_class(obedience_decision.status)
    obedience_enter_values = {
        "accepted": obedience_decision.lawful_continue,
        "usability_class": obedience_usability_class,
        "top_restrictions": top_restrictions,
        "blocked_reason": None if obedience_decision.lawful_continue else obedience_decision.reason,
        "restriction_count": len(obedience_decision.restrictions),
    }
    trace_emit_active("downstream_obedience", "enter", obedience_enter_values)
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
    obedience_trace_values = {
        "accepted": obedience_decision.lawful_continue,
        "usability_class": obedience_usability_class,
        "top_restrictions": top_restrictions,
        "blocked_reason": None if obedience_decision.lawful_continue else obedience_reason,
        "restriction_count": len(obedience_decision.restrictions),
    }
    trace_emit_active("downstream_obedience", "decision", obedience_trace_values)
    if not obedience_decision.lawful_continue:
        trace_emit_active(
            "downstream_obedience",
            "blocked",
            obedience_trace_values,
            note=obedience_reason,
        )
    trace_emit_active("downstream_obedience", "exit", obedience_trace_values)
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

    adapter_input = context.world_adapter_input
    world_adapter_enter_values = {
        "adapter_presence": False if adapter_input is None else adapter_input.adapter_presence,
        "adapter_available": False if adapter_input is None else adapter_input.adapter_available,
        "adapter_degraded": False if adapter_input is None else adapter_input.adapter_degraded,
    }
    trace_emit_active("world_adapter", "enter", world_adapter_enter_values)
    world_adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode=active_execution_mode,
        adapter_input=adapter_input,
        request_action_candidate=(
            context.emit_world_action_candidate
            or context.require_world_effect_feedback_for_success_claim
        ),
        source_lineage=lineage,
    )
    world_adapter_trace_values = {
        "adapter_presence": world_adapter_result.state.adapter_presence,
        "adapter_available": world_adapter_result.state.adapter_available,
        "adapter_degraded": world_adapter_result.state.adapter_degraded,
        "world_link_status": world_adapter_result.state.world_link_status,
        "effect_status": world_adapter_result.state.effect_status,
        "world_grounded_transition_allowed": (
            world_adapter_result.gate.world_grounded_transition_allowed
        ),
        "effect_feedback_correlated": world_adapter_result.gate.effect_feedback_correlated,
    }
    trace_emit_active("world_adapter", "decision", world_adapter_trace_values)
    if not world_adapter_result.gate.world_grounded_transition_allowed:
        trace_emit_active(
            "world_adapter",
            "blocked",
            world_adapter_trace_values,
            note=world_adapter_result.gate.reason,
        )
    trace_emit_active("world_adapter", "exit", world_adapter_trace_values)
    world_entry_enter_values = {
        "world_presence_mode": world_adapter_result.state.world_link_status,
        "observation_basis_present": (
            world_adapter_result.state.last_observation_packet is not None
        ),
        "action_trace_present": world_adapter_result.state.last_action_packet is not None,
        "effect_basis_present": world_adapter_result.state.last_effect_packet is not None,
        "effect_feedback_correlated": world_adapter_result.gate.effect_feedback_correlated,
    }
    trace_emit_active("world_entry_contract", "enter", world_entry_enter_values)
    world_entry_result = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=world_adapter_result,
        source_lineage=lineage,
    )
    world_entry_trace_values = {
        "world_presence_mode": world_entry_result.episode.world_presence_mode,
        "observation_basis_present": world_entry_result.episode.observation_basis_present,
        "action_trace_present": world_entry_result.episode.action_trace_present,
        "effect_basis_present": world_entry_result.episode.effect_basis_present,
        "effect_feedback_correlated": world_entry_result.episode.effect_feedback_correlated,
        "w01_admission_ready": world_entry_result.w01_admission.admission_ready,
    }
    trace_emit_active("world_entry_contract", "decision", world_entry_trace_values)
    if not world_entry_result.w01_admission.admission_ready:
        trace_emit_active(
            "world_entry_contract",
            "blocked",
            world_entry_trace_values,
            note=world_entry_result.w01_admission.reason,
        )
    trace_emit_active("world_entry_contract", "exit", world_entry_trace_values)
    world_seam_enter_values = {
        "world_transition_allowed": (
            (not context.require_world_grounded_transition)
            or world_entry_result.world_grounded_transition_admissible
        )
        and (
            (not context.require_world_effect_feedback_for_success_claim)
            or world_entry_result.world_effect_success_admissible
        ),
        "seam_blocked": False,
        "seam_block_reason": None,
        "world_grounded_ready": world_entry_result.world_grounded_transition_admissible,
    }
    trace_emit_active("world_seam_enforcement", "enter", world_seam_enter_values)
    world_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    world_checkpoint_reason = world_entry_result.reason
    world_seam_block_reason: str | None = None
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
            world_seam_block_reason = "grounded_transition_required_unmet"
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
            world_seam_block_reason = "effect_feedback_required_unmet"
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        world_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        world_checkpoint_reason = "world seam enforcement disabled in ablation context"
        world_seam_block_reason = "enforcement_disabled"

    world_seam_trace_values = {
        "world_transition_allowed": world_checkpoint_status == SubjectTickCheckpointStatus.ALLOWED,
        "seam_blocked": world_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
        "seam_block_reason": world_seam_block_reason,
        "world_grounded_ready": world_entry_result.world_grounded_transition_admissible,
    }
    trace_emit_active("world_seam_enforcement", "decision", world_seam_trace_values)
    if world_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "world_seam_enforcement",
            "blocked",
            world_seam_trace_values,
            note=world_seam_block_reason or "world_seam_detour",
        )
    trace_emit_active("world_seam_enforcement", "exit", world_seam_trace_values)

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
    s01_result = build_s01_efference_copy(
        tick_id=tick_id,
        tick_index=tick_index,
        c04_selected_mode=mode_arbitration.state.active_mode.value,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        c05_no_safe_reuse=bool(temporal_validity.state.no_safe_reuse_item_ids),
        c05_revalidation_required=bool(
            temporal_validity.state.revalidation_item_ids
            or temporal_validity.state.selective_scope_targets
            or temporal_validity.state.selective_scope_uncertain
            or temporal_validity.state.insufficient_basis_for_revalidation
        ),
        c05_dependency_contaminated=bool(
            temporal_validity.state.dependency_contaminated_item_ids
        ),
        world_grounded_transition_admissible=(
            world_entry_result.world_grounded_transition_admissible
        ),
        world_effect_feedback_correlated=world_entry_result.episode.effect_feedback_correlated,
        world_confidence=world_entry_result.episode.confidence,
        world_incomplete=world_entry_result.episode.incomplete,
        world_degraded=world_entry_result.episode.degraded,
        emit_world_action_candidate=context.emit_world_action_candidate,
        prior_selected_mode=(
            None if prior_state is None else prior_state.c04_selected_mode
        ),
        prior_state=(
            context.prior_s01_state
            if isinstance(context.prior_s01_state, S01EfferenceCopyState)
            else None
        ),
        source_lineage=lineage,
        register_prediction=not context.disable_s01_prediction_registration,
    )
    s01_enter_values = {
        "efference_available": bool(
            s01_result.state.pending_predictions or s01_result.state.forward_packets
        ),
        "trace_ready": s01_result.gate.comparison_ready,
        "action_projection_present": bool(s01_result.state.forward_packets),
        "efference_blocked": False,
    }
    trace_emit_active("s01_efference_copy", "enter", s01_enter_values)
    s01_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    s01_checkpoint_reason = s01_result.gate.reason
    if not context.disable_s01_enforcement:
        if (
            context.require_s01_comparison_consumer
            and not s01_result.gate.comparison_ready
            and halt_reason is None
        ):
            revalidation_needed = True
            s01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s01_checkpoint_reason = (
                "s01 comparison consumer requested but no lawful intended-vs-observed entry is ready"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s01_prediction_validity_consumer
            and not s01_result.gate.prediction_validity_ready
            and halt_reason is None
        ):
            revalidation_needed = True
            s01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s01_checkpoint_reason = (
                "s01 prediction validity consumer requested but pending predictions are stale/contaminated"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s01_unexpected_change_consumer
            and s01_result.gate.unexpected_change_detected
            and halt_reason is None
            and not revalidation_needed
        ):
            repair_needed = True
            s01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s01_checkpoint_reason = (
                "s01 unexpected observed change requires bounded repair detour before continuation"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
    else:
        s01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        s01_checkpoint_reason = "s01 efference copy enforcement disabled in ablation context"
    s01_trace_values = {
        "efference_available": bool(
            s01_result.state.pending_predictions or s01_result.state.forward_packets
        ),
        "trace_ready": s01_result.gate.comparison_ready,
        "action_projection_present": bool(s01_result.state.forward_packets),
        "efference_blocked": s01_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("s01_efference_copy", "decision", s01_trace_values)
    if s01_trace_values["efference_blocked"]:
        trace_emit_active(
            "s01_efference_copy",
            "blocked",
            s01_trace_values,
            note="s01_checkpoint_not_allowed",
        )
    trace_emit_active("s01_efference_copy", "exit", s01_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.s01_efference_copy_checkpoint",
            source_contract="s01_efference_copy.intended_vs_observed_change",
            status=s01_checkpoint_status,
            required_action=(
                "require_s01_comparison_and_unexpected_and_prediction_validity"
                if (
                    context.require_s01_comparison_consumer
                    and context.require_s01_unexpected_change_consumer
                    and context.require_s01_prediction_validity_consumer
                )
                else "require_s01_comparison_consumer"
                if context.require_s01_comparison_consumer
                else "require_s01_unexpected_change_consumer"
                if context.require_s01_unexpected_change_consumer
                else "require_s01_prediction_validity_consumer"
                if context.require_s01_prediction_validity_consumer
                else "s01_optional"
            ),
            applied_action=active_execution_mode,
            reason=s01_checkpoint_reason,
        )
    )
    s02_result = build_s02_prediction_boundary(
        tick_id=tick_id,
        tick_index=tick_index,
        s01_result=s01_result,
        c04_selected_mode=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=bool(
            temporal_validity.state.revalidation_item_ids
            or temporal_validity.state.selective_scope_targets
            or temporal_validity.state.selective_scope_uncertain
            or temporal_validity.state.insufficient_basis_for_revalidation
        ),
        c05_dependency_contaminated=bool(
            temporal_validity.state.dependency_contaminated_item_ids
            or temporal_validity.state.no_safe_reuse_item_ids
        ),
        context_shift_detected=bool(context.context_shift_markers),
        effector_available=bool(context.emit_world_action_candidate),
        observation_degraded=bool(
            world_entry_result.episode.degraded or world_entry_result.episode.incomplete
        ),
        prior_state=context.prior_s02_state,
        source_lineage=lineage,
        context_scope=("c04_mode", c04_execution_mode_claim, "c05_action", c05_validity_action),
    )
    s02_view = derive_s02_boundary_consumer_view(s02_result)
    s02_enter_values = {
        "prediction_boundary_status": s02_result.state.active_boundary_status.value,
        "boundary_integrity": _s02_boundary_integrity(s02_result),
        "boundary_blocked": False,
        "prediction_ready": s02_view.can_consume_boundary,
    }
    trace_emit_active("s02_prediction_boundary", "enter", s02_enter_values)
    s02_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    s02_checkpoint_reason = s02_result.gate.reason
    if not context.disable_s02_enforcement:
        if (
            context.require_s02_boundary_consumer
            and not s02_view.can_consume_boundary
            and halt_reason is None
        ):
            revalidation_needed = True
            s02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s02_checkpoint_reason = (
                "s02 boundary consumer requested but prediction seam is uncertain/stale; revalidate detour enforced"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s02_controllability_consumer
            and not s02_view.can_consume_controllability
            and halt_reason is None
        ):
            repair_needed = True
            s02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s02_checkpoint_reason = (
                "s02 controllability consumer requested but controllability basis is not distinguishable from predictability"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_s02_mixed_source_consumer
            and not s02_view.can_consume_mixed_source
            and halt_reason is None
        ):
            revalidation_needed = True
            s02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s02_checkpoint_reason = (
                "s02 mixed-source consumer requested but mixed boundary is not preserved"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        s02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        s02_checkpoint_reason = "s02 prediction boundary enforcement disabled in ablation context"
    s02_trace_values = {
        "prediction_boundary_status": s02_result.state.active_boundary_status.value,
        "boundary_integrity": _s02_boundary_integrity(s02_result),
        "boundary_blocked": s02_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
        "prediction_ready": s02_view.can_consume_boundary,
    }
    trace_emit_active("s02_prediction_boundary", "decision", s02_trace_values)
    if s02_trace_values["boundary_blocked"]:
        trace_emit_active(
            "s02_prediction_boundary",
            "blocked",
            s02_trace_values,
            note="s02_checkpoint_not_allowed",
        )
    trace_emit_active("s02_prediction_boundary", "exit", s02_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.s02_prediction_boundary_checkpoint",
            source_contract="s02_prediction_boundary.self_vs_world_seam",
            status=s02_checkpoint_status,
            required_action=(
                "require_s02_boundary_and_controllability_and_mixed_source_consumer"
                if (
                    context.require_s02_boundary_consumer
                    and context.require_s02_controllability_consumer
                    and context.require_s02_mixed_source_consumer
                )
                else "require_s02_boundary_and_controllability_consumer"
                if (
                    context.require_s02_boundary_consumer
                    and context.require_s02_controllability_consumer
                )
                else "require_s02_boundary_consumer"
                if context.require_s02_boundary_consumer
                else "require_s02_controllability_consumer"
                if context.require_s02_controllability_consumer
                else "require_s02_mixed_source_consumer"
                if context.require_s02_mixed_source_consumer
                else "s02_optional"
            ),
            applied_action=active_execution_mode,
            reason=s02_checkpoint_reason,
        )
    )
    s03_result = build_s03_ownership_weighted_learning(
        tick_id=tick_id,
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        c04_selected_mode=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=bool(
            temporal_validity.state.revalidation_item_ids
            or temporal_validity.state.selective_scope_targets
            or temporal_validity.state.selective_scope_uncertain
            or temporal_validity.state.insufficient_basis_for_revalidation
        ),
        c05_dependency_contaminated=bool(
            temporal_validity.state.dependency_contaminated_item_ids
            or temporal_validity.state.no_safe_reuse_item_ids
        ),
        c05_no_safe_reuse=bool(
            temporal_validity.state.no_safe_reuse_item_ids
        ),
        context_shift_detected=bool(context.context_shift_markers),
        prior_state=context.prior_s03_state,
        source_lineage=lineage,
    )
    s03_view = derive_s03_update_packet_consumer_view(s03_result)
    s03_enter_values = {
        "ownership_status": s03_result.state.latest_update_class.value,
        "ownership_confidence": _s03_ownership_confidence(s03_result),
        "learning_weight_applied": _s03_learning_weight_applied(s03_result),
        "ownership_blocked": False,
    }
    trace_emit_active("s03_ownership_weighted_learning", "enter", s03_enter_values)
    s03_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    s03_checkpoint_reason = s03_result.gate.reason
    if not context.disable_s03_enforcement:
        if (
            context.require_s03_learning_packet_consumer
            and not s03_view.can_consume_learning_packet
            and halt_reason is None
        ):
            repair_needed = True
            s03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s03_checkpoint_reason = (
                "s03 learning packet consumer requested but ownership-weighted packet is deferred/frozen"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_s03_mixed_update_consumer
            and not s03_view.can_consume_mixed_update
            and halt_reason is None
        ):
            revalidation_needed = True
            s03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s03_checkpoint_reason = (
                "s03 mixed-update consumer requested but bounded split update packet is unavailable"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s03_freeze_obedience_consumer
            and not s03_view.can_obey_freeze
            and halt_reason is None
        ):
            revalidation_needed = True
            s03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s03_checkpoint_reason = (
                "s03 freeze-obedience consumer requested but freeze/defer packet cannot be lawfully consumed"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        s03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        s03_checkpoint_reason = (
            "s03 ownership-weighted learning enforcement disabled in ablation context"
        )
    s03_trace_values = {
        "ownership_status": s03_result.state.latest_update_class.value,
        "ownership_confidence": _s03_ownership_confidence(s03_result),
        "learning_weight_applied": _s03_learning_weight_applied(s03_result),
        "ownership_blocked": s03_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("s03_ownership_weighted_learning", "decision", s03_trace_values)
    if s03_trace_values["ownership_blocked"]:
        trace_emit_active(
            "s03_ownership_weighted_learning",
            "blocked",
            s03_trace_values,
            note="s03_checkpoint_not_allowed",
        )
    trace_emit_active("s03_ownership_weighted_learning", "exit", s03_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.s03_ownership_weighted_learning_checkpoint",
            source_contract="s03_ownership_weighted_learning.update_routing",
            status=s03_checkpoint_status,
            required_action=(
                "require_s03_learning_packet_and_mixed_update_and_freeze_obedience_consumer"
                if (
                    context.require_s03_learning_packet_consumer
                    and context.require_s03_mixed_update_consumer
                    and context.require_s03_freeze_obedience_consumer
                )
                else "require_s03_learning_packet_and_mixed_update_consumer"
                if (
                    context.require_s03_learning_packet_consumer
                    and context.require_s03_mixed_update_consumer
                )
                else "require_s03_learning_packet_consumer"
                if context.require_s03_learning_packet_consumer
                else "require_s03_mixed_update_consumer"
                if context.require_s03_mixed_update_consumer
                else "require_s03_freeze_obedience_consumer"
                if context.require_s03_freeze_obedience_consumer
                else "s03_optional"
            ),
            applied_action=active_execution_mode,
            reason=s03_checkpoint_reason,
        )
    )
    s04_result = build_s04_interoceptive_self_binding(
        tick_id=tick_id,
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        regulation_pressure_level=viability.state.pressure_level,
        regulation_dominant_axis=regulation.tradeoff.dominant_axis,
        c05_revalidation_required=bool(
            temporal_validity.state.revalidation_item_ids
            or temporal_validity.state.selective_scope_targets
            or temporal_validity.state.selective_scope_uncertain
            or temporal_validity.state.insufficient_basis_for_revalidation
        ),
        context_shift_detected=bool(context.context_shift_markers),
        prior_state=context.prior_s04_state,
        source_lineage=lineage,
        binding_enabled=not context.disable_s04_enforcement,
    )
    s04_view = derive_s04_interoceptive_self_binding_consumer_view(s04_result)
    s04_enter_values = {
        "strong_bound_count": len(s04_result.state.core_bound_channels),
        "weak_bound_count": len(
            [
                item
                for item in s04_result.state.entries
                if item.binding_status.value == "weakly_self_bound"
            ]
        ),
        "contested_count": len(s04_result.state.contested_channels),
        "provisional_count": len(
            [
                item
                for item in s04_result.state.entries
                if item.binding_status.value == "provisionally_bound"
            ]
        ),
        "no_stable_core_claim": s04_result.state.no_stable_self_core_claim,
        "strongest_binding_strength": s04_result.state.strongest_binding_strength,
        "contamination_detected": s04_result.state.contamination_detected,
        "rebinding_event": s04_result.state.rebinding_event,
        "stale_binding_drop_count": s04_result.state.stale_binding_drop_count,
    }
    trace_emit_active("s04_interoceptive_self_binding", "enter", s04_enter_values)
    s04_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    s04_checkpoint_reason = s04_result.gate.reason
    if not context.disable_s04_enforcement:
        if (
            context.require_s04_stable_core_consumer
            and not s04_view.can_consume_stable_core
            and halt_reason is None
        ):
            repair_needed = True
            s04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s04_checkpoint_reason = (
                "s04 stable-core consumer requested but no convergent self-binding core is available"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_s04_contested_consumer
            and not s04_view.can_consume_contested
            and halt_reason is None
        ):
            revalidation_needed = True
            s04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s04_checkpoint_reason = (
                "s04 contested consumer requested but no contested/mixed channels are present"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s04_no_stable_core_consumer
            and not s04_view.can_consume_no_stable_core
            and halt_reason is None
        ):
            revalidation_needed = True
            s04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s04_checkpoint_reason = (
                "s04 no-stable-core consumer requested but stable self-core claim is active"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        s04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        s04_checkpoint_reason = (
            "s04 interoceptive self-binding enforcement disabled in ablation context"
        )
    s04_trace_values = {
        "strong_bound_count": len(s04_result.state.core_bound_channels),
        "weak_bound_count": len(
            [
                item
                for item in s04_result.state.entries
                if item.binding_status.value == "weakly_self_bound"
            ]
        ),
        "contested_count": len(s04_result.state.contested_channels),
        "provisional_count": len(
            [
                item
                for item in s04_result.state.entries
                if item.binding_status.value == "provisionally_bound"
            ]
        ),
        "no_stable_core_claim": s04_result.state.no_stable_self_core_claim,
        "strongest_binding_strength": s04_result.state.strongest_binding_strength,
        "contamination_detected": s04_result.state.contamination_detected,
        "rebinding_event": s04_result.state.rebinding_event,
        "stale_binding_drop_count": s04_result.state.stale_binding_drop_count,
    }
    trace_emit_active("s04_interoceptive_self_binding", "decision", s04_trace_values)
    if s04_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "s04_interoceptive_self_binding",
            "blocked",
            s04_trace_values,
            note="s04_checkpoint_not_allowed",
        )
    trace_emit_active("s04_interoceptive_self_binding", "exit", s04_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.s04_interoceptive_self_binding_checkpoint",
            source_contract="s04_interoceptive_self_binding.binding_ledger",
            status=s04_checkpoint_status,
            required_action=(
                "require_s04_stable_core_and_contested_and_no_stable_core_consumer"
                if (
                    context.require_s04_stable_core_consumer
                    and context.require_s04_contested_consumer
                    and context.require_s04_no_stable_core_consumer
                )
                else "require_s04_stable_core_consumer"
                if context.require_s04_stable_core_consumer
                else "require_s04_contested_consumer"
                if context.require_s04_contested_consumer
                else "require_s04_no_stable_core_consumer"
                if context.require_s04_no_stable_core_consumer
                else "s04_optional"
            ),
            applied_action=active_execution_mode,
            reason=s04_checkpoint_reason,
        )
    )
    s05_result = build_s05_multi_cause_attribution_factorization(
        tick_id=tick_id,
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        s04_result=s04_result,
        c04_selected_mode=mode_arbitration.state.active_mode.value,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=_c05_revalidation_required(
            temporal_validity, c05_validity_action
        ),
        world_presence_mode=world_entry_result.episode.world_presence_mode.value,
        world_effect_feedback_correlated=world_entry_result.episode.effect_feedback_correlated,
        context_shift_detected=bool(context.context_shift_markers),
        late_evidence_tokens=tuple(
            dict.fromkeys(
                (
                    *context.context_shift_markers,
                    *context.contradicted_source_refs,
                    *context.withdrawn_source_refs,
                )
            )
        ),
        prior_state=context.prior_s05_state,
        source_lineage=lineage,
        factorization_enabled=not context.disable_s05_enforcement,
    )
    s05_view = derive_s05_multi_cause_attribution_consumer_view(s05_result)
    s05_dominant_causes = set(s05_result.state.dominant_cause_classes)
    s05_internal_present = bool(
        s05_dominant_causes
        & {
            S05CauseClass.SELF_INITIATED_ACT,
            S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION,
            S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT,
        }
    )
    s05_external_present = bool(
        s05_dominant_causes
        & {
            S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
            S05CauseClass.OBSERVATION_OR_CHANNEL_ARTIFACT,
        }
    )
    s05_shape_profile = _classify_s05_shape_profile(
        downstream_route_class=s05_result.telemetry.downstream_route_class,
        internal_present=s05_internal_present,
        external_present=s05_external_present,
    )
    s05_shape_aware_collapse_forbidden = (
        s05_view.do_not_collapse_to_single_cause
        and s05_internal_present
        and s05_external_present
    )
    s05_enter_values = {
        "dominant_slot_count": s05_result.telemetry.dominant_slot_count,
        "residual_share": s05_result.telemetry.residual_share,
        "residual_class": s05_result.telemetry.residual_class.value,
        "underdetermined_split": s05_result.telemetry.underdetermined_split,
        "contamination_present": s05_result.telemetry.contamination_present,
        "temporal_misalignment_present": s05_result.telemetry.temporal_misalignment_present,
        "reattribution_happened": s05_result.telemetry.reattribution_happened,
        "downstream_route_class": s05_result.telemetry.downstream_route_class.value,
        "factorization_consumer_ready": s05_result.telemetry.factorization_consumer_ready,
        "learning_route_ready": s05_result.telemetry.learning_route_ready,
    }
    trace_emit_active(
        "s05_multi_cause_attribution_factorization", "enter", s05_enter_values
    )
    s05_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    s05_checkpoint_reason = s05_result.gate.reason
    if not context.disable_s05_enforcement:
        if (
            s05_shape_profile == "mixed_internal_external"
            and halt_reason is None
            and not context.require_s05_factorized_consumer
            and not context.require_s05_low_residual_learning_route
        ):
            revalidation_needed = True
            s05_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s05_checkpoint_reason = (
                "s05 mixed internal/external split requires split-preserving revalidation before continuation"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s05_factorized_consumer
            and not s05_view.can_consume_factorization
            and halt_reason is None
        ):
            revalidation_needed = True
            s05_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s05_checkpoint_reason = (
                "s05 factorized-consumer requested but compatible factorization packet is not consumable"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_s05_low_residual_learning_route
            and not s05_view.can_route_learning_attribution
            and halt_reason is None
        ):
            revalidation_needed = True
            s05_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            s05_checkpoint_reason = (
                "s05 low-residual learning-route requested but residual/compatibility keeps routing underdetermined"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        s05_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        s05_checkpoint_reason = (
            "s05 multi-cause attribution enforcement disabled in ablation context"
        )
    s05_required_actions: list[str] = []
    if context.require_s05_factorized_consumer and context.require_s05_low_residual_learning_route:
        s05_required_actions.append(
            "require_s05_factorized_consumer_and_low_residual_learning_route"
        )
    elif context.require_s05_factorized_consumer:
        s05_required_actions.append("require_s05_factorized_consumer")
    elif context.require_s05_low_residual_learning_route:
        s05_required_actions.append("require_s05_low_residual_learning_route")
    if s05_shape_profile == "mixed_internal_external":
        s05_required_actions.append("split_shape_mixed_internal_external")
    elif s05_shape_profile == "world_or_artifact_heavy":
        s05_required_actions.append("split_shape_world_or_artifact_heavy")
    elif s05_shape_profile == "internal_multi_cause":
        s05_required_actions.append("split_shape_internal_multi_cause")
    if s05_shape_aware_collapse_forbidden:
        s05_required_actions.append("forbid_single_cause_collapse_shape_aware")
    if not s05_required_actions:
        s05_required_actions.append("s05_optional")
    s05_trace_values = {
        "dominant_slot_count": s05_result.telemetry.dominant_slot_count,
        "residual_share": s05_result.telemetry.residual_share,
        "residual_class": s05_result.telemetry.residual_class.value,
        "underdetermined_split": s05_result.telemetry.underdetermined_split,
        "contamination_present": s05_result.telemetry.contamination_present,
        "temporal_misalignment_present": s05_result.telemetry.temporal_misalignment_present,
        "reattribution_happened": s05_result.telemetry.reattribution_happened,
        "downstream_route_class": s05_result.telemetry.downstream_route_class.value,
        "factorization_consumer_ready": s05_result.telemetry.factorization_consumer_ready,
        "learning_route_ready": s05_result.telemetry.learning_route_ready,
    }
    trace_emit_active(
        "s05_multi_cause_attribution_factorization", "decision", s05_trace_values
    )
    if s05_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "s05_multi_cause_attribution_factorization",
            "blocked",
            s05_trace_values,
            note="s05_checkpoint_not_allowed",
        )
    trace_emit_active(
        "s05_multi_cause_attribution_factorization", "exit", s05_trace_values
    )
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.s05_multi_cause_attribution_checkpoint",
            source_contract="s05_multi_cause_attribution_factorization.factorization_packet",
            status=s05_checkpoint_status,
            required_action=";".join(dict.fromkeys(s05_required_actions)),
            applied_action=active_execution_mode,
            reason=s05_checkpoint_reason,
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
    s_minimal_enter_values = {
        "minimal_self_status": s_minimal_result.state.internal_vs_external_source_status.value,
        "minimal_self_ready": s_minimal_result.admission.admission_ready_for_s01,
        "contour_blocked": False,
    }
    trace_emit_active("s_minimal_contour", "enter", s_minimal_enter_values)
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
    s_minimal_trace_values = {
        "minimal_self_status": s_minimal_result.state.internal_vs_external_source_status.value,
        "minimal_self_ready": s_minimal_result.admission.admission_ready_for_s01,
        "contour_blocked": s_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("s_minimal_contour", "decision", s_minimal_trace_values)
    if s_minimal_trace_values["contour_blocked"]:
        trace_emit_active(
            "s_minimal_contour",
            "blocked",
            s_minimal_trace_values,
            note="s_minimal_checkpoint_not_allowed",
        )
    trace_emit_active("s_minimal_contour", "exit", s_minimal_trace_values)
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
    a_line_enter_values = {
        "normalization_status": a_line_result.state.capability_status.value,
        "normalized_ready": a_line_result.a04_readiness.admission_ready_for_a04,
        "normalization_blocked": False,
        "normalization_scope": a_line_result.scope_marker.scope,
    }
    trace_emit_active("a_line_normalization", "enter", a_line_enter_values)
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
    a_line_trace_values = {
        "normalization_status": a_line_result.state.capability_status.value,
        "normalized_ready": a_line_result.a04_readiness.admission_ready_for_a04,
        "normalization_blocked": a_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
        "normalization_scope": a_line_result.scope_marker.scope,
    }
    trace_emit_active("a_line_normalization", "decision", a_line_trace_values)
    if a_line_trace_values["normalization_blocked"]:
        trace_emit_active(
            "a_line_normalization",
            "blocked",
            a_line_trace_values,
            note="a_line_checkpoint_not_allowed",
        )
    trace_emit_active("a_line_normalization", "exit", a_line_trace_values)

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
    m_minimal_enter_values = {
        "minimal_memory_status": m_minimal_result.state.lifecycle_status.value,
        "memory_ready": m_minimal_result.admission.admission_ready_for_m01,
        "memory_blocked": False,
    }
    trace_emit_active("m_minimal", "enter", m_minimal_enter_values)
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
    m_minimal_trace_values = {
        "minimal_memory_status": m_minimal_result.state.lifecycle_status.value,
        "memory_ready": m_minimal_result.admission.admission_ready_for_m01,
        "memory_blocked": m_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("m_minimal", "decision", m_minimal_trace_values)
    if m_minimal_trace_values["memory_blocked"]:
        trace_emit_active(
            "m_minimal",
            "blocked",
            m_minimal_trace_values,
            note="m_minimal_checkpoint_not_allowed",
        )
    trace_emit_active("m_minimal", "exit", m_minimal_trace_values)
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
    n_minimal_result = build_n_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        claim_pressure=context.require_narrative_safe_claim,
        source_lineage=lineage,
    )
    n_minimal_enter_values = {
        "minimal_narrative_status": n_minimal_result.state.commitment_status.value,
        "narrative_ready": n_minimal_result.admission.admission_ready_for_n01,
        "narrative_blocked": False,
    }
    trace_emit_active("n_minimal", "enter", n_minimal_enter_values)
    n_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    n_checkpoint_reason = n_minimal_result.gate.reason
    if not context.disable_n_minimal_enforcement:
        if (
            context.require_narrative_safe_claim
            and not n_minimal_result.gate.safe_narrative_commitment_allowed
            and halt_reason is None
        ):
            n_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            if (
                n_minimal_result.state.ambiguity_residue
                or n_minimal_result.state.contradiction_risk.value in {"medium", "high"}
                or n_minimal_result.state.underconstrained
            ):
                revalidation_needed = True
                n_checkpoint_reason = (
                    "safe narrative commitment requested but basis remains ambiguous/contradictory or underconstrained"
                )
                if active_execution_mode != "halt_execution":
                    active_execution_mode = "revalidate_scope"
            else:
                repair_needed = True
                n_checkpoint_reason = (
                    "safe narrative commitment requested but no safe narrative basis is available"
                )
                if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                    active_execution_mode = "repair_runtime_path"
    else:
        n_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        n_checkpoint_reason = "n-minimal contour enforcement disabled in ablation context"
    n_minimal_trace_values = {
        "minimal_narrative_status": n_minimal_result.state.commitment_status.value,
        "narrative_ready": n_minimal_result.admission.admission_ready_for_n01,
        "narrative_blocked": n_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("n_minimal", "decision", n_minimal_trace_values)
    if n_minimal_trace_values["narrative_blocked"]:
        trace_emit_active(
            "n_minimal",
            "blocked",
            n_minimal_trace_values,
            note="n_minimal_checkpoint_not_allowed",
        )
    trace_emit_active("n_minimal", "exit", n_minimal_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.n_minimal_contour_checkpoint",
            source_contract="n_minimal.narrative_commitment",
            status=n_checkpoint_status,
            required_action=(
                "require_narrative_safe_claim"
                if context.require_narrative_safe_claim
                else "n_minimal_optional"
            ),
            applied_action=active_execution_mode,
            reason=n_checkpoint_reason,
        )
    )
    t01_result = build_t01_active_semantic_field(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        prior_state=None,
        maintain_unresolved_slots=not context.disable_t01_unresolved_slot_maintenance,
        source_lineage=lineage,
    )
    t01_enter_values = {
        "scene_status": t01_result.state.scene_status,
        "unresolved_slots_count": len(t01_result.state.unresolved_slots),
    }
    trace_emit_active("t01_semantic_field", "enter", t01_enter_values)
    t01_preverbal_view = derive_t01_preverbal_consumer_view(t01_result)
    t01_scene_comparison_ready = bool(
        t01_preverbal_view.comparison_ready and not t01_preverbal_view.clarification_required
    )
    t01_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    t01_checkpoint_reason = t01_result.gate.reason
    if not context.disable_t01_field_enforcement:
        if (
            context.require_t01_preverbal_scene_consumer
            and "premature_scene_closure" in t01_result.gate.forbidden_shortcuts
            and halt_reason is None
        ):
            t01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t01_checkpoint_reason = (
                "t01 unresolved laundering risk detected under pre-verbal consumer pressure; revalidate detour enforced"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_t01_preverbal_scene_consumer
            and not t01_result.gate.pre_verbal_consumer_ready
            and halt_reason is None
        ):
            t01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            if t01_result.gate.no_clean_scene_commit:
                revalidation_needed = True
                t01_checkpoint_reason = (
                    "t01 pre-verbal consumer requested but scene is no-clean/contested; clarification/revalidate required"
                )
                if active_execution_mode != "halt_execution":
                    active_execution_mode = "revalidate_scope"
            else:
                repair_needed = True
                t01_checkpoint_reason = (
                    "t01 pre-verbal consumer requested but scene remains fragmentary/authority-insufficient"
                )
                if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                    active_execution_mode = "repair_runtime_path"
        if (
            context.require_t01_scene_comparison_consumer
            and not t01_scene_comparison_ready
            and halt_reason is None
        ):
            t01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t01_checkpoint_reason = (
                "t01 comparison consumer requested but scene is not comparison-ready; revalidate detour enforced"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        t01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        t01_checkpoint_reason = "t01 semantic field enforcement disabled in ablation context"
    t01_trace_values = {
        "scene_status": t01_result.state.scene_status,
        "unresolved_slots_count": len(t01_result.state.unresolved_slots),
        "pre_verbal_consumer_ready": t01_result.gate.pre_verbal_consumer_ready,
        "no_clean_scene_commit": t01_result.gate.no_clean_scene_commit,
    }
    trace_emit_active("t01_semantic_field", "decision", t01_trace_values)
    if t01_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "t01_semantic_field",
            "blocked",
            t01_trace_values,
            note=t01_checkpoint_reason,
        )
    trace_emit_active("t01_semantic_field", "exit", t01_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.t01_semantic_field_checkpoint",
            source_contract="t01_semantic_field.active_non_verbal_scene",
            status=t01_checkpoint_status,
            required_action=(
                "require_t01_preverbal_and_comparison_consumer"
                if (
                    context.require_t01_preverbal_scene_consumer
                    and context.require_t01_scene_comparison_consumer
                )
                else "require_t01_preverbal_scene_consumer"
                if context.require_t01_preverbal_scene_consumer
                else "require_t01_scene_comparison_consumer"
                if context.require_t01_scene_comparison_consumer
                else "t01_optional"
            ),
            applied_action=active_execution_mode,
            reason=t01_checkpoint_reason,
        )
    )
    t02_assembly_mode = _resolve_t02_assembly_mode(context.t02_assembly_mode)
    t02_result = build_t02_constrained_scene(
        tick_id=tick_id,
        t01_result=t01_result,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        c05_validity_action=c05_validity_action,
        assembly_mode=t02_assembly_mode,
        source_lineage=lineage,
    )
    t02_enter_values = {
        "scene_status": t02_result.state.scene_status,
    }
    trace_emit_active("t02_relation_binding", "enter", t02_enter_values)
    t02_preverbal_view = derive_t02_preverbal_constraint_consumer_view(t02_result)
    t02_raw_vs_propagated_distinct = t02_preverbal_view.raw_vs_propagated_distinct
    t02_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    t02_checkpoint_reason = t02_result.gate.reason
    if not context.disable_t02_enforcement:
        if (
            context.require_t02_constrained_scene_consumer
            and "silent_conflict_overwrite" in t02_result.gate.forbidden_shortcuts
            and halt_reason is None
        ):
            t02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t02_checkpoint_reason = (
                "t02 conflict preservation shortcut detected under constrained-scene consumer pressure; revalidate detour enforced"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_t02_constrained_scene_consumer
            and not t02_preverbal_view.can_consume_constrained_scene
            and halt_reason is None
        ):
            t02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            if t02_result.gate.no_clean_binding_commit:
                revalidation_needed = True
                t02_checkpoint_reason = (
                    "t02 constrained-scene consumer requested but bindings remain no-clean/conflicted; revalidate detour enforced"
                )
                if active_execution_mode != "halt_execution":
                    active_execution_mode = "revalidate_scope"
            else:
                repair_needed = True
                t02_checkpoint_reason = (
                    "t02 constrained-scene consumer requested but relation binding surface is not consumable"
                )
                if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                    active_execution_mode = "repair_runtime_path"
    else:
        t02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        t02_checkpoint_reason = "t02 relation binding enforcement disabled in ablation context"
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.t02_relation_binding_checkpoint",
            source_contract="t02_relation_binding.constraint_propagation",
            status=t02_checkpoint_status,
            required_action=(
                "require_t02_constrained_scene_consumer"
                if context.require_t02_constrained_scene_consumer
                else "t02_optional"
            ),
            applied_action=active_execution_mode,
            reason=t02_checkpoint_reason,
        )
    )
    t02_integrity_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    t02_integrity_checkpoint_reason = (
        "t02 raw-vs-propagated distinction preserved for bounded downstream use"
    )
    if not context.disable_t02_enforcement:
        if (
            context.require_t02_raw_vs_propagated_distinction
            and not t02_raw_vs_propagated_distinct
            and halt_reason is None
        ):
            t02_integrity_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t02_integrity_checkpoint_reason = (
                "t02 raw-vs-propagated distinction required but collapsed; revalidate detour enforced"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        t02_integrity_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        t02_integrity_checkpoint_reason = (
            "t02 raw-vs-propagated integrity enforcement disabled in ablation context"
        )
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.t02_raw_vs_propagated_integrity_checkpoint",
            source_contract="t02_relation_binding.raw_vs_propagated_distinction",
            status=t02_integrity_checkpoint_status,
            required_action=(
                "require_t02_raw_vs_propagated_distinction"
                if context.require_t02_raw_vs_propagated_distinction
                else "t02_raw_vs_propagated_optional"
            ),
            applied_action=active_execution_mode,
            reason=t02_integrity_checkpoint_reason,
        )
    )
    t02_trace_values = {
        "scene_status": t02_result.state.scene_status,
        "no_clean_binding_commit": t02_result.gate.no_clean_binding_commit,
        "pre_verbal_constraint_consumer_ready": (
            t02_result.gate.pre_verbal_constraint_consumer_ready
        ),
        "raw_vs_propagated_distinct": t02_raw_vs_propagated_distinct,
    }
    trace_emit_active("t02_relation_binding", "decision", t02_trace_values)
    if (
        t02_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED
        or t02_integrity_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED
    ):
        trace_emit_active(
            "t02_relation_binding",
            "blocked",
            t02_trace_values,
            note=f"{t02_checkpoint_reason}; {t02_integrity_checkpoint_reason}",
        )
    trace_emit_active("t02_relation_binding", "exit", t02_trace_values)
    t03_competition_mode = _resolve_t03_competition_mode(context.t03_competition_mode)
    t03_result = build_t03_hypothesis_competition(
        tick_id=tick_id,
        t01_result=t01_result,
        t02_result=t02_result,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        c05_validity_action=c05_validity_action,
        competition_mode=t03_competition_mode,
        source_lineage=lineage,
    )
    t03_enter_values = {
        "leader": t03_result.state.publication_frontier.current_leader,
        "conflict_count": len(t03_result.state.publication_frontier.unresolved_conflicts),
        "open_slot_count": len(t03_result.state.publication_frontier.open_slots),
    }
    trace_emit_active("t03_hypothesis_competition", "enter", t03_enter_values)
    t03_preverbal_view = derive_t03_preverbal_competition_consumer_view(t03_result)
    t03_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    t03_checkpoint_reason = t03_result.gate.reason
    if not context.disable_t03_enforcement:
        if (
            context.require_t03_convergence_consumer
            and not t03_preverbal_view.can_consume_convergence
            and halt_reason is None
        ):
            t03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            if t03_result.state.honest_nonconvergence:
                revalidation_needed = True
                t03_checkpoint_reason = (
                    "t03 convergence consumer requested but frontier remains honestly non-converged; revalidate detour enforced"
                )
                if active_execution_mode != "halt_execution":
                    active_execution_mode = "revalidate_scope"
            else:
                repair_needed = True
                t03_checkpoint_reason = (
                    "t03 convergence consumer requested but no lawful local converged leader is consumable"
                )
                if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                    active_execution_mode = "repair_runtime_path"
        if (
            context.require_t03_frontier_consumer
            and not t03_preverbal_view.frontier_consumer_ready
            and halt_reason is None
        ):
            t03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            repair_needed = True
            t03_checkpoint_reason = (
                "t03 frontier consumer requested but publication frontier is structurally incomplete"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_t03_nonconvergence_preservation
            and not t03_preverbal_view.nonconvergence_preserved
            and halt_reason is None
        ):
            t03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t03_checkpoint_reason = (
                "t03 nonconvergence preservation requested but unresolved competition frontier was collapsed"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        t03_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        t03_checkpoint_reason = (
            "t03 hypothesis competition enforcement disabled in ablation context"
        )
    t03_no_viable_leader = t03_result.state.publication_frontier.current_leader is None
    t03_nonconvergence_basis = _t03_nonconvergence_basis(
        convergence_status=t03_result.state.convergence_status.value,
        conflict_count=len(t03_result.state.publication_frontier.unresolved_conflicts),
        open_slot_count=len(t03_result.state.publication_frontier.open_slots),
        no_viable_leader=t03_no_viable_leader,
    )
    t03_trace_values = {
        "leader": t03_result.state.publication_frontier.current_leader,
        "conflict_count": len(t03_result.state.publication_frontier.unresolved_conflicts),
        "open_slot_count": len(t03_result.state.publication_frontier.open_slots),
        "convergence_status": t03_result.state.convergence_status,
        "nonconvergence_preserved": t03_result.gate.nonconvergence_preserved,
        "no_viable_leader": t03_no_viable_leader,
        "nonconvergence_basis": t03_nonconvergence_basis,
    }
    trace_emit_active("t03_hypothesis_competition", "decision", t03_trace_values)
    if t03_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "t03_hypothesis_competition",
            "blocked",
            t03_trace_values,
            note=t03_checkpoint_reason,
        )
    trace_emit_active("t03_hypothesis_competition", "exit", t03_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.t03_hypothesis_competition_checkpoint",
            source_contract="t03_hypothesis_competition.silent_convergence",
            status=t03_checkpoint_status,
            required_action=(
                "require_t03_convergence_and_frontier_and_nonconvergence_preservation"
                if (
                    context.require_t03_convergence_consumer
                    and context.require_t03_frontier_consumer
                    and context.require_t03_nonconvergence_preservation
                )
                else "require_t03_convergence_and_frontier_consumer"
                if (
                    context.require_t03_convergence_consumer
                    and context.require_t03_frontier_consumer
                )
                else "require_t03_convergence_consumer"
                if context.require_t03_convergence_consumer
                else "require_t03_frontier_consumer"
                if context.require_t03_frontier_consumer
                else "require_t03_nonconvergence_preservation"
                if context.require_t03_nonconvergence_preservation
                else "t03_optional"
            ),
            applied_action=active_execution_mode,
            reason=t03_checkpoint_reason,
        )
    )
    t04_result = build_t04_attention_schema(
        tick_id=tick_id,
        t03_result=t03_result,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        source_lineage=lineage,
    )
    t04_enter_values = {
        "attention_owner": t04_result.state.attention_owner,
        "focus_mode": t04_result.state.focus_mode,
        "reportability_status": t04_result.state.reportability_status,
    }
    trace_emit_active("t04_attention_schema", "enter", t04_enter_values)
    t04_preverbal_view = derive_t04_preverbal_focus_consumer_view(t04_result)
    t04_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    t04_checkpoint_reason = t04_result.gate.reason
    if not context.disable_t04_enforcement:
        if (
            context.require_t04_focus_ownership_consumer
            and not t04_preverbal_view.can_consume_focus_ownership
            and halt_reason is None
        ):
            t04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            repair_needed = True
            t04_checkpoint_reason = (
                "t04 focus-ownership consumer requested but lawful owner/control basis is not consumable"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_t04_reportable_focus_consumer
            and not t04_preverbal_view.can_consume_reportable_focus
            and halt_reason is None
        ):
            t04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t04_checkpoint_reason = (
                "t04 reportable-focus consumer requested but stability/reportability remains underconstrained"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_t04_peripheral_preservation
            and not t04_preverbal_view.peripheral_preservation_ready
            and halt_reason is None
        ):
            t04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            revalidation_needed = True
            t04_checkpoint_reason = (
                "t04 peripheral-preservation consumer requested but unresolved competitive targets were collapsed"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        t04_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        t04_checkpoint_reason = "t04 attention schema enforcement disabled in ablation context"
    t04_trace_values = {
        "attention_owner": t04_result.state.attention_owner,
        "focus_mode": t04_result.state.focus_mode,
        "reportability_status": t04_result.state.reportability_status,
        "focus_ownership_consumer_ready": t04_result.gate.focus_ownership_consumer_ready,
    }
    trace_emit_active("t04_attention_schema", "decision", t04_trace_values)
    if t04_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "t04_attention_schema",
            "blocked",
            t04_trace_values,
            note=t04_checkpoint_reason,
        )
    trace_emit_active("t04_attention_schema", "exit", t04_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.t04_attention_schema_checkpoint",
            source_contract="t04_attention_schema.focus_ownership_model",
            status=t04_checkpoint_status,
            required_action=(
                "require_t04_focus_ownership_and_reportable_focus_and_peripheral_preservation"
                if (
                    context.require_t04_focus_ownership_consumer
                    and context.require_t04_reportable_focus_consumer
                    and context.require_t04_peripheral_preservation
                )
                else "require_t04_focus_ownership_and_reportable_focus_consumer"
                if (
                    context.require_t04_focus_ownership_consumer
                    and context.require_t04_reportable_focus_consumer
                )
                else "require_t04_focus_ownership_consumer"
                if context.require_t04_focus_ownership_consumer
                else "require_t04_reportable_focus_consumer"
                if context.require_t04_reportable_focus_consumer
                else "require_t04_peripheral_preservation"
                if context.require_t04_peripheral_preservation
                else "t04_optional"
            ),
            applied_action=active_execution_mode,
            reason=t04_checkpoint_reason,
        )
    )

    o01_result = build_o01_other_entity_model(
        tick_id=tick_id,
        tick_index=tick_index,
        signals=context.o01_entity_signals,
        prior_state=context.prior_o01_state,
        source_lineage=lineage,
        model_enabled=not context.disable_o01_enforcement,
    )
    o01_view = derive_o01_other_entity_model_consumer_view(o01_result)
    o01_enter_values = {
        "entity_count": o01_result.telemetry.entity_count,
        "current_user_model_ready": o01_result.telemetry.current_user_model_ready,
        "third_party_models_active": o01_result.telemetry.third_party_models_active,
        "stable_claim_count": o01_result.telemetry.stable_claim_count,
        "temporary_hypothesis_count": o01_result.telemetry.temporary_hypothesis_count,
        "contradiction_count": o01_result.telemetry.contradiction_count,
        "knowledge_boundary_known_count": o01_result.telemetry.knowledge_boundary_known_count,
        "projection_guard_triggered": o01_result.telemetry.projection_guard_triggered,
        "no_safe_state_claim": o01_result.telemetry.no_safe_state_claim,
        "downstream_consumer_ready": o01_result.telemetry.downstream_consumer_ready,
    }
    trace_emit_active("o01_other_entity_model", "enter", o01_enter_values)
    o01_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    o01_checkpoint_reason = o01_result.gate.reason
    o01_default_competing_clarification = False
    o01_default_overlay_clarification = False
    if not context.disable_o01_enforcement:
        if (
            context.require_o01_entity_individuation_consumer
            and not o01_view.can_consume_current_user_model
            and halt_reason is None
            and not revalidation_needed
        ):
            repair_needed = True
            o01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o01_checkpoint_reason = (
                "o01 entity-individuation consumer requested but current-user model remains underconstrained"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
        if (
            context.require_o01_clarification_ready_consumer
            and o01_view.clarification_required
            and halt_reason is None
        ):
            revalidation_needed = True
            o01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o01_checkpoint_reason = (
                "o01 clarification-ready consumer requested but perspective remains ambiguous/competing"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            not context.require_o01_entity_individuation_consumer
            and not context.require_o01_clarification_ready_consumer
            and o01_result.state.competing_entity_models
            and halt_reason is None
            and not revalidation_needed
        ):
            revalidation_needed = True
            o01_default_competing_clarification = True
            o01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o01_checkpoint_reason = (
                "o01 default contour requires clarification when competing entity models remain unresolved"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            not context.require_o01_entity_individuation_consumer
            and not context.require_o01_clarification_ready_consumer
            and "belief_overlay_underconstrained" in o01_result.gate.restrictions
            and o01_result.state.current_user_entity_id is not None
            and halt_reason is None
            and not revalidation_needed
        ):
            revalidation_needed = True
            o01_default_overlay_clarification = True
            o01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o01_checkpoint_reason = (
                "o01 default contour requires clarification when belief/ignorance overlay stays underconstrained"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
    else:
        o01_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        o01_checkpoint_reason = "o01 other-entity model enforcement disabled in ablation context"
    o01_required_actions: list[str] = []
    if context.require_o01_entity_individuation_consumer:
        o01_required_actions.append("require_o01_entity_individuation_consumer")
    if context.require_o01_clarification_ready_consumer:
        o01_required_actions.append("require_o01_clarification_ready_consumer")
    if o01_result.state.projection_guard_triggered:
        o01_required_actions.append("o01_projection_guard_triggered")
    if o01_result.state.competing_entity_models:
        o01_required_actions.append("o01_competing_entity_models")
    if o01_default_competing_clarification:
        o01_required_actions.append("default_o01_competing_entity_clarification")
    if o01_default_overlay_clarification:
        o01_required_actions.append("default_o01_belief_overlay_clarification")
    if not o01_required_actions:
        o01_required_actions.append("o01_optional")
    o01_trace_values = {
        "entity_count": o01_result.telemetry.entity_count,
        "current_user_model_ready": o01_result.telemetry.current_user_model_ready,
        "third_party_models_active": o01_result.telemetry.third_party_models_active,
        "stable_claim_count": o01_result.telemetry.stable_claim_count,
        "temporary_hypothesis_count": o01_result.telemetry.temporary_hypothesis_count,
        "contradiction_count": o01_result.telemetry.contradiction_count,
        "knowledge_boundary_known_count": o01_result.telemetry.knowledge_boundary_known_count,
        "projection_guard_triggered": o01_result.telemetry.projection_guard_triggered,
        "no_safe_state_claim": o01_result.telemetry.no_safe_state_claim,
        "downstream_consumer_ready": o01_result.telemetry.downstream_consumer_ready,
    }
    trace_emit_active("o01_other_entity_model", "decision", o01_trace_values)
    if o01_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "o01_other_entity_model",
            "blocked",
            o01_trace_values,
            note=o01_checkpoint_reason,
        )
    trace_emit_active("o01_other_entity_model", "exit", o01_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.o01_other_entity_model_checkpoint",
            source_contract="o01_other_entity_model.entities",
            status=o01_checkpoint_status,
            required_action=";".join(dict.fromkeys(o01_required_actions)),
            applied_action=active_execution_mode,
            reason=o01_checkpoint_reason,
        )
    )

    o02_diagnostics = context.o02_interaction_diagnostics
    if o02_diagnostics is None:
        o02_diagnostics = O02InteractionDiagnosticsInput()
    o02_result = build_o02_intersubjective_allostasis(
        tick_id=tick_id,
        tick_index=tick_index,
        o01_result=o01_result,
        s05_result=s05_result,
        c04_selected_mode=mode_arbitration.state.active_mode.value,
        c05_revalidation_required=_c05_revalidation_required(
            temporal_validity, c05_validity_action
        ),
        regulation_pressure_level=viability.state.pressure_level,
        interaction_diagnostics=o02_diagnostics,
        prior_state=context.prior_o02_state,
        source_lineage=lineage,
        allostasis_enabled=not context.disable_o02_enforcement,
    )
    o02_view = derive_o02_intersubjective_allostasis_consumer_view(o02_result)
    o02_enter_values = {
        "interaction_mode": o02_result.telemetry.interaction_mode.value,
        "predicted_other_load": o02_result.telemetry.predicted_other_load.value,
        "predicted_self_load": o02_result.telemetry.predicted_self_load.value,
        "repair_pressure": o02_result.telemetry.repair_pressure.value,
        "other_model_reliance_status": o02_result.telemetry.other_model_reliance_status.value,
        "boundary_protection_status": o02_result.telemetry.boundary_protection_status.value,
        "no_safe_regulation_claim": o02_result.telemetry.no_safe_regulation_claim,
        "other_load_underconstrained": o02_result.state.other_load_underconstrained,
        "self_other_constraint_conflict": o02_result.state.self_other_constraint_conflict,
        "downstream_consumer_ready": o02_result.telemetry.downstream_consumer_ready,
    }
    trace_emit_active("o02_intersubjective_allostasis", "enter", o02_enter_values)
    o02_checkpoint_status = SubjectTickCheckpointStatus.ALLOWED
    o02_checkpoint_reason = o02_result.gate.reason
    o02_default_repair_clarification_detour = False
    o02_default_conservative_detour = False
    if not context.disable_o02_enforcement:
        if (
            context.require_o02_repair_sensitive_consumer
            and not o02_view.repair_sensitive_consumer_ready
            and halt_reason is None
        ):
            revalidation_needed = True
            o02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o02_checkpoint_reason = (
                "o02 repair-sensitive consumer requested but repair posture remains underconstrained"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            context.require_o02_boundary_preserving_consumer
            and not o02_view.boundary_preserving_consumer_ready
            and halt_reason is None
        ):
            revalidation_needed = True
            o02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o02_checkpoint_reason = (
                "o02 boundary-preserving consumer requested but self/other boundary posture is conflicted"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            not context.require_o02_repair_sensitive_consumer
            and not context.require_o02_boundary_preserving_consumer
            and o02_view.repair_sensitive_detour_recommended
            and o02_view.clarification_required
            and halt_reason is None
            and not revalidation_needed
        ):
            revalidation_needed = True
            o02_default_repair_clarification_detour = True
            o02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o02_checkpoint_reason = (
                "o02 default contour requires repair-sensitive clarification before continuation"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            not context.require_o02_repair_sensitive_consumer
            and not context.require_o02_boundary_preserving_consumer
            and o02_view.conservative_mode_only
            and (
                o02_result.state.other_load_underconstrained
                or o02_result.state.no_safe_regulation_claim
            )
            and o02_result.state.repair_pressure.value in {"medium", "high"}
            and halt_reason is None
        ):
            revalidation_needed = True
            o02_default_conservative_detour = True
            o02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o02_checkpoint_reason = (
                "o02 default contour requires conservative clarification when other-model basis is underconstrained"
            )
            if active_execution_mode != "halt_execution":
                active_execution_mode = "revalidate_scope"
        if (
            o02_view.boundary_preservation_required
            and not o02_view.boundary_preserving_consumer_ready
            and halt_reason is None
            and not revalidation_needed
        ):
            repair_needed = True
            o02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
            o02_checkpoint_reason = (
                "o02 boundary-protection conflict requires repair before continuation"
            )
            if active_execution_mode not in {"halt_execution", "revalidate_scope"}:
                active_execution_mode = "repair_runtime_path"
    else:
        o02_checkpoint_status = SubjectTickCheckpointStatus.ENFORCED_DETOUR
        o02_checkpoint_reason = (
            "o02 intersubjective allostasis enforcement disabled in ablation context"
        )
    o02_required_actions: list[str] = []
    if context.require_o02_repair_sensitive_consumer:
        o02_required_actions.append("require_o02_repair_sensitive_consumer")
    if context.require_o02_boundary_preserving_consumer:
        o02_required_actions.append("require_o02_boundary_preserving_consumer")
    if o02_default_repair_clarification_detour:
        o02_required_actions.append("default_o02_repair_sensitive_clarification_detour")
    if o02_default_conservative_detour:
        o02_required_actions.append("default_o02_conservative_clarification_detour")
    if o02_result.state.other_load_underconstrained:
        o02_required_actions.append("other_load_underconstrained")
    if o02_result.state.self_other_constraint_conflict:
        o02_required_actions.append("self_other_constraint_conflict")
    if o02_view.do_not_collapse_to_politeness:
        o02_required_actions.append("o02_politeness_only_collapse_forbidden")
    if not o02_required_actions:
        o02_required_actions.append("o02_optional")
    o02_trace_values = {
        "interaction_mode": o02_result.telemetry.interaction_mode.value,
        "predicted_other_load": o02_result.telemetry.predicted_other_load.value,
        "predicted_self_load": o02_result.telemetry.predicted_self_load.value,
        "repair_pressure": o02_result.telemetry.repair_pressure.value,
        "other_model_reliance_status": o02_result.telemetry.other_model_reliance_status.value,
        "boundary_protection_status": o02_result.telemetry.boundary_protection_status.value,
        "no_safe_regulation_claim": o02_result.telemetry.no_safe_regulation_claim,
        "other_load_underconstrained": o02_result.state.other_load_underconstrained,
        "self_other_constraint_conflict": o02_result.state.self_other_constraint_conflict,
        "downstream_consumer_ready": o02_result.telemetry.downstream_consumer_ready,
    }
    trace_emit_active("o02_intersubjective_allostasis", "decision", o02_trace_values)
    if o02_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED:
        trace_emit_active(
            "o02_intersubjective_allostasis",
            "blocked",
            o02_trace_values,
            note=o02_checkpoint_reason,
        )
    trace_emit_active("o02_intersubjective_allostasis", "exit", o02_trace_values)
    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.o02_intersubjective_allostasis_checkpoint",
            source_contract="o02_intersubjective_allostasis.regulation_state",
            status=o02_checkpoint_status,
            required_action=";".join(dict.fromkeys(o02_required_actions)),
            applied_action=active_execution_mode,
            reason=o02_checkpoint_reason,
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

    bounded_outcome_checkpoint_status = (
        SubjectTickCheckpointStatus.BLOCKED
        if final_outcome == SubjectTickOutcome.HALT
        else SubjectTickCheckpointStatus.ENFORCED_DETOUR
        if final_outcome != SubjectTickOutcome.CONTINUE
        else SubjectTickCheckpointStatus.ALLOWED
    )
    bounded_outcome_enter_values = {
        "bounded_outcome_class": execution_stance.value,
        "output_allowed": final_outcome == SubjectTickOutcome.CONTINUE,
        "materialization_mode": active_execution_mode,
        "bounded_reason": _bounded_outcome_reason(
            final_outcome=final_outcome,
            halt_reason=halt_reason,
            output_allowed=final_outcome == SubjectTickOutcome.CONTINUE,
        ),
        "outcome_ready": bounded_outcome_checkpoint_status == SubjectTickCheckpointStatus.ALLOWED,
    }
    trace_emit_active("bounded_outcome_resolution", "enter", bounded_outcome_enter_values)

    checkpoints.append(
        SubjectTickCheckpointResult(
            checkpoint_id="rt01.outcome_resolution_checkpoint",
            source_contract="rt01.runtime_outcome",
            status=bounded_outcome_checkpoint_status,
            required_action="bounded_outcome_must_be_resolved",
            applied_action=f"{execution_stance.value}:{active_execution_mode}",
            reason="runtime contour resolved bounded outcome from enforced contracts",
        )
    )

    r_restrictions = tuple(
        dict.fromkeys(
            (
                *epistemic_allowance.restrictions,
                "epistemic_should_abstain"
                if epistemic_allowance.should_abstain
                else "epistemic_admission_allowed",
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
                "epistemic admission and regulation/affordance/preference/viability stack produced typed upstream basis"
                if r_gate_accepted
                else "epistemic and/or r-stack gate degraded; downstream continuation must be repaired"
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
        epistemic_unit_id=epistemic.unit.unit_id,
        epistemic_status=epistemic.unit.status.value,
        epistemic_confidence=epistemic.unit.confidence.value,
        epistemic_source_class=epistemic.unit.source_class.value,
        epistemic_modality=epistemic.unit.modality.value,
        epistemic_classification_basis=epistemic.unit.classification_basis,
        epistemic_can_treat_as_observation=epistemic_allowance.can_treat_as_observation,
        epistemic_should_abstain=epistemic_allowance.should_abstain,
        epistemic_claim_strength=epistemic_allowance.claim_strength,
        epistemic_allowance_restrictions=epistemic_allowance.restrictions,
        epistemic_allowance_reason=epistemic_allowance.reason,
        epistemic_unknown_reason=(
            None if epistemic.unit.unknown is None else epistemic.unit.unknown.reason
        ),
        epistemic_conflict_reason=(
            None if epistemic.unit.conflict is None else epistemic.unit.conflict.reason
        ),
        epistemic_abstain_reason=(
            None if epistemic.unit.abstention is None else epistemic.unit.abstention.reason
        ),
        c04_selected_mode=mode_arbitration.state.active_mode.value,
        c05_validity_action=c05_validity_action,
        regulation_pressure_level=viability.state.pressure_level,
        regulation_escalation_stage=viability.state.escalation_stage.value,
        regulation_override_scope=viability.state.override_scope.value,
        regulation_no_strong_override_claim=viability.state.no_strong_override_claim,
        regulation_gate_accepted=viability.downstream_gate.accepted,
        regulation_source_state_ref=viability.state.input_regulation_snapshot_ref,
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
        n_narrative_commitment_id=n_minimal_result.state.narrative_commitment_id,
        n_commitment_status=n_minimal_result.state.commitment_status.value,
        n_commitment_scope=n_minimal_result.state.commitment_scope,
        n_narrative_basis_present=n_minimal_result.state.narrative_basis_present,
        n_self_basis_present=n_minimal_result.state.self_basis_present,
        n_world_basis_present=n_minimal_result.state.world_basis_present,
        n_memory_basis_present=n_minimal_result.state.memory_basis_present,
        n_capability_basis_present=n_minimal_result.state.capability_basis_present,
        n_ambiguity_residue=n_minimal_result.state.ambiguity_residue,
        n_contradiction_risk=n_minimal_result.state.contradiction_risk.value,
        n_confidence=n_minimal_result.state.confidence,
        n_degraded=n_minimal_result.state.degraded,
        n_underconstrained=n_minimal_result.state.underconstrained,
        n_safe_narrative_commitment_allowed=(
            n_minimal_result.gate.safe_narrative_commitment_allowed
        ),
        n_bounded_commitment_allowed=n_minimal_result.gate.bounded_commitment_allowed,
        n_no_safe_narrative_claim=n_minimal_result.gate.no_safe_narrative_claim,
        n_forbidden_shortcuts=n_minimal_result.gate.forbidden_shortcuts,
        n_restrictions=n_minimal_result.gate.restrictions,
        n_n01_admission_ready=n_minimal_result.admission.admission_ready_for_n01,
        n_n01_blockers=n_minimal_result.admission.blockers,
        n_n01_implemented=n_minimal_result.admission.n01_implemented,
        n_n02_implemented=n_minimal_result.admission.n02_implemented,
        n_n03_implemented=n_minimal_result.admission.n03_implemented,
        n_n04_implemented=n_minimal_result.admission.n04_implemented,
        n_scope=n_minimal_result.scope_marker.scope,
        n_scope_rt01_contour_only=n_minimal_result.scope_marker.rt01_contour_only,
        n_scope_n_minimal_only=n_minimal_result.scope_marker.n_minimal_only,
        n_scope_readiness_gate_only=n_minimal_result.scope_marker.readiness_gate_only,
        n_scope_n01_implemented=n_minimal_result.scope_marker.n01_implemented,
        n_scope_n02_implemented=n_minimal_result.scope_marker.n02_implemented,
        n_scope_n03_implemented=n_minimal_result.scope_marker.n03_implemented,
        n_scope_n04_implemented=n_minimal_result.scope_marker.n04_implemented,
        n_scope_full_narrative_line_implemented=(
            n_minimal_result.scope_marker.full_narrative_line_implemented
        ),
        n_scope_repo_wide_adoption=n_minimal_result.scope_marker.repo_wide_adoption,
        n_scope_reason=n_minimal_result.scope_marker.reason,
        n_reason=n_minimal_result.reason,
        n_require_narrative_safe_claim=context.require_narrative_safe_claim,
        t01_scene_id=t01_result.state.scene_id,
        t01_scene_status=t01_result.state.scene_status.value,
        t01_stability_state=t01_result.state.stability_state.value,
        t01_active_entities_count=len(t01_result.state.active_entities),
        t01_relation_edges_count=len(t01_result.state.relation_edges),
        t01_role_bindings_count=len(t01_result.state.role_bindings),
        t01_unresolved_slots_count=len(t01_result.state.unresolved_slots),
        t01_contested_relations_count=sum(
            1 for edge in t01_result.state.relation_edges if edge.contested
        ),
        t01_preverbal_consumer_ready=t01_result.gate.pre_verbal_consumer_ready,
        t01_scene_comparison_ready=t01_scene_comparison_ready,
        t01_no_clean_scene_commit=t01_result.gate.no_clean_scene_commit,
        t01_forbidden_shortcuts=t01_result.gate.forbidden_shortcuts,
        t01_restrictions=t01_result.gate.restrictions,
        t01_scope=t01_result.scope_marker.scope,
        t01_scope_rt01_contour_only=t01_result.scope_marker.rt01_contour_only,
        t01_scope_t01_first_slice_only=t01_result.scope_marker.t01_first_slice_only,
        t01_scope_t02_implemented=t01_result.scope_marker.t02_implemented,
        t01_scope_t03_implemented=t01_result.scope_marker.t03_implemented,
        t01_scope_t04_implemented=t01_result.scope_marker.t04_implemented,
        t01_scope_o01_implemented=t01_result.scope_marker.o01_implemented,
        t01_scope_full_silent_thought_line_implemented=(
            t01_result.scope_marker.full_silent_thought_line_implemented
        ),
        t01_scope_repo_wide_adoption=t01_result.scope_marker.repo_wide_adoption,
        t01_scope_reason=t01_result.scope_marker.reason,
        t01_reason=t01_result.reason,
        t01_require_preverbal_scene_consumer=(
            context.require_t01_preverbal_scene_consumer
        ),
        t01_require_scene_comparison_consumer=(
            context.require_t01_scene_comparison_consumer
        ),
        s01_latest_comparison_status=(
            None
            if s01_result.state.latest_comparison_status is None
            else s01_result.state.latest_comparison_status.value
        ),
        s01_comparison_ready=s01_result.gate.comparison_ready,
        s01_unexpected_change_detected=s01_result.gate.unexpected_change_detected,
        s01_prediction_validity_ready=s01_result.gate.prediction_validity_ready,
        s01_comparison_blocked_by_contamination=(
            s01_result.state.comparison_blocked_by_contamination
        ),
        s01_stale_prediction_detected=s01_result.state.stale_prediction_detected,
        s01_pending_predictions_count=len(s01_result.state.pending_predictions),
        s01_comparisons_count=len(s01_result.state.comparisons),
        s01_require_comparison_consumer=context.require_s01_comparison_consumer,
        s01_require_unexpected_change_consumer=(
            context.require_s01_unexpected_change_consumer
        ),
        s01_require_prediction_validity_consumer=(
            context.require_s01_prediction_validity_consumer
        ),
        s02_boundary_id=s02_result.state.boundary_id,
        s02_active_boundary_status=s02_result.state.active_boundary_status.value,
        s02_boundary_uncertain=s02_result.state.boundary_uncertain,
        s02_insufficient_coverage=s02_result.state.insufficient_coverage,
        s02_no_clean_seam_claim=s02_result.state.no_clean_seam_claim,
        s02_controllability_estimate=(
            0.0
            if not s02_result.state.seam_entries
            else max(item.controllability_estimate for item in s02_result.state.seam_entries)
        ),
        s02_prediction_reliability_estimate=(
            0.0
            if not s02_result.state.seam_entries
            else max(
                item.prediction_reliability_estimate
                for item in s02_result.state.seam_entries
            )
        ),
        s02_external_dominance_estimate=(
            0.0
            if not s02_result.state.seam_entries
            else max(item.external_dominance_estimate for item in s02_result.state.seam_entries)
        ),
        s02_mixed_source_score=(
            0.0
            if not s02_result.state.seam_entries
            else max(item.mixed_source_score for item in s02_result.state.seam_entries)
        ),
        s02_boundary_confidence=(
            0.0
            if not s02_result.state.seam_entries
            else max(item.boundary_confidence for item in s02_result.state.seam_entries)
        ),
        s02_boundary_consumer_ready=s02_result.gate.boundary_consumer_ready,
        s02_controllability_consumer_ready=(
            s02_result.gate.controllability_consumer_ready
        ),
        s02_mixed_source_consumer_ready=s02_result.gate.mixed_source_consumer_ready,
        s02_forbidden_shortcuts=s02_result.gate.forbidden_shortcuts,
        s02_restrictions=s02_result.gate.restrictions,
        s02_scope=s02_result.scope_marker.scope,
        s02_scope_rt01_contour_only=s02_result.scope_marker.rt01_contour_only,
        s02_scope_s02_first_slice_only=s02_result.scope_marker.s02_first_slice_only,
        s02_scope_s03_implemented=s02_result.scope_marker.s03_implemented,
        s02_scope_s04_implemented=s02_result.scope_marker.s04_implemented,
        s02_scope_s05_implemented=s02_result.scope_marker.s05_implemented,
        s02_scope_full_self_model_implemented=(
            s02_result.scope_marker.full_self_model_implemented
        ),
        s02_scope_repo_wide_adoption=s02_result.scope_marker.repo_wide_adoption,
        s02_scope_reason=s02_result.scope_marker.reason,
        s02_reason=s02_result.reason,
        s02_require_boundary_consumer=context.require_s02_boundary_consumer,
        s02_require_controllability_consumer=(
            context.require_s02_controllability_consumer
        ),
        s02_require_mixed_source_consumer=context.require_s02_mixed_source_consumer,
        s03_learning_id=s03_result.state.learning_id,
        s03_latest_packet_id=s03_result.state.latest_packet_id,
        s03_latest_update_class=s03_result.state.latest_update_class.value,
        s03_latest_commit_class=s03_result.state.latest_commit_class.value,
        s03_latest_ambiguity_class=(
            None
            if s03_result.state.latest_ambiguity_class is None
            else s03_result.state.latest_ambiguity_class.value
        ),
        s03_freeze_or_defer_state=s03_result.state.freeze_or_defer_state.value,
        s03_requested_revalidation=s03_result.state.requested_revalidation,
        s03_self_update_weight=s03_result.state.packets[-1].self_update_weight,
        s03_world_update_weight=s03_result.state.packets[-1].world_update_weight,
        s03_observation_update_weight=s03_result.state.packets[-1].observation_update_weight,
        s03_anomaly_update_weight=s03_result.state.packets[-1].anomaly_update_weight,
        s03_learning_packet_consumer_ready=s03_result.gate.learning_packet_consumer_ready,
        s03_mixed_update_consumer_ready=s03_result.gate.mixed_update_consumer_ready,
        s03_freeze_obedience_consumer_ready=s03_result.gate.freeze_obedience_consumer_ready,
        s03_scope=s03_result.scope_marker.scope,
        s03_scope_rt01_contour_only=s03_result.scope_marker.rt01_contour_only,
        s03_scope_s03_first_slice_only=s03_result.scope_marker.s03_first_slice_only,
        s03_scope_s04_implemented=s03_result.scope_marker.s04_implemented,
        s03_scope_s05_implemented=s03_result.scope_marker.s05_implemented,
        s03_scope_repo_wide_adoption=s03_result.scope_marker.repo_wide_adoption,
        s03_scope_reason=s03_result.scope_marker.reason,
        s03_reason=s03_result.reason,
        s03_require_learning_packet_consumer=(
            context.require_s03_learning_packet_consumer
        ),
        s03_require_mixed_update_consumer=(
            context.require_s03_mixed_update_consumer
        ),
        s03_require_freeze_obedience_consumer=(
            context.require_s03_freeze_obedience_consumer
        ),
        t02_require_constrained_scene_consumer=(
            context.require_t02_constrained_scene_consumer
        ),
        t02_require_raw_vs_propagated_distinction=(
            context.require_t02_raw_vs_propagated_distinction
        ),
        t02_raw_vs_propagated_distinct=t02_raw_vs_propagated_distinct,
        t03_competition_id=t03_result.state.competition_id,
        t03_convergence_status=t03_result.state.convergence_status.value,
        t03_current_leader_hypothesis_id=t03_result.state.current_leader_hypothesis_id,
        t03_provisional_frontrunner_hypothesis_id=(
            t03_result.state.provisional_frontrunner_hypothesis_id
        ),
        t03_tied_competitor_count=len(t03_result.state.tied_competitor_ids),
        t03_blocked_hypothesis_count=len(t03_result.state.blocked_hypothesis_ids),
        t03_eliminated_hypothesis_count=len(t03_result.state.eliminated_hypothesis_ids),
        t03_reactivated_hypothesis_count=len(t03_result.state.reactivated_hypothesis_ids),
        t03_honest_nonconvergence=t03_result.state.honest_nonconvergence,
        t03_bounded_plurality=t03_result.state.bounded_plurality,
        t03_convergence_consumer_ready=t03_result.gate.convergence_consumer_ready,
        t03_frontier_consumer_ready=t03_result.gate.frontier_consumer_ready,
        t03_nonconvergence_preserved=t03_result.gate.nonconvergence_preserved,
        t03_forbidden_shortcuts=t03_result.gate.forbidden_shortcuts,
        t03_restrictions=t03_result.gate.restrictions,
        t03_publication_current_leader=t03_result.state.publication_frontier.current_leader,
        t03_publication_competitive_neighborhood=(
            t03_result.state.publication_frontier.competitive_neighborhood
        ),
        t03_publication_unresolved_conflicts=(
            t03_result.state.publication_frontier.unresolved_conflicts
        ),
        t03_publication_open_slots=t03_result.state.publication_frontier.open_slots,
        t03_publication_stability_status=(
            t03_result.state.publication_frontier.stability_status
        ),
        t03_scope=t03_result.scope_marker.scope,
        t03_scope_rt01_contour_only=t03_result.scope_marker.rt01_contour_only,
        t03_scope_t03_first_slice_only=t03_result.scope_marker.t03_first_slice_only,
        t03_scope_t04_implemented=t03_result.scope_marker.t04_implemented,
        t03_scope_o01_implemented=t03_result.scope_marker.o01_implemented,
        t03_scope_o02_implemented=t03_result.scope_marker.o02_implemented,
        t03_scope_o03_implemented=t03_result.scope_marker.o03_implemented,
        t03_scope_full_silent_thought_line_implemented=(
            t03_result.scope_marker.full_silent_thought_line_implemented
        ),
        t03_scope_repo_wide_adoption=t03_result.scope_marker.repo_wide_adoption,
        t03_scope_reason=t03_result.scope_marker.reason,
        t03_reason=t03_result.reason,
        t03_require_convergence_consumer=context.require_t03_convergence_consumer,
        t03_require_frontier_consumer=context.require_t03_frontier_consumer,
        t03_require_nonconvergence_preservation=(
            context.require_t03_nonconvergence_preservation
        ),
        t04_require_focus_ownership_consumer=(
            context.require_t04_focus_ownership_consumer
        ),
        t04_require_reportable_focus_consumer=(
            context.require_t04_reportable_focus_consumer
        ),
        t04_require_peripheral_preservation=(
            context.require_t04_peripheral_preservation
        ),
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
        o02_interaction_mode=o02_result.state.interaction_mode.value,
        o02_boundary_protection_status=o02_result.state.boundary_protection_status.value,
        o02_other_model_reliance_status=o02_result.state.other_model_reliance_status.value,
        o02_no_safe_regulation_claim=o02_result.state.no_safe_regulation_claim,
        o02_s05_shape_modulation_applied=o02_result.state.s05_shape_modulation_applied,
        o02_prior_mode_carry_applied=o02_result.state.prior_mode_carry_applied,
        o02_strong_disagreement_guard_applied=o02_result.state.strong_disagreement_guard_applied,
    )
    gate = evaluate_subject_tick_downstream_gate(state)
    telemetry = build_subject_tick_telemetry(
        state=state,
        attempted_paths=ATTEMPTED_SUBJECT_TICK_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "bounded runtime execution spine enforces roadmap authority roles for C04/C05, consumes world-entry, s01 efference-copy, s02 prediction-boundary seam, s03 ownership-weighted learning, s04 interoceptive self-binding, s05 multi-cause attribution, s-minimal, a-line, m-minimal, n-minimal, t01 semantic-field, t02 relation-binding, t03 hypothesis-competition, t04 attention-schema, o01 other-entity modeling, and o02 intersubjective allostasis gates, and keeps D01 observability-only over fixed R->C order"
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
    materialized_output = gate.accepted
    bounded_outcome_trace_values = {
        "bounded_outcome_class": execution_stance.value,
        "output_allowed": materialized_output,
        "materialization_mode": active_execution_mode,
        "bounded_reason": _bounded_outcome_reason(
            final_outcome=final_outcome,
            halt_reason=halt_reason,
            output_allowed=materialized_output,
        ),
        "outcome_ready": (
            bounded_outcome_checkpoint_status == SubjectTickCheckpointStatus.ALLOWED
            and materialized_output
        ),
    }
    trace_emit_active("bounded_outcome_resolution", "decision", bounded_outcome_trace_values)
    if (
        bounded_outcome_checkpoint_status != SubjectTickCheckpointStatus.ALLOWED
        or not materialized_output
    ):
        trace_emit_active(
            "bounded_outcome_resolution",
            "blocked",
            bounded_outcome_trace_values,
            note=str(bounded_outcome_trace_values["bounded_reason"]),
        )
    trace_emit_active("bounded_outcome_resolution", "exit", bounded_outcome_trace_values)
    output_kind = _classify_output_kind(
        final_execution_outcome=final_outcome,
        active_execution_mode=active_execution_mode,
        abstain=abstain,
        materialized_output=materialized_output,
    )
    subject_tick_trace_values = {
        "output_kind": output_kind,
        "final_execution_outcome": final_outcome,
        "active_execution_mode": active_execution_mode,
        "abstain": abstain,
        "abstain_reason": abstain_reason,
        "materialized_output": materialized_output,
    }
    trace_emit_active("subject_tick", "decision", subject_tick_trace_values)
    if final_outcome != SubjectTickOutcome.CONTINUE or not materialized_output:
        trace_emit_active(
            "subject_tick",
            "blocked",
            subject_tick_trace_values,
            note=abstain_reason or gate.reason,
        )
    trace_emit_active("subject_tick", "exit", subject_tick_trace_values)
    return SubjectTickResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        epistemic_result=epistemic,
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
        n_minimal_result=n_minimal_result,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        s04_result=s04_result,
        s05_result=s05_result,
        o01_result=o01_result,
        o02_result=o02_result,
        t01_result=t01_result,
        t02_result=t02_result,
        t03_result=t03_result,
        t04_result=t04_result,
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


def _resolve_t02_assembly_mode(token: str | None) -> T02AssemblyMode:
    if token is None:
        return T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION
    normalized = str(token).strip()
    if not normalized:
        return T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION
    try:
        return T02AssemblyMode(normalized)
    except ValueError:
        return T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION


def _resolve_t03_competition_mode(token: str | None) -> T03CompetitionMode:
    if token is None:
        return T03CompetitionMode.BOUNDED_COMPETITION
    normalized = str(token).strip()
    if not normalized:
        return T03CompetitionMode.BOUNDED_COMPETITION
    try:
        return T03CompetitionMode(normalized)
    except ValueError:
        return T03CompetitionMode.BOUNDED_COMPETITION


def _c01_stream_load(stream: object) -> int:
    state = getattr(stream, "state", None)
    return int(
        len(getattr(state, "carryover_items", ()))
        + len(getattr(state, "pending_operations", ()))
        + len(getattr(state, "unresolved_anchors", ()))
    )


def _s02_boundary_integrity(s02_result: object) -> bool:
    state = getattr(s02_result, "state", None)
    return bool(
        not getattr(state, "boundary_uncertain", True)
        and not getattr(state, "insufficient_coverage", True)
        and not getattr(state, "no_clean_seam_claim", True)
    )


def _s03_ownership_confidence(s03_result: object) -> float:
    state = getattr(s03_result, "state", None)
    packets = tuple(getattr(state, "packets", ()))
    if not packets:
        return 0.0
    latest = packets[-1]
    return float(getattr(latest, "confidence", 0.0))


def _s03_learning_weight_applied(s03_result: object) -> float:
    state = getattr(s03_result, "state", None)
    packets = tuple(getattr(state, "packets", ()))
    if not packets:
        return 0.0
    latest = packets[-1]
    return float(getattr(latest, "self_update_weight", 0.0))


def _c04_mode_conflict_present(mode_arbitration: object, mode_view: object) -> bool:
    state = getattr(mode_arbitration, "state", None)
    decision_raw = getattr(state, "hold_or_switch_decision", "")
    decision = str(getattr(decision_raw, "value", decision_raw))
    restriction_tokens = {
        str(getattr(code, "value", code)) for code in getattr(mode_view, "restrictions", ())
    }
    return (
        decision in {"arbitration_conflict", "no_clear_mode_winner", "insufficient_internal_basis"}
        or "arbitration_conflict_present" in restriction_tokens
        or "no_clear_mode_winner_present" in restriction_tokens
        or "insufficient_internal_basis_present" in restriction_tokens
    )


def _c04_arbitration_stable(mode_arbitration: object, mode_view: object) -> bool:
    state = getattr(mode_arbitration, "state", None)
    forced_rearbitration = bool(getattr(state, "forced_rearbitration", False))
    return (
        bool(getattr(mode_view, "gate_accepted", False))
        and not forced_rearbitration
        and not _c04_mode_conflict_present(mode_arbitration, mode_view)
    )


def _c05_revalidation_required(temporal_validity: object, c05_validity_action: str) -> bool:
    state = getattr(temporal_validity, "state", None)
    return bool(
        getattr(state, "revalidation_item_ids", ())
        or getattr(state, "selective_scope_targets", ())
        or getattr(state, "insufficient_basis_for_revalidation", False)
        or getattr(state, "selective_scope_uncertain", False)
        or c05_validity_action
        in {"run_selective_revalidation", "run_bounded_revalidation", "suspend_until_revalidation_basis"}
    )


def _bounded_outcome_reason(
    *,
    final_outcome: SubjectTickOutcome,
    halt_reason: str | None,
    output_allowed: bool,
) -> str:
    if final_outcome == SubjectTickOutcome.HALT:
        return str(halt_reason or "halt_required")
    if final_outcome == SubjectTickOutcome.REVALIDATE:
        return "revalidation_required"
    if final_outcome == SubjectTickOutcome.REPAIR:
        return "repair_required"
    if not output_allowed:
        return "downstream_gate_blocked"
    return "continue_ready"


def _top_restrictions(
    restrictions: tuple[str, ...],
    *,
    limit: int = 3,
) -> tuple[str, ...]:
    return tuple(restrictions[: max(0, limit)])


def _downstream_usability_class(status: ObedienceStatus) -> str:
    if status == ObedienceStatus.ALLOW_CONTINUE:
        return "usable_bounded"
    if status == ObedienceStatus.ALLOW_CONTINUE_WITH_RESTRICTION:
        return "degraded_bounded"
    return "blocked"


def _classify_output_kind(
    *,
    final_execution_outcome: SubjectTickOutcome,
    active_execution_mode: str,
    abstain: bool,
    materialized_output: bool,
) -> str:
    if abstain:
        return "abstention_output"
    if not materialized_output or final_execution_outcome == SubjectTickOutcome.HALT:
        return "no_material_output"
    if active_execution_mode in {"idle", "hold_safe_idle"}:
        return "bounded_idle_continuation"
    return "contentful_output"


def _t03_nonconvergence_basis(
    *,
    convergence_status: str,
    conflict_count: int,
    open_slot_count: int,
    no_viable_leader: bool,
) -> str:
    if convergence_status != "honest_nonconvergence":
        return "converged_or_provisional"
    if conflict_count > 0:
        return "conflict"
    if open_slot_count > 0:
        return "open_slot_incompleteness"
    if no_viable_leader:
        return "no_admissible_leader"
    return "nonconvergence_unspecified"


def _classify_s05_shape_profile(
    *,
    downstream_route_class: S05DownstreamRouteClass,
    internal_present: bool,
    external_present: bool,
) -> str:
    if (
        downstream_route_class is S05DownstreamRouteClass.MIXED_FACTORIZED
        and internal_present
        and external_present
    ):
        return "mixed_internal_external"
    if downstream_route_class in {
        S05DownstreamRouteClass.WORLD_HEAVY,
        S05DownstreamRouteClass.OBSERVATION_ARTIFACT_HEAVY,
    }:
        return "world_or_artifact_heavy"
    if downstream_route_class in {
        S05DownstreamRouteClass.SELF_ACT_HEAVY,
        S05DownstreamRouteClass.MODE_DRIFT_HEAVY,
        S05DownstreamRouteClass.INTEROCEPTIVE_DRIFT_HEAVY,
    }:
        return "internal_multi_cause"
    if downstream_route_class is S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED:
        return "high_residual_underdetermined"
    return "other"


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


def _resolve_epistemic_source_class(token: str | None) -> SourceClass:
    normalized = str(token or "").strip()
    if not normalized:
        return SourceClass.REPORTER
    try:
        return SourceClass(normalized)
    except ValueError:
        return SourceClass.UNKNOWN


def _resolve_epistemic_modality_class(token: str | None) -> ModalityClass:
    normalized = str(token or "").strip()
    if not normalized:
        return ModalityClass.USER_TEXT
    try:
        return ModalityClass(normalized)
    except ValueError:
        return ModalityClass.UNSPECIFIED


def _resolve_epistemic_confidence_level(token: str | None) -> ConfidenceLevel | None:
    normalized = str(token or "").strip()
    if not normalized:
        return None
    try:
        return ConfidenceLevel(normalized)
    except ValueError:
        return None


def _resolve_epistemic_claim_polarity(token: str | None) -> ClaimPolarity:
    normalized = str(token or "").strip()
    if not normalized:
        return ClaimPolarity.UNSPECIFIED
    try:
        return ClaimPolarity(normalized)
    except ValueError:
        return ClaimPolarity.UNSPECIFIED


def _coerce_epistemic_units(units: tuple[EpistemicUnit, ...]) -> tuple[EpistemicUnit, ...]:
    return tuple(unit for unit in units if isinstance(unit, EpistemicUnit))


def _union_unique(*chunks: Iterable[str]) -> tuple[str, ...]:
    acc: list[str] = []
    for chunk in chunks:
        for item in chunk:
            token = str(item or "").strip()
            if token and token not in acc:
                acc.append(token)
    return tuple(acc)
