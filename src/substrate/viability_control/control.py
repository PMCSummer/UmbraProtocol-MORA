from __future__ import annotations

from uuid import uuid4

from substrate.affordances.models import AffordanceResult, AffordanceStatus
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.regulation.models import (
    DeviationDirection,
    NeedAxis,
    NeedState,
    RegulationConfidence,
    RegulationResult,
    RegulationState,
    TradeoffState,
)
from substrate.regulatory_preferences.models import (
    PreferenceSign,
    PreferenceState,
    PreferenceUpdateResult,
)
from substrate.transition import execute_transition
from substrate.viability_control.models import (
    ViabilityAxisBoundary,
    ViabilityBoundarySpec,
    ViabilityCalibrationSpec,
    ViabilityContext,
    ViabilityControlDirective,
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityDirectiveType,
    ViabilityEscalationStage,
    ViabilityGateDecision,
    ViabilityOverrideScope,
    ViabilityPersistenceState,
    ViabilityRecoverabilityComponents,
    ViabilityUncertaintyState,
)
from substrate.viability_control.policy import evaluate_viability_downstream_gate
from substrate.viability_control.telemetry import (
    build_viability_telemetry,
    viability_result_snapshot,
)


ATTEMPTED_VIABILITY_PATHS: tuple[str, ...] = (
    "viability.validate_typed_inputs",
    "viability.boundary_compatibility_guard",
    "viability.calibration_compatibility_guard",
    "viability.severity_computation",
    "viability.worsening_and_time_to_boundary",
    "viability.recoverability_estimation",
    "viability.escalation_stage",
    "viability.persistence_and_deescalation",
    "viability.directive_surface",
    "viability.downstream_gate",
)


def create_default_viability_boundary_spec() -> ViabilityBoundarySpec:
    boundaries = (
        ViabilityAxisBoundary(
            axis=NeedAxis.ENERGY,
            elevated_pressure=18.0,
            threat_pressure=34.0,
            critical_pressure=55.0,
            elevated_deviation=6.0,
            threat_deviation=12.0,
            critical_deviation=22.0,
            threat_unresolved_steps=5,
            critical_unresolved_steps=10,
        ),
        ViabilityAxisBoundary(
            axis=NeedAxis.COGNITIVE_LOAD,
            elevated_pressure=16.0,
            threat_pressure=30.0,
            critical_pressure=50.0,
            elevated_deviation=6.0,
            threat_deviation=12.0,
            critical_deviation=20.0,
            threat_unresolved_steps=4,
            critical_unresolved_steps=9,
        ),
        ViabilityAxisBoundary(
            axis=NeedAxis.SAFETY,
            elevated_pressure=14.0,
            threat_pressure=26.0,
            critical_pressure=42.0,
            elevated_deviation=5.0,
            threat_deviation=10.0,
            critical_deviation=16.0,
            threat_unresolved_steps=4,
            critical_unresolved_steps=8,
        ),
        ViabilityAxisBoundary(
            axis=NeedAxis.SOCIAL_CONTACT,
            elevated_pressure=18.0,
            threat_pressure=32.0,
            critical_pressure=52.0,
            elevated_deviation=7.0,
            threat_deviation=14.0,
            critical_deviation=22.0,
            threat_unresolved_steps=6,
            critical_unresolved_steps=11,
        ),
        ViabilityAxisBoundary(
            axis=NeedAxis.NOVELTY,
            elevated_pressure=18.0,
            threat_pressure=33.0,
            critical_pressure=53.0,
            elevated_deviation=7.0,
            threat_deviation=13.0,
            critical_deviation=22.0,
            threat_unresolved_steps=6,
            critical_unresolved_steps=11,
        ),
    )
    return ViabilityBoundarySpec(
        boundary_id="r04-default-boundary",
        axis_boundaries=boundaries,
        critical_time_to_boundary=1.5,
        threat_time_to_boundary=4.0,
    )


def create_default_viability_calibration_spec() -> ViabilityCalibrationSpec:
    return ViabilityCalibrationSpec(
        calibration_id="r04-default-calibration",
    )


def compute_viability_control_state(
    regulation_state_or_result: RegulationState | RegulationResult,
    affordance_result: AffordanceResult,
    preference_result_or_state: PreferenceUpdateResult | PreferenceState,
    context: ViabilityContext | None = None,
    boundary_spec: ViabilityBoundarySpec | None = None,
    calibration_spec: ViabilityCalibrationSpec | None = None,
) -> ViabilityControlResult:
    context = context or ViabilityContext()
    boundary = boundary_spec or create_default_viability_boundary_spec()
    calibration = calibration_spec or create_default_viability_calibration_spec()

    regulation_state, tradeoff_state, regulation_ref = _extract_regulation_input(
        regulation_state_or_result
    )
    preference_state, preference_result, preference_ref = _extract_preference_input(
        preference_result_or_state
    )
    if not isinstance(affordance_result, AffordanceResult):
        raise TypeError("compute_viability_control_state requires typed AffordanceResult")
    if not isinstance(context, ViabilityContext):
        raise TypeError("context must be ViabilityContext")
    if not isinstance(boundary, ViabilityBoundarySpec):
        raise TypeError("boundary_spec must be ViabilityBoundarySpec")
    if not isinstance(calibration, ViabilityCalibrationSpec):
        raise TypeError("calibration_spec must be ViabilityCalibrationSpec")

    is_valid, compatibility, blocked_reasons = validate_viability_inputs(
        regulation_state=regulation_state,
        affordance_result=affordance_result,
        preference_state=preference_state,
        context=context,
        boundary=boundary,
        calibration=calibration,
    )
    if not is_valid:
        return _abstain_result(
            regulation_ref=regulation_ref,
            affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
            preference_ref=preference_ref,
            source_lineage=tuple(
                dict.fromkeys(
                    (*context.source_lineage, *affordance_result.telemetry.source_lineage)
                )
            ),
            reason="; ".join(blocked_reasons) or "invalid viability input contract",
            boundary_compatibility=compatibility,
            calibration=calibration,
        )

    boundaries_by_axis = {entry.axis: entry for entry in boundary.axis_boundaries}
    axis_risks: dict[NeedAxis, float] = {}
    affected_needs: list[NeedAxis] = []
    max_unresolved = 0
    directions: set[DeviationDirection] = set()
    for need in regulation_state.needs:
        b = boundaries_by_axis.get(need.axis)
        if b is None:
            continue
        axis_risks[need.axis] = _axis_risk(need=need, boundary=b)
        max_unresolved = max(max_unresolved, need.unresolved_steps)
        if (
            need.pressure >= b.elevated_pressure
            or need.deviation >= b.elevated_deviation
            or need.unresolved_steps >= max(1, b.threat_unresolved_steps // 2)
        ):
            affected_needs.append(need.axis)
            directions.add(need.deviation_direction)

    if not affected_needs and axis_risks:
        top_axis = max(axis_risks.items(), key=lambda item: item[1])[0]
        affected_needs = [top_axis]
        top_need = _need_by_axis(regulation_state, top_axis)
        if top_need is not None:
            directions.add(top_need.deviation_direction)

    worsening_signal = _worsening_signal(
        current_state=regulation_state,
        prior_state=context.prior_regulation_state,
        step_delta=context.step_delta,
    )
    predicted_time_to_boundary = _predicted_time_to_boundary(
        current_state=regulation_state,
        prior_state=context.prior_regulation_state,
        boundaries=boundaries_by_axis,
        step_delta=context.step_delta,
    )
    recent_failed_recovery_count = context.recent_failed_recovery_attempts
    preference_epistemic_block_count = (
        len(preference_result.blocked_updates) if preference_result is not None else 0
    )

    recoverability_estimate, recoverability_components, recoverability_notes = _recoverability_estimate(
        affordance_result=affordance_result,
        preference_state=preference_state,
        recent_failed_recovery_count=recent_failed_recovery_count,
        calibration=calibration,
    )

    pressure_level = _pressure_level(
        axis_risks=axis_risks,
        worsening_signal=worsening_signal,
        max_unresolved=max_unresolved,
        predicted_time_to_boundary=predicted_time_to_boundary,
        recent_failed_recovery_count=recent_failed_recovery_count,
        calibration=calibration,
        boundary=boundary,
    )
    clean_threat_attribution_basis = _clean_threat_attribution_basis(
        axis_risks=axis_risks,
        predicted_time_to_boundary=predicted_time_to_boundary,
        regulation_confidence=regulation_state.confidence,
        tradeoff_state=tradeoff_state,
        boundary=boundary,
        calibration=calibration,
    )
    escalation_stage = _escalation_stage(
        pressure_level=pressure_level,
        predicted_time_to_boundary=predicted_time_to_boundary,
        boundary=boundary,
        calibration=calibration,
    )
    incompatibility_markers_for_prior_reuse = {
        "calibration_schema_incompatible",
        "calibration_id_incompatible",
        "calibration_formula_incompatible",
        "prior_viability_calibration_mismatch",
        "prior_viability_formula_mismatch",
    }
    prior_viability_state_for_persistence = context.prior_viability_state
    if set(compatibility) & incompatibility_markers_for_prior_reuse:
        prior_viability_state_for_persistence = None
        blocked_reasons += ("prior_viability_state_incompatible_for_reuse",)
    persistence_state, deescalation_conditions = _persistence_and_deescalation(
        escalation_stage=escalation_stage,
        pressure_level=pressure_level,
        max_unresolved=max_unresolved,
        recent_failed_recovery_count=recent_failed_recovery_count,
        prior_viability_state=prior_viability_state_for_persistence,
    )

    mixed_deterioration = len(affected_needs) >= 2 and len(directions) > 1
    uncertainty: list[ViabilityUncertaintyState] = []
    if regulation_state.confidence == RegulationConfidence.LOW or regulation_state.abstention is not None:
        uncertainty.append(ViabilityUncertaintyState.INSUFFICIENT_OBSERVABILITY)
    if mixed_deterioration:
        uncertainty.append(ViabilityUncertaintyState.MIXED_DETERIORATION)
    if tradeoff_state is not None and len(tradeoff_state.competing_pairs) >= 1:
        uncertainty.append(ViabilityUncertaintyState.UNRESOLVED_CONFLICT)
    if predicted_time_to_boundary is None and escalation_stage in {
        ViabilityEscalationStage.THREAT,
        ViabilityEscalationStage.CRITICAL,
    }:
        uncertainty.append(ViabilityUncertaintyState.BOUNDARY_UNCERTAIN)
    if recoverability_estimate is None:
        uncertainty.append(ViabilityUncertaintyState.DEGRADED_MODE_ONLY)
    if (
        recoverability_components is not None
        and recoverability_components.evidence_quality
        < calibration.strong_override_min_recoverability_evidence
    ):
        uncertainty.append(ViabilityUncertaintyState.DEGRADED_MODE_ONLY)

    no_strong_override_claim = bool(
        context.require_strong_override and regulation_state.confidence != RegulationConfidence.HIGH
    ) or bool(
        set(uncertainty)
        & {
            ViabilityUncertaintyState.INSUFFICIENT_OBSERVABILITY,
            ViabilityUncertaintyState.BOUNDARY_UNCERTAIN,
            ViabilityUncertaintyState.UNRESOLVED_CONFLICT,
            ViabilityUncertaintyState.DEGRADED_MODE_ONLY,
        }
    ) or bool(compatibility)
    if (
        mixed_deterioration
        and calibration.mixed_deterioration_requires_cap
        and not clean_threat_attribution_basis
    ):
        no_strong_override_claim = True
    if (
        preference_epistemic_block_count >= calibration.epistemic_block_override_cap_threshold
        and not clean_threat_attribution_basis
    ):
        no_strong_override_claim = True
    if no_strong_override_claim:
        uncertainty.append(ViabilityUncertaintyState.NO_STRONG_OVERRIDE_CLAIM)

    confidence = regulation_state.confidence
    if compatibility or regulation_state.partial_known is not None:
        confidence = min(confidence, RegulationConfidence.MEDIUM, key=_confidence_rank)
    if no_strong_override_claim:
        confidence = min(confidence, RegulationConfidence.MEDIUM, key=_confidence_rank)

    override_scope = _override_scope(
        escalation_stage=escalation_stage,
        no_strong_override_claim=no_strong_override_claim,
        recoverability_estimate=recoverability_estimate,
    )
    directives = _build_directives(
        escalation_stage=escalation_stage,
        pressure_level=pressure_level,
        affected_need_ids=tuple(dict.fromkeys(affected_needs)),
        override_scope=override_scope,
        no_strong_override_claim=no_strong_override_claim,
        recoverability_estimate=recoverability_estimate,
        persistence_state=persistence_state,
    )

    state = ViabilityControlState(
        pressure_level=pressure_level,
        escalation_stage=escalation_stage,
        affected_need_ids=tuple(dict.fromkeys(affected_needs)),
        predicted_time_to_boundary=predicted_time_to_boundary,
        recoverability_estimate=recoverability_estimate,
        recoverability_components=recoverability_components,
        calibration_id=calibration.calibration_id,
        calibration_schema_version=calibration.schema_version,
        calibration_formula_version=calibration.formula_version,
        override_scope=override_scope,
        persistence_state=persistence_state,
        deescalation_conditions=deescalation_conditions,
        confidence=confidence,
        uncertainty_state=tuple(dict.fromkeys(uncertainty)),
        recent_failed_recovery_count=recent_failed_recovery_count,
        preference_epistemic_block_count=preference_epistemic_block_count,
        mixed_deterioration=mixed_deterioration,
        no_strong_override_claim=no_strong_override_claim,
        input_regulation_snapshot_ref=regulation_ref,
        input_affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
        input_preference_ref=preference_ref,
        provenance="r04.viability_control_from_r01_r02_r03",
    )
    provisional = ViabilityControlResult(
        state=state,
        directives=directives,
        downstream_gate=ViabilityGateDecision(
            accepted=False,
            restrictions=(),
            reason="placeholder",
            accepted_directive_ids=(),
            rejected_directive_ids=(),
            state_ref=None,
        ),
        telemetry=build_viability_telemetry(
            state=state,
            directives=directives,
            source_lineage=tuple(
                dict.fromkeys(
                    (*context.source_lineage, *affordance_result.telemetry.source_lineage)
                )
            ),
            blocked_reasons=tuple(dict.fromkeys((*blocked_reasons, *recoverability_notes))),
            boundary_compatibility=compatibility,
            calibration=calibration,
            downstream_gate=ViabilityGateDecision(
                accepted=False,
                restrictions=(),
                reason="placeholder",
                accepted_directive_ids=(),
                rejected_directive_ids=(),
                state_ref=None,
            ),
            causal_basis="placeholder",
            attempted_computation_paths=ATTEMPTED_VIABILITY_PATHS,
        ),
        abstain=False,
        abstain_reason=None,
        no_action_selection_performed=True,
    )
    gate = evaluate_viability_downstream_gate(provisional)
    telemetry = build_viability_telemetry(
        state=state,
        directives=directives,
        source_lineage=tuple(
            dict.fromkeys((*context.source_lineage, *affordance_result.telemetry.source_lineage))
        ),
        blocked_reasons=tuple(dict.fromkeys((*blocked_reasons, *recoverability_notes))),
        boundary_compatibility=compatibility,
        calibration=calibration,
        downstream_gate=gate,
        causal_basis=(
            "R01 boundary severity + worsening + persistence, constrained by R02 means and R03 recoverability hints"
        ),
        attempted_computation_paths=ATTEMPTED_VIABILITY_PATHS,
    )
    return ViabilityControlResult(
        state=state,
        directives=directives,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=False,
        abstain_reason=None,
        no_action_selection_performed=True,
    )


def validate_viability_inputs(
    *,
    regulation_state: RegulationState,
    affordance_result: AffordanceResult,
    preference_state: PreferenceState,
    context: ViabilityContext,
    boundary: ViabilityBoundarySpec,
    calibration: ViabilityCalibrationSpec,
) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    compatibility: list[str] = []
    blocked: list[str] = []
    if not regulation_state.needs:
        blocked.append("regulation_state has no tracked need axes")
    if context.step_delta < 1:
        blocked.append("context.step_delta must be >= 1")
    boundary_axes = {entry.axis for entry in boundary.axis_boundaries}
    state_axes = {need.axis for need in regulation_state.needs}
    if not state_axes.issubset(boundary_axes):
        blocked.append("boundary spec missing regulation axes")
    for entry in boundary.axis_boundaries:
        if (
            entry.elevated_pressure >= entry.threat_pressure
            or entry.threat_pressure >= entry.critical_pressure
            or entry.elevated_deviation >= entry.threat_deviation
            or entry.threat_deviation >= entry.critical_deviation
        ):
            blocked.append(f"invalid monotonic boundary thresholds for axis {entry.axis.value}")
        if entry.threat_unresolved_steps >= entry.critical_unresolved_steps:
            blocked.append(f"invalid unresolved step thresholds for axis {entry.axis.value}")

    if preference_state.schema_version != context.expected_preference_schema_version:
        compatibility.append("preference_schema_incompatible")
    if preference_state.taxonomy_version != context.expected_taxonomy_version:
        compatibility.append("taxonomy_version_incompatible")
    if preference_state.measurement_version != context.expected_measurement_version:
        compatibility.append("measurement_version_incompatible")
    if boundary.schema_version != context.expected_boundary_schema_version:
        compatibility.append("boundary_schema_incompatible")
    if boundary.taxonomy_version != context.expected_taxonomy_version:
        compatibility.append("boundary_taxonomy_incompatible")
    if boundary.measurement_version != context.expected_measurement_version:
        compatibility.append("boundary_measurement_incompatible")
    if calibration.schema_version != context.expected_calibration_schema_version:
        compatibility.append("calibration_schema_incompatible")
    if (
        context.expected_calibration_id is not None
        and calibration.calibration_id != context.expected_calibration_id
    ):
        compatibility.append("calibration_id_incompatible")
    if calibration.pressure_elevated_threshold >= calibration.pressure_threat_threshold:
        blocked.append("invalid calibration pressure thresholds (elevated>=threat)")
    if calibration.pressure_threat_threshold >= calibration.pressure_critical_threshold:
        blocked.append("invalid calibration pressure thresholds (threat>=critical)")
    if calibration.worsening_normalizer <= 0:
        blocked.append("invalid calibration worsening_normalizer")
    if calibration.persistence_normalizer_steps <= 0:
        blocked.append("invalid calibration persistence_normalizer_steps")
    if calibration.failed_recovery_step_penalty < 0:
        blocked.append("invalid calibration failed_recovery_step_penalty")
    if calibration.min_recoverability_evidence_quality < 0 or calibration.min_recoverability_evidence_quality > 1:
        blocked.append("invalid calibration min_recoverability_evidence_quality")
    if (
        calibration.strong_override_min_recoverability_evidence < 0
        or calibration.strong_override_min_recoverability_evidence > 1
    ):
        blocked.append("invalid calibration strong_override_min_recoverability_evidence")
    if (
        calibration.mixed_deterioration_dominance_margin < 0
        or calibration.mixed_deterioration_dominance_margin > 1
    ):
        blocked.append("invalid calibration mixed_deterioration_dominance_margin")
    if calibration.epistemic_block_override_cap_threshold < 0:
        blocked.append("invalid calibration epistemic_block_override_cap_threshold")
    if calibration.formula_version != context.expected_calibration_formula_version:
        compatibility.append("calibration_formula_incompatible")
    if (
        context.prior_viability_state is not None
        and context.prior_viability_state.calibration_id != calibration.calibration_id
    ):
        compatibility.append("prior_viability_calibration_mismatch")
    if (
        context.prior_viability_state is not None
        and context.prior_viability_state.calibration_formula_version
        != calibration.formula_version
    ):
        compatibility.append("prior_viability_formula_mismatch")
    _ = affordance_result
    return len(blocked) == 0, tuple(dict.fromkeys(compatibility)), tuple(dict.fromkeys(blocked))


def viability_result_to_payload(result: ViabilityControlResult) -> dict[str, object]:
    return viability_result_snapshot(result)


def persist_viability_control_result_via_f01(
    *,
    result: ViabilityControlResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("r04-viability-control",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"viability-step-{transition_id}",
            "viability_control_snapshot": viability_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_regulation_input(
    regulation_state_or_result: RegulationState | RegulationResult,
) -> tuple[RegulationState, TradeoffState | None, str]:
    if isinstance(regulation_state_or_result, RegulationResult):
        state = regulation_state_or_result.state
        return state, regulation_state_or_result.tradeoff, f"regulation-step-{state.last_updated_step}"
    if isinstance(regulation_state_or_result, RegulationState):
        return (
            regulation_state_or_result,
            None,
            f"regulation-step-{regulation_state_or_result.last_updated_step}",
        )
    raise TypeError(
        "compute_viability_control_state requires RegulationState or RegulationResult"
    )


def _extract_preference_input(
    preference_result_or_state: PreferenceUpdateResult | PreferenceState,
) -> tuple[PreferenceState, PreferenceUpdateResult | None, str]:
    if isinstance(preference_result_or_state, PreferenceUpdateResult):
        state = preference_result_or_state.updated_preference_state
        return (
            state,
            preference_result_or_state,
            f"preference-step-{state.last_updated_step}:{state.schema_version}",
        )
    if isinstance(preference_result_or_state, PreferenceState):
        return (
            preference_result_or_state,
            None,
            f"preference-step-{preference_result_or_state.last_updated_step}:{preference_result_or_state.schema_version}",
        )
    raise TypeError(
        "compute_viability_control_state requires PreferenceUpdateResult or PreferenceState"
    )


def _axis_risk(*, need: NeedState, boundary: ViabilityAxisBoundary) -> float:
    pressure_ratio = need.pressure / max(0.01, boundary.critical_pressure)
    deviation_ratio = need.deviation / max(0.01, boundary.critical_deviation)
    unresolved_ratio = need.unresolved_steps / max(1, boundary.critical_unresolved_steps)
    score = max(pressure_ratio, deviation_ratio, unresolved_ratio * 0.85)
    return max(0.0, min(1.0, round(score, 4)))


def _worsening_signal(
    *,
    current_state: RegulationState,
    prior_state: object | None,
    step_delta: int,
) -> float | None:
    if not isinstance(prior_state, RegulationState):
        return None
    prior_map = {need.axis: need for need in prior_state.needs}
    worsening_sum = 0.0
    worsening_count = 0
    for current in current_state.needs:
        prior = prior_map.get(current.axis)
        if prior is None:
            continue
        delta_pressure = current.pressure - prior.pressure
        delta_deviation = current.deviation - prior.deviation
        worsening = max(0.0, (delta_pressure * 0.6) + (delta_deviation * 0.4))
        if worsening > 0.0:
            worsening_sum += worsening
            worsening_count += 1
    if worsening_count == 0:
        return 0.0
    return round(worsening_sum / max(1, worsening_count * step_delta), 4)


def _predicted_time_to_boundary(
    *,
    current_state: RegulationState,
    prior_state: object | None,
    boundaries: dict[NeedAxis, ViabilityAxisBoundary],
    step_delta: int,
) -> float | None:
    if not isinstance(prior_state, RegulationState):
        return None
    prior_map = {need.axis: need for need in prior_state.needs}
    estimates: list[float] = []
    for need in current_state.needs:
        boundary = boundaries.get(need.axis)
        prior_need = prior_map.get(need.axis)
        if boundary is None or prior_need is None:
            continue
        if need.pressure >= boundary.critical_pressure or need.deviation >= boundary.critical_deviation:
            return 0.0
        delta_pressure = max(0.0, (need.pressure - prior_need.pressure) / max(1, step_delta))
        delta_deviation = max(0.0, (need.deviation - prior_need.deviation) / max(1, step_delta))
        rate = max(delta_pressure, delta_deviation)
        if rate <= 0.0:
            continue
        pressure_distance = max(0.0, boundary.critical_pressure - need.pressure)
        deviation_distance = max(0.0, boundary.critical_deviation - need.deviation)
        estimates.append(min(pressure_distance / rate, deviation_distance / rate))
    if not estimates:
        return None
    return round(min(estimates), 4)


def _recoverability_estimate(
    *,
    affordance_result: AffordanceResult,
    preference_state: PreferenceState,
    recent_failed_recovery_count: int,
    calibration: ViabilityCalibrationSpec,
) -> tuple[float | None, ViabilityRecoverabilityComponents | None, tuple[str, ...]]:
    candidates = affordance_result.candidates
    if not candidates:
        return None, None, ("no_affordance_candidates",)
    total = len(candidates)
    available = [candidate for candidate in candidates if candidate.status == AffordanceStatus.AVAILABLE]
    blocked = [
        candidate
        for candidate in candidates
        if candidate.status in {AffordanceStatus.BLOCKED, AffordanceStatus.UNAVAILABLE, AffordanceStatus.UNSAFE}
    ]
    if not available:
        return None, None, ("no_available_recovery_means",)
    available_ratio = len(available) / total
    restorative_capacity = sum(
        candidate.expected_effect.effect_strength_estimate for candidate in available
    ) / max(1, len(available))
    by_option = {entry.option_class_id: entry for entry in preference_state.entries}
    positive = 0
    negative = 0
    matched = 0
    for candidate in available:
        entry = by_option.get(candidate.option_class)
        if entry is None:
            continue
        matched += 1
        if entry.preference_sign == PreferenceSign.POSITIVE and entry.confidence != RegulationConfidence.LOW:
            positive += 1
        elif entry.preference_sign == PreferenceSign.NEGATIVE:
            negative += 1
    preference_ratio = (positive - negative) / max(1, len(available))
    preference_coverage = matched / max(1, len(available))
    affordance_confidence_quality = sum(
        _confidence_rank(candidate.confidence) for candidate in available
    ) / max(1, len(available) * 3)
    evidence_quality = max(
        0.0,
        min(
            1.0,
            round((0.65 * affordance_confidence_quality) + (0.35 * preference_coverage), 4),
        ),
    )
    blocked_ratio = len(blocked) / total
    failed_penalty = max(0.0, min(1.0, round(recent_failed_recovery_count * 0.2, 4)))
    components = ViabilityRecoverabilityComponents(
        viable_affordance_coverage=round(available_ratio, 4),
        restorative_capacity_evidence=round(max(0.0, min(1.0, restorative_capacity)), 4),
        blocked_or_unavailable_fraction=round(blocked_ratio, 4),
        preference_support_bias=round(preference_ratio, 4),
        evidence_quality=evidence_quality,
        recent_failed_restoration_penalty=failed_penalty,
    )
    if evidence_quality < calibration.min_recoverability_evidence_quality:
        return None, components, ("weak_recoverability_basis",)
    estimate = (
        0.15
        + (0.35 * components.viable_affordance_coverage)
        + (0.3 * components.restorative_capacity_evidence)
        + (0.08 * components.preference_support_bias)
        + (0.2 * components.evidence_quality)
        - (0.25 * components.blocked_or_unavailable_fraction)
        - (0.2 * components.recent_failed_restoration_penalty)
    )
    return max(0.0, min(1.0, round(estimate, 4))), components, ()


def _pressure_level(
    *,
    axis_risks: dict[NeedAxis, float],
    worsening_signal: float | None,
    max_unresolved: int,
    predicted_time_to_boundary: float | None,
    recent_failed_recovery_count: int,
    calibration: ViabilityCalibrationSpec,
    boundary: ViabilityBoundarySpec,
) -> float:
    base = (max(axis_risks.values()) if axis_risks else 0.0) * calibration.base_weight
    worsening_component = 0.0
    if worsening_signal is not None:
        worsening_component = min(
            calibration.max_worsening_component,
            (worsening_signal / calibration.worsening_normalizer) * calibration.worsening_weight,
        )
    persistence_component = min(
        calibration.max_persistence_component,
        (max_unresolved / calibration.persistence_normalizer_steps) * calibration.persistence_weight,
    )
    failed_component = min(
        calibration.max_failed_component,
        (recent_failed_recovery_count * calibration.failed_recovery_step_penalty)
        * calibration.failed_recovery_weight,
    )
    time_component = 0.0
    if predicted_time_to_boundary is not None:
        if predicted_time_to_boundary <= boundary.critical_time_to_boundary:
            time_component = calibration.time_to_boundary_critical_boost
        elif predicted_time_to_boundary <= boundary.threat_time_to_boundary:
            time_component = calibration.time_to_boundary_threat_boost
    total = base + worsening_component + persistence_component + failed_component + time_component
    return max(0.0, min(1.0, round(total, 4)))


def _escalation_stage(
    *,
    pressure_level: float,
    predicted_time_to_boundary: float | None,
    boundary: ViabilityBoundarySpec,
    calibration: ViabilityCalibrationSpec,
) -> ViabilityEscalationStage:
    if pressure_level >= calibration.pressure_critical_threshold:
        return ViabilityEscalationStage.CRITICAL
    if predicted_time_to_boundary is not None and predicted_time_to_boundary <= boundary.critical_time_to_boundary:
        return ViabilityEscalationStage.CRITICAL
    if pressure_level >= calibration.pressure_threat_threshold:
        return ViabilityEscalationStage.THREAT
    if predicted_time_to_boundary is not None and predicted_time_to_boundary <= boundary.threat_time_to_boundary:
        return ViabilityEscalationStage.THREAT
    if pressure_level >= calibration.pressure_elevated_threshold:
        return ViabilityEscalationStage.ELEVATED
    return ViabilityEscalationStage.BASELINE


def _clean_threat_attribution_basis(
    *,
    axis_risks: dict[NeedAxis, float],
    predicted_time_to_boundary: float | None,
    regulation_confidence: RegulationConfidence,
    tradeoff_state: TradeoffState | None,
    boundary: ViabilityBoundarySpec,
    calibration: ViabilityCalibrationSpec,
) -> bool:
    if not axis_risks:
        return False
    sorted_risks = sorted(axis_risks.values(), reverse=True)
    top = sorted_risks[0]
    second = sorted_risks[1] if len(sorted_risks) > 1 else 0.0
    dominance = top - second
    has_dominant_axis = dominance >= calibration.mixed_deterioration_dominance_margin
    urgent_boundary = (
        predicted_time_to_boundary is not None
        and predicted_time_to_boundary <= boundary.threat_time_to_boundary
    )
    no_tradeoff_conflict = tradeoff_state is None or len(tradeoff_state.competing_pairs) == 0
    return (
        has_dominant_axis
        and urgent_boundary
        and regulation_confidence == RegulationConfidence.HIGH
        and no_tradeoff_conflict
    )


def _persistence_and_deescalation(
    *,
    escalation_stage: ViabilityEscalationStage,
    pressure_level: float,
    max_unresolved: int,
    recent_failed_recovery_count: int,
    prior_viability_state: ViabilityControlState | None,
) -> tuple[ViabilityPersistenceState, tuple[str, ...]]:
    if escalation_stage == ViabilityEscalationStage.BASELINE:
        if prior_viability_state is not None and _stage_rank(prior_viability_state.escalation_stage) > _stage_rank(escalation_stage):
            return (
                ViabilityPersistenceState.RECOVERING,
                (
                    "sustain_pressure_below_elevated_for_2_steps",
                    "maintain_no_new_worsening_signal",
                ),
            )
        return ViabilityPersistenceState.STABLE, ("keep_within_viability_boundaries",)
    if max_unresolved >= 10 or recent_failed_recovery_count >= 3:
        persistence = ViabilityPersistenceState.CHRONIC
    elif max_unresolved >= 6:
        persistence = ViabilityPersistenceState.PERSISTENT
    else:
        persistence = ViabilityPersistenceState.EMERGING
    conditions = [
        "reduce_pressure_below_elevated_thresholds",
        "clear_recent_failed_recovery_attempt_pattern",
    ]
    if pressure_level >= 0.65:
        conditions.append("increase_time_to_boundary_above_threat_window")
    return persistence, tuple(conditions)


def _override_scope(
    *,
    escalation_stage: ViabilityEscalationStage,
    no_strong_override_claim: bool,
    recoverability_estimate: float | None,
) -> ViabilityOverrideScope:
    if escalation_stage == ViabilityEscalationStage.BASELINE:
        return ViabilityOverrideScope.NONE
    if no_strong_override_claim:
        return (
            ViabilityOverrideScope.NARROW
            if escalation_stage == ViabilityEscalationStage.ELEVATED
            else ViabilityOverrideScope.FOCUSED
        )
    if escalation_stage == ViabilityEscalationStage.ELEVATED:
        return ViabilityOverrideScope.NARROW
    if escalation_stage == ViabilityEscalationStage.THREAT:
        return ViabilityOverrideScope.FOCUSED
    if recoverability_estimate is not None and recoverability_estimate < 0.3:
        return ViabilityOverrideScope.EMERGENCY
    return ViabilityOverrideScope.BROAD


def _build_directives(
    *,
    escalation_stage: ViabilityEscalationStage,
    pressure_level: float,
    affected_need_ids: tuple[NeedAxis, ...],
    override_scope: ViabilityOverrideScope,
    no_strong_override_claim: bool,
    recoverability_estimate: float | None,
    persistence_state: ViabilityPersistenceState,
) -> tuple[ViabilityControlDirective, ...]:
    directives: list[ViabilityControlDirective] = []
    if escalation_stage == ViabilityEscalationStage.BASELINE:
        if persistence_state == ViabilityPersistenceState.RECOVERING:
            directives.append(
                _directive(
                    directive_type=ViabilityDirectiveType.FOCUS_RETENTION,
                    intensity=0.25,
                    affected_need_ids=affected_need_ids,
                    override_scope=ViabilityOverrideScope.NARROW,
                    reason="recovery phase retains minimal focus without broad restrictions",
                    no_strong_override_claim=no_strong_override_claim,
                )
            )
        return tuple(directives)

    priority_intensity = 0.35 if escalation_stage == ViabilityEscalationStage.ELEVATED else 0.55
    directives.append(
        _directive(
            directive_type=ViabilityDirectiveType.PRIORITY_RAISE,
            intensity=max(priority_intensity, pressure_level * 0.7),
            affected_need_ids=affected_need_ids,
            override_scope=override_scope,
            reason="viability pressure requires elevated priority over non-viability goals",
            no_strong_override_claim=no_strong_override_claim,
        )
    )
    directives.append(
        _directive(
            directive_type=ViabilityDirectiveType.FOCUS_RETENTION,
            intensity=0.4 if escalation_stage == ViabilityEscalationStage.ELEVATED else 0.62,
            affected_need_ids=affected_need_ids,
            override_scope=override_scope,
            reason="retain focus on unresolved viability-affecting deficits",
            no_strong_override_claim=no_strong_override_claim,
        )
    )
    if escalation_stage in {ViabilityEscalationStage.THREAT, ViabilityEscalationStage.CRITICAL}:
        directives.append(
            _directive(
                directive_type=ViabilityDirectiveType.TASK_PERMISSIVENESS_REDUCTION,
                intensity=0.65 if escalation_stage == ViabilityEscalationStage.THREAT else 0.85,
                affected_need_ids=affected_need_ids,
                override_scope=override_scope,
                reason="reduce permissiveness for tasks not improving viability trajectory",
                no_strong_override_claim=no_strong_override_claim,
            )
        )
        directives.append(
            _directive(
                directive_type=ViabilityDirectiveType.INTERRUPT_RECOMMENDATION,
                intensity=0.5 if escalation_stage == ViabilityEscalationStage.THREAT else 0.8,
                affected_need_ids=affected_need_ids,
                override_scope=override_scope,
                reason="interrupt ongoing flow when viability deterioration is unresolved",
                no_strong_override_claim=no_strong_override_claim,
            )
        )
    if escalation_stage == ViabilityEscalationStage.CRITICAL:
        reason = "request protective mode under near-boundary viability threat"
        if recoverability_estimate is not None and recoverability_estimate < 0.3:
            reason = "critical threat with poor recoverability requests strong protective mode"
        directives.append(
            _directive(
                directive_type=ViabilityDirectiveType.PROTECTIVE_MODE_REQUEST,
                intensity=0.9,
                affected_need_ids=affected_need_ids,
                override_scope=override_scope,
                reason=reason,
                no_strong_override_claim=no_strong_override_claim,
            )
        )
    return tuple(directives)


def _directive(
    *,
    directive_type: ViabilityDirectiveType,
    intensity: float,
    affected_need_ids: tuple[NeedAxis, ...],
    override_scope: ViabilityOverrideScope,
    reason: str,
    no_strong_override_claim: bool,
) -> ViabilityControlDirective:
    capped_intensity = min(0.5, intensity) if no_strong_override_claim else intensity
    return ViabilityControlDirective(
        directive_id=f"viability-dir-{uuid4().hex[:10]}",
        directive_type=directive_type,
        intensity=round(max(0.0, min(1.0, capped_intensity)), 4),
        affected_need_ids=affected_need_ids,
        override_scope=override_scope,
        reason=reason,
        capped_by_uncertainty=no_strong_override_claim,
        provenance="r04.viability_directive_surface",
    )


def _confidence_rank(value: RegulationConfidence) -> int:
    if value == RegulationConfidence.HIGH:
        return 3
    if value == RegulationConfidence.MEDIUM:
        return 2
    return 1


def _stage_rank(value: ViabilityEscalationStage) -> int:
    if value == ViabilityEscalationStage.CRITICAL:
        return 4
    if value == ViabilityEscalationStage.THREAT:
        return 3
    if value == ViabilityEscalationStage.ELEVATED:
        return 2
    return 1


def _need_by_axis(state: RegulationState, axis: NeedAxis) -> NeedState | None:
    for need in state.needs:
        if need.axis == axis:
            return need
    return None


def _abstain_result(
    *,
    regulation_ref: str,
    affordance_ref: str,
    preference_ref: str,
    source_lineage: tuple[str, ...],
    reason: str,
    boundary_compatibility: tuple[str, ...],
    calibration: ViabilityCalibrationSpec,
) -> ViabilityControlResult:
    state = ViabilityControlState(
        pressure_level=0.0,
        escalation_stage=ViabilityEscalationStage.BASELINE,
        affected_need_ids=(),
        predicted_time_to_boundary=None,
        recoverability_estimate=None,
        recoverability_components=None,
        calibration_id=calibration.calibration_id,
        calibration_schema_version=calibration.schema_version,
        calibration_formula_version=calibration.formula_version,
        override_scope=ViabilityOverrideScope.NONE,
        persistence_state=ViabilityPersistenceState.STABLE,
        deescalation_conditions=("invalid_input_contract",),
        confidence=RegulationConfidence.LOW,
        uncertainty_state=(
            ViabilityUncertaintyState.INSUFFICIENT_OBSERVABILITY,
            ViabilityUncertaintyState.NO_STRONG_OVERRIDE_CLAIM,
        ),
        recent_failed_recovery_count=0,
        preference_epistemic_block_count=0,
        mixed_deterioration=False,
        no_strong_override_claim=True,
        input_regulation_snapshot_ref=regulation_ref,
        input_affordance_ref=affordance_ref,
        input_preference_ref=preference_ref,
        provenance="r04.abstain_invalid_input_contract",
    )
    directives: tuple[ViabilityControlDirective, ...] = ()
    gate = ViabilityGateDecision(
        accepted=False,
        restrictions=("invalid_viability_input_contract",),
        reason="abstain",
        accepted_directive_ids=(),
        rejected_directive_ids=(),
        state_ref=regulation_ref,
    )
    telemetry = build_viability_telemetry(
        state=state,
        directives=directives,
        source_lineage=source_lineage,
        blocked_reasons=(reason,),
        boundary_compatibility=boundary_compatibility,
        calibration=calibration,
        downstream_gate=gate,
        causal_basis="invalid input contract -> no strong viability claim",
        attempted_computation_paths=ATTEMPTED_VIABILITY_PATHS,
    )
    return ViabilityControlResult(
        state=state,
        directives=directives,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=True,
        abstain_reason=reason,
        no_action_selection_performed=True,
    )
