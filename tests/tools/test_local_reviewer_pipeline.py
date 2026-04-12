from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from reviewer.config import ReviewerPipelineConfig
from reviewer.models import GeneratedCase, ReviewerSchemaError, validate_reviewer_output
from reviewer.pipeline import LocalStatelessReviewerPipeline
from reviewer.queue import CaseWorkQueue
from reviewer.triage import decide_triage


def _write_trace(path: Path, *, case_id: str) -> None:
    events = [
        {
            "tick_id": f"subject-tick-{case_id}-1",
            "order": 0,
            "module": "runtime_topology",
            "step": "decision",
            "values": {"route_class": "production_contour", "accepted": True},
            "note": None,
        },
        {
            "tick_id": f"subject-tick-{case_id}-1",
            "order": 1,
            "module": "subject_tick",
            "step": "decision",
            "values": {
                "output_kind": "bounded_idle_continuation",
                "final_execution_outcome": "continue",
                "active_execution_mode": "idle",
                "abstain": False,
                "abstain_reason": None,
                "materialized_output": True,
            },
            "note": None,
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True))
            handle.write("\n")


class DummyGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str | None]] = []

    def available_themes(self) -> set[str]:
        return {
            "world_absence_poverty",
            "epistemic_fragility",
            "regulation_mode_validity_pressure",
            "ownership_self_prediction_instability",
            "memory_narrative_temptation",
        }

    def generate_case(self, *, seed: int, theme: str | None, traces_output_dir: str | Path) -> GeneratedCase:
        self.calls.append((seed, theme))
        case_id = f"dummy-case-{seed}"
        trace_path = Path(traces_output_dir) / f"subject-tick-{case_id}-1.jsonl"
        _write_trace(trace_path, case_id=case_id)
        return GeneratedCase(
            case_id=case_id,
            seed=seed,
            theme=theme or "epistemic_fragility",
            scenario_family=theme or "epistemic_fragility",
            scenario_intent="dummy scenario",
            paired_with=None,
            key_tension_axis=("dummy_axis",),
            what_to_inspect_in_trace=("subject_tick",),
            why_this_case_exists="test fixture",
            trace_path=str(trace_path.resolve()),
            generation_params={"seed": seed, "theme": theme},
        )


class FakeClient:
    def __init__(self, payload_factory) -> None:
        self.payload_factory = payload_factory
        self.calls: list[dict[str, str]] = []

    def generate(self, *, model: str, prompt: str) -> str:
        marker = "REVIEW_PACKAGE_JSON:\n"
        payload = json.loads(prompt.split(marker, 1)[1])
        case_id = str(payload["case_id"])
        self.calls.append({"model": model, "prompt": prompt, "case_id": case_id})
        return json.dumps(self.payload_factory(case_id), ensure_ascii=True)

    def health(self) -> dict[str, object]:
        return {"ok": True, "models_count": 3}


def _coherent_payload(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "overall_reading": "coherent",
        "confidence": 0.93,
        "behavior_summary": ["bounded and coherent"],
        "coherent_segments": [{"module": "subject_tick", "why_it_looks_coherent": "bounded output"}],
        "suspicious_segments": [],
        "likely_observability_gaps": [],
        "paired_case_comparison": {
            "used": False,
            "paired_case_id": None,
            "main_behavior_shift": "",
            "is_shift_plausible": True,
            "notes": "",
        },
        "human_review_priority": "low",
        "code_focus_candidates": [],
        "final_note": "coherent enough",
    }


def _suspicious_payload(case_id: str) -> dict[str, object]:
    payload = _coherent_payload(case_id)
    payload["overall_reading"] = "likely_problematic"
    payload["human_review_priority"] = "high"
    payload["confidence"] = 0.8
    payload["suspicious_segments"] = [
        {
            "module": "c05_temporal_validity",
            "signal": "unexpected halt",
            "why_it_may_be_suspicious": "detour seems abrupt",
            "alternative_explanations": ["validity pressure"],
            "severity": "high",
        }
    ]
    payload["final_note"] = "needs human review"
    return payload


def test_stateless_review_calls_do_not_accumulate_context(tmp_path: Path) -> None:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.generation.base_seed = 10
    cfg.generation.max_cases_per_cycle = 2
    generator = DummyGenerator()
    client = FakeClient(_coherent_payload)
    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=generator, client=client)
    pipeline.run_cycle(case_count=2, themes=["epistemic_fragility"])

    assert len(client.calls) == 2
    first_case = client.calls[0]["case_id"]
    second_case = client.calls[1]["case_id"]
    assert first_case != second_case
    assert first_case in client.calls[0]["prompt"]
    assert second_case in client.calls[1]["prompt"]
    assert first_case not in client.calls[1]["prompt"]


def test_storage_discipline_ordinary_and_suspicious(tmp_path: Path) -> None:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.generation.max_cases_per_cycle = 1
    cfg.generation.base_seed = 40
    cfg.retention.keep_non_suspicious_trace = False
    generator = DummyGenerator()

    ordinary = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=generator,
        client=FakeClient(_coherent_payload),
    )
    ordinary.run_cycle(case_count=1, themes=["epistemic_fragility"])
    ordinary_summary = Path(cfg.artifacts_root) / "summaries" / "ordinary_cases.jsonl"
    assert ordinary_summary.exists()
    ordinary_rows = [line for line in ordinary_summary.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert ordinary_rows
    ordinary_trace_path = Path(json.loads(ordinary_rows[-1])["trace_path"])
    assert not ordinary_trace_path.exists()

    cfg.generation.base_seed = 41
    suspicious = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=generator,
        client=FakeClient(_suspicious_payload),
    )
    suspicious.run_cycle(case_count=1, themes=["epistemic_fragility"])
    suspicious_idx = Path(cfg.artifacts_root) / "summaries" / "suspicious_cases.jsonl"
    assert suspicious_idx.exists()
    suspicious_row = json.loads(
        [line for line in suspicious_idx.read_text(encoding="utf-8").splitlines() if line.strip()][-1]
    )
    artifact_dir = Path(suspicious_row["artifact_dir"])
    assert (artifact_dir / "trace.jsonl").exists()
    assert (artifact_dir / "case.json").exists()
    assert (artifact_dir / "reviews.json").exists()


def test_retention_cap_for_non_suspicious_traces(tmp_path: Path) -> None:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.generation.max_cases_per_cycle = 2
    cfg.generation.base_seed = 100
    cfg.retention.keep_non_suspicious_trace = True
    cfg.retention.max_non_suspicious_traces = 1
    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=DummyGenerator(),
        client=FakeClient(_coherent_payload),
    )
    pipeline.run_cycle(case_count=2, themes=["epistemic_fragility"])
    active_traces = sorted((Path(cfg.artifacts_root) / "active").glob("*.jsonl"))
    assert len(active_traces) <= 1


def test_triage_routing_policy() -> None:
    cfg = ReviewerPipelineConfig.default()
    d1 = decide_triage(
        review_json=_coherent_payload("c1"),
        tier_name="tier1",
        config=cfg,
    )
    assert d1.action == "close"

    d2 = decide_triage(
        review_json=_suspicious_payload("c2"),
        tier_name="tier1",
        config=cfg,
    )
    assert d2.action in {"escalate", "freeze"}

    d3 = decide_triage(
        review_json=_suspicious_payload("c3"),
        tier_name="tier3",
        config=cfg,
    )
    assert d3.action == "freeze"


def test_malformed_json_and_schema_failure_are_handled(tmp_path: Path) -> None:
    class BadClient(FakeClient):
        def generate(self, *, model: str, prompt: str) -> str:  # type: ignore[override]
            return "NOT_JSON"

    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.generation.max_cases_per_cycle = 1
    cfg.tiers["tier2"].enabled = False
    cfg.tiers["tier3"].enabled = False
    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=DummyGenerator(),
        client=BadClient(_coherent_payload),
    )
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["suspicious_cases"] == 1


def test_validate_reviewer_output_rejects_bad_schema() -> None:
    bad = {"case_id": "x", "overall_reading": "coherent"}
    with pytest.raises(ReviewerSchemaError):
        validate_reviewer_output(bad, expected_case_id="x")


def test_queue_workers_do_not_double_process_same_case() -> None:
    class Item:
        def __init__(self, case_id: str) -> None:
            self.case_id = case_id

    queue = CaseWorkQueue([Item("same"), Item("same"), Item("other")], id_getter=lambda i: i.case_id)
    processed: list[str] = []
    lock = threading.Lock()

    def worker() -> None:
        while True:
            item = queue.get(timeout=0.05)
            if item is None:
                stats = queue.stats()
                if stats.pending == 0 and stats.in_flight == 0:
                    return
                continue
            with lock:
                processed.append(item.case_id)
            queue.mark_done(item)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert processed.count("same") == 1
    assert processed.count("other") == 1


def test_seed_recording_is_reproducible(tmp_path: Path) -> None:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.generation.base_seed = 200
    cfg.generation.max_cases_per_cycle = 3
    generator = DummyGenerator()
    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=generator,
        client=FakeClient(_coherent_payload),
    )
    pipeline.run_cycle(case_count=3, themes=["epistemic_fragility"])
    assert generator.calls == [(200, "epistemic_fragility"), (201, "epistemic_fragility"), (202, "epistemic_fragility")]

    rows = Path(cfg.artifacts_root, "summaries", "ordinary_cases.jsonl").read_text(encoding="utf-8").splitlines()
    seeds = [json.loads(line)["seed"] for line in rows if line.strip()]
    assert sorted(seeds[-3:]) == [200, 201, 202]


def test_ui_smoke_instantiates_basic_views(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from reviewer.ui.app import ReviewerOperatorApp

    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    app = QApplication.instance() or QApplication([])
    win = ReviewerOperatorApp(config=cfg)
    assert win.suspicious_table.columnCount() == 6
    assert win.case_count_spin.value() >= 1
    win.close()


def test_integration_smoke_one_full_cycle(tmp_path: Path) -> None:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.generation.base_seed = 310
    cfg.generation.max_cases_per_cycle = 1
    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        client=FakeClient(_coherent_payload),
    )
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["generated_cases"] == 1
    assert summary["closed_cases"] + summary["suspicious_cases"] == 1
    ordinary_summary = Path(cfg.artifacts_root) / "summaries" / "ordinary_cases.jsonl"
    assert ordinary_summary.exists()
