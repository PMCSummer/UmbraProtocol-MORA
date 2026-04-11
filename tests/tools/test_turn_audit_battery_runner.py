from __future__ import annotations

import json
from pathlib import Path

import tools.turn_audit_battery as battery_module
from tools.turn_audit_battery import BatteryCase, get_battery_case_registry, run_turn_audit_battery


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_battery_run_creates_expected_outputs(tmp_path) -> None:
    run = run_turn_audit_battery(output_dir=tmp_path / "battery")
    index_path = Path(run["index_json_path"])
    index_md_path = Path(run["index_markdown_path"])
    index = _load_json(index_path)

    assert index_path.exists()
    assert index_md_path.exists()
    assert index["case_count"] == len(get_battery_case_registry())
    assert len(index["cases"]) == len(get_battery_case_registry())

    for case_entry in index["cases"]:
        assert Path(case_entry["artifact_path"]).exists()
        assert Path(case_entry["markdown_path"]).exists()

    case_ids = {case["case_id"] for case in index["cases"]}
    assert "epistemic_unknown_abstain_detour" in case_ids
    assert "epistemic_observation_requirement_block" in case_ids
    assert "epistemic_conflict_no_laundering" in case_ids
    assert "regulation_high_override_scope_detour" in case_ids
    assert "regulation_no_strong_override_claim_guard" in case_ids
    assert "regulation_pressure_tradeoff_shift" in case_ids


def test_battery_index_preserves_per_case_verdicts_from_artifacts(tmp_path) -> None:
    run = run_turn_audit_battery(output_dir=tmp_path / "battery")
    index = _load_json(Path(run["index_json_path"]))

    assert index["cases"]
    for case_entry in index["cases"]:
        artifact = _load_json(Path(case_entry["artifact_path"]))
        assert case_entry["route_class"] == artifact["route_and_scope"]["route_class"]
        assert case_entry["final_execution_outcome"] == artifact["final_outcome"]["final_execution_outcome"]
        assert case_entry["overall_verdict"] == artifact["verdicts"]["overall"]["status"]
        assert case_entry["mechanistic_integrity"] == artifact["verdicts"]["mechanistic_integrity"]["status"]
        assert case_entry["claim_honesty"] == artifact["verdicts"]["claim_honesty"]["status"]
        assert (
            case_entry["path_affecting_sensitivity"]
            == artifact["verdicts"]["path_affecting_sensitivity"]["status"]
        )
        assert case_entry["unresolved_count"] == len(artifact.get("unresolved", []))
        epistemics = artifact.get("phase_surfaces", {}).get("epistemics", {})
        regulation = artifact.get("phase_surfaces", {}).get("regulation", {})
        assert case_entry["epistemic_status"] == (
            epistemics.get("epistemic_status", "UNRESOLVED_FOR_V1")
            if isinstance(epistemics, dict)
            else "UNRESOLVED_FOR_V1"
        )
        assert case_entry["epistemic_should_abstain"] == (
            epistemics.get("epistemic_should_abstain", "UNRESOLVED_FOR_V1")
            if isinstance(epistemics, dict)
            else "UNRESOLVED_FOR_V1"
        )
        assert case_entry["epistemic_claim_strength"] == (
            epistemics.get("epistemic_claim_strength", "UNRESOLVED_FOR_V1")
            if isinstance(epistemics, dict)
            else "UNRESOLVED_FOR_V1"
        )
        assert case_entry["regulation_override_scope"] == (
            regulation.get("regulation_override_scope", "UNRESOLVED_FOR_V1")
            if isinstance(regulation, dict)
            else "UNRESOLVED_FOR_V1"
        )
        assert case_entry["regulation_no_strong_override_claim"] == (
            regulation.get("regulation_no_strong_override_claim", "UNRESOLVED_FOR_V1")
            if isinstance(regulation, dict)
            else "UNRESOLVED_FOR_V1"
        )
        assert case_entry["regulation_gate_accepted"] == (
            regulation.get("regulation_gate_accepted", "UNRESOLVED_FOR_V1")
            if isinstance(regulation, dict)
            else "UNRESOLVED_FOR_V1"
        )


def test_battery_continues_when_one_case_fails_generation(tmp_path, monkeypatch) -> None:
    registry = list(get_battery_case_registry())
    broken = BatteryCase(
        case_id="broken_case_for_failure_path",
        description="Intentional invalid collector input for failure-path coverage.",
        collector_input={
            "case_id": "battery-broken-case",
            "energy": 66.0,
            "cognitive": 44.0,
            "safety": 74.0,
            "unresolved_preference": False,
            "context_flags": {"unsupported_flag_for_test": True},
        },
        expected_emphasis_verdict="mechanistic_integrity",
        tags=("failure_path",),
    )
    monkeypatch.setattr(
        battery_module,
        "get_battery_case_registry",
        lambda: tuple(registry + [broken]),
    )

    run = run_turn_audit_battery(output_dir=tmp_path / "battery")
    index = _load_json(Path(run["index_json_path"]))

    assert index["case_count"] == len(registry) + 1
    broken_entries = [item for item in index["cases"] if item["case_id"] == broken.case_id]
    assert len(broken_entries) == 1
    broken_entry = broken_entries[0]
    assert broken_entry["failed_generation"] is True
    assert broken_entry["overall_verdict"] == "FAIL"
    assert broken_entry["error_type"] in {"ValueError", "TypeError"}
    assert "unsupported" in broken_entry["error_message"].lower()

    successful = [item for item in index["cases"] if item["case_id"] != broken.case_id]
    assert successful
    assert all(item["failed_generation"] is False for item in successful)


def test_battery_regression_causal_trace_honesty_for_core_cases(tmp_path) -> None:
    run = run_turn_audit_battery(
        output_dir=tmp_path / "battery-causal-regression",
        case_filter=[
            "bounded_clean_production_turn",
            "epistemic_unknown_abstain_detour",
            "regulation_high_override_scope_detour",
        ],
    )
    index = _load_json(Path(run["index_json_path"]))
    by_case = {item["case_id"]: item for item in index["cases"]}

    for case_id in (
        "bounded_clean_production_turn",
        "epistemic_unknown_abstain_detour",
        "regulation_high_override_scope_detour",
    ):
        artifact = _load_json(Path(by_case[case_id]["artifact_path"]))
        causal_trace = artifact.get("causal_trace", {})
        assert isinstance(causal_trace.get("entries"), list)
        assert isinstance(causal_trace.get("trigger_inventory"), list)
        assert causal_trace.get("ownership_status") in {"resolved", "mixed", "unresolved"}

    epistemic = _load_json(Path(by_case["epistemic_unknown_abstain_detour"]["artifact_path"]))
    assert any(
        isinstance(row, dict)
        and row.get("cause_family") in {"epistemic_constraint", "mixed"}
        and row.get("load_bearing") is True
        for row in epistemic["causal_trace"]["entries"]
    )

    regulation = _load_json(Path(by_case["regulation_high_override_scope_detour"]["artifact_path"]))
    assert any(
        isinstance(row, dict)
        and row.get("event_ref") == "rt01.shared_runtime_domain_checkpoint"
        and row.get("cause_family") in {"shared_runtime_regulation", "mixed"}
        and row.get("load_bearing") is True
        for row in regulation["causal_trace"]["entries"]
    )
