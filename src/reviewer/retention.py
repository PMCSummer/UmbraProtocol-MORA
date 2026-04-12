from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reviewer.config import RetentionPolicy
from reviewer.models import GeneratedCase, ReviewCallResult


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True))
        handle.write("\n")


@dataclass(slots=True)
class ArtifactRetentionManager:
    root: Path
    policy: RetentionPolicy
    active_dir: Path = field(init=False)
    suspicious_dir: Path = field(init=False)
    summaries_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    diagnostics_dir: Path = field(init=False)
    semantic_reviews_dir: Path = field(init=False)
    failures_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.active_dir = self.root / "active"
        self.suspicious_dir = self.root / "suspicious"
        self.summaries_dir = self.root / "summaries"
        self.logs_dir = self.root / "logs"
        self.diagnostics_dir = self.root / "diagnostics"
        self.semantic_reviews_dir = self.root / "semantic_reviews"
        self.failures_dir = self.root / "failures"
        for directory in (
            self.active_dir,
            self.suspicious_dir,
            self.summaries_dir,
            self.logs_dir,
            self.diagnostics_dir,
            self.semantic_reviews_dir,
            self.failures_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def _call_artifact_name(self, *, tier: str, model: str, status: str) -> str:
        safe_model = model.replace(":", "_").replace("/", "_")
        return f"{int(time.time_ns())}_{tier}_{safe_model}_{status}.json"

    def record_call_diagnostics(
        self,
        *,
        case: GeneratedCase,
        review: ReviewCallResult,
    ) -> Path:
        case_dir = self.diagnostics_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        path = case_dir / self._call_artifact_name(
            tier=review.tier,
            model=review.model,
            status=review.status,
        )
        payload = {
            "case_id": case.case_id,
            "tier": review.tier,
            "model": review.model,
            "status": review.status,
            "endpoint": review.endpoint,
            "request_payload": review.request_payload,
            "raw_http_response_body": review.raw_http_response_body,
            "extracted_text": review.extracted_text,
            "response_field_used": review.response_field_used,
            "thinking_present": review.thinking_present,
            "prompt_eval_count": review.prompt_eval_count,
            "eval_count": review.eval_count,
            "latency_ms": review.latency_ms,
            "timeout": review.timeout,
            "retry_count": review.retry_count,
            "schema_warnings": list(review.schema_warnings),
            "nonfatal_warnings": list(review.nonfatal_warnings),
            "error_message": review.error_message,
            "model_case_id": review.model_case_id,
            "parsed_json": review.parsed_json,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def record_semantic_review(
        self,
        *,
        case: GeneratedCase,
        review: ReviewCallResult,
    ) -> Path:
        case_dir = self.semantic_reviews_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        path = case_dir / self._call_artifact_name(
            tier=review.tier,
            model=review.model,
            status=review.status,
        )
        payload = {
            "case_id": case.case_id,
            "tier": review.tier,
            "model": review.model,
            "status": review.status,
            "parsed_json": review.parsed_json,
            "schema_warnings": list(review.schema_warnings),
            "nonfatal_warnings": list(review.nonfatal_warnings),
            "model_case_id": review.model_case_id,
            "response_field_used": review.response_field_used,
            "thinking_present": review.thinking_present,
            "prompt_eval_count": review.prompt_eval_count,
            "eval_count": review.eval_count,
            "latency_ms": review.latency_ms,
            "retry_count": review.retry_count,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def record_failure(
        self,
        *,
        case: GeneratedCase,
        review: ReviewCallResult,
    ) -> Path:
        case_dir = self.failures_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        path = case_dir / self._call_artifact_name(
            tier=review.tier,
            model=review.model,
            status=review.status,
        )
        payload = {
            "case_id": case.case_id,
            "tier": review.tier,
            "model": review.model,
            "status": review.status,
            "endpoint": review.endpoint,
            "error_message": review.error_message,
            "timeout": review.timeout,
            "retry_count": review.retry_count,
            "latency_ms": review.latency_ms,
            "schema_warnings": list(review.schema_warnings),
            "nonfatal_warnings": list(review.nonfatal_warnings),
            "raw_http_response_body": review.raw_http_response_body,
            "extracted_text": review.extracted_text,
            "response_field_used": review.response_field_used,
            "thinking_present": review.thinking_present,
            "prompt_eval_count": review.prompt_eval_count,
            "eval_count": review.eval_count,
            "model_case_id": review.model_case_id,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def write_status(self, status: dict[str, Any]) -> Path:
        path = self.logs_dir / "pipeline_status.json"
        path.write_text(
            json.dumps(status, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def record_ordinary(
        self,
        *,
        case: GeneratedCase,
        reviews: list[ReviewCallResult],
        triage_reason: str,
    ) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        latest = reviews[-1]
        row = {
            "timestamp": now,
            "case_id": case.case_id,
            "seed": case.seed,
            "theme": case.theme,
            "scenario_family": case.scenario_family,
            "tier": latest.tier,
            "model": latest.model,
            "status": latest.status,
            "overall_reading": (latest.parsed_json or {}).get("overall_reading"),
            "priority": (latest.parsed_json or {}).get("human_review_priority"),
            "confidence": (latest.parsed_json or {}).get("confidence"),
            "triage_reason": triage_reason,
            "trace_path": case.trace_path,
        }
        _append_jsonl(self.summaries_dir / "ordinary_cases.jsonl", row)

        if not self.policy.keep_non_suspicious_trace:
            trace_path = Path(case.trace_path)
            if trace_path.exists():
                trace_path.unlink()
        else:
            self._apply_non_suspicious_retention_cap()

    def _apply_non_suspicious_retention_cap(self) -> None:
        if self.policy.max_non_suspicious_traces <= 0:
            return
        traces = sorted(self.active_dir.glob("*.jsonl"), key=lambda path: path.stat().st_mtime)
        overflow = max(0, len(traces) - self.policy.max_non_suspicious_traces)
        for path in traces[:overflow]:
            path.unlink(missing_ok=True)

    def record_suspicious(
        self,
        *,
        case: GeneratedCase,
        reviews: list[ReviewCallResult],
        triage_reason: str,
    ) -> Path:
        dst = self.suspicious_dir / case.case_id
        dst.mkdir(parents=True, exist_ok=True)
        trace_src = Path(case.trace_path)
        trace_dst = dst / "trace.jsonl"
        if trace_src.exists():
            shutil.copy2(trace_src, trace_dst)
        (dst / "case.json").write_text(
            json.dumps(
                {
                    "case_id": case.case_id,
                    "seed": case.seed,
                    "theme": case.theme,
                    "scenario_family": case.scenario_family,
                    "scenario_intent": case.scenario_intent,
                    "paired_with": case.paired_with,
                    "key_tension_axis": list(case.key_tension_axis),
                    "what_to_inspect_in_trace": list(case.what_to_inspect_in_trace),
                    "why_this_case_exists": case.why_this_case_exists,
                    "generation_params": case.generation_params,
                    "trace_path": str(trace_dst),
                },
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        (dst / "reviews.json").write_text(
            json.dumps(
                [
                    {
                        "tier": item.tier,
                        "model": item.model,
                        "status": item.status,
                        "parsed_json": item.parsed_json,
                        "raw_http_response_body": item.raw_http_response_body,
                        "extracted_text": item.extracted_text,
                        "schema_warnings": list(item.schema_warnings),
                        "nonfatal_warnings": list(item.nonfatal_warnings),
                        "error_message": item.error_message,
                        "timeout": item.timeout,
                        "retry_count": item.retry_count,
                        "latency_ms": item.latency_ms,
                        "response_field_used": item.response_field_used,
                        "thinking_present": item.thinking_present,
                        "prompt_eval_count": item.prompt_eval_count,
                        "eval_count": item.eval_count,
                        "model_case_id": item.model_case_id,
                    }
                    for item in reviews
                ],
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        index_row = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "case_id": case.case_id,
            "theme": case.theme,
            "scenario_family": case.scenario_family,
            "status": reviews[-1].status,
            "priority": (reviews[-1].parsed_json or {}).get("human_review_priority"),
            "overall_reading": (reviews[-1].parsed_json or {}).get("overall_reading"),
            "tier": reviews[-1].tier,
            "model": reviews[-1].model,
            "triage_reason": triage_reason,
            "artifact_dir": str(dst),
        }
        _append_jsonl(self.summaries_dir / "suspicious_cases.jsonl", index_row)
        return dst
