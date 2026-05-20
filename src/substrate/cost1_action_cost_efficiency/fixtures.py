from __future__ import annotations

from .models import (
    ActionCostDimension,
    ActionCostVector,
    ActionCostVectorInput,
    CostComparisonInput,
    CostDimension,
    CostDimensionStatus,
    CostEvidenceKind,
    CostPreferenceDirection,
)
from .policy import build_action_cost_vector, build_declared_observed_cost_delta, build_throughput_support_frame


def material_vs_energy_tradeoff_fixture() -> CostComparisonInput:
    a = build_action_cost_vector(
        ActionCostVectorInput(
            vector_id="cost:v:a",
            candidate_ref="candidate:a",
            candidate_kind="micro_operation",
            micro_operation_refs=("micro:inspect:a",),
            current_pressure_context_refs=("pressure:resource_shortage",),
            dimensions=(
                _dim(CostDimension.MATERIAL, 2.0, "u_material", CostEvidenceKind.OBSERVED, ("src:obs:mat:a",), effect_refs=("effect:mat:a",), preference=CostPreferenceDirection.LOWER_IS_BETTER),
                _dim(CostDimension.ENERGY, 8.0, "u_energy", CostEvidenceKind.OBSERVED, ("src:obs:energy:a",), effect_refs=("effect:energy:a",), preference=CostPreferenceDirection.LOWER_IS_BETTER),
            ),
        )
    ).vectors[0]
    b = build_action_cost_vector(
        ActionCostVectorInput(
            vector_id="cost:v:b",
            candidate_ref="candidate:b",
            candidate_kind="micro_operation",
            micro_operation_refs=("micro:inspect:b",),
            current_pressure_context_refs=("pressure:resource_shortage",),
            dimensions=(
                _dim(CostDimension.MATERIAL, 7.0, "u_material", CostEvidenceKind.OBSERVED, ("src:obs:mat:b",), effect_refs=("effect:mat:b",), preference=CostPreferenceDirection.LOWER_IS_BETTER),
                _dim(CostDimension.ENERGY, 3.0, "u_energy", CostEvidenceKind.OBSERVED, ("src:obs:energy:b",), effect_refs=("effect:energy:b",), preference=CostPreferenceDirection.LOWER_IS_BETTER),
            ),
        )
    ).vectors[0]
    return CostComparisonInput(
        comparison_id="cost:cmp:material_vs_energy",
        vectors=(a, b),
        context_refs=("ctx:normal",),
        pressure_refs=("pressure:resource_shortage",),
    )


def provider_declared_cost_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:provider_declared",
        candidate_ref="candidate:provider",
        candidate_kind="provider_hint",
        current_pressure_context_refs=("pressure:time_budget",),
        dimensions=(
            _dim(CostDimension.TIME, 5.0, "s", CostEvidenceKind.PROVIDER_DECLARED, ("provider:manual:1",), notes=("provider_declared",)),
            _dim(CostDimension.ENERGY, 2.0, "u_energy", CostEvidenceKind.PROVIDER_DECLARED, ("provider:manual:1",), notes=("provider_declared",)),
        ),
    )


def observed_cost_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:observed",
        candidate_ref="candidate:observed",
        candidate_kind="micro_operation",
        micro_operation_refs=("micro:store:1",),
        current_pressure_context_refs=("pressure:inventory",),
        dimensions=(
            _dim(CostDimension.MATERIAL, 3.0, "u_material", CostEvidenceKind.OBSERVED, ("src:obs:material",), effect_refs=("effect:inventory_delta",)),
            _dim(CostDimension.TIME, 12.0, "s", CostEvidenceKind.OBSERVED, ("src:obs:time",), observation_refs=("obs:tick:12",)),
        ),
    )


def unknown_dimension_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:unknown",
        candidate_ref="candidate:unknown",
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:repair",),
        dimensions=(
            _dim(CostDimension.TOOL_WEAR, None, "u_wear", CostEvidenceKind.UNKNOWN, ("src:unknown:wear",), status=CostDimensionStatus.UNKNOWN),
            _dim(CostDimension.ENERGY, 4.0, "u_energy", CostEvidenceKind.ESTIMATED, ("src:est:energy",)),
        ),
    )


def scalar_hiding_blocked_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:scalar_only",
        candidate_ref="candidate:scalar",
        candidate_kind="route",
        current_pressure_context_refs=("pressure:throughput",),
        dimensions=(),
        scalar_score_ref="score:0.75",
    )


def risk_vs_material_fixture() -> CostComparisonInput:
    low_material = build_action_cost_vector(
        ActionCostVectorInput(
            vector_id="cost:v:risk:a",
            candidate_ref="candidate:risk_a",
            candidate_kind="micro_operation",
            current_pressure_context_refs=("pressure:survival",),
            dimensions=(
                _dim(CostDimension.MATERIAL, 1.0, "u_material", CostEvidenceKind.OBSERVED, ("src:mat:a",), effect_refs=("effect:mat:a",)),
                _dim(CostDimension.RISK, 9.0, "risk_idx", CostEvidenceKind.ESTIMATED, ("src:risk:a",), notes=("risk:high",)),
            ),
        )
    ).vectors[0]
    safer = build_action_cost_vector(
        ActionCostVectorInput(
            vector_id="cost:v:risk:b",
            candidate_ref="candidate:risk_b",
            candidate_kind="micro_operation",
            current_pressure_context_refs=("pressure:survival",),
            dimensions=(
                _dim(CostDimension.MATERIAL, 4.0, "u_material", CostEvidenceKind.OBSERVED, ("src:mat:b",), effect_refs=("effect:mat:b",)),
                _dim(CostDimension.RISK, 2.0, "risk_idx", CostEvidenceKind.ESTIMATED, ("src:risk:b",), notes=("risk:lower",)),
            ),
        )
    ).vectors[0]
    return CostComparisonInput(
        comparison_id="cost:cmp:risk_vs_material",
        vectors=(low_material, safer),
        context_refs=("ctx:hazard_zone",),
        pressure_refs=("pressure:survival",),
    )


def setup_time_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:setup",
        candidate_ref="candidate:setup",
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:delivery_deadline",),
        dimensions=(
            _dim(CostDimension.ENERGY, 2.0, "u_energy", CostEvidenceKind.OBSERVED, ("src:energy",), effect_refs=("effect:energy",)),
            _dim(CostDimension.SETUP, 15.0, "min", CostEvidenceKind.ESTIMATED, ("src:setup",), notes=("setup:heavy",)),
        ),
    )


def tool_wear_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:tool_wear",
        candidate_ref="candidate:wear",
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:tool_budget",),
        dimensions=(
            _dim(CostDimension.TOOL_WEAR, 6.0, "wear_idx", CostEvidenceKind.ESTIMATED, ("src:wear",), notes=("tool_wear:high",)),
        ),
    )


def station_occupation_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:station_occ",
        candidate_ref="candidate:station",
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:queue",),
        dimensions=(
            _dim(CostDimension.STATION_OCCUPATION, 20.0, "s", CostEvidenceKind.OBSERVED, ("src:station",), effect_refs=("effect:station_busy",), notes=("station:occupied",)),
        ),
    )


def throughput_single_run_fixture() -> ThroughputSupportFrame:
    return build_throughput_support_frame(
        candidate_ref="candidate:throughput_single",
        observation_trace_refs=("trace:1",),
        source_refs=("src:trace:single",),
    )


def throughput_repeated_fixture() -> ThroughputSupportFrame:
    return build_throughput_support_frame(
        candidate_ref="candidate:throughput_repeated",
        observation_trace_refs=("trace:1", "trace:2", "trace:3", "trace:4"),
        source_refs=("src:trace:repeated",),
    )


def declared_observed_mismatch_fixture() -> tuple[ActionCostVector, DeclaredObservedCostDelta]:
    vector = build_action_cost_vector(observed_cost_fixture()).vectors[0]
    delta = build_declared_observed_cost_delta(
        delta_id="delta:energy:1",
        candidate_ref=vector.candidate_ref,
        dimension=CostDimension.ENERGY,
        declared_cost_ref="declared:energy:2",
        observed_cost_ref="observed:energy:7",
        delta_direction="higher_than_declared",
        mismatch_residue_refs=("residue:cost_mismatch:energy",),
        source_refs=("src:delta",),
    )
    return vector, delta


def cost_comparison_no_action_fixture() -> CostComparisonInput:
    return material_vs_energy_tradeoff_fixture()


def hidden_backend_cost_blocked_fixture() -> ActionCostVectorInput:
    return ActionCostVectorInput(
        vector_id="cost:v:hidden",
        candidate_ref="candidate:hidden",
        candidate_kind="provider_hint",
        current_pressure_context_refs=("pressure:unknown",),
        dimensions=(
            _dim(CostDimension.MATERIAL, 1.0, "u_material", CostEvidenceKind.ESTIMATED, ("src:hidden_backend:table",), notes=("backend_cost",)),
        ),
    )


def cost_hint_permission_blocked_fixture() -> CostComparisonInput:
    vector = build_action_cost_vector(provider_declared_cost_fixture()).vectors[0]
    return CostComparisonInput(
        comparison_id="cost:cmp:permission_blocked",
        vectors=(vector,),
        context_refs=("ctx:test",),
        pressure_refs=("pressure:time_budget",),
        metadata_refs=("permission:authorized", "provider_efficiency_truth"),
    )


def value_assignment_blocked_fixture() -> CostComparisonInput:
    vector = build_action_cost_vector(observed_cost_fixture()).vectors[0]
    return CostComparisonInput(
        comparison_id="cost:cmp:value_blocked",
        vectors=(vector,),
        context_refs=("ctx:test",),
        pressure_refs=("pressure:inventory",),
        value_assignment_attempt=True,
        metadata_refs=("intrinsic_value:cheap",),
    )


def _dim(
    dimension: CostDimension,
    amount_value: float | None,
    unit: str,
    evidence_kind: CostEvidenceKind,
    source_refs: tuple[str, ...],
    *,
    effect_refs: tuple[str, ...] = (),
    observation_refs: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
    status: CostDimensionStatus = CostDimensionStatus.PRESENT,
    preference: CostPreferenceDirection = CostPreferenceDirection.LOWER_IS_BETTER,
) -> ActionCostDimension:
    return ActionCostDimension(
        dimension=dimension,
        amount_value=amount_value,
        unit=unit,
        evidence_kind=evidence_kind,
        source_refs=source_refs,
        effect_refs=effect_refs,
        observation_refs=observation_refs,
        status=status,
        preference_direction=preference,
        notes=notes,
    )
