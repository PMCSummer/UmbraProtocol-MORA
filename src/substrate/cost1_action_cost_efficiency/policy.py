from __future__ import annotations

from dataclasses import asdict

from .models import (
    ActionCostDimension,
    ActionCostVector,
    ActionCostVectorInput,
    CostAuthorityFlags,
    CostBlockReason,
    CostComparisonCounters,
    CostComparisonFrame,
    CostComparisonInput,
    CostComparisonStatus,
    CostDimension,
    CostDimensionBreakdown,
    CostDimensionStatus,
    CostEvidenceKind,
    CostPreferenceDirection,
    CostValidationResult,
    DeclaredObservedCostDelta,
    EfficiencyEstimate,
    ThroughputSupportFrame,
    ThroughputSupportStatus,
)

_HIDDEN_TOKENS: tuple[str, ...] = ("hidden", "backend", "private", "scenario", "eval")
_SCENARIO_TOKENS: tuple[str, ...] = ("scenario_label", "scenario:")
_SELECT_ACTION_TOKENS: tuple[str, ...] = (
    "selected_action",
    "selected_candidate",
    "choose_candidate",
    "chosen_operation",
    "best_action",
    "execute_this",
    "goal_selected",
    "cheapest_candidate",
    "cost_winner",
    "scalar_winner",
)
_AP01_TOKENS: tuple[str, ...] = ("ap01_emit", "ap01_create", "publish_ap01")
_WORLD_SUBMIT_TOKENS: tuple[str, ...] = ("world_submit", "submit_world_action", "execute_world")
_VALUE_TOKENS: tuple[str, ...] = ("value_assigned", "intrinsic_value", "assign_value")
_PROVIDER_TRUTH_TOKENS: tuple[str, ...] = (
    "provider_efficiency_truth",
    "declared_is_truth",
    "oracle_cost",
    "final_efficiency_truth",
    "mature_skill",
    "mature_option",
    "automation_claim",
    "mature_recipe",
)
_DECLARED_MARKERS: tuple[str, ...] = ("provider_declared", "provider:", "hint_declared")
_RISK_HINTS: tuple[str, ...] = ("risk", "hazard", "danger")
_SETUP_HINTS: tuple[str, ...] = ("setup", "bootstrap", "init")
_STATION_HINTS: tuple[str, ...] = ("station", "occupy", "busy")
_TOOL_WEAR_HINTS: tuple[str, ...] = ("wear", "durability", "tool_wear")


def build_action_cost_vector(input_data: ActionCostVectorInput) -> CostValidationResult:
    blocked: list[CostBlockReason] = []
    warnings: list[str] = []
    trace: list[str] = ["cost1:vector:build:start"]
    count_data = asdict(CostComparisonCounters(vector_count=1))

    if not input_data.current_pressure_context_refs:
        blocked.append(CostBlockReason.PRESSURE_CONTEXT_MISSING)

    if input_data.selected_action_attempt or _contains_any(_joined(*input_data.metadata_refs), _SELECT_ACTION_TOKENS):
        blocked.append(CostBlockReason.SELECTED_ACTION_ATTEMPTED)
        count_data["selected_action_attempt_count"] += 1
    if input_data.ap01_emission_attempt or _contains_any(_joined(*input_data.metadata_refs), _AP01_TOKENS):
        blocked.append(CostBlockReason.AP01_EMISSION_ATTEMPTED)
        count_data["ap01_emission_attempt_count"] += 1
    if input_data.world_submission_attempt or _contains_any(_joined(*input_data.metadata_refs), _WORLD_SUBMIT_TOKENS):
        blocked.append(CostBlockReason.WORLD_SUBMISSION_ATTEMPTED)
    if input_data.value_assignment_attempt or _contains_any(_joined(*input_data.metadata_refs), _VALUE_TOKENS):
        blocked.append(CostBlockReason.VALUE_ASSIGNMENT_ATTEMPTED)
        count_data["value_assignment_attempt_count"] += 1
    if _contains_any(_joined(*input_data.metadata_refs), _HIDDEN_TOKENS):
        blocked.append(CostBlockReason.HIDDEN_BACKEND_COST_DETECTED)
        count_data["hidden_backend_cost_block_count"] += 1
    if _contains_any(_joined(*input_data.metadata_refs), _SCENARIO_TOKENS):
        blocked.append(CostBlockReason.SCENARIO_LABEL_COST_DETECTED)
        count_data["hidden_backend_cost_block_count"] += 1
    if _contains_any(_joined(*input_data.metadata_refs), _PROVIDER_TRUTH_TOKENS):
        blocked.append(CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH)

    if input_data.scalar_score_ref and not input_data.dimensions:
        blocked.append(CostBlockReason.SCALAR_HIDES_DIMENSIONS)
        count_data["scalar_hiding_block_count"] += 1

    all_source_refs: list[str] = list(input_data.source_refs)
    all_effect_refs: list[str] = list(input_data.effect_refs)
    all_observation_refs: list[str] = list(input_data.observation_refs)
    all_uncertainty_refs: list[str] = list(input_data.uncertainty_refs)
    all_lossiness_refs: list[str] = list(input_data.lossiness_refs)
    all_conflict_refs: list[str] = list(input_data.conflict_refs)
    missing_dimensions: list[str] = []

    for dim in input_data.dimensions:
        d_blocked, d_warnings, d_counts = validate_cost_dimension(dim)
        blocked.extend(d_blocked)
        warnings.extend(d_warnings)
        for key, value in d_counts.items():
            count_data[key] += value

        all_source_refs.extend(dim.source_refs)
        all_effect_refs.extend(dim.effect_refs)
        all_observation_refs.extend(dim.observation_refs)
        all_uncertainty_refs.extend(dim.uncertainty_refs)
        all_lossiness_refs.extend(dim.lossiness_refs)
        all_conflict_refs.extend(dim.conflict_refs)

        if dim.status in {CostDimensionStatus.MISSING, CostDimensionStatus.UNKNOWN, CostDimensionStatus.PARTIAL}:
            missing_dimensions.append(dim.dimension.value)

        if dim.dimension is CostDimension.THROUGHPUT:
            throughput = build_throughput_support_frame(
                candidate_ref=input_data.candidate_ref,
                observation_trace_refs=(*dim.effect_refs, *dim.observation_refs),
                source_refs=dim.source_refs,
                uncertainty_refs=dim.uncertainty_refs,
                lossiness_refs=dim.lossiness_refs,
                conflict_refs=dim.conflict_refs,
            )
            if not validate_throughput_requires_repeated_traces(throughput):
                blocked.append(CostBlockReason.THROUGHPUT_WITHOUT_REPETITION)
                count_data["throughput_without_repetition_count"] += 1
                warnings.append("throughput:single_observation_only")

    declared_dimensions = {item.dimension for item in input_data.dimensions}
    for item in CostDimension:
        if item not in declared_dimensions:
            missing_dimensions.append(item.value)

    if not input_data.dimensions and not input_data.scalar_score_ref:
        status = CostComparisonStatus.NOOP
    else:
        status = CostComparisonStatus.BLOCKED if blocked else (CostComparisonStatus.PARTIAL if (warnings or missing_dimensions) else CostComparisonStatus.ACCEPTED)

    blocked_unique = tuple(dict.fromkeys(blocked))
    warnings_unique = tuple(dict.fromkeys(warnings))

    vector = ActionCostVector(
        vector_id=input_data.vector_id,
        candidate_ref=input_data.candidate_ref,
        candidate_kind=input_data.candidate_kind,
        micro_operation_refs=input_data.micro_operation_refs,
        dimensions=input_data.dimensions,
        source_refs=tuple(dict.fromkeys(all_source_refs)),
        effect_refs=tuple(dict.fromkeys(all_effect_refs)),
        observation_refs=tuple(dict.fromkeys(all_observation_refs)),
        uncertainty_refs=tuple(dict.fromkeys(all_uncertainty_refs)),
        lossiness_refs=tuple(dict.fromkeys(all_lossiness_refs)),
        conflict_refs=tuple(dict.fromkeys(all_conflict_refs)),
        missing_dimension_refs=tuple(dict.fromkeys(missing_dimensions)),
        current_pressure_context_refs=input_data.current_pressure_context_refs,
        authority_flags=CostAuthorityFlags(),
        validation_trace=("cost1:vector:constructed", f"cost1:vector:status:{status.value}"),
    )
    trace.extend(vector.validation_trace)

    return CostValidationResult(
        status=status,
        blocked_reasons=blocked_unique,
        warnings=warnings_unique,
        counters=CostComparisonCounters(**count_data),
        vector_refs=(vector.vector_id,),
        comparison=None,
        vectors=(vector,),
        authority_flags=CostAuthorityFlags(),
        conformance_trace=tuple(trace),
    )


def validate_action_cost_vector(vector: ActionCostVector) -> CostValidationResult:
    input_data = ActionCostVectorInput(
        vector_id=vector.vector_id,
        candidate_ref=vector.candidate_ref,
        candidate_kind=vector.candidate_kind,
        micro_operation_refs=vector.micro_operation_refs,
        dimensions=vector.dimensions,
        source_refs=vector.source_refs,
        effect_refs=vector.effect_refs,
        observation_refs=vector.observation_refs,
        uncertainty_refs=vector.uncertainty_refs,
        lossiness_refs=vector.lossiness_refs,
        conflict_refs=vector.conflict_refs,
        current_pressure_context_refs=vector.current_pressure_context_refs,
    )
    return build_action_cost_vector(input_data)


def build_cost_comparison_frame(input_data: CostComparisonInput) -> CostValidationResult:
    blocked: list[CostBlockReason] = []
    warnings: list[str] = []
    trace: list[str] = ["cost1:comparison:build:start"]
    count_data = asdict(CostComparisonCounters(comparison_count=1, vector_count=len(input_data.vectors)))

    if input_data.selected_candidate_ref or _contains_any(_joined(*input_data.metadata_refs), _SELECT_ACTION_TOKENS):
        blocked.append(CostBlockReason.SELECTED_ACTION_ATTEMPTED)
        count_data["selected_action_attempt_count"] += 1
    if input_data.ap01_emission_attempt or _contains_any(_joined(*input_data.metadata_refs), _AP01_TOKENS):
        blocked.append(CostBlockReason.AP01_EMISSION_ATTEMPTED)
        count_data["ap01_emission_attempt_count"] += 1
    if input_data.world_submission_attempt or _contains_any(_joined(*input_data.metadata_refs), _WORLD_SUBMIT_TOKENS):
        blocked.append(CostBlockReason.WORLD_SUBMISSION_ATTEMPTED)
    if input_data.value_assignment_attempt or _contains_any(_joined(*input_data.metadata_refs), _VALUE_TOKENS):
        blocked.append(CostBlockReason.VALUE_ASSIGNMENT_ATTEMPTED)
        count_data["value_assignment_attempt_count"] += 1
    if _contains_any(_joined(*input_data.metadata_refs), _HIDDEN_TOKENS):
        blocked.append(CostBlockReason.HIDDEN_BACKEND_COST_DETECTED)
        count_data["hidden_backend_cost_block_count"] += 1
    if _contains_any(_joined(*input_data.metadata_refs), _SCENARIO_TOKENS):
        blocked.append(CostBlockReason.SCENARIO_LABEL_COST_DETECTED)
        count_data["hidden_backend_cost_block_count"] += 1
    if _contains_any(_joined(*input_data.metadata_refs), _PROVIDER_TRUTH_TOKENS):
        blocked.append(CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH)
    if not validate_cost_hint_not_action_permission(input_data):
        blocked.append(CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH)

    if not input_data.pressure_refs:
        blocked.append(CostBlockReason.PRESSURE_CONTEXT_MISSING)
    if input_data.vectors and not input_data.context_refs:
        blocked.append(CostBlockReason.PRESSURE_CONTEXT_MISSING)

    for item in input_data.deltas:
        if not validate_mismatch_creates_residue(item):
            blocked.append(CostBlockReason.MISMATCH_WITHOUT_RESIDUE)
        else:
            count_data["mismatch_residue_count"] += 1

    if not input_data.vectors:
        status = CostComparisonStatus.NOOP
        comparison = CostComparisonFrame(
            comparison_id=input_data.comparison_id,
            compared_candidate_refs=(),
            cost_vector_refs=(),
            context_refs=input_data.context_refs,
            pressure_refs=input_data.pressure_refs,
            dimension_breakdown_refs=(),
            efficiency_estimate_refs=(),
            mismatch_residue_refs=(),
            warning_refs=(),
            comparison_trace_refs=(),
            lower_cost_candidate_refs_by_dimension={},
            higher_cost_candidate_refs_by_dimension={},
            unresolved_candidate_refs=(),
            blocked_candidate_refs=(),
            no_selected_candidate=True,
            authority_flags=CostAuthorityFlags(),
            validation_status=CostComparisonStatus.NOOP,
            counters=CostComparisonCounters(**count_data),
        )
        return CostValidationResult(
            status=status,
            blocked_reasons=(),
            warnings=(),
            counters=CostComparisonCounters(**count_data),
            vector_refs=(),
            comparison=comparison,
            vectors=(),
            authority_flags=CostAuthorityFlags(),
            conformance_trace=tuple(trace),
        )

    vector_refs = tuple(item.vector_id for item in input_data.vectors)
    candidate_refs = tuple(item.candidate_ref for item in input_data.vectors)
    breakdowns: list[CostDimensionBreakdown] = []
    estimates: list[EfficiencyEstimate] = []
    warning_refs: list[str] = []
    lower_by_dimension: dict[str, list[str]] = {}
    higher_by_dimension: dict[str, list[str]] = {}
    unresolved: list[str] = []

    for vector in input_data.vectors:
        vector_check = validate_action_cost_vector(vector)
        blocked.extend(vector_check.blocked_reasons)
        warnings.extend(vector_check.warnings)
        _accumulate_counters(count_data, vector_check.counters)
        summary = _dimension_summary(vector)
        missing = tuple(dim.value for dim in _missing_dimensions(vector))
        breakdown = CostDimensionBreakdown(
            breakdown_id=f"breakdown:{input_data.comparison_id}:{vector.candidate_ref}",
            comparison_ref=input_data.comparison_id,
            candidate_ref=vector.candidate_ref,
            dimension_summaries=summary,
            missing_dimensions=missing,
            warnings=tuple(vector_check.warnings),
            no_hidden_scalar=True,
        )
        breakdowns.append(breakdown)
        warning_refs.extend(breakdown.warnings)
        estimates.append(build_efficiency_estimate(vector=vector))
        if missing:
            unresolved.append(vector.candidate_ref)

    for dimension in CostDimension:
        numeric = _numeric_dimension_candidates(input_data.vectors, dimension)
        if len(numeric) < 2:
            continue
        numeric.sort(key=lambda item: item[1])
        low_val = numeric[0][1]
        high_val = numeric[-1][1]
        low = tuple(item[0] for item in numeric if item[1] == low_val)
        high = tuple(item[0] for item in numeric if item[1] == high_val)
        lower_by_dimension[dimension.value] = list(low)
        higher_by_dimension[dimension.value] = list(high)

    comparison_status = CostComparisonStatus.BLOCKED if blocked else (CostComparisonStatus.PARTIAL if (warnings or unresolved) else CostComparisonStatus.ACCEPTED)
    blocked_unique = tuple(dict.fromkeys(blocked))
    warnings_unique = tuple(dict.fromkeys(warnings))

    comparison = CostComparisonFrame(
        comparison_id=input_data.comparison_id,
        compared_candidate_refs=candidate_refs,
        cost_vector_refs=vector_refs,
        context_refs=input_data.context_refs,
        pressure_refs=input_data.pressure_refs,
        dimension_breakdown_refs=tuple(item.breakdown_id for item in breakdowns),
        efficiency_estimate_refs=tuple(item.estimate_id for item in estimates),
        mismatch_residue_refs=tuple(dict.fromkeys(ref for item in input_data.deltas for ref in item.mismatch_residue_refs)),
        warning_refs=tuple(dict.fromkeys((*warning_refs, *warnings_unique))),
        comparison_trace_refs=("cost1:comparison:dimension_breakdown", f"cost1:comparison:status:{comparison_status.value}"),
        lower_cost_candidate_refs_by_dimension={key: tuple(value) for key, value in lower_by_dimension.items()},
        higher_cost_candidate_refs_by_dimension={key: tuple(value) for key, value in higher_by_dimension.items()},
        unresolved_candidate_refs=tuple(dict.fromkeys(unresolved)),
        blocked_candidate_refs=tuple(dict.fromkeys(item.candidate_ref for item in input_data.vectors if item.validation_trace and "blocked" in " ".join(item.validation_trace))),
        no_selected_candidate=True,
        authority_flags=CostAuthorityFlags(),
        validation_status=comparison_status,
        counters=CostComparisonCounters(**count_data),
    )
    trace.extend(comparison.comparison_trace_refs)

    return CostValidationResult(
        status=comparison_status,
        blocked_reasons=blocked_unique,
        warnings=warnings_unique,
        counters=CostComparisonCounters(**count_data),
        vector_refs=vector_refs,
        comparison=comparison,
        vectors=input_data.vectors,
        authority_flags=CostAuthorityFlags(),
        conformance_trace=tuple(trace),
    )


def validate_cost_comparison_frame(frame: CostComparisonFrame) -> CostValidationResult:
    return CostValidationResult(
        status=frame.validation_status,
        blocked_reasons=(),
        warnings=frame.warning_refs,
        counters=frame.counters,
        vector_refs=frame.cost_vector_refs,
        comparison=frame,
        vectors=(),
        authority_flags=frame.authority_flags,
        conformance_trace=frame.comparison_trace_refs,
    )


def build_efficiency_estimate(*, vector: ActionCostVector) -> EfficiencyEstimate:
    lower: list[str] = []
    higher: list[str] = []
    unknown: list[str] = []
    risk_warnings: list[str] = []
    setup_warnings: list[str] = []
    station_warnings: list[str] = []
    uncertainty: list[str] = list(vector.uncertainty_refs)

    for item in vector.dimensions:
        ref = f"{item.dimension.value}:{vector.candidate_ref}"
        if item.status in {CostDimensionStatus.UNKNOWN, CostDimensionStatus.MISSING, CostDimensionStatus.PARTIAL}:
            unknown.append(ref)
        elif item.preference_direction is CostPreferenceDirection.LOWER_IS_BETTER and item.amount_value is not None:
            lower.append(ref)
        elif item.preference_direction is CostPreferenceDirection.HIGHER_IS_BETTER and item.amount_value is not None:
            higher.append(ref)
        if item.dimension is CostDimension.RISK:
            risk_warnings.append(f"risk:{vector.candidate_ref}")
        if item.dimension is CostDimension.SETUP:
            setup_warnings.append(f"setup:{vector.candidate_ref}")
        if item.dimension is CostDimension.STATION_OCCUPATION:
            station_warnings.append(f"station:{vector.candidate_ref}")
        uncertainty.extend(item.uncertainty_refs)

    return EfficiencyEstimate(
        estimate_id=f"estimate:{vector.vector_id}",
        candidate_ref=vector.candidate_ref,
        support_vector_refs=(vector.vector_id,),
        lower_cost_dimension_refs=tuple(dict.fromkeys(lower)),
        higher_cost_dimension_refs=tuple(dict.fromkeys(higher)),
        unknown_dimension_refs=tuple(dict.fromkeys(unknown)),
        risk_warning_refs=tuple(dict.fromkeys(risk_warnings)),
        setup_warning_refs=tuple(dict.fromkeys(setup_warnings)),
        station_occupation_warning_refs=tuple(dict.fromkeys(station_warnings)),
        uncertainty_refs=tuple(dict.fromkeys(uncertainty)),
        confidence_band="provisional",
        provisional=True,
        final_efficiency_truth=False,
    )


def build_declared_observed_cost_delta(
    *,
    delta_id: str,
    candidate_ref: str,
    dimension: CostDimension,
    declared_cost_ref: str,
    observed_cost_ref: str,
    delta_direction: str,
    mismatch_residue_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...] = (),
    source_refs: tuple[str, ...] = (),
    delta_magnitude_ref: str | None = None,
) -> DeclaredObservedCostDelta:
    return DeclaredObservedCostDelta(
        delta_id=delta_id,
        candidate_ref=candidate_ref,
        dimension=dimension,
        declared_cost_ref=declared_cost_ref,
        observed_cost_ref=observed_cost_ref,
        delta_direction=delta_direction,
        delta_magnitude_ref=delta_magnitude_ref,
        mismatch_residue_refs=mismatch_residue_refs,
        uncertainty_refs=uncertainty_refs,
        source_refs=source_refs,
        status=CostDimensionStatus.MISMATCH,
    )


def build_throughput_support_frame(
    *,
    candidate_ref: str,
    observation_trace_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...] = (),
    lossiness_refs: tuple[str, ...] = (),
    conflict_refs: tuple[str, ...] = (),
) -> ThroughputSupportFrame:
    repeated = len(observation_trace_refs)
    if repeated == 0:
        status = ThroughputSupportStatus.NONE
    elif repeated == 1:
        status = ThroughputSupportStatus.SINGLE_OBSERVATION_ONLY
    elif repeated < 4:
        status = ThroughputSupportStatus.PROVISIONAL_REPEATED
    else:
        status = ThroughputSupportStatus.SUPPORTED_REPEATED
    return ThroughputSupportFrame(
        throughput_id=f"throughput:{candidate_ref}",
        candidate_ref=candidate_ref,
        observation_trace_refs=observation_trace_refs,
        repeated_trace_count=repeated,
        support_status=status,
        source_refs=source_refs,
        uncertainty_refs=uncertainty_refs,
        lossiness_refs=lossiness_refs,
        conflict_refs=conflict_refs,
        no_final_truth=True,
    )


def validate_cost_dimension(dimension: ActionCostDimension) -> tuple[tuple[CostBlockReason, ...], tuple[str, ...], dict[str, int]]:
    blocked: list[CostBlockReason] = []
    warnings: list[str] = []
    counts = asdict(CostComparisonCounters())

    _count_evidence_kind(dimension.evidence_kind, counts)
    if dimension.status in {CostDimensionStatus.UNKNOWN, CostDimensionStatus.MISSING, CostDimensionStatus.PARTIAL}:
        warnings.append(f"dimension:{dimension.dimension.value}:{dimension.status.value}")
    if dimension.dimension is CostDimension.RISK:
        counts["risk_warning_count"] += 1
    if dimension.dimension is CostDimension.SETUP:
        counts["setup_warning_count"] += 1
    if dimension.dimension is CostDimension.STATION_OCCUPATION:
        counts["station_occupation_warning_count"] += 1
    if dimension.dimension is CostDimension.TOOL_WEAR:
        counts["tool_wear_warning_count"] += 1
    if dimension.uncertainty_refs or dimension.status in {CostDimensionStatus.UNKNOWN, CostDimensionStatus.PARTIAL}:
        counts["uncertainty_warning_count"] += 1

    if not dimension.source_refs:
        blocked.append(CostBlockReason.MISSING_SOURCE_REFS)
        counts["missing_source_count"] += 1

    if dimension.evidence_kind is CostEvidenceKind.OBSERVED and not validate_observed_cost_requires_effect_refs(dimension):
        blocked.append(CostBlockReason.OBSERVED_COST_WITHOUT_EFFECT_REFS)
        counts["observed_without_effect_block_count"] += 1

    if reject_declared_cost_as_observed(dimension):
        blocked.append(CostBlockReason.DECLARED_COST_AS_OBSERVED)
        counts["declared_as_observed_block_count"] += 1

    if reject_hidden_backend_cost(dimension):
        blocked.append(CostBlockReason.HIDDEN_BACKEND_COST_DETECTED)
        counts["hidden_backend_cost_block_count"] += 1

    if reject_scenario_label_cost(dimension):
        blocked.append(CostBlockReason.SCENARIO_LABEL_COST_DETECTED)
        counts["hidden_backend_cost_block_count"] += 1

    if reject_unknown_default_zero(dimension):
        blocked.append(CostBlockReason.UNKNOWN_DIMENSION_DEFAULTED_TO_ZERO)
        counts["unknown_default_zero_block_count"] += 1

    if _contains_any(_joined(*dimension.notes, *dimension.metadata.values()), _PROVIDER_TRUTH_TOKENS):
        blocked.append(CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH)

    return tuple(dict.fromkeys(blocked)), tuple(dict.fromkeys(warnings)), counts


def validate_cost_evidence_kind(dimension: ActionCostDimension) -> bool:
    return isinstance(dimension.evidence_kind, CostEvidenceKind)


def reject_declared_cost_as_observed(dimension: ActionCostDimension) -> bool:
    if dimension.evidence_kind is not CostEvidenceKind.OBSERVED:
        return False
    return _contains_any(_joined(*dimension.notes, *dimension.metadata.values(), *dimension.source_refs), _DECLARED_MARKERS)


def reject_hidden_backend_cost(dimension: ActionCostDimension) -> bool:
    return _contains_any(
        _joined(*dimension.source_refs, *dimension.effect_refs, *dimension.observation_refs, *dimension.notes, *dimension.metadata.values()),
        _HIDDEN_TOKENS,
    )


def reject_scenario_label_cost(dimension: ActionCostDimension) -> bool:
    return _contains_any(_joined(*dimension.source_refs, *dimension.notes, *dimension.metadata.values()), _SCENARIO_TOKENS)


def reject_single_scalar_hiding_dimensions(input_data: ActionCostVectorInput) -> bool:
    return bool(input_data.scalar_score_ref and not input_data.dimensions)


def reject_unknown_default_zero(dimension: ActionCostDimension) -> bool:
    return dimension.evidence_kind is CostEvidenceKind.UNKNOWN and (dimension.amount_value == 0)


def validate_observed_cost_requires_effect_refs(dimension: ActionCostDimension) -> bool:
    if dimension.evidence_kind is not CostEvidenceKind.OBSERVED:
        return True
    if not (dimension.effect_refs or dimension.observation_refs):
        return False
    marker_haystack = _joined(*dimension.effect_refs, *dimension.observation_refs, *dimension.notes, *dimension.metadata.values())
    if "expected" in marker_haystack or "predicted" in marker_haystack:
        return False
    return True


def validate_throughput_requires_repeated_traces(frame: ThroughputSupportFrame) -> bool:
    return frame.support_status in {ThroughputSupportStatus.PROVISIONAL_REPEATED, ThroughputSupportStatus.SUPPORTED_REPEATED, ThroughputSupportStatus.NONE}


def validate_mismatch_creates_residue(delta: DeclaredObservedCostDelta) -> bool:
    return bool(delta.mismatch_residue_refs)


def validate_comparison_does_not_select_action(input_data: CostComparisonInput) -> bool:
    return input_data.selected_candidate_ref is None and not _contains_any(_joined(*input_data.metadata_refs), _SELECT_ACTION_TOKENS)


def validate_cost_hint_not_action_permission(input_data: CostComparisonInput) -> bool:
    return not _contains_any(_joined(*input_data.metadata_refs), ("permission", "authorized", "must_execute"))


def validate_no_value_assignment(input_data: CostComparisonInput) -> bool:
    return not input_data.value_assignment_attempt and not _contains_any(_joined(*input_data.metadata_refs), _VALUE_TOKENS)


def summarize_cost_conformance(result: CostValidationResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": result.status.value,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "authority_flags": asdict(result.authority_flags),
        "vector_refs": result.vector_refs,
    }
    if result.comparison is not None:
        payload["comparison"] = {
            "comparison_id": result.comparison.comparison_id,
            "candidates": result.comparison.compared_candidate_refs,
            "dimension_breakdown_refs": result.comparison.dimension_breakdown_refs,
            "mismatch_residue_refs": result.comparison.mismatch_residue_refs,
            "validation_status": result.comparison.validation_status.value,
        }
    return payload


def _count_evidence_kind(kind: CostEvidenceKind, counters: dict[str, int]) -> None:
    if kind is CostEvidenceKind.OBSERVED:
        counters["observed_dimension_count"] += 1
    elif kind is CostEvidenceKind.ESTIMATED:
        counters["estimated_dimension_count"] += 1
    elif kind is CostEvidenceKind.PROVIDER_DECLARED:
        counters["provider_declared_dimension_count"] += 1
    elif kind is CostEvidenceKind.INFERRED:
        counters["inferred_dimension_count"] += 1
    elif kind is CostEvidenceKind.UNKNOWN:
        counters["unknown_dimension_count"] += 1


def _missing_dimensions(vector: ActionCostVector) -> tuple[CostDimension, ...]:
    present = {item.dimension for item in vector.dimensions}
    return tuple(item for item in CostDimension if item not in present)


def _dimension_summary(vector: ActionCostVector) -> dict[str, str]:
    summary: dict[str, str] = {}
    for item in vector.dimensions:
        amount = "na" if item.amount_value is None else str(item.amount_value)
        summary[item.dimension.value] = f"{item.status.value}|{item.evidence_kind.value}|{amount}"
    return summary


def _numeric_dimension_candidates(vectors: tuple[ActionCostVector, ...], dimension: CostDimension) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for vector in vectors:
        for item in vector.dimensions:
            if item.dimension is dimension and item.amount_value is not None:
                out.append((vector.candidate_ref, item.amount_value))
    return out


def _accumulate_counters(target: dict[str, int], source: CostComparisonCounters) -> None:
    for key, value in asdict(source).items():
        if key in target:
            target[key] += value


def _joined(*values: str) -> str:
    return " ".join(values).lower()


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(token in haystack for token in needles)
