from __future__ import annotations

from dataclasses import replace

from substrate.cost1_action_cost_efficiency import (
    ActionCostDimension,
    ActionCostVectorInput,
    CostBlockReason,
    CostComparisonInput,
    CostComparisonStatus,
    CostDimension,
    CostDimensionStatus,
    CostEvidenceKind,
    CostPreferenceDirection,
    ThroughputSupportStatus,
    build_action_cost_vector,
    build_cost_comparison_frame,
    build_declared_observed_cost_delta,
    build_throughput_support_frame,
    declared_observed_mismatch_fixture,
    hidden_backend_cost_blocked_fixture,
    material_vs_energy_tradeoff_fixture,
    observed_cost_fixture,
    provider_declared_cost_fixture,
    risk_vs_material_fixture,
    scalar_hiding_blocked_fixture,
    setup_time_fixture,
    station_occupation_fixture,
    throughput_repeated_fixture,
    throughput_single_run_fixture,
    tool_wear_fixture,
    unknown_dimension_fixture,
    validate_throughput_requires_repeated_traces,
    value_assignment_blocked_fixture,
)


def _dim(
    dimension: CostDimension,
    amount: float | None,
    evidence: CostEvidenceKind,
    source: str,
    *,
    effect: str | None = None,
    obs: str | None = None,
    status: CostDimensionStatus = CostDimensionStatus.PRESENT,
    notes: tuple[str, ...] = (),
) -> ActionCostDimension:
    return ActionCostDimension(
        dimension=dimension,
        amount_value=amount,
        unit="u",
        evidence_kind=evidence,
        source_refs=(source,),
        effect_refs=((effect,) if effect else ()),
        observation_refs=((obs,) if obs else ()),
        status=status,
        preference_direction=CostPreferenceDirection.LOWER_IS_BETTER,
        notes=notes,
    )


def test_cost1_builds_multidimensional_cost_vector() -> None:
    inp = ActionCostVectorInput(
        vector_id="v:multi",
        candidate_ref="c:1",
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:1",),
        dimensions=(
            _dim(CostDimension.MATERIAL, 2, CostEvidenceKind.OBSERVED, "src:m", effect="e:m"),
            _dim(CostDimension.ENERGY, 3, CostEvidenceKind.OBSERVED, "src:e", effect="e:e"),
            _dim(CostDimension.TIME, 4, CostEvidenceKind.OBSERVED, "src:t", obs="obs:t"),
            _dim(CostDimension.TOOL_WEAR, 1, CostEvidenceKind.ESTIMATED, "src:w"),
            _dim(CostDimension.SETUP, 5, CostEvidenceKind.ESTIMATED, "src:s"),
            _dim(CostDimension.RISK, 2, CostEvidenceKind.ESTIMATED, "src:r"),
            _dim(CostDimension.UNCERTAINTY, None, CostEvidenceKind.UNKNOWN, "src:u", status=CostDimensionStatus.UNKNOWN),
        ),
    )
    run = build_action_cost_vector(inp)
    assert run.status in {CostComparisonStatus.ACCEPTED, CostComparisonStatus.PARTIAL}
    assert run.vectors[0].dimensions and len(run.vectors[0].dimensions) == 7


def test_cost1_declared_cost_not_observed() -> None:
    run = build_action_cost_vector(provider_declared_cost_fixture())
    assert all(dim.evidence_kind is CostEvidenceKind.PROVIDER_DECLARED for dim in run.vectors[0].dimensions)


def test_cost1_observed_cost_requires_effect_refs() -> None:
    bad = replace(observed_cost_fixture(), dimensions=(_dim(CostDimension.TIME, 5, CostEvidenceKind.OBSERVED, "src:obs"),))
    run = build_action_cost_vector(bad)
    assert CostBlockReason.OBSERVED_COST_WITHOUT_EFFECT_REFS in run.blocked_reasons


def test_cost1_unknown_dimension_not_zero() -> None:
    run = build_action_cost_vector(unknown_dimension_fixture())
    vec = run.vectors[0]
    unknown = [d for d in vec.dimensions if d.status is CostDimensionStatus.UNKNOWN]
    assert unknown and unknown[0].amount_value is None


def test_cost1_single_scalar_cannot_hide_depletion() -> None:
    run = build_action_cost_vector(scalar_hiding_blocked_fixture())
    assert CostBlockReason.SCALAR_HIDES_DIMENSIONS in run.blocked_reasons


def test_cost1_low_material_cost_does_not_erase_risk() -> None:
    run = build_cost_comparison_frame(risk_vs_material_fixture())
    assert run.counters.risk_warning_count > 0


def test_cost1_low_energy_cost_does_not_erase_setup_time() -> None:
    run = build_action_cost_vector(setup_time_fixture())
    assert run.counters.setup_warning_count > 0


def test_cost1_tool_wear_preserved_as_dimension() -> None:
    run = build_action_cost_vector(tool_wear_fixture())
    assert any(item.dimension is CostDimension.TOOL_WEAR for item in run.vectors[0].dimensions)


def test_cost1_station_occupation_preserved_as_dimension() -> None:
    run = build_action_cost_vector(station_occupation_fixture())
    assert any(item.dimension is CostDimension.STATION_OCCUPATION for item in run.vectors[0].dimensions)


def test_cost1_throughput_requires_repeated_traces() -> None:
    single = throughput_single_run_fixture()
    repeated = throughput_repeated_fixture()
    assert validate_throughput_requires_repeated_traces(single) is False
    assert validate_throughput_requires_repeated_traces(repeated) is True


def test_cost1_mismatch_creates_residue() -> None:
    _, delta = declared_observed_mismatch_fixture()
    run = build_cost_comparison_frame(
        CostComparisonInput(
            comparison_id="cmp:mismatch",
            vectors=(),
            pressure_refs=("pressure:1",),
            deltas=(delta,),
        )
    )
    assert delta.mismatch_residue_refs
    assert run.status is CostComparisonStatus.NOOP


def test_cost1_comparison_does_not_select_action() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    assert run.comparison is not None
    assert run.comparison.no_selected_candidate is True


def test_cost1_comparison_does_not_emit_ap01() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    assert CostBlockReason.AP01_EMISSION_ATTEMPTED not in run.blocked_reasons


def test_cost1_cost_hint_not_action_permission() -> None:
    run = build_cost_comparison_frame(
        replace(
            material_vs_energy_tradeoff_fixture(),
            metadata_refs=("permission:authorized",),
        )
    )
    assert run.status is CostComparisonStatus.BLOCKED


def test_cost1_provider_efficiency_not_truth() -> None:
    bad = replace(provider_declared_cost_fixture(), metadata_refs=("provider_efficiency_truth",))
    run = build_action_cost_vector(bad)
    assert CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH in run.blocked_reasons


def test_cost1_no_intrinsic_value_assignment() -> None:
    run = build_cost_comparison_frame(value_assignment_blocked_fixture())
    assert CostBlockReason.VALUE_ASSIGNMENT_ATTEMPTED in run.blocked_reasons


def test_cost1_context_sensitive_pressure_visible() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    assert run.comparison is not None
    assert run.comparison.pressure_refs


def test_cost1_micro_operation_candidate_carries_cost_without_permission() -> None:
    run = build_action_cost_vector(observed_cost_fixture())
    assert run.vectors[0].micro_operation_refs
    assert run.authority_flags.can_select_action is False


def test_cost1_hidden_backend_cost_rejected() -> None:
    run = build_action_cost_vector(hidden_backend_cost_blocked_fixture())
    assert CostBlockReason.HIDDEN_BACKEND_COST_DETECTED in run.blocked_reasons


def test_cost1_partial_vector_reports_uncertainty() -> None:
    run = build_action_cost_vector(unknown_dimension_fixture())
    assert run.status is CostComparisonStatus.PARTIAL
    assert run.counters.uncertainty_warning_count > 0


def test_cost1_unknown_energy_does_not_default_to_zero() -> None:
    inp = replace(
        unknown_dimension_fixture(),
        dimensions=(
            _dim(CostDimension.ENERGY, 0, CostEvidenceKind.UNKNOWN, "src:unknown:energy", status=CostDimensionStatus.UNKNOWN),
        ),
    )
    run = build_action_cost_vector(inp)
    assert CostBlockReason.UNKNOWN_DIMENSION_DEFAULTED_TO_ZERO in run.blocked_reasons


def test_cost1_provider_declared_time_not_observed_time() -> None:
    run = build_action_cost_vector(provider_declared_cost_fixture())
    time_dim = [d for d in run.vectors[0].dimensions if d.dimension is CostDimension.TIME][0]
    assert time_dim.evidence_kind is CostEvidenceKind.PROVIDER_DECLARED


def test_cost1_low_risk_does_not_erase_high_material_cost() -> None:
    run = build_cost_comparison_frame(risk_vs_material_fixture())
    assert run.comparison is not None
    assert "material" in run.comparison.lower_cost_candidate_refs_by_dimension
    assert "risk" in run.comparison.lower_cost_candidate_refs_by_dimension


def test_cost1_throughput_single_observation_is_provisional() -> None:
    single = throughput_single_run_fixture()
    assert single.support_status is ThroughputSupportStatus.SINGLE_OBSERVATION_ONLY


def test_cost1_comparison_preserves_dimension_breakdown() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    assert run.comparison is not None
    assert run.comparison.dimension_breakdown_refs


def test_cost1_cost_mismatch_does_not_overwrite_declared_cost() -> None:
    vector, delta = declared_observed_mismatch_fixture()
    run = build_cost_comparison_frame(
        CostComparisonInput(
            comparison_id="cmp:delta",
            vectors=(vector,),
            pressure_refs=("pressure:1",),
            deltas=(delta,),
        )
    )
    assert run.comparison is not None
    assert "residue:cost_mismatch:energy" in run.comparison.mismatch_residue_refs


def test_cost1_no_recipe_or_skill_maturity_from_efficiency() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    flags = run.authority_flags
    assert flags.can_mature_recipe is False
    assert flags.can_mature_skill is False
    assert flags.can_claim_automation is False


def test_cost1_no_goal_selection_from_cheapest_candidate() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    assert run.comparison is not None
    assert run.comparison.no_selected_candidate is True


def test_cost1_no_world_submission_from_cost_comparison() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), world_submission_attempt=True)
    )
    assert CostBlockReason.WORLD_SUBMISSION_ATTEMPTED in run.blocked_reasons


def test_cost1_metadata_hidden_backend_cost_rejected() -> None:
    run = build_action_cost_vector(
        replace(
            observed_cost_fixture(),
            metadata_refs=("payload:{'backend_cost_table':1}",),
        )
    )
    assert CostBlockReason.HIDDEN_BACKEND_COST_DETECTED in run.blocked_reasons


def test_cost1_rejects_selected_candidate_in_comparison_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("selected_candidate:candidate:a",))
    )
    assert CostBlockReason.SELECTED_ACTION_ATTEMPTED in run.blocked_reasons


def test_cost1_rejects_ap01_request_creation_in_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("ap01_create:request",))
    )
    assert CostBlockReason.AP01_EMISSION_ATTEMPTED in run.blocked_reasons


def test_cost1_rejects_world_submission_in_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("submit_world_action:true",))
    )
    assert CostBlockReason.WORLD_SUBMISSION_ATTEMPTED in run.blocked_reasons


def test_cost1_rejects_hidden_backend_cost_in_nested_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("payload:{'cost':{'backend_table':1}}",))
    )
    assert CostBlockReason.HIDDEN_BACKEND_COST_DETECTED in run.blocked_reasons


def test_cost1_rejects_scenario_label_cost_in_nested_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("meta:{'scenario_label':'eval:1'}",))
    )
    assert CostBlockReason.SCENARIO_LABEL_COST_DETECTED in run.blocked_reasons


def test_cost1_expected_cost_is_not_observed_cost() -> None:
    inp = replace(
        observed_cost_fixture(),
        dimensions=(
            _dim(
                CostDimension.TIME,
                7,
                CostEvidenceKind.OBSERVED,
                "src:obs:expected",
                effect="effect:expected_cost_delta",
                notes=("expected",),
            ),
        ),
    )
    run = build_action_cost_vector(inp)
    assert CostBlockReason.OBSERVED_COST_WITHOUT_EFFECT_REFS in run.blocked_reasons


def test_cost1_provider_declared_cost_cannot_satisfy_observed_requirement() -> None:
    inp = replace(
        observed_cost_fixture(),
        dimensions=(
            _dim(
                CostDimension.TIME,
                5,
                CostEvidenceKind.OBSERVED,
                "provider:manual:1",
                effect="effect:time",
                notes=("provider_declared",),
            ),
        ),
    )
    run = build_action_cost_vector(inp)
    assert CostBlockReason.DECLARED_COST_AS_OBSERVED in run.blocked_reasons


def test_cost1_scalar_score_cannot_override_dimension_breakdown() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("scalar_winner:candidate:a",))
    )
    assert CostBlockReason.SELECTED_ACTION_ATTEMPTED in run.blocked_reasons


def test_cost1_dimension_breakdown_required_when_summary_present() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("summary:scoreboard",))
    )
    assert run.comparison is not None
    assert run.comparison.dimension_breakdown_refs


def test_cost1_throughput_repeated_count_cannot_be_forged_by_metadata() -> None:
    inp = ActionCostVectorInput(
        vector_id="v:throughput:forged",
        candidate_ref="candidate:forged",
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:throughput",),
        metadata_refs=("repeated_trace_count:10",),
        dimensions=(
            _dim(
                CostDimension.THROUGHPUT,
                1,
                CostEvidenceKind.OBSERVED,
                "src:throughput:single",
                effect="trace:1",
            ),
        ),
    )
    run = build_action_cost_vector(inp)
    assert CostBlockReason.THROUGHPUT_WITHOUT_REPETITION in run.blocked_reasons


def test_cost1_declared_observed_mismatch_preserves_both_sources() -> None:
    vector, delta = declared_observed_mismatch_fixture()
    run = build_cost_comparison_frame(
        CostComparisonInput(
            comparison_id="cmp:delta:sources",
            vectors=(vector,),
            context_refs=("ctx:delta",),
            pressure_refs=("pressure:1",),
            deltas=(delta,),
        )
    )
    assert delta.declared_cost_ref != delta.observed_cost_ref
    assert run.comparison is not None
    assert "residue:cost_mismatch:energy" in run.comparison.mismatch_residue_refs


def test_cost1_low_cost_does_not_assign_goal_or_value() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("cheapest_candidate:candidate:a",))
    )
    assert CostBlockReason.SELECTED_ACTION_ATTEMPTED in run.blocked_reasons


def test_cost1_low_cost_does_not_create_micro1_permission() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("permission:authorized",))
    )
    assert CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH in run.blocked_reasons


def test_cost1_efficiency_does_not_mature_skill_or_option() -> None:
    run = build_cost_comparison_frame(material_vs_energy_tradeoff_fixture())
    flags = run.authority_flags
    assert flags.can_mature_skill is False
    assert flags.can_claim_automation is False
    assert flags.can_select_goal is False


def test_cost1_missing_risk_tool_wear_station_occupation_remain_visible() -> None:
    run = build_action_cost_vector(observed_cost_fixture())
    missing = set(run.vectors[0].missing_dimension_refs)
    assert "risk" in missing
    assert "tool_wear" in missing
    assert "station_occupation" in missing


def test_cost1_context_refs_required_for_non_noop_comparison() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), context_refs=())
    )
    assert CostBlockReason.PRESSURE_CONTEXT_MISSING in run.blocked_reasons


def test_cost1_provider_efficiency_does_not_become_final_truth() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("provider_efficiency_truth",))
    )
    assert CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH in run.blocked_reasons
    assert run.authority_flags.can_claim_final_efficiency_truth is False


def test_cost1_comparison_trace_preserves_candidate_refs_without_selection() -> None:
    base = material_vs_energy_tradeoff_fixture()
    run = build_cost_comparison_frame(base)
    assert run.comparison is not None
    assert run.comparison.compared_candidate_refs == tuple(item.candidate_ref for item in base.vectors)
    assert run.comparison.no_selected_candidate is True


def test_cost1_efficiency_does_not_mature_skill_or_option_via_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("mature_skill:true", "mature_option:true"))
    )
    assert CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH in run.blocked_reasons


def test_cost1_efficiency_does_not_claim_automation_via_metadata() -> None:
    run = build_cost_comparison_frame(
        replace(material_vs_energy_tradeoff_fixture(), metadata_refs=("automation_claim:true",))
    )
    assert CostBlockReason.PROVIDER_EFFICIENCY_AS_TRUTH in run.blocked_reasons
