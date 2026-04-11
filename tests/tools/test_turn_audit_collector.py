from __future__ import annotations

import json

from tools.turn_audit import (
    UNRESOLVED_TOKEN,
    build_turn_audit_artifact,
    collect_turn_audit_artifact,
    collect_turn_audit_artifact_to_disk,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    dispatch_runtime_tick,
)
from substrate.runtime_topology.models import RuntimeRegulationSharedDomainInput
from substrate.subject_tick import SubjectTickInput


REQUIRED_TOP_LEVEL_SECTIONS = {
    "artifact_metadata",
    "input_summary",
    "route_and_scope",
    "phase_surfaces",
    "checkpoints",
    "restrictions_and_forbidden_shortcuts",
    "uncertainty_and_fallbacks",
    "final_outcome",
    "verdicts",
    "unresolved",
}

VERDICT_KEYS = (
    "mechanistic_integrity",
    "claim_honesty",
    "path_affecting_sensitivity",
    "overall",
)
ALLOWED_VERDICT_STATUSES = {"PASS", "FAIL", "PARTIAL", "UNRESOLVED"}


def test_collector_writes_bounded_clean_production_artifact(tmp_path) -> None:
    output_path, artifact = collect_turn_audit_artifact_to_disk(
        case_id="collector-mvp-clean",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        output_path=tmp_path / "collector-mvp-clean.json",
    )
    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert REQUIRED_TOP_LEVEL_SECTIONS.issubset(set(loaded))
    assert loaded["route_and_scope"]["accepted"] is True
    assert loaded["route_and_scope"]["lawful_production_route"] is True
    assert loaded["route_and_scope"]["route_class"] == "production_contour"
    assert loaded["checkpoints"]["epistemic_admission_checkpoint"] != UNRESOLVED_TOKEN
    assert loaded["phase_surfaces"]["epistemics"]["epistemic_status"] != UNRESOLVED_TOKEN
    assert loaded["phase_surfaces"]["epistemics"]["epistemic_claim_strength"] != UNRESOLVED_TOKEN
    assert "epistemic_allowance_restrictions" in loaded["restrictions_and_forbidden_shortcuts"]
    assert "active_execution_mode" in loaded["final_outcome"]
    assert loaded["final_outcome"]["final_execution_outcome"] in {
        "continue",
        "repair",
        "revalidate",
        "halt",
    }

    for verdict_key in VERDICT_KEYS:
        assert verdict_key in loaded["verdicts"]
        assert loaded["verdicts"][verdict_key]["status"] in ALLOWED_VERDICT_STATUSES
    assert isinstance(loaded["unresolved"], list)
    assert artifact["artifact_metadata"]["seam_phase"] == "RT01"


def test_collector_preserves_path_affecting_evidence_on_triggered_turn() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-mvp-path-affecting",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context_flags={"require_s02_boundary_consumer": True},
    )
    assert artifact["route_and_scope"]["accepted"] is True

    detours = artifact["checkpoints"]["enforced_detour_checkpoint_ids"]
    blocked = artifact["checkpoints"]["blocked_checkpoint_ids"]
    assert "rt01.s02_prediction_boundary_checkpoint" in detours

    status = artifact["verdicts"]["path_affecting_sensitivity"]["status"]
    assert status in ALLOWED_VERDICT_STATUSES
    if status == "PASS":
        assert bool(detours or blocked) is True

    assert isinstance(
        artifact["restrictions_and_forbidden_shortcuts"]["phase_restrictions"]["s02"],
        list,
    )
    assert artifact["checkpoints"]["epistemic_admission_checkpoint"] != UNRESOLVED_TOKEN


def test_collector_materializes_regulation_surfaces_v2() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-mvp-regulation-v2",
        energy=64.0,
        cognitive=46.0,
        safety=78.0,
        unresolved_preference=False,
    )
    regulation = artifact["phase_surfaces"]["regulation"]
    assert "regulation_pressure_level" in regulation
    assert "regulation_escalation_stage" in regulation
    assert "regulation_override_scope" in regulation
    assert "regulation_no_strong_override_claim" in regulation
    assert "regulation_gate_accepted" in regulation
    assert "regulation_source_state_ref" in regulation
    assert artifact["uncertainty_and_fallbacks"]["regulation_no_strong_override_claim"] in {
        True,
        False,
        UNRESOLVED_TOKEN,
    }
    assert "regulation_gate_restrictions" in artifact["restrictions_and_forbidden_shortcuts"]


def _collect_regulation_case_artifact(
    *,
    case_id: str,
    shared_domain_input: RuntimeRegulationSharedDomainInput,
) -> dict[str, object]:
    dispatch_result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=SubjectTickInput(
                case_id=case_id,
                energy=66.0,
                cognitive=44.0,
                safety=74.0,
                unresolved_preference=False,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            regulation_shared_domain_input=shared_domain_input,
        )
    )
    return build_turn_audit_artifact(result=dispatch_result)


def test_collector_materializes_regulation_observability_fields_for_shared_domain_pair() -> None:
    high_override = _collect_regulation_case_artifact(
        case_id="collector-regulation-observability-high",
        shared_domain_input=RuntimeRegulationSharedDomainInput(
            pressure_level=0.98,
            escalation_stage="critical",
            override_scope="emergency",
            no_strong_override_claim=False,
            gate_accepted=True,
            source_state_ref="tests.regulation.high_override",
        ),
    )
    guard = _collect_regulation_case_artifact(
        case_id="collector-regulation-observability-guard",
        shared_domain_input=RuntimeRegulationSharedDomainInput(
            pressure_level=0.92,
            escalation_stage="critical",
            override_scope="emergency",
            no_strong_override_claim=True,
            gate_accepted=True,
            source_state_ref="tests.regulation.no_strong_override",
        ),
    )

    expected_keys = {
        "effective_regulation_shared_domain_source_surface",
        "effective_shared_runtime_domain_checkpoint_status",
        "effective_shared_runtime_domain_checkpoint_applied_action",
        "effective_regulation_path_consequence",
        "effective_regulation_causal_reason",
        "effective_regulation_influence_source",
        "effective_regulation_restriction_source",
    }
    high_regulation = high_override["phase_surfaces"]["regulation"]
    guard_regulation = guard["phase_surfaces"]["regulation"]
    assert expected_keys.issubset(set(high_regulation))
    assert expected_keys.issubset(set(guard_regulation))
    assert high_regulation["effective_regulation_influence_source"] in {
        "local_regulation_surface",
        "shared_runtime_domain_precedence",
        "both",
        UNRESOLVED_TOKEN,
    }
    assert guard_regulation["effective_regulation_influence_source"] in {
        "local_regulation_surface",
        "shared_runtime_domain_precedence",
        "both",
        UNRESOLVED_TOKEN,
    }
    assert (
        high_regulation["effective_shared_runtime_domain_checkpoint_status"]
        != guard_regulation["effective_shared_runtime_domain_checkpoint_status"]
        or high_regulation["effective_shared_runtime_domain_checkpoint_applied_action"]
        != guard_regulation["effective_shared_runtime_domain_checkpoint_applied_action"]
    )
    assert high_regulation["effective_regulation_path_consequence"] != UNRESOLVED_TOKEN
    assert guard_regulation["effective_regulation_path_consequence"] != UNRESOLVED_TOKEN
    assert high_override["checkpoints"]["shared_runtime_domain_checkpoint"] != UNRESOLVED_TOKEN
    assert guard["checkpoints"]["shared_runtime_domain_checkpoint"] != UNRESOLVED_TOKEN


def test_collector_emits_unresolved_for_pre_execution_rejection() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-mvp-preexec-reject",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        route_class="helper_path",
    )
    assert artifact["route_and_scope"]["accepted"] is False
    assert artifact["route_and_scope"]["route_class"] == "helper_path"
    assert artifact["phase_surfaces"]["downstream_obedience"]["status"] == UNRESOLVED_TOKEN
    assert artifact["phase_surfaces"]["epistemics"]["status"] == UNRESOLVED_TOKEN
    assert artifact["checkpoints"]["downstream_obedience_checkpoint"] == UNRESOLVED_TOKEN
    assert artifact["checkpoints"]["epistemic_admission_checkpoint"] == UNRESOLVED_TOKEN
    assert artifact["restrictions_and_forbidden_shortcuts"]["regulation_gate_restrictions"] == UNRESOLVED_TOKEN

    unresolved_codes = {entry["code"] for entry in artifact["unresolved"]}
    assert "PRE_EXECUTION_DISPATCH_REJECTION" in unresolved_codes
    assert "REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" in unresolved_codes

    for entry in artifact["unresolved"]:
        assert set(entry) == {
            "code",
            "message",
            "blocking_surface",
            "severity",
            "impacted_sections",
            "requires_non_v1_extension",
        }
