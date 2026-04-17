from __future__ import annotations

from substrate.o01_other_entity_model import O01OtherEntityModelResult
from substrate.o02_intersubjective_allostasis.models import (
    O02BoundaryProtectionStatus,
    O02BudgetBand,
    O02IntersubjectiveAllostasisGateDecision,
    O02IntersubjectiveAllostasisResult,
    O02IntersubjectiveAllostasisState,
    O02InteractionDiagnosticsInput,
    O02InteractionMode,
    O02OtherModelRelianceStatus,
    O02PredictedLoadBand,
    O02RegulationLeverPreference,
    O02RepairPressureBand,
    O02ScopeMarker,
    O02Telemetry,
)
from substrate.s05_multi_cause_attribution_factorization import S05MultiCauseAttributionResult


def build_o02_intersubjective_allostasis(
    *,
    tick_id: str,
    tick_index: int,
    o01_result: O01OtherEntityModelResult,
    s05_result: S05MultiCauseAttributionResult,
    c04_selected_mode: str,
    c05_revalidation_required: bool,
    regulation_pressure_level: float,
    interaction_diagnostics: O02InteractionDiagnosticsInput | None = None,
    prior_state: O02IntersubjectiveAllostasisState | None = None,
    source_lineage: tuple[str, ...] = (),
    allostasis_enabled: bool = True,
) -> O02IntersubjectiveAllostasisResult:
    if not allostasis_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )
    if not isinstance(o01_result, O01OtherEntityModelResult):
        raise TypeError("o01_result must be O01OtherEntityModelResult")
    if not isinstance(s05_result, S05MultiCauseAttributionResult):
        raise TypeError("s05_result must be S05MultiCauseAttributionResult")

    diagnostics = interaction_diagnostics or O02InteractionDiagnosticsInput()
    o01_state = o01_result.state
    o01_gate = o01_result.gate

    other_underconstrained = bool(
        o01_state.no_safe_state_claim
        or o01_state.entity_not_individuated
        or o01_state.perspective_underconstrained
        or o01_state.knowledge_boundary_unknown
        or bool(o01_state.competing_entity_models)
    )
    belief_uncertainty = _current_user_belief_uncertainty(o01_result)
    repair_score = (
        diagnostics.recent_corrections_count
        + diagnostics.recent_misunderstanding_count
        + diagnostics.clarification_failures
        + diagnostics.repetition_request_count
    )
    repair_pressure = _repair_band(repair_score)
    predicted_other_load = _other_load_band(
        repair_score=repair_score,
        other_underconstrained=other_underconstrained,
        belief_uncertainty=belief_uncertainty,
        precision_request=diagnostics.precision_request,
    )
    predicted_self_load = _self_load_band(
        regulation_pressure_level=regulation_pressure_level,
        self_side_caution_required=diagnostics.self_side_caution_required,
    )
    self_other_constraint_conflict = bool(
        diagnostics.self_side_caution_required and diagnostics.impatience_or_compression_request
    )
    interaction_mode = _select_interaction_mode(
        repair_pressure=repair_pressure,
        other_underconstrained=other_underconstrained,
        self_other_constraint_conflict=self_other_constraint_conflict,
        precision_request=diagnostics.precision_request,
        impatience_or_compression_request=diagnostics.impatience_or_compression_request,
        c05_revalidation_required=c05_revalidation_required,
    )
    detail_budget, pace_budget = _mode_budgets(interaction_mode)
    clarification_threshold = _clarification_threshold(interaction_mode, repair_pressure)
    initiative_posture = _initiative_posture(interaction_mode)
    uncertainty_notice_policy = (
        "preserve_explicit_uncertainty"
        if (
            other_underconstrained
            or c05_revalidation_required
            or diagnostics.self_side_caution_required
        )
        else "bounded_directness"
    )
    other_model_reliance_status = (
        O02OtherModelRelianceStatus.UNDERCONSTRAINED
        if other_underconstrained
        else O02OtherModelRelianceStatus.GROUNDED
        if o01_gate.current_user_model_ready
        else O02OtherModelRelianceStatus.BOUNDED_UNCERTAIN
    )
    no_safe_regulation_claim = bool(
        other_underconstrained
        and repair_pressure is O02RepairPressureBand.LOW
        and not diagnostics.precision_request
    )
    boundary_protection_status = (
        O02BoundaryProtectionStatus.CONFLICTED
        if self_other_constraint_conflict
        else O02BoundaryProtectionStatus.PRESERVED
        if diagnostics.self_side_caution_required
        else O02BoundaryProtectionStatus.NOT_REQUIRED
    )
    levers = _select_levers(
        mode=interaction_mode,
        repair_pressure=repair_pressure,
        diagnostics=diagnostics,
        self_other_constraint_conflict=self_other_constraint_conflict,
        uncertainty_notice_policy=uncertainty_notice_policy,
    )

    justification_links = tuple(
        dict.fromkeys(
            (
                f"o01:{o01_result.state.model_id}",
                f"s05:{s05_result.state.factorization_id}",
                f"c04_mode:{c04_selected_mode}",
                f"c05_revalidation:{str(c05_revalidation_required).lower()}",
                f"repair_score:{repair_score}",
            )
        )
    )
    source_lineage_full = tuple(
        dict.fromkeys(
            (
                *source_lineage,
                *o01_result.state.source_lineage,
                *s05_result.state.source_lineage,
            )
        )
    )
    state = O02IntersubjectiveAllostasisState(
        regulation_id=f"o02-regulation:{tick_id}",
        tick_index=tick_index,
        interaction_mode=interaction_mode,
        predicted_other_load=predicted_other_load,
        predicted_self_load=predicted_self_load,
        repair_pressure=repair_pressure,
        detail_budget=detail_budget,
        pace_budget=pace_budget,
        clarification_threshold=clarification_threshold,
        initiative_posture=initiative_posture,
        uncertainty_notice_policy=uncertainty_notice_policy,
        boundary_protection_status=boundary_protection_status,
        other_model_reliance_status=other_model_reliance_status,
        lever_preferences=levers,
        justification_links=justification_links,
        no_safe_regulation_claim=no_safe_regulation_claim,
        other_load_underconstrained=other_underconstrained,
        self_other_constraint_conflict=self_other_constraint_conflict,
        source_lineage=source_lineage_full,
        last_update_provenance="o02.intersubjective_allostasis.policy",
    )
    gate = _build_gate(state)
    scope_marker = O02ScopeMarker(
        scope="rt01_hosted_o02_first_slice",
        rt01_hosted_only=True,
        o02_first_slice_only=True,
        o03_not_implemented=True,
        repo_wide_adoption=False,
        reason="first bounded o02 slice; social strategy line remains out-of-scope",
    )
    telemetry = O02Telemetry(
        regulation_id=state.regulation_id,
        tick_index=tick_index,
        interaction_mode=state.interaction_mode,
        predicted_other_load=state.predicted_other_load,
        predicted_self_load=state.predicted_self_load,
        repair_pressure=state.repair_pressure,
        detail_budget=state.detail_budget,
        pace_budget=state.pace_budget,
        boundary_protection_status=state.boundary_protection_status,
        other_model_reliance_status=state.other_model_reliance_status,
        no_safe_regulation_claim=state.no_safe_regulation_claim,
        downstream_consumer_ready=gate.downstream_consumer_ready,
    )
    reason = (
        "o02 produced bounded intersubjective regulation posture from o01 quality, self-side caution and repair diagnostics"
    )
    if prior_state is not None and _prior_repair_lineage_relevant(prior_state=prior_state, state=state):
        reason = (
            f"{reason}; prior repair posture persisted under continued repair pressure"
        )
    return O02IntersubjectiveAllostasisResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> O02IntersubjectiveAllostasisResult:
    state = O02IntersubjectiveAllostasisState(
        regulation_id=f"o02-regulation:{tick_id}",
        tick_index=tick_index,
        interaction_mode=O02InteractionMode.CONSERVATIVE_MODE_ONLY,
        predicted_other_load=O02PredictedLoadBand.HIGH,
        predicted_self_load=O02PredictedLoadBand.MEDIUM,
        repair_pressure=O02RepairPressureBand.MEDIUM,
        detail_budget=O02BudgetBand.NARROW,
        pace_budget=O02BudgetBand.NARROW,
        clarification_threshold=0.78,
        initiative_posture="clarify_before_commit",
        uncertainty_notice_policy="preserve_explicit_uncertainty",
        boundary_protection_status=O02BoundaryProtectionStatus.PRESERVED,
        other_model_reliance_status=O02OtherModelRelianceStatus.UNDERCONSTRAINED,
        lever_preferences=(
            O02RegulationLeverPreference.ASK_TARGETED_CHECK,
            O02RegulationLeverPreference.PRESERVE_EXPLICIT_UNCERTAINTY,
            O02RegulationLeverPreference.PRESERVE_BOUNDARY,
        ),
        justification_links=("o02_disabled",),
        no_safe_regulation_claim=True,
        other_load_underconstrained=True,
        self_other_constraint_conflict=False,
        source_lineage=source_lineage,
        last_update_provenance="o02.intersubjective_allostasis.disabled",
    )
    gate = O02IntersubjectiveAllostasisGateDecision(
        repair_sensitive_consumer_ready=False,
        boundary_preserving_consumer_ready=False,
        clarification_ready=False,
        downstream_consumer_ready=False,
        restrictions=(
            "o02_disabled",
            "other_load_underconstrained",
            "no_safe_regulation_claim",
        ),
        reason="o02 intersubjective allostasis disabled in ablation context",
    )
    scope_marker = O02ScopeMarker(
        scope="rt01_hosted_o02_first_slice",
        rt01_hosted_only=True,
        o02_first_slice_only=True,
        o03_not_implemented=True,
        repo_wide_adoption=False,
        reason="o02 disabled path",
    )
    telemetry = O02Telemetry(
        regulation_id=state.regulation_id,
        tick_index=tick_index,
        interaction_mode=state.interaction_mode,
        predicted_other_load=state.predicted_other_load,
        predicted_self_load=state.predicted_self_load,
        repair_pressure=state.repair_pressure,
        detail_budget=state.detail_budget,
        pace_budget=state.pace_budget,
        boundary_protection_status=state.boundary_protection_status,
        other_model_reliance_status=state.other_model_reliance_status,
        no_safe_regulation_claim=True,
        downstream_consumer_ready=False,
    )
    return O02IntersubjectiveAllostasisResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _build_gate(
    state: O02IntersubjectiveAllostasisState,
) -> O02IntersubjectiveAllostasisGateDecision:
    clarification_ready = bool(
        not state.other_load_underconstrained
        and not state.no_safe_regulation_claim
        and state.clarification_threshold <= 0.72
    )
    repair_sensitive_ready = bool(
        state.repair_pressure in {O02RepairPressureBand.MEDIUM, O02RepairPressureBand.HIGH}
        and not state.no_safe_regulation_claim
    )
    boundary_preserving_ready = state.boundary_protection_status is not O02BoundaryProtectionStatus.CONFLICTED
    downstream_ready = bool(
        boundary_preserving_ready
        and (clarification_ready or state.interaction_mode is O02InteractionMode.CONSERVATIVE_MODE_ONLY)
    )
    restrictions: list[str] = []
    if state.other_load_underconstrained:
        restrictions.append("other_load_underconstrained")
    if state.no_safe_regulation_claim:
        restrictions.append("no_safe_regulation_claim")
    if state.self_other_constraint_conflict:
        restrictions.append("self_other_constraint_conflict")
    if state.interaction_mode is O02InteractionMode.CONSERVATIVE_MODE_ONLY:
        restrictions.append("conservative_mode_only")
    if state.interaction_mode is O02InteractionMode.REPAIR_HEAVY:
        restrictions.append("repair_heavy")
    if state.uncertainty_notice_policy == "preserve_explicit_uncertainty":
        restrictions.append("preserve_explicit_uncertainty")
    if not clarification_ready:
        restrictions.append("clarification_required")
    return O02IntersubjectiveAllostasisGateDecision(
        repair_sensitive_consumer_ready=repair_sensitive_ready,
        boundary_preserving_consumer_ready=boundary_preserving_ready,
        clarification_ready=clarification_ready,
        downstream_consumer_ready=downstream_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="o02 gate exposes bounded repair/boundary/clarification readiness",
    )


def _current_user_belief_uncertainty(result: O01OtherEntityModelResult) -> float:
    current_id = result.state.current_user_entity_id
    if not current_id:
        return 1.0
    for entity in result.state.entities:
        if entity.entity_id == current_id:
            return max(0.0, min(1.0, float(entity.belief_overlay.belief_attribution_uncertainty)))
    return 1.0


def _repair_band(repair_score: int) -> O02RepairPressureBand:
    if repair_score >= 4:
        return O02RepairPressureBand.HIGH
    if repair_score >= 2:
        return O02RepairPressureBand.MEDIUM
    return O02RepairPressureBand.LOW


def _other_load_band(
    *,
    repair_score: int,
    other_underconstrained: bool,
    belief_uncertainty: float,
    precision_request: bool,
) -> O02PredictedLoadBand:
    if other_underconstrained or repair_score >= 4 or belief_uncertainty >= 0.8:
        return O02PredictedLoadBand.HIGH
    if repair_score >= 2 or precision_request:
        return O02PredictedLoadBand.MEDIUM
    return O02PredictedLoadBand.LOW


def _self_load_band(
    *,
    regulation_pressure_level: float,
    self_side_caution_required: bool,
) -> O02PredictedLoadBand:
    pressure = max(0.0, min(1.0, float(regulation_pressure_level)))
    if pressure >= 0.72 or self_side_caution_required:
        return O02PredictedLoadBand.HIGH
    if pressure >= 0.42:
        return O02PredictedLoadBand.MEDIUM
    return O02PredictedLoadBand.LOW


def _select_interaction_mode(
    *,
    repair_pressure: O02RepairPressureBand,
    other_underconstrained: bool,
    self_other_constraint_conflict: bool,
    precision_request: bool,
    impatience_or_compression_request: bool,
    c05_revalidation_required: bool,
) -> O02InteractionMode:
    if self_other_constraint_conflict:
        return O02InteractionMode.BOUNDARY_PROTECTIVE_MODE
    if other_underconstrained:
        return O02InteractionMode.CONSERVATIVE_MODE_ONLY
    if repair_pressure is O02RepairPressureBand.HIGH:
        return O02InteractionMode.REPAIR_HEAVY
    if precision_request and not impatience_or_compression_request:
        return O02InteractionMode.HIGH_PRECISION_MODE
    if impatience_or_compression_request:
        return O02InteractionMode.COMPRESSED_TASK_MODE
    if c05_revalidation_required:
        return O02InteractionMode.CONSERVATIVE_MODE_ONLY
    return O02InteractionMode.LOW_FRICTION_MODE


def _mode_budgets(mode: O02InteractionMode) -> tuple[O02BudgetBand, O02BudgetBand]:
    if mode is O02InteractionMode.CONSERVATIVE_MODE_ONLY:
        return (O02BudgetBand.NARROW, O02BudgetBand.NARROW)
    if mode is O02InteractionMode.REPAIR_HEAVY:
        return (O02BudgetBand.BALANCED, O02BudgetBand.NARROW)
    if mode is O02InteractionMode.COMPRESSED_TASK_MODE:
        return (O02BudgetBand.NARROW, O02BudgetBand.EXPANDED)
    if mode is O02InteractionMode.HIGH_PRECISION_MODE:
        return (O02BudgetBand.EXPANDED, O02BudgetBand.NARROW)
    if mode is O02InteractionMode.BOUNDARY_PROTECTIVE_MODE:
        return (O02BudgetBand.BALANCED, O02BudgetBand.BALANCED)
    return (O02BudgetBand.BALANCED, O02BudgetBand.BALANCED)


def _clarification_threshold(
    mode: O02InteractionMode,
    repair_pressure: O02RepairPressureBand,
) -> float:
    if mode in {O02InteractionMode.CONSERVATIVE_MODE_ONLY, O02InteractionMode.BOUNDARY_PROTECTIVE_MODE}:
        return 0.82
    if mode is O02InteractionMode.REPAIR_HEAVY:
        return 0.78 if repair_pressure is O02RepairPressureBand.HIGH else 0.72
    if mode is O02InteractionMode.HIGH_PRECISION_MODE:
        return 0.68
    if mode is O02InteractionMode.COMPRESSED_TASK_MODE:
        return 0.6
    return 0.58


def _initiative_posture(mode: O02InteractionMode) -> str:
    if mode is O02InteractionMode.CONSERVATIVE_MODE_ONLY:
        return "clarify_before_commit"
    if mode is O02InteractionMode.REPAIR_HEAVY:
        return "repair_first"
    if mode is O02InteractionMode.BOUNDARY_PROTECTIVE_MODE:
        return "boundary_first"
    if mode is O02InteractionMode.HIGH_PRECISION_MODE:
        return "precision_first"
    if mode is O02InteractionMode.COMPRESSED_TASK_MODE:
        return "compressed_task_progress"
    return "balanced_progress"


def _select_levers(
    *,
    mode: O02InteractionMode,
    repair_pressure: O02RepairPressureBand,
    diagnostics: O02InteractionDiagnosticsInput,
    self_other_constraint_conflict: bool,
    uncertainty_notice_policy: str,
) -> tuple[O02RegulationLeverPreference, ...]:
    levers: list[O02RegulationLeverPreference] = []
    if mode in {O02InteractionMode.REPAIR_HEAVY, O02InteractionMode.CONSERVATIVE_MODE_ONLY}:
        levers.extend(
            (
                O02RegulationLeverPreference.SLOW_DOWN,
                O02RegulationLeverPreference.INCREASE_STRUCTURE,
                O02RegulationLeverPreference.ASK_TARGETED_CHECK,
            )
        )
    if mode is O02InteractionMode.HIGH_PRECISION_MODE:
        levers.append(O02RegulationLeverPreference.KEEP_DIRECTNESS)
    if mode is O02InteractionMode.COMPRESSED_TASK_MODE:
        levers.append(O02RegulationLeverPreference.REDUCE_DETAIL)
    if diagnostics.precision_request:
        levers.append(O02RegulationLeverPreference.INCREASE_STRUCTURE)
    if diagnostics.impatience_or_compression_request:
        levers.append(O02RegulationLeverPreference.REDUCE_DETAIL)
    if uncertainty_notice_policy == "preserve_explicit_uncertainty":
        levers.append(O02RegulationLeverPreference.PRESERVE_EXPLICIT_UNCERTAINTY)
        levers.append(O02RegulationLeverPreference.POSTPONE_STRONG_COMMIT)
    if self_other_constraint_conflict or diagnostics.self_side_caution_required:
        levers.append(O02RegulationLeverPreference.PRESERVE_BOUNDARY)
    if repair_pressure is O02RepairPressureBand.LOW and mode is O02InteractionMode.LOW_FRICTION_MODE:
        levers.append(O02RegulationLeverPreference.KEEP_DIRECTNESS)
    return tuple(dict.fromkeys(levers))


def _prior_repair_lineage_relevant(
    *,
    prior_state: O02IntersubjectiveAllostasisState,
    state: O02IntersubjectiveAllostasisState,
) -> bool:
    return bool(
        prior_state.interaction_mode is O02InteractionMode.REPAIR_HEAVY
        and state.interaction_mode in {O02InteractionMode.REPAIR_HEAVY, O02InteractionMode.CONSERVATIVE_MODE_ONLY}
        and state.repair_pressure in {O02RepairPressureBand.MEDIUM, O02RepairPressureBand.HIGH}
    )
