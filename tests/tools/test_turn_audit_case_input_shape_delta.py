from __future__ import annotations

import json
from pathlib import Path

from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.runtime_topology.models import (
    RuntimeEpistemicCaseInput,
    RuntimeRegulationSharedDomainInput,
)
from substrate.subject_tick import SubjectTickInput
from tools.turn_audit_battery import run_turn_audit_battery


def _tick_input(case_id: str, *, unresolved_preference: bool = False) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=unresolved_preference,
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_epistemic_input_shape_can_materialize_non_trivial_rt01_epistemic_path() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("shape-delta-epistemic-unknown", unresolved_preference=True),
            epistemic_case_input=RuntimeEpistemicCaseInput(
                content="ungrounded claim for epistemic unknown case",
                source_id="tests.case_shape.epistemic.unknown",
                source_class="unknown",
                modality="unspecified",
                confidence_hint="low",
                claim_key="tests_shape_delta_epistemic_unknown",
                claim_polarity="affirm",
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.decision.accepted is True
    assert result.subject_tick_result is not None
    state = result.subject_tick_result.state
    assert state.epistemic_status == "unknown"
    assert state.epistemic_should_abstain is True
    assert "unknown_or_conflict" in state.epistemic_allowance_restrictions
    checkpoint = next(
        item
        for item in state.execution_checkpoints
        if item.checkpoint_id == "rt01.epistemic_admission_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"


def test_regulation_shared_domain_prep_can_materialize_in_contour_regulation_path() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("shape-delta-regulation-shared-domain"),
            regulation_shared_domain_input=RuntimeRegulationSharedDomainInput(
                pressure_level=0.98,
                escalation_stage="critical",
                override_scope="emergency",
                no_strong_override_claim=False,
                gate_accepted=True,
                source_state_ref="tests.shape_delta.shared_regulation.high_override",
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.decision.accepted is True
    assert result.subject_tick_result is not None
    state = result.subject_tick_result.state
    assert state.downstream_obedience_source_of_truth_surface == "runtime_state.domains"
    shared_checkpoint = next(
        item
        for item in state.execution_checkpoints
        if item.checkpoint_id == "rt01.shared_runtime_domain_checkpoint"
    )
    assert shared_checkpoint.status.value == "enforced_detour"
    assert "shared_regulation.high_override_scope" in shared_checkpoint.reason


def test_updated_battery_registry_cases_materialize_honest_epistemic_and_regulation_paths(
    tmp_path,
) -> None:
    selected = [
        "epistemic_unknown_abstain_detour",
        "epistemic_observation_requirement_block",
        "epistemic_conflict_no_laundering",
        "regulation_high_override_scope_detour",
        "regulation_no_strong_override_claim_guard",
    ]
    run = run_turn_audit_battery(
        output_dir=tmp_path / "battery-shape-delta",
        case_filter=selected,
    )
    index = _load_json(Path(run["index_json_path"]))
    by_case = {item["case_id"]: item for item in index["cases"]}

    assert set(by_case) == set(selected)
    assert by_case["epistemic_unknown_abstain_detour"]["failed_generation"] is False
    assert by_case["epistemic_observation_requirement_block"]["failed_generation"] is False
    assert by_case["epistemic_conflict_no_laundering"]["failed_generation"] is False
    assert by_case["regulation_high_override_scope_detour"]["failed_generation"] is False
    assert by_case["regulation_no_strong_override_claim_guard"]["failed_generation"] is False

    unknown_artifact = _load_json(Path(by_case["epistemic_unknown_abstain_detour"]["artifact_path"]))
    unknown_epi = unknown_artifact["phase_surfaces"]["epistemics"]
    assert unknown_epi["epistemic_status"] == "unknown"
    assert unknown_epi["epistemic_should_abstain"] is True

    observation_artifact = _load_json(
        Path(by_case["epistemic_observation_requirement_block"]["artifact_path"])
    )
    observation_epi = observation_artifact["phase_surfaces"]["epistemics"]
    assert "observation_required" in observation_epi["epistemic_allowance_restrictions"]
    assert observation_epi["epistemic_should_abstain"] is True

    conflict_artifact = _load_json(Path(by_case["epistemic_conflict_no_laundering"]["artifact_path"]))
    conflict_epi = conflict_artifact["phase_surfaces"]["epistemics"]
    assert conflict_epi["epistemic_status"] == "conflict"
    assert conflict_epi["epistemic_conflict_reason"] not in {None, ""}
    assert conflict_epi["epistemic_should_abstain"] is True

    high_override_artifact = _load_json(
        Path(by_case["regulation_high_override_scope_detour"]["artifact_path"])
    )
    high_shared = high_override_artifact["checkpoints"]["shared_runtime_domain_checkpoint"]
    assert high_shared["status"] == "enforced_detour"
    assert "shared_regulation.high_override_scope" in high_shared["reason"]

    no_strong_override_artifact = _load_json(
        Path(by_case["regulation_no_strong_override_claim_guard"]["artifact_path"])
    )
    guard_shared = no_strong_override_artifact["checkpoints"]["shared_runtime_domain_checkpoint"]
    assert guard_shared["status"] == "allowed"
