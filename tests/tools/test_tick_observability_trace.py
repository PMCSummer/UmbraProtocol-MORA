from __future__ import annotations

import json
from pathlib import Path

from substrate.simple_trace import (
    MODULE_ALLOWED_FIELDS,
    MODULE_ORDER,
    extract_module_values,
    reset_trace_state,
    run_tick_and_write_simple_trace,
)
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


def _run_sample_trace(tmp_path: Path, *, case_id: str = "simple-trace-case") -> tuple[Path, list[dict[str, object]]]:
    reset_trace_state()
    result = run_tick_and_write_simple_trace(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        output_root=tmp_path / "trace-out",
    )
    trace_path = Path(result["trace_path"])
    assert trace_path.exists()
    events = _load_events(trace_path)
    assert events
    return trace_path, events


def test_one_tick_produces_one_jsonl_trace(tmp_path: Path) -> None:
    reset_trace_state()
    result = run_tick_and_write_simple_trace(
        case_id="simple-one-file",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        output_root=tmp_path / "trace-out",
    )
    trace_path = Path(result["trace_path"])
    assert trace_path.suffix == ".jsonl"
    assert trace_path.name.startswith(result["tick_id"])
    assert result["event_count"] > 0


def test_events_are_ordered_and_have_minimal_envelope(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="simple-ordering")
    expected_keys = {"tick_id", "order", "module", "step", "values", "note"}
    orders = [int(event["order"]) for event in events]
    assert orders == list(range(len(events)))
    for event in events:
        assert set(event.keys()) == expected_keys
        assert event["module"] in MODULE_ORDER
        assert event["step"] in {"enter", "decision", "exit", "blocked"}
        assert isinstance(event["values"], dict)


def test_enter_decision_exit_present_and_blocked_present_where_expected(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="simple-steps")
    grouped: dict[str, list[dict[str, object]]] = {}
    for event in events:
        grouped.setdefault(str(event["module"]), []).append(event)
    assert set(grouped.keys()) == set(MODULE_ORDER)
    for module in MODULE_ORDER:
        steps = [str(item["step"]) for item in grouped[module]]
        assert "enter" in steps
        assert "decision" in steps
        assert "exit" in steps
    # If module emits blocked step, it must include an explicit note from a concrete field.
    for module, module_events in grouped.items():
        blocked_events = [event for event in module_events if event["step"] == "blocked"]
        for blocked in blocked_events:
            note = blocked.get("note")
            assert isinstance(note, str)
            assert "=" in note
            assert note.split("=", maxsplit=1)[0]


def test_no_verdict_vocabulary_appears_anywhere(tmp_path: Path) -> None:
    trace_path, events = _run_sample_trace(tmp_path, case_id="simple-neutral-case")
    payload = trace_path.read_text(encoding="utf-8")
    for token in FORBIDDEN_VOCABULARY:
        assert token not in payload
    for event in events:
        assert isinstance(event["values"], dict)


def test_no_synthetic_fields_and_allowlisted_values_only(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="simple-allowed-fields")
    for event in events:
        module = str(event["module"])
        values = event["values"]
        assert isinstance(values, dict)
        assert set(values.keys()) == set(MODULE_ALLOWED_FIELDS[module])


def test_missing_field_emits_null_instead_of_surrogate() -> None:
    values = extract_module_values("epistemics", snapshots={})
    assert set(values.keys()) == set(MODULE_ALLOWED_FIELDS["epistemics"])
    assert all(values[field] is None for field in MODULE_ALLOWED_FIELDS["epistemics"])


def test_cli_smoke_writes_single_jsonl(tmp_path: Path) -> None:
    reset_trace_state()
    output_dir = tmp_path / "cli-out"
    exit_code = tick_trace_main(
        [
            "--case-id",
            "simple-cli",
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
    assert _load_events(files[0])
