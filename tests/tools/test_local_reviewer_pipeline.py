from __future__ import annotations

import json
from pathlib import Path

import pytest

from reviewer.api_client import OllamaGenerateDiagnostics
from reviewer.config import ReviewerPipelineConfig
from reviewer.models import GeneratedCase, ReviewerSchemaError, validate_reviewer_output
from reviewer.pipeline import LocalStatelessReviewerPipeline


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


def _minimal_payload() -> dict[str, object]:
    return {
        "overall_reading": "coherent",
        "confidence": 0.91,
        "suspicious_segments": [],
        "likely_observability_gaps": [],
        "human_review_priority": "low",
        "final_note": "looks coherent",
    }


class FakeDiagnosticClient:
    def __init__(self, handler) -> None:
        self.handler = handler
        self.calls: list[dict[str, object]] = []

    def generate_with_diagnostics(
        self,
        *,
        model: str,
        prompt: str,
        timeout_seconds: float | None = None,
        retry_count: int | None = None,
        output_json_schema: dict | None = None,
        temperature: float = 0.0,
        num_predict: int = 384,
        num_ctx: int = 8192,
        think: bool = False,
    ) -> OllamaGenerateDiagnostics:
        marker = "REVIEW_PACKAGE_JSON:\n"
        package = json.loads(prompt.split(marker, 1)[1])
        case_id = str(package["case_id"])
        self.calls.append(
            {
                "model": model,
                "prompt": prompt,
                "case_id": case_id,
                "timeout_seconds": timeout_seconds,
                "retry_count": retry_count,
                "output_json_schema": output_json_schema,
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": num_ctx,
                "think": think,
                "package": package,
            }
        )
        return self.handler(case_id=case_id, model=model, prompt=prompt)

    def health(self) -> dict[str, object]:
        return {"ok": True, "models_count": 1}


def _diag(
    *,
    model: str,
    prompt: str,
    status: str,
    extracted_text: str = "",
    error_message: str | None = None,
    raw_http_response_body: str | None = None,
    timeout: bool = False,
    retry_count: int = 0,
    prompt_eval_count: int | None = 1800,
    eval_count: int | None = 90,
    thinking_present: bool = False,
) -> OllamaGenerateDiagnostics:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "format": {"type": "object"},
        "options": {"temperature": 0.0, "num_predict": 256, "num_ctx": 8192},
        "keep_alive": 0,
    }
    raw_http = raw_http_response_body
    if raw_http is None:
        raw_http = json.dumps({"message": {"role": "assistant", "content": extracted_text}}, ensure_ascii=True)
    return OllamaGenerateDiagnostics(
        endpoint="/api/chat",
        request_payload=payload,
        raw_http_response_body=raw_http,
        extracted_text=extracted_text,
        response_field_used="message.content",
        thinking_present=thinking_present,
        prompt_eval_count=prompt_eval_count,
        eval_count=eval_count,
        status=status,
        error_message=error_message,
        timeout=timeout,
        retry_count=retry_count,
        latency_ms=15.0,
    )


def _cfg(tmp_path: Path) -> ReviewerPipelineConfig:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str(tmp_path / "artifacts")
    cfg.diagnostic_mode = True
    cfg.generation.max_cases_per_cycle = 1
    cfg.tiers["tier1"].enabled = True
    cfg.tiers["tier2"].enabled = False
    cfg.tiers["tier3"].enabled = False
    cfg.tiers["tier1"].max_parallel_workers = 1
    return cfg


def test_thinking_only_no_answer_classification(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        return _diag(
            model=model,
            prompt=prompt,
            status="thinking_only_no_answer",
            extracted_text="",
            thinking_present=True,
            error_message="thinking present but answer field empty",
        )

    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=DummyGenerator(),
        client=FakeDiagnosticClient(handler),
    )
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["per_status_reviews"]["thinking_only_no_answer"] == 1


def test_canonical_case_id_injection_with_reduced_schema(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = dict(_minimal_payload())
        payload["case_id"] = "wrong-id-from-model"
        return _diag(
            model=model,
            prompt=prompt,
            status="ok",
            extracted_text=json.dumps(payload, ensure_ascii=True),
        )

    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=DummyGenerator(),
        client=FakeDiagnosticClient(handler),
    )
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["per_status_reviews"]["semantic_review_completed"] == 1
    semantic = list((Path(cfg.artifacts_root) / "semantic_reviews").glob("**/*.json"))[0]
    payload = json.loads(semantic.read_text(encoding="utf-8"))
    assert payload["parsed_json"]["case_id"].startswith("dummy-case-")
    assert payload["model_case_id"] == "wrong-id-from-model"


def test_minimal_schema_validation() -> None:
    valid = dict(_minimal_payload())
    valid["case_id"] = "x"
    normalized = validate_reviewer_output(valid, expected_case_id="x")
    assert set(normalized.keys()) == {
        "case_id",
        "overall_reading",
        "confidence",
        "suspicious_segments",
        "likely_observability_gaps",
        "human_review_priority",
        "final_note",
    }

    bad = {"overall_reading": "coherent"}
    with pytest.raises(ReviewerSchemaError):
        validate_reviewer_output(bad, expected_case_id="x")


def test_one_endpoint_structured_output_extraction(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = dict(_minimal_payload())
        payload["case_id"] = case_id
        return _diag(
            model=model,
            prompt=prompt,
            status="ok",
            extracted_text=json.dumps(payload, ensure_ascii=True),
        )

    client = FakeDiagnosticClient(handler)
    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=client)
    pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert client.calls
    assert client.calls[0]["output_json_schema"] is not None
    assert client.calls[0]["think"] is False


def test_reduced_payload_path(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = dict(_minimal_payload())
        payload["case_id"] = case_id
        return _diag(
            model=model,
            prompt=prompt,
            status="ok",
            extracted_text=json.dumps(payload, ensure_ascii=True),
        )

    client = FakeDiagnosticClient(handler)
    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=client)
    pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    package = client.calls[0]["package"]
    assert sorted(package.keys()) == [
        "case_id",
        "key_tension_axis",
        "scenario_family",
        "scenario_intent",
        "trace_jsonl",
    ]


def test_live_call_config_assembly_includes_contract_settings(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.tiers["tier1"].num_ctx = 6144
    cfg.tiers["tier1"].num_predict = 200
    cfg.tiers["tier1"].temperature = 0.0

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = dict(_minimal_payload())
        payload["case_id"] = case_id
        return _diag(
            model=model,
            prompt=prompt,
            status="ok",
            extracted_text=json.dumps(payload, ensure_ascii=True),
            prompt_eval_count=2048,
        )

    client = FakeDiagnosticClient(handler)
    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=client)
    pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    call = client.calls[0]
    assert call["think"] is False
    assert call["num_ctx"] == 6144
    assert call["num_predict"] == 200
    assert call["temperature"] == 0.0


def test_sequential_single_model_diagnostic_mode(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = dict(_minimal_payload())
        payload["case_id"] = case_id
        return _diag(
            model=model,
            prompt=prompt,
            status="ok",
            extracted_text=json.dumps(payload, ensure_ascii=True),
        )

    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=DummyGenerator(),
        client=FakeDiagnosticClient(handler),
    )
    summary = pipeline.run_sequential_diagnostics(
        tier_name="tier1",
        case_count=1,
        themes=["epistemic_fragility"],
    )
    assert summary["sequential_diagnostic_mode"] is True
    assert summary["per_tier_reviews"] == {"tier1": 1}


def test_tiny_batch_summary_metrics(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.generation.max_cases_per_cycle = 3

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = dict(_minimal_payload())
        payload["case_id"] = case_id
        return _diag(
            model=model,
            prompt=prompt,
            status="ok",
            extracted_text=json.dumps(payload, ensure_ascii=True),
            prompt_eval_count=3000,
            eval_count=120,
        )

    pipeline = LocalStatelessReviewerPipeline(
        config=cfg,
        generator=DummyGenerator(),
        client=FakeDiagnosticClient(handler),
    )
    summary = pipeline.run_cycle(case_count=3, themes=["epistemic_fragility"])
    assert summary["generated_cases"] == 3
    assert summary["per_status_reviews"]["semantic_review_completed"] == 3
    assert summary["avg_latency_ms"] > 0.0
    assert summary["prompt_eval_count_distribution"]["count"] == 3
    assert summary["prompt_eval_count_distribution"]["max"] == 3000


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
