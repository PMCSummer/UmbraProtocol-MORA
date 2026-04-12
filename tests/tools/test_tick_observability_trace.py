from __future__ import annotations

import json
from pathlib import Path

import pytest

from substrate.runtime_tap_trace import (
    MODULE_ALLOWED_FIELDS,
    TRACE_STEP_ALLOWED,
    activate_tick_trace,
    deactivate_tick_trace,
    finish_tick_trace,
    reset_trace_state,
)
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.simple_trace import run_tick_and_write_simple_trace
from substrate.subject_tick import SubjectTickInput
from tools.tick_observability_trace import main as tick_trace_main

FORBIDDEN_VOCABULARY = (
    "likely_subject_issue",
    "likely_observability_gap",
    "likely_harness_gap",
    "mixed_or_ambiguous",
    "reconciliation_triage",
    "sensitivity",
    "verdict",
)


def _load_events(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _run_sample_trace(
    tmp_path: Path,
    *,
    case_id: str = "runtime-trace-case",
    route_class: str = "production_contour",
) -> tuple[Path, list[dict[str, object]]]:
    reset_trace_state()
    result = run_tick_and_write_simple_trace(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        output_root=tmp_path / "trace-out",
        route_class=route_class,
    )
    trace_path = Path(result["trace_path"])
    assert trace_path.exists()
    events = _load_events(trace_path)
    assert events
    return trace_path, events


def _module_decision_event(events: list[dict[str, object]], module: str) -> dict[str, object]:
    for event in events:
        if str(event["module"]) == module and str(event["step"]) == "decision":
            return event
    raise AssertionError(f"decision event not found for module={module}")


def test_runtime_truth_trace_survives_mid_tick_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import substrate.subject_tick.update as subject_tick_update

    reset_trace_state()
    tick_id = "subject-tick-midfail-1"
    token = activate_tick_trace(tick_id=tick_id, output_root=tmp_path / "trace-out")
    monkeypatch.setattr(
        subject_tick_update,
        "build_t02_constrained_scene",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("forced_t02_failure")),
    )

    with pytest.raises(RuntimeError, match="forced_t02_failure"):
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=SubjectTickInput(
                    case_id="midfail",
                    energy=66.0,
                    cognitive=44.0,
                    safety=74.0,
                    unresolved_preference=False,
                ),
                route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            )
        )

    deactivate_tick_trace(token)
    meta = finish_tick_trace(tick_id=tick_id)
    trace_path = Path(meta["trace_path"])
    events = _load_events(trace_path)
    modules = {str(event["module"]) for event in events}
    assert "runtime_topology" in modules
    assert "world_adapter" in modules
    assert "t01_semantic_field" in modules
    subject_tick_steps = {
        str(event["step"]) for event in events if str(event["module"]) == "subject_tick"
    }
    assert "decision" not in subject_tick_steps
    assert "exit" not in subject_tick_steps
    assert int(meta["event_count"]) == len(events)


def test_trace_lines_have_minimal_envelope_and_runtime_order(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-ordering")
    expected_keys = {"tick_id", "order", "module", "step", "values", "note"}
    orders = [int(event["order"]) for event in events]
    assert orders == list(range(len(events)))
    for event in events:
        assert set(event.keys()) == expected_keys
        assert event["step"] in TRACE_STEP_ALLOWED
        assert isinstance(event["values"], dict)


def test_non_accepted_route_does_not_replay_static_module_order(tmp_path: Path) -> None:
    _, events = _run_sample_trace(
        tmp_path,
        case_id="runtime-helper-blocked",
        route_class="helper_path",
    )
    modules = {str(event["module"]) for event in events}
    assert modules == {"runtime_topology"}
    steps = [str(event["step"]) for event in events]
    assert "blocked" in steps
    assert "decision" in steps


def test_no_synthetic_enter_with_all_none(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-enter-values")
    enter_events = [event for event in events if event["step"] == "enter"]
    assert enter_events
    for event in enter_events:
        values = event["values"]
        assert isinstance(values, dict)
        assert values
        assert not all(value is None for value in values.values())


def test_field_whitelists_are_enforced_per_module(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-whitelist")
    for event in events:
        module = str(event["module"])
        values = event["values"]
        assert isinstance(values, dict)
        assert set(values.keys()).issubset(set(MODULE_ALLOWED_FIELDS[module]))
        if module == "downstream_obedience":
            assert "restrictions" not in values
            assert "restriction_count" in values


def test_regulation_trace_enrichment_fields_are_compact_and_runtime_local(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-regulation-enrichment")
    event = _module_decision_event(events, "regulation")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        (
            "pressure_level",
            "escalation_stage",
            "override_scope",
            "gate_accepted",
            "dominant_axis",
            "claim_strength",
        )
    ).issubset(set(values.keys()))
    assert isinstance(values["pressure_level"], (int, float))
    assert isinstance(values["escalation_stage"], str)
    assert isinstance(values["override_scope"], str)
    assert isinstance(values["gate_accepted"], bool)
    assert isinstance(values["claim_strength"], str)
    assert len(json.dumps(values, ensure_ascii=True)) < 500


def test_downstream_trace_enrichment_is_compact_and_no_full_payload_leak(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-downstream-enrichment")
    event = _module_decision_event(events, "downstream_obedience")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        ("accepted", "usability_class", "top_restrictions", "restriction_count", "blocked_reason")
    ).issubset(set(values.keys()))
    assert isinstance(values["accepted"], bool)
    assert isinstance(values["usability_class"], str)
    assert isinstance(values["restriction_count"], int)
    assert isinstance(values["top_restrictions"], list)
    assert len(values["top_restrictions"]) <= 3
    assert all(isinstance(item, str) and len(item) <= 96 for item in values["top_restrictions"])
    assert "restrictions" not in values
    assert len(json.dumps(values, ensure_ascii=True)) < 500


def test_subject_output_kind_is_emitted_and_consistent(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-output-kind")
    event = _module_decision_event(events, "subject_tick")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        (
            "output_kind",
            "materialized_output",
            "final_execution_outcome",
            "active_execution_mode",
            "abstain",
            "abstain_reason",
        )
    ).issubset(set(values.keys()))

    output_kind = values["output_kind"]
    assert output_kind in {
        "contentful_output",
        "bounded_idle_continuation",
        "abstention_output",
        "no_material_output",
    }
    if output_kind == "bounded_idle_continuation":
        assert values["materialized_output"] is True
        assert values["final_execution_outcome"] == "continue"
        assert values["abstain"] is False
        assert values["active_execution_mode"] in {"idle", "hold_safe_idle"}
    if output_kind == "abstention_output":
        assert values["abstain"] is True
    if output_kind == "no_material_output":
        assert (values["materialized_output"] is False) or (
            values["final_execution_outcome"] == "halt"
        )
    if output_kind == "contentful_output":
        assert values["materialized_output"] is True
        assert values["abstain"] is False
        assert values["active_execution_mode"] not in {"idle", "hold_safe_idle"}


def test_t03_clarity_emits_nonconvergence_basis_signal(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-t03-clarity")
    event = _module_decision_event(events, "t03_hypothesis_competition")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        (
            "leader",
            "conflict_count",
            "open_slot_count",
            "convergence_status",
            "nonconvergence_preserved",
            "no_viable_leader",
            "nonconvergence_basis",
        )
    ).issubset(set(values.keys()))
    assert isinstance(values["conflict_count"], int)
    assert isinstance(values["open_slot_count"], int)
    assert isinstance(values["no_viable_leader"], bool)
    assert isinstance(values["nonconvergence_basis"], str)
    assert values["nonconvergence_basis"] in {
        "converged_or_provisional",
        "conflict",
        "open_slot_incompleteness",
        "no_admissible_leader",
        "nonconvergence_unspecified",
    }
    assert " " not in values["nonconvergence_basis"]
    assert len(values["nonconvergence_basis"]) <= 64
    if values["convergence_status"] == "honest_nonconvergence":
        assert values["nonconvergence_basis"] != "converged_or_provisional"


def test_blocked_steps_only_appear_on_actual_blocked_paths(tmp_path: Path) -> None:
    _, events = _run_sample_trace(
        tmp_path,
        case_id="runtime-blocked-route",
        route_class="helper_path",
    )
    blocked_events = [event for event in events if event["step"] == "blocked"]
    assert blocked_events
    for blocked in blocked_events:
        module = str(blocked["module"])
        values = blocked["values"]
        if module == "runtime_topology":
            assert values.get("accepted") is False


def test_representative_modules_have_runtime_steps(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-step-presence")
    by_module: dict[str, list[str]] = {}
    for event in events:
        by_module.setdefault(str(event["module"]), []).append(str(event["step"]))

    for module in (
        "runtime_topology",
        "world_adapter",
        "world_entry_contract",
        "epistemics",
        "regulation",
        "t01_semantic_field",
        "t02_relation_binding",
        "t03_hypothesis_competition",
        "downstream_obedience",
        "subject_tick",
    ):
        assert "enter" in by_module[module]
        assert "decision" in by_module[module]
        assert "exit" in by_module[module]


def test_no_verdict_vocabulary_anywhere_on_main_path(tmp_path: Path) -> None:
    trace_path, _ = _run_sample_trace(tmp_path, case_id="runtime-neutral-vocab")
    payload = trace_path.read_text(encoding="utf-8")
    for token in FORBIDDEN_VOCABULARY:
        assert token not in payload


def test_no_snapshot_map_reconstruction_path_in_simple_trace_module() -> None:
    source = Path("src/substrate/simple_trace.py").read_text(encoding="utf-8")
    assert "_build_snapshot_map" not in source
    assert "_MODULE_FIELD_PATHS" not in source
    assert "_MODULE_BLOCKED_RULES" not in source


def test_cli_smoke_writes_single_jsonl(tmp_path: Path) -> None:
    reset_trace_state()
    output_dir = tmp_path / "cli-out"
    exit_code = tick_trace_main(
        [
            "--case-id",
            "runtime-cli",
            "--energy",
            "66",
            "--cognitive",
            "44",
            "--safety",
            "74",
            "--unresolved-preference",
            "false",
            "--output-dir",
            str(output_dir),
        ]
    )
    assert exit_code == 0
    files = sorted(item for item in output_dir.iterdir() if item.is_file())
    assert len(files) == 1
    assert files[0].suffix == ".jsonl"
    events = _load_events(files[0])
    assert events
    assert {"tick_id", "order", "module", "step", "values", "note"} == set(events[0].keys())
