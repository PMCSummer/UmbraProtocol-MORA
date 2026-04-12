from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.edgy_behavioral_case_battery import (
    CASE_BATTERY,
    REQUIRED_SCENARIO_FAMILIES,
    generate_edgy_behavioral_case_battery,
)


@pytest.fixture(scope="module")
def battery_result(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    output_dir = tmp_path_factory.mktemp("edgy-battery")
    return generate_edgy_behavioral_case_battery(output_dir=output_dir)


def _load_events(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_battery_generation_sanity(battery_result: dict[str, object]) -> None:
    manifest = battery_result["manifest"]
    assert isinstance(manifest, dict)
    cases = manifest["cases"]
    assert isinstance(cases, list)
    assert 12 <= len(cases) <= 18
    assert len(cases) == len(CASE_BATTERY)

    case_ids = [str(case["case_id"]) for case in cases]
    assert len(case_ids) == len(set(case_ids))

    for case in cases:
        trace_path = Path(str(case["trace_path"]))
        assert trace_path.exists()
        events = _load_events(trace_path)
        assert events


def test_manifest_sanity_and_pairs(battery_result: dict[str, object]) -> None:
    manifest = battery_result["manifest"]
    cases = manifest["cases"]
    case_ids = {str(case["case_id"]) for case in cases}

    for case in cases:
        assert str(case["scenario_intent"]).strip()
        inspect_nodes = case["what_to_inspect_in_trace"]
        assert isinstance(inspect_nodes, list)
        assert inspect_nodes
        pair = case["paired_with"]
        if pair is not None:
            assert str(pair) in case_ids

    spec_ids = {spec.case_id for spec in CASE_BATTERY}
    assert case_ids == spec_ids


def test_diversity_sanity_and_required_families(battery_result: dict[str, object]) -> None:
    manifest = battery_result["manifest"]
    cases = manifest["cases"]
    families = {str(case["scenario_family"]) for case in cases}
    assert len(families) > 1
    assert REQUIRED_SCENARIO_FAMILIES.issubset(families)


def test_trace_execution_sanity_jsonl_validity(battery_result: dict[str, object]) -> None:
    manifest = battery_result["manifest"]
    cases = manifest["cases"]
    expected_keys = {"tick_id", "order", "module", "step", "values", "note"}

    for case in cases:
        events = _load_events(Path(str(case["trace_path"])))
        for index, event in enumerate(events):
            assert set(event.keys()) == expected_keys
            assert int(event["order"]) == index
            assert isinstance(event["values"], dict)
