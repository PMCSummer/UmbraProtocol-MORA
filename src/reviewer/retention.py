from __future__ import annotations

import json
import shutil
import time
from hashlib import sha1
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
    summaries_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    diagnostics_dir: Path = field(init=False)
    semantic_reviews_dir: Path = field(init=False)
    failures_dir: Path = field(init=False)
    behavioral_review_dir: Path = field(init=False)
    infra_review_dir: Path = field(init=False)
    ordinary_samples_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.active_dir = self.root / "active"
        self.summaries_dir = self.root / "summaries"
        self.logs_dir = self.root / "logs"
        self.diagnostics_dir = self.root / "diagnostics"
        self.semantic_reviews_dir = self.root / "semantic_reviews"
        self.failures_dir = self.root / "failures"
        self.behavioral_review_dir = self.root / "behavioral_review_queue"
        self.infra_review_dir = self.root / "infra_review_queue"
        self.ordinary_samples_dir = self.root / "ordinary_samples"
        for directory in (
            self.active_dir,
            self.summaries_dir,
            self.logs_dir,
            self.diagnostics_dir,
            self.semantic_reviews_dir,
            self.failures_dir,
            self.behavioral_review_dir,
            self.infra_review_dir,
            self.ordinary_samples_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def _call_artifact_name(self, *, tier: str, model: str, status: str) -> str:
        safe_model = model.replace(":", "_").replace("/", "_")
        return f"{int(time.time_ns())}_{tier}_{safe_model}_{status}.json"

    def _write_case_bundle(
        self,
        *,
        queue_dir: Path,
        case: GeneratedCase,
        reviews: list[ReviewCallResult],
    ) -> Path:
        dst = queue_dir / case.case_id
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
        return dst

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
        self._apply_diagnostics_retention_cap()
        return path

    def _apply_diagnostics_retention_cap(self) -> None:
        cap = self.policy.diagnostics_retention_max_files
        if cap is None or cap <= 0:
            return
        files = sorted(
            self.diagnostics_dir.glob("**/*.json"),
            key=lambda item: item.stat().st_mtime,
        )
        overflow = max(0, len(files) - cap)
        for path in files[:overflow]:
            path.unlink(missing_ok=True)

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

        keep_traces = (
            self.policy.keep_non_suspicious_trace
            if self.policy.keep_full_for_ordinary is None
            else bool(self.policy.keep_full_for_ordinary)
        )
        if not keep_traces:
            trace_path = Path(case.trace_path)
            if trace_path.exists():
                trace_path.unlink()
        else:
            self._apply_non_suspicious_retention_cap()

        sample_rate = max(0.0, min(1.0, float(self.policy.ordinary_full_bundle_sample_rate)))
        if sample_rate > 0.0:
            digest = sha1(case.case_id.encode("utf-8")).hexdigest()
            ratio = int(digest[:8], 16) / float(0xFFFFFFFF)
            if ratio <= sample_rate:
                self._write_case_bundle(
                    queue_dir=self.ordinary_samples_dir,
                    case=case,
                    reviews=reviews,
                )

    def _apply_non_suspicious_retention_cap(self) -> None:
        if self.policy.max_non_suspicious_traces <= 0:
            return
        traces = sorted(self.active_dir.glob("*.jsonl"), key=lambda path: path.stat().st_mtime)
        overflow = max(0, len(traces) - self.policy.max_non_suspicious_traces)
        for path in traces[:overflow]:
            path.unlink(missing_ok=True)

    def record_behavioral_review(
        self,
        *,
        case: GeneratedCase,
        reviews: list[ReviewCallResult],
        triage_reason: str,
    ) -> Path:
        dst = self._write_case_bundle(
            queue_dir=self.behavioral_review_dir,
            case=case,
            reviews=reviews,
        )
        latest = reviews[-1]
        index_row = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "case_id": case.case_id,
            "theme": case.theme,
            "scenario_family": case.scenario_family,
            "status": latest.status,
            "priority": (latest.parsed_json or {}).get("human_review_priority"),
            "overall_reading": (latest.parsed_json or {}).get("overall_reading"),
            "tier": latest.tier,
            "model": latest.model,
            "triage_reason": triage_reason,
            "artifact_dir": str(dst),
        }
        _append_jsonl(self.summaries_dir / "behavioral_review_queue.jsonl", index_row)
        # Keep existing UI compatibility: show behavioral queue in legacy suspicious list.
        _append_jsonl(self.summaries_dir / "suspicious_cases.jsonl", index_row)
        return dst

    def record_infra_review(
        self,
        *,
        case: GeneratedCase,
        reviews: list[ReviewCallResult],
        triage_reason: str,
    ) -> Path:
        dst = self._write_case_bundle(
            queue_dir=self.infra_review_dir,
            case=case,
            reviews=reviews,
        )
        latest = reviews[-1]
        index_row = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "case_id": case.case_id,
            "theme": case.theme,
            "scenario_family": case.scenario_family,
            "status": latest.status,
            "priority": (latest.parsed_json or {}).get("human_review_priority"),
            "overall_reading": (latest.parsed_json or {}).get("overall_reading"),
            "tier": latest.tier,
            "model": latest.model,
            "triage_reason": triage_reason,
            "artifact_dir": str(dst),
        }
        _append_jsonl(self.summaries_dir / "infra_review_queue.jsonl", index_row)
        return dst
