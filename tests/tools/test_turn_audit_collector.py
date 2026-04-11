from __future__ import annotations

import json

from tools.turn_audit import (
    UNRESOLVED_TOKEN,
    _build_trigger_inventory,
    _cause_source_covered_by_evidence,
    _classify_shared_regulation_cause,
    _collect_causal_trace,
    build_turn_audit_artifact,
    collect_turn_audit_artifact,
    collect_turn_audit_artifact_to_disk,
    main as turn_audit_main,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    dispatch_runtime_tick,
)
from substrate.runtime_topology.models import RuntimeEpistemicCaseInput, RuntimeRegulationSharedDomainInput
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
    "causal_trace",
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
    assert "entries" in loaded["causal_trace"]
    assert "trigger_inventory" in loaded["causal_trace"]
    assert loaded["causal_trace"]["ownership_status"] in {"resolved", "mixed", "unresolved"}

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
    assert artifact["causal_trace"]["trigger_inventory"]
    entries = artifact["causal_trace"]["entries"]
    assert isinstance(entries, list)
    assert any(isinstance(row, dict) and "cause_family" in row for row in entries)


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
    assert "t02_restrictions" in artifact["restrictions_and_forbidden_shortcuts"]

    unresolved_codes = {entry["code"] for entry in artifact["unresolved"]}
    regulation_gate_restrictions = artifact["restrictions_and_forbidden_shortcuts"]["regulation_gate_restrictions"]
    t02_restrictions = artifact["restrictions_and_forbidden_shortcuts"]["t02_restrictions"]
    if regulation_gate_restrictions == UNRESOLVED_TOKEN:
        assert "REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" in unresolved_codes
    else:
        assert isinstance(regulation_gate_restrictions, list)
        assert "REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" not in unresolved_codes
    if t02_restrictions == UNRESOLVED_TOKEN:
        assert "T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" in unresolved_codes
    else:
        assert isinstance(t02_restrictions, list)
        assert "T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" not in unresolved_codes


def test_causal_trace_observability_only_is_not_load_bearing() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-causal-observability-only",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    perturb = json.loads(json.dumps(artifact))
    perturb["phase_surfaces"]["regulation"]["effective_regulation_causal_reason"] = (
        "cosmetic_observability_note_only"
    )
    perturb["phase_surfaces"]["regulation"]["effective_regulation_influence_source"] = (
        "shared_runtime_domain_precedence"
    )
    perturb["final_outcome"]["final_execution_outcome"] = "continue"
    perturb["final_outcome"]["repair_needed"] = False
    perturb["final_outcome"]["revalidation_needed"] = False
    perturb["checkpoints"]["blocked_checkpoint_ids"] = []
    perturb["checkpoints"]["enforced_detour_checkpoint_ids"] = []
    observed = perturb["checkpoints"].get("observed_checkpoint_results", [])
    if isinstance(observed, list):
        for row in observed:
            if isinstance(row, dict):
                row["status"] = "passed"
                row["applied_action"] = "continue"

    causal_trace = _collect_causal_trace(
        route_and_scope=perturb["route_and_scope"],
        phase_surfaces=perturb["phase_surfaces"],
        checkpoints=perturb["checkpoints"],
        restrictions=perturb["restrictions_and_forbidden_shortcuts"],
        uncertainty=perturb["uncertainty_and_fallbacks"],
        final_outcome=perturb["final_outcome"],
        input_summary=perturb["input_summary"],
    )
    entries = causal_trace["entries"]
    assert any(
        isinstance(row, dict)
        and row.get("cause_family") == "observability_only_difference"
        and row.get("load_bearing") is False
        for row in entries
    )
    assert not any(isinstance(row, dict) and row.get("load_bearing") is True for row in entries)


def test_causal_trace_promotes_shared_runtime_override_to_load_bearing() -> None:
    artifact = _collect_regulation_case_artifact(
        case_id="collector-causal-shared-runtime-load-bearing",
        shared_domain_input=RuntimeRegulationSharedDomainInput(
            pressure_level=0.98,
            escalation_stage="critical",
            override_scope="emergency",
            no_strong_override_claim=False,
            gate_accepted=True,
            source_state_ref="tests.regulation.override.load_bearing",
        ),
    )
    entries = artifact["causal_trace"]["entries"]
    assert any(
        isinstance(row, dict)
        and row.get("event_ref") == "rt01.shared_runtime_domain_checkpoint"
        and row.get("load_bearing") is True
        and row.get("cause_family") in {"shared_runtime_regulation", "mixed"}
        for row in entries
    )


def test_causal_trace_mixed_or_unresolved_ownership_is_explicit() -> None:
    artifact = _collect_regulation_case_artifact(
        case_id="collector-causal-mixed-unresolved",
        shared_domain_input=RuntimeRegulationSharedDomainInput(
            pressure_level=0.96,
            escalation_stage="critical",
            override_scope="emergency",
            no_strong_override_claim=False,
            gate_accepted=True,
            source_state_ref="tests.regulation.mixed_unresolved",
        ),
    )
    perturb = json.loads(json.dumps(artifact))
    perturb["phase_surfaces"]["regulation"]["effective_regulation_influence_source"] = UNRESOLVED_TOKEN
    perturb["restrictions_and_forbidden_shortcuts"]["regulation_gate_restrictions"] = UNRESOLVED_TOKEN

    causal_trace = _collect_causal_trace(
        route_and_scope=perturb["route_and_scope"],
        phase_surfaces=perturb["phase_surfaces"],
        checkpoints=perturb["checkpoints"],
        restrictions=perturb["restrictions_and_forbidden_shortcuts"],
        uncertainty=perturb["uncertainty_and_fallbacks"],
        final_outcome=perturb["final_outcome"],
        input_summary=perturb["input_summary"],
    )
    assert causal_trace["ownership_status"] in {"mixed", "unresolved"}
    assert any(
        isinstance(row, dict)
        and row.get("cause_family") in {"mixed", "unresolved"}
        and row.get("observability_gap_candidate") is True
        for row in causal_trace["entries"]
    )


def test_causal_trace_invariant_non_pass_verdict_has_entries() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-causal-invariant",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    statuses = {
        artifact["verdicts"]["mechanistic_integrity"]["status"],
        artifact["verdicts"]["claim_honesty"]["status"],
        artifact["verdicts"]["path_affecting_sensitivity"]["status"],
    }
    if "FAIL" in statuses or "PARTIAL" in statuses:
        assert artifact["causal_trace"]["entries"], "non-pass verdict must have causal trace entries"


def test_verdicts_do_not_emit_compact_success_when_causal_ownership_unresolved() -> None:
    from tools.turn_audit import _compute_verdicts

    verdicts = _compute_verdicts(
        route_and_scope={
            "accepted": True,
            "lawful_production_route": True,
        },
        checkpoints={
            "checkpoint_coverage_complete": True,
            "blocked_checkpoint_ids": [],
            "enforced_detour_checkpoint_ids": ["rt01.shared_runtime_domain_checkpoint"],
            "epistemic_admission_checkpoint": {
                "status": "passed",
                "applied_action": "continue",
            },
        },
        uncertainty={
            "epistemic_should_abstain": False,
            "epistemic_unknown_reason": None,
            "epistemic_conflict_reason": None,
            "uncertainty_markers": {},
            "no_safe_markers": {},
            "degraded_markers": {},
        },
        final_outcome={
            "final_execution_outcome": "revalidate",
        },
        input_summary={
            "context_flags": {"require_t02_constrained_scene_consumer": True},
        },
        causal_trace={
            "entries": [
                {
                    "event_type": "checkpoint_consequence",
                    "event_ref": "rt01.shared_runtime_domain_checkpoint",
                    "cause_family": "unresolved",
                    "cause_source": "phase_surfaces.regulation.effective_regulation_influence_source",
                    "load_bearing": True,
                    "confidence": 0.4,
                    "evidence_field_paths": [
                        "checkpoints.shared_runtime_domain_checkpoint.status",
                    ],
                    "competing_causes": ["shared_runtime_regulation"],
                    "observability_gap_candidate": True,
                }
            ],
            "trigger_inventory": [
                {
                    "trigger_source": "input_summary.context_flags.require_t02_constrained_scene_consumer",
                    "trigger_class": "context_flag",
                    "active": True,
                    "value": True,
                }
            ],
            "ownership_status": "unresolved",
        },
    )
    assert verdicts["path_affecting_sensitivity"]["status"] in {"PARTIAL", "UNRESOLVED"}


def test_local_regulation_surface_is_not_promoted_to_shared_runtime_cause_family() -> None:
    family, source, _, _ = _classify_shared_regulation_cause(
        regulation_surface={
            "effective_regulation_influence_source": "local_regulation_surface",
            "regulation_override_scope": "bounded",
            "regulation_gate_accepted": True,
        },
        restrictions={"regulation_gate_restrictions": []},
    )
    assert family == "local_regulation_constraint"
    assert source == "phase_surfaces.regulation.effective_regulation_influence_source"


def test_unknown_checkpoint_consequence_does_not_default_to_subject_internal() -> None:
    causal_trace = _collect_causal_trace(
        route_and_scope={"accepted": True},
        phase_surfaces={"regulation": {}, "epistemics": {}},
        checkpoints={
            "observed_checkpoint_results": [
                {
                    "checkpoint_id": "rt01.unknown_checkpoint",
                    "status": "blocked",
                    "applied_action": "halt",
                    "reason": "test",
                }
            ],
            "shared_runtime_domain_checkpoint": UNRESOLVED_TOKEN,
        },
        restrictions={"regulation_gate_restrictions": UNRESOLVED_TOKEN},
        uncertainty={},
        final_outcome={
            "final_execution_outcome": "halt",
            "active_execution_mode": "halted",
            "repair_needed": False,
            "revalidation_needed": False,
            "halt_reason": None,
        },
        input_summary={"context_flags": {}, "epistemic_case_input": None, "regulation_shared_domain_input": None},
    )
    assert any(
        isinstance(entry, dict)
        and entry.get("event_ref") == "rt01.unknown_checkpoint"
        and entry.get("cause_family") in {"unresolved", "mixed", "harness_inference_only"}
        for entry in causal_trace["entries"]
    )
    assert not any(
        isinstance(entry, dict)
        and entry.get("event_ref") == "rt01.unknown_checkpoint"
        and entry.get("cause_family") == "subject_internal"
        for entry in causal_trace["entries"]
    )


def test_load_bearing_entries_have_evidence_covering_cause_source() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-causal-evidence-discipline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context_flags={"require_s02_boundary_consumer": True},
    )
    for entry in artifact["causal_trace"]["entries"]:
        if not isinstance(entry, dict):
            continue
        if entry.get("load_bearing") is not True:
            continue
        cause_source = str(entry.get("cause_source", UNRESOLVED_TOKEN))
        evidence_paths = [str(path) for path in entry.get("evidence_field_paths", [])]
        assert _cause_source_covered_by_evidence(cause_source, evidence_paths)


def test_harness_inference_only_is_not_load_bearing_by_default() -> None:
    causal_trace = _collect_causal_trace(
        route_and_scope={"accepted": True},
        phase_surfaces={"regulation": {}, "epistemics": {}},
        checkpoints={"observed_checkpoint_results": [], "shared_runtime_domain_checkpoint": UNRESOLVED_TOKEN},
        restrictions={"regulation_gate_restrictions": UNRESOLVED_TOKEN},
        uncertainty={},
        final_outcome={
            "final_execution_outcome": "halt",
            "active_execution_mode": "halted",
            "repair_needed": False,
            "revalidation_needed": False,
            "halt_reason": "collector_inference_only_probe",
        },
        input_summary={"context_flags": {}, "epistemic_case_input": None, "regulation_shared_domain_input": None},
    )
    assert any(
        isinstance(entry, dict)
        and entry.get("cause_family") == "harness_inference_only"
        and entry.get("load_bearing") is False
        for entry in causal_trace["entries"]
    )


def test_metadata_only_fields_do_not_inflate_trigger_inventory() -> None:
    triggers = _build_trigger_inventory(
        input_summary={
            "context_flags": {},
            "epistemic_case_input": {
                "source_class": "reporter",
                "modality": "user_text",
                "claim_key": "metadata_only",
                "require_observation": False,
                "prior_units_count": 0,
            },
            "regulation_shared_domain_input": {
                "source_state_ref": "metadata.only.source",
            },
        },
        checkpoints={"observed_checkpoint_results": []},
    )
    assert triggers == []


def test_baseline_path_presence_does_not_auto_pass_sensitivity() -> None:
    artifact = collect_turn_audit_artifact(
        case_id="collector-causal-baseline-sensitivity-guard",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    assert artifact["verdicts"]["path_affecting_sensitivity"]["status"] in {"PARTIAL", "UNRESOLVED", "FAIL"}
    assert artifact["verdicts"]["path_affecting_sensitivity"]["status"] != "PASS"


def test_cli_disk_parity_supports_epistemic_and_regulation_inputs(tmp_path) -> None:
    artifact_path = tmp_path / "collector-cli-parity.json"
    exit_code = turn_audit_main(
        [
            "--case-id",
            "collector-cli-parity",
            "--energy",
            "66",
            "--cognitive",
            "44",
            "--safety",
            "74",
            "--unresolved-preference",
            "false",
            "--epistemic-case-input-json",
            "{\"source_class\":\"unknown\",\"require_observation\":true}",
            "--regulation-shared-domain-input-json",
            "{\"pressure_level\":0.93,\"override_scope\":\"emergency\",\"gate_accepted\":true}",
            "--output",
            str(artifact_path),
        ]
    )
    assert exit_code == 0
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    epistemic_input = artifact["input_summary"]["epistemic_case_input"]
    regulation_input = artifact["input_summary"]["regulation_shared_domain_input"]
    assert isinstance(epistemic_input, dict)
    assert isinstance(regulation_input, dict)
    assert epistemic_input["source_class"] == "unknown"
    assert epistemic_input["require_observation"] is True
    assert regulation_input["override_scope"] == "emergency"
    assert regulation_input["gate_accepted"] is True
    trigger_classes = {
        row.get("trigger_class")
        for row in artifact.get("causal_trace", {}).get("trigger_inventory", [])
        if isinstance(row, dict)
    }
    assert "epistemic_input_pressure" in trigger_classes
    assert "regulation_input_pressure" in trigger_classes


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
    assert artifact["restrictions_and_forbidden_shortcuts"]["t02_restrictions"] == UNRESOLVED_TOKEN

    unresolved_codes = {entry["code"] for entry in artifact["unresolved"]}
    assert "PRE_EXECUTION_DISPATCH_REJECTION" in unresolved_codes
    assert "REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" in unresolved_codes
    assert "T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD" in unresolved_codes

    for entry in artifact["unresolved"]:
        assert set(entry) == {
            "code",
            "message",
            "blocking_surface",
            "severity",
            "impacted_sections",
            "requires_non_v1_extension",
        }
