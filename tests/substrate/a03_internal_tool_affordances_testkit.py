from __future__ import annotations

from dataclasses import dataclass

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01CanonicalOntologyResult,
)
from substrate.a02_capability_gap_detection import (
    A02CapabilityGapResult,
)
from substrate.a03_internal_tool_affordances import (
    A03InternalOperationCandidate,
    A03InternalOperationCandidateSet,
    A03InternalToolAffordanceResult,
    A03InvocationContract,
    A03ObservationHook,
    A03OperationBoundaryKind,
    A03OperationSourceProfile,
    A03ToolClass,
    A03ToolCostProfile,
    A03ToolFailureSignature,
    A03ToolInputSpec,
    A03ToolOutputSpec,
    A03ToolSideEffectProfile,
    build_a03_internal_tool_affordances,
)


@dataclass(frozen=True, slots=True)
class A03HarnessCase:
    case_id: str
    a01_result: A01CanonicalOntologyResult | None
    a02_result: A02CapabilityGapResult | None
    operation_candidate_set: A03InternalOperationCandidateSet | None
    tool_affordance_enabled: bool = True


@dataclass(frozen=True, slots=True)
class A03HarnessRun:
    a03_result: A03InternalToolAffordanceResult


def a03_operation_candidate(
    *,
    operation_ref: str,
    local_label: str,
    tool_class: A03ToolClass,
    boundary_kind: A03OperationBoundaryKind,
    accepted_input_types: tuple[A03ToolInputSpec, ...],
    produced_output_types: tuple[A03ToolOutputSpec, ...],
    required_context: tuple[str, ...],
    preconditions: tuple[str, ...],
    abort_conditions: tuple[str, ...],
    completion_criteria: tuple[str, ...],
    observation_hooks: tuple[A03ObservationHook, ...],
    failure_signatures: tuple[A03ToolFailureSignature, ...],
    canonical_tool_id_hint: str | None = None,
    source_module: str = "tests.a03",
    source_surface: str = "tests.surface",
    provenance_refs: tuple[str, ...] = ("tests.a03",),
    source_lineage: tuple[str, ...] = ("tests.a03",),
    latency_class: str = "bounded_tick",
    cost_band: str = "low",
    side_effect_refs: tuple[str, ...] = (),
    risk_band: str = "bounded",
    controllability_hint: float = 0.8,
    reliability_hint: float = 0.8,
    reuse_scope: str = "frontier_narrow",
    validity_hint: str = "valid",
    legacy_module_only: bool = False,
) -> A03InternalOperationCandidate:
    return A03InternalOperationCandidate(
        operation_ref=operation_ref,
        local_label=local_label,
        tool_class=tool_class,
        source_profile=A03OperationSourceProfile(
            source_module=source_module,
            source_surface=source_surface,
            provenance_refs=provenance_refs,
            source_lineage=source_lineage,
        ),
        boundary_kind=boundary_kind,
        invocation_contract=A03InvocationContract(
            accepted_input_types=accepted_input_types,
            produced_output_types=produced_output_types,
            required_context=required_context,
            preconditions=preconditions,
            abort_conditions=abort_conditions,
            completion_criteria=completion_criteria,
        ),
        observation_hooks=observation_hooks,
        failure_signatures=failure_signatures,
        cost_profile=A03ToolCostProfile(latency_class=latency_class, cost_band=cost_band),
        side_effect_profile=A03ToolSideEffectProfile(
            side_effect_refs=side_effect_refs,
            risk_band=risk_band,
        ),
        controllability_hint=controllability_hint,
        reliability_hint=reliability_hint,
        reuse_scope=reuse_scope,
        required_context=required_context,
        canonical_tool_id_hint=canonical_tool_id_hint,
        validity_hint=validity_hint,
        legacy_module_only=legacy_module_only,
    )


def a03_candidate_set(
    *,
    set_id: str,
    candidates: tuple[A03InternalOperationCandidate, ...],
    reason: str,
    source_lineage: tuple[str, ...] | None = None,
    active_mode: str = "continue_stream",
    resource_pressure: bool = False,
    available_observation_channels: tuple[str, ...] = (),
) -> A03InternalOperationCandidateSet:
    return A03InternalOperationCandidateSet(
        candidate_set_id=set_id,
        candidates=candidates,
        source_lineage=source_lineage if source_lineage is not None else ("tests.a03", set_id),
        active_mode=active_mode,
        resource_pressure=resource_pressure,
        available_observation_channels=available_observation_channels,
        reason=reason,
    )


def build_a03_harness_case(case: A03HarnessCase) -> A03HarnessRun:
    result = build_a03_internal_tool_affordances(
        tick_id=f"tests.a03:{case.case_id}",
        tick_index=1,
        operation_candidate_set=case.operation_candidate_set,
        a01_result=case.a01_result,
        a02_result=case.a02_result,
        tool_affordance_enabled=case.tool_affordance_enabled,
    )
    return A03HarnessRun(a03_result=result)
