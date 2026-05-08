from __future__ import annotations

from dataclasses import dataclass

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01CanonicalOntologyResult,
    A01ControllabilityClass,
)
from substrate.a02_capability_gap_detection import (
    A02CapabilityGapInput,
    A02CapabilityGapResult,
    A02ControllabilityStatus,
    A02DemandClass,
    A02DemandLegitimacyStatus,
    A02DemandPacket,
    A02DemandSet,
    build_a02_capability_gap_detection,
)
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    A01HarnessCase,
    a01_candidate,
    a01_candidate_set,
    build_a01_harness_case,
)


@dataclass(frozen=True, slots=True)
class A02HarnessCase:
    case_id: str
    a01_result: A01CanonicalOntologyResult
    demand_set: A02DemandSet | None
    source_lineage: tuple[str, ...] = ("tests.a02",)
    ownership_boundary_basis: tuple[str, ...] = ()
    composition_enabled: bool = True
    gap_detection_enabled: bool = True


@dataclass(frozen=True, slots=True)
class A02HarnessRun:
    a02_result: A02CapabilityGapResult


def a02_demand(
    *,
    demand_id: str,
    demanded_change_class: A02DemandClass,
    demanded_scope: tuple[str, ...],
    target_channels: tuple[str, ...],
    source_kind: str = "tests",
    source_ref: str = "tests.a02",
    urgency: str = "normal",
    severity: int = 1,
    allowed_latency: str = "bounded_tick",
    legitimacy_status: A02DemandLegitimacyStatus = A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
    required_controllability: A02ControllabilityStatus = A02ControllabilityStatus.CONTROLLABLE_CURRENTLY,
    world_side_requirement: str = "optional",
    provenance: tuple[str, ...] = ("tests.a02",),
    planner_deadend_signal: bool = False,
    low_confidence_signal: bool = False,
) -> A02DemandPacket:
    return A02DemandPacket(
        demand_id=demand_id,
        demanded_change_class=demanded_change_class,
        demanded_scope=demanded_scope,
        target_channels=target_channels,
        source_kind=source_kind,
        source_ref=source_ref,
        urgency=urgency,
        severity=severity,
        allowed_latency=allowed_latency,
        legitimacy_status=legitimacy_status,
        required_controllability=required_controllability,
        world_side_requirement=world_side_requirement,
        provenance=provenance,
        planner_deadend_signal=planner_deadend_signal,
        low_confidence_signal=low_confidence_signal,
    )


def a02_demand_set(
    *,
    set_id: str,
    demands: tuple[A02DemandPacket, ...],
    reason: str,
    source_lineage: tuple[str, ...] | None = None,
) -> A02DemandSet:
    return A02DemandSet(
        demand_set_id=set_id,
        demands=demands,
        source_lineage=source_lineage if source_lineage is not None else ("tests.a02", set_id),
        reason=reason,
    )


def build_a02_harness_case(case: A02HarnessCase) -> A02HarnessRun:
    result = build_a02_capability_gap_detection(
        tick_id=f"tests.a02:{case.case_id}",
        tick_index=1,
        capability_input=A02CapabilityGapInput(
            demand_set=case.demand_set,
            source_lineage=case.source_lineage,
            ownership_boundary_basis=case.ownership_boundary_basis,
            composition_enabled=case.composition_enabled,
        ),
        a01_result=case.a01_result,
        gap_detection_enabled=case.gap_detection_enabled,
    )
    return A02HarnessRun(a02_result=result)


def build_a02_a01_seed(case_id: str) -> A01CanonicalOntologyResult:
    return build_a01_harness_case(
        A01HarnessCase(
            case_id=f"{case_id}:a01-seed",
            raw_candidate_set=a01_candidate_set(
                set_id=f"{case_id}:a01:set",
                reason="a02 harness seed",
                candidates=(
                    a01_candidate(
                        candidate_id=f"{case_id}:reg",
                        local_label="pause_and_recover",
                        affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                        aliases=(),
                        provenance=f"tests.a02:{case_id}:reg",
                        preconditions=("energy_low",),
                        primary_outcomes=("reduce_overload",),
                        target_channels=("internal",),
                        controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                        controllability_confidence=0.8,
                        observation_signals=("calmer_state",),
                        observation_verification_required=True,
                        canonical_id_hint=f"a01:{case_id}:pause_and_recover",
                    ),
                ),
            ),
        )
    ).a01_result
