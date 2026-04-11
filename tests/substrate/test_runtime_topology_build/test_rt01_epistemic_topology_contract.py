from __future__ import annotations

from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    derive_runtime_dispatch_contract_view,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickInput


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
    )


def test_runtime_topology_contract_reflects_epistemic_rt01_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert graph.runtime_order[0] == "EPISTEMICS"
    assert "rt01.epistemic_admission_checkpoint" in graph.mandatory_checkpoint_ids
    assert "epistemics.grounded_unit" in graph.source_of_truth_surfaces
    assert "epistemics.downstream_allowance" in graph.source_of_truth_surfaces

    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-epistemic-contract"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    assert "rt01.epistemic_admission_checkpoint" in view.mandatory_checkpoints
    assert view.epistemic_status is not None
    assert view.epistemic_confidence is not None
    assert view.epistemic_source_class is not None
    assert view.epistemic_modality is not None
    assert view.epistemic_claim_strength is not None
    assert view.regulation_pressure_level is not None
    assert view.regulation_escalation_stage is not None
    assert view.regulation_override_scope is not None
