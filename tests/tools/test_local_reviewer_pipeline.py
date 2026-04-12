from __future__ import annotations

import json
from pathlib import Path

import pytest

from reviewer.api_client import OllamaGenerateDiagnostics
from reviewer.config import ReviewerPipelineConfig
from reviewer.models import (
    GeneratedCase,
    ReviewerSchemaError,
    normalize_reviewer_output,
    validate_reviewer_output,
)
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


def _minimal_payload(
    *,
    overall_reading: str = "coherent_bounded_caution",
    priority: str = "low",
) -> dict[str, object]:
    return {
        "overall_reading": overall_reading,
        "confidence": 0.91,
        "suspicious_segments": [],
        "likely_observability_gaps": [],
        "human_review_priority": priority,
        "final_note": "bounded coherent trace",
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
        "options": {"temperature": 0.0, "num_predict": 512, "num_ctx": 8192},
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


def _read_jsonl_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def test_signal_code_schema_enforcement() -> None:
    good = _minimal_payload(overall_reading="likely_behavioral_problem", priority="high")
    good["case_id"] = "x"
    good["suspicious_segments"] = [
        {"module": "t03_hypothesis_competition", "signal_code": "t03_honest_nonconvergence", "severity": "medium"}
    ]
    normalized = validate_reviewer_output(good, expected_case_id="x")
    assert normalized["suspicious_segments"][0]["signal_code"] == "t03_honest_nonconvergence"

    bad = dict(good)
    bad["suspicious_segments"] = [
        {"module": "t03_hypothesis_competition", "signal_code": "raw_trace_fragment", "severity": "medium"}
    ]
    with pytest.raises(ReviewerSchemaError):
        validate_reviewer_output(bad, expected_case_id="x")


def test_no_free_form_signal_field() -> None:
    payload = _minimal_payload(overall_reading="likely_behavioral_problem", priority="high")
    payload["case_id"] = "x"
    payload["suspicious_segments"] = [
        {"module": "t04_attention_schema", "signal": "bad raw string", "severity": "low"}
    ]
    with pytest.raises(ReviewerSchemaError):
        validate_reviewer_output(payload, expected_case_id="x")


def test_bounded_coherent_trace_can_be_coherent_bounded_caution(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = _minimal_payload(overall_reading="coherent_bounded_caution", priority="high")
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["coherent_ordinary_cases"] == 1
    assert summary["behavioral_review_cases"] == 0
    assert summary["priority_distribution"] == {"low": 1}


def test_revalidation_abstention_can_be_coherent_abstention_or_revalidation(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = _minimal_payload(overall_reading="coherent_abstention_or_revalidation", priority="low")
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["coherent_ordinary_cases"] == 1
    assert summary["behavioral_review_cases"] == 0
    assert summary["priority_distribution"] == {"low": 1}


def test_t03_honest_nonconvergence_alone_does_not_force_behavioral_review(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = _minimal_payload(overall_reading="plausible_but_needs_review", priority="high")
        payload["suspicious_segments"] = [
            {"module": "t03_hypothesis_competition", "signal_code": "t03_honest_nonconvergence", "severity": "medium"}
        ]
        payload["likely_observability_gaps"] = [
            {"module_or_transition": "t03_hypothesis_competition", "gap_code": "unclear_resolution_step"}
        ]
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["behavioral_review_cases"] == 0
    assert summary["coherent_ordinary_cases"] == 1
    assert summary["priority_distribution"] == {"low": 1}


def test_bounded_revalidation_alone_does_not_force_behavioral_review(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = _minimal_payload(overall_reading="plausible_but_needs_review", priority="high")
        payload["suspicious_segments"] = [
            {"module": "bounded_outcome_resolution", "signal_code": "bounded_revalidation_required", "severity": "medium"}
        ]
        payload["likely_observability_gaps"] = [
            {"module_or_transition": "bounded_outcome_resolution", "gap_code": "unclear_resolution_step"}
        ]
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=1, themes=["regulation_mode_validity_pressure"])
    assert summary["behavioral_review_cases"] == 0
    assert summary["coherent_ordinary_cases"] == 1
    assert summary["priority_distribution"] == {"low": 1}


def test_likely_behavioral_problem_routes_to_behavioral_queue(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = _minimal_payload(overall_reading="likely_behavioral_problem", priority="high")
        payload["suspicious_segments"] = [
            {"module": "bounded_outcome_resolution", "signal_code": "causal_transition_mismatch", "severity": "high"}
        ]
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["behavioral_review_cases"] == 1
    assert summary["infra_review_cases"] == 0
    assert summary["priority_distribution"] in ({"high": 1}, {"medium": 1})
    assert list((Path(cfg.artifacts_root) / "behavioral_review_queue").glob("**/reviews.json"))
    assert list((Path(cfg.artifacts_root) / "summaries").glob("behavioral_review_queue.jsonl"))


def test_infra_failures_route_to_infra_queue_not_behavioral(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        return _diag(model=model, prompt=prompt, status="parse_error", error_message="bad json")

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    assert summary["infra_review_cases"] == 1
    assert summary["behavioral_review_cases"] == 0
    assert list((Path(cfg.artifacts_root) / "infra_review_queue").glob("**/reviews.json"))


def test_output_schema_request_reduces_signal_quote_pollution_risk(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        payload = _minimal_payload(overall_reading="coherent_bounded_caution")
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    client = FakeDiagnosticClient(handler)
    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=client)
    pipeline.run_cycle(case_count=1, themes=["epistemic_fragility"])
    schema = client.calls[0]["output_json_schema"]
    assert isinstance(schema, dict)
    suspicious_props = schema["properties"]["suspicious_segments"]["items"]["properties"]
    assert "signal_code" in suspicious_props
    assert "signal" not in suspicious_props


def test_small_run_summary_metrics_are_separated(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.generation.max_cases_per_cycle = 3

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        seed = int(case_id.rsplit("-", 1)[-1])
        if seed % 3 == 0:
            payload = _minimal_payload(overall_reading="coherent_bounded_caution", priority="low")
            return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))
        if seed % 3 == 1:
            payload = _minimal_payload(overall_reading="likely_behavioral_problem", priority="high")
            payload["suspicious_segments"] = [
                {"module": "subject_tick", "signal_code": "causal_transition_mismatch", "severity": "high"}
            ]
            return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))
        return _diag(model=model, prompt=prompt, status="parse_error", error_message="broken")

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=3, themes=["epistemic_fragility"])
    assert summary["generated_cases"] == 3
    assert summary["coherent_ordinary_cases"] == 1
    assert summary["behavioral_review_cases"] == 1
    assert summary["infra_review_cases"] == 1
    assert summary["per_status_reviews"]["semantic_review_completed"] == 2
    assert summary["per_status_reviews"]["parse_error"] == 1


def test_unclear_resolution_gap_is_pruned_for_default_nonconvergence_without_mismatch() -> None:
    payload = _minimal_payload(overall_reading="coherent_bounded_caution", priority="high")
    payload["case_id"] = "x"
    payload["suspicious_segments"] = [
        {"module": "t03_hypothesis_competition", "signal_code": "t03_honest_nonconvergence", "severity": "medium"}
    ]
    payload["likely_observability_gaps"] = [
        {"module_or_transition": "t03_hypothesis_competition", "gap_code": "unclear_resolution_step"},
        {"module_or_transition": "bounded_outcome_resolution", "gap_code": "unclear_resolution_step"},
    ]
    normalized = normalize_reviewer_output(payload, expected_case_id="x")
    assert normalized.normalized_payload["likely_observability_gaps"] == []
    assert "default_unclear_resolution_gaps_pruned" in normalized.nonfatal_warnings


def test_stronger_support_mismatch_counterfactual_still_routes_behavioral_review(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.generation.max_cases_per_cycle = 2

    def handler(*, case_id: str, model: str, prompt: str) -> OllamaGenerateDiagnostics:
        seed = int(case_id.rsplit("-", 1)[-1])
        if seed % 2 == 0:
            payload = _minimal_payload(overall_reading="plausible_but_needs_review", priority="high")
            payload["suspicious_segments"] = [
                {"module": "t03_hypothesis_competition", "signal_code": "t03_honest_nonconvergence", "severity": "medium"}
            ]
            return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))
        payload = _minimal_payload(overall_reading="plausible_but_needs_review", priority="high")
        payload["suspicious_segments"] = [
            {"module": "bounded_outcome_resolution", "signal_code": "causal_transition_mismatch", "severity": "high"},
            {"module": "subject_tick", "signal_code": "unexpected_mode_shift", "severity": "high"},
        ]
        payload["likely_observability_gaps"] = [
            {"module_or_transition": "world_entry_contract", "gap_code": "ambiguous_world_basis"},
            {"module_or_transition": "subject_tick", "gap_code": "unclear_resolution_step"},
        ]
        return _diag(model=model, prompt=prompt, status="ok", extracted_text=json.dumps(payload, ensure_ascii=True))

    pipeline = LocalStatelessReviewerPipeline(config=cfg, generator=DummyGenerator(), client=FakeDiagnosticClient(handler))
    summary = pipeline.run_cycle(case_count=2, themes=["epistemic_fragility"])
    assert summary["generated_cases"] == 2
    assert summary["coherent_ordinary_cases"] == 1
    assert summary["behavioral_review_cases"] == 1
    assert summary["priority_distribution"].get("high", 0) >= 1
    assert summary["priority_distribution"].get("low", 0) >= 1


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
