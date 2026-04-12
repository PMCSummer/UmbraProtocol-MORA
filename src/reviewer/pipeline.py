from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reviewer.api_client import OllamaClient, OllamaGenerateDiagnostics
from reviewer.case_generator import SeededCaseGenerator
from reviewer.config import ReviewerPipelineConfig, TierConfig
from reviewer.models import (
    GAP_CODE_ALLOWED,
    SIGNAL_CODE_ALLOWED,
    GeneratedCase,
    ReviewCallResult,
    ReviewerSchemaError,
    extract_first_json_object,
    normalize_reviewer_output,
)
from reviewer.queue import CaseWorkQueue
from reviewer.retention import ArtifactRetentionManager
from reviewer.triage import decide_triage

SEMANTIC_STATUS = "semantic_review_completed"
PROMPT_FILE_BY_TIER = {
    "tier1": "v4_tier1_calibrated_bounded_deoverflag.md",
    "tier2": "v4_tier1_calibrated_bounded_deoverflag.md",
    "tier3": "v4_tier1_calibrated_bounded_deoverflag.md",
}
MINIMAL_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "overall_reading": {
            "type": "string",
            "enum": [
                "coherent_bounded_caution",
                "coherent_abstention_or_revalidation",
                "plausible_but_needs_review",
                "likely_behavioral_problem",
                "insufficient_evidence",
            ],
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "suspicious_segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                    "signal_code": {
                        "type": "string",
                        "enum": sorted(SIGNAL_CODE_ALLOWED),
                    },
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["module", "signal_code", "severity"],
                "additionalProperties": False,
            },
        },
        "likely_observability_gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "module_or_transition": {"type": "string"},
                    "gap_code": {
                        "type": "string",
                        "enum": sorted(GAP_CODE_ALLOWED),
                    },
                },
                "required": ["module_or_transition", "gap_code"],
                "additionalProperties": False,
            },
        },
        "human_review_priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "final_note": {"type": "string"},
    },
    "required": [
        "overall_reading",
        "confidence",
        "suspicious_segments",
        "likely_observability_gaps",
        "human_review_priority",
        "final_note",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True, slots=True)
class _TierCaseResult:
    case: GeneratedCase
    review: ReviewCallResult


class LocalStatelessReviewerPipeline:
    def __init__(
        self,
        *,
        config: ReviewerPipelineConfig,
        generator: SeededCaseGenerator | None = None,
        client: OllamaClient | None = None,
        retention: ArtifactRetentionManager | None = None,
    ) -> None:
        self.config = config
        self.generator = generator or SeededCaseGenerator()
        self.client = client or OllamaClient(
            base_url=config.ollama_base_url,
            timeout_seconds=config.request_timeout_seconds,
            retry_count=config.retry_count,
        )
        self.artifacts_root = Path(config.artifacts_root).expanduser().resolve()
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.retention = retention or ArtifactRetentionManager(
            root=self.artifacts_root,
            policy=config.retention,
        )
        self._prompt_cache: dict[str, str] = {}
        self._pause_flag = threading.Event()
        self._stop_flag = threading.Event()
        self._seed_cursor = config.generation.base_seed
        self._status_lock = threading.Lock()
        self._last_status: dict[str, Any] = {}

    def set_paused(self, paused: bool) -> None:
        if paused:
            self._pause_flag.set()
        else:
            self._pause_flag.clear()

    def stop(self) -> None:
        self._stop_flag.set()

    def health(self) -> dict[str, Any]:
        return self.client.health()

    def _wait_if_paused(self) -> None:
        while self._pause_flag.is_set() and not self._stop_flag.is_set():
            time.sleep(0.05)

    def _enabled_tiers(self) -> list[str]:
        ordered = ["tier1", "tier2", "tier3"]
        return [
            name
            for name in ordered
            if name in self.config.tiers and self.config.tiers[name].enabled
        ]

    def _load_prompt_template(self, tier_name: str) -> str:
        if tier_name in self._prompt_cache:
            return self._prompt_cache[tier_name]
        prompt_name = PROMPT_FILE_BY_TIER[tier_name]
        path = Path(self.config.prompt_dir).expanduser().resolve() / prompt_name
        template = path.read_text(encoding="utf-8")
        self._prompt_cache[tier_name] = template
        return template

    def _compact_trace_payload(self, trace_text: str, *, tier_config: TierConfig) -> str:
        max_chars = tier_config.max_trace_payload_chars
        if max_chars is None or int(max_chars) <= 0 or len(trace_text) <= int(max_chars):
            return trace_text
        limit = int(max_chars)
        policy = str(tier_config.trace_compaction_policy or "none").lower()
        if policy == "tail":
            return trace_text[-limit:]
        if policy == "head_tail":
            head = max(1, int(limit * 0.6))
            tail = max(1, limit - head)
            marker = "\n...TRUNCATED...\n"
            return trace_text[:head] + marker + trace_text[-tail:]
        return trace_text[:limit]

    def _build_review_prompt(
        self,
        *,
        tier_name: str,
        tier_config: TierConfig,
        case: GeneratedCase,
    ) -> str:
        trace_text = Path(case.trace_path).read_text(encoding="utf-8")
        trace_text = self._compact_trace_payload(trace_text, tier_config=tier_config)
        package = {
            "case_id": case.case_id,
            "scenario_family": case.scenario_family,
            "scenario_intent": case.scenario_intent,
            "key_tension_axis": list(case.key_tension_axis),
            "trace_jsonl": trace_text,
        }
        template = self._load_prompt_template(tier_name)
        return f"{template}\n\nREVIEW_PACKAGE_JSON:\n{json.dumps(package, ensure_ascii=True)}"

    def _client_call(
        self,
        *,
        model: str,
        prompt: str,
        timeout_seconds: float,
        retry_count: int,
        tier_config: TierConfig,
    ) -> OllamaGenerateDiagnostics:
        if hasattr(self.client, "generate_with_diagnostics"):
            return self.client.generate_with_diagnostics(
                model=model,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
                output_json_schema=MINIMAL_REVIEW_SCHEMA,
                temperature=tier_config.temperature,
                num_predict=tier_config.num_predict,
                num_ctx=tier_config.num_ctx,
                think=False,
            )
        raw = self.client.generate(
            model=model,
            prompt=prompt,
            timeout_seconds=timeout_seconds,  # type: ignore[call-arg]
            retry_count=retry_count,  # type: ignore[call-arg]
        )
        return OllamaGenerateDiagnostics(
            endpoint="/api/chat",
            request_payload={"model": model},
            raw_http_response_body="",
            extracted_text=raw,
            response_field_used="response",
            thinking_present=False,
            prompt_eval_count=None,
            eval_count=None,
            status="ok" if str(raw).strip() else "empty_response",
            error_message=None if str(raw).strip() else "empty model response text",
            timeout=False,
            retry_count=0,
            latency_ms=0.0,
        )

    def _review_case(self, *, tier_name: str, tier_config: TierConfig, case: GeneratedCase) -> ReviewCallResult:
        prompt = self._build_review_prompt(
            tier_name=tier_name,
            tier_config=tier_config,
            case=case,
        )
        timeout_s = (
            self.config.request_timeout_seconds
            if tier_config.request_timeout_seconds is None
            else float(tier_config.request_timeout_seconds)
        )
        retry_count = (
            self.config.retry_count
            if tier_config.retry_count is None
            else int(tier_config.retry_count)
        )
        diagnostics = self._client_call(
            model=tier_config.model,
            prompt=prompt,
            timeout_seconds=timeout_s,
            retry_count=retry_count,
            tier_config=tier_config,
        )
        base = {
            "tier": tier_name,
            "model": tier_config.model,
            "case_id": case.case_id,
            "endpoint": diagnostics.endpoint,
            "request_payload": diagnostics.request_payload,
            "raw_http_response_body": diagnostics.raw_http_response_body,
            "extracted_text": diagnostics.extracted_text,
            "response_field_used": diagnostics.response_field_used,
            "thinking_present": diagnostics.thinking_present,
            "prompt_eval_count": diagnostics.prompt_eval_count,
            "eval_count": diagnostics.eval_count,
            "latency_ms": diagnostics.latency_ms,
            "timeout": diagnostics.timeout,
            "retry_count": diagnostics.retry_count,
        }
        if diagnostics.status != "ok":
            return ReviewCallResult(
                status=diagnostics.status,
                parsed_json=None,
                schema_warnings=(),
                nonfatal_warnings=(),
                error_message=diagnostics.error_message,
                model_case_id=None,
                **base,
            )
        try:
            parsed = extract_first_json_object(diagnostics.extracted_text)
        except ReviewerSchemaError as exc:
            return ReviewCallResult(
                status="parse_error",
                parsed_json=None,
                schema_warnings=(),
                nonfatal_warnings=(),
                error_message=str(exc),
                model_case_id=None,
                **base,
            )
        normalized = normalize_reviewer_output(parsed, expected_case_id=case.case_id)
        status = SEMANTIC_STATUS if not normalized.schema_warnings else "schema_warning"
        error_message = None
        if normalized.schema_warnings:
            error_message = "schema_warning:" + ",".join(normalized.schema_warnings)
        return ReviewCallResult(
            status=status,
            parsed_json=normalized.normalized_payload,
            schema_warnings=normalized.schema_warnings,
            nonfatal_warnings=normalized.nonfatal_warnings,
            error_message=error_message,
            model_case_id=normalized.model_case_id,
            **base,
        )

    def _run_tier_workers(self, *, tier_name: str, cases: list[GeneratedCase]) -> list[_TierCaseResult]:
        if not cases:
            return []
        tier_cfg = self.config.tiers[tier_name]
        queue = CaseWorkQueue(cases, id_getter=lambda item: item.case_id)
        output: list[_TierCaseResult] = []
        output_lock = threading.Lock()

        def worker_loop() -> None:
            while not self._stop_flag.is_set():
                self._wait_if_paused()
                item = queue.get(timeout=0.1)
                if item is None:
                    stats = queue.stats()
                    if stats.pending == 0 and stats.in_flight == 0:
                        return
                    continue
                try:
                    review = self._review_case(tier_name=tier_name, tier_config=tier_cfg, case=item)
                    with output_lock:
                        output.append(_TierCaseResult(case=item, review=review))
                finally:
                    queue.mark_done(item)

        workers = [
            threading.Thread(target=worker_loop, daemon=True, name=f"{tier_name}-worker-{idx}")
            for idx in range(max(1, tier_cfg.max_parallel_workers))
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        return output

    def _set_status(self, payload: dict[str, Any]) -> None:
        with self._status_lock:
            self._last_status = payload
        self.retention.write_status(payload)

    def latest_status(self) -> dict[str, Any]:
        with self._status_lock:
            return dict(self._last_status)

    def current_seed_cursor(self) -> int:
        return int(self._seed_cursor)

    def set_seed_cursor(self, seed: int) -> None:
        self._seed_cursor = int(seed)

    def _generate_cases(self, *, count: int, themes: list[str] | None) -> list[GeneratedCase]:
        traces_dir = self.artifacts_root / "active"
        cases: list[GeneratedCase] = []
        available_themes = sorted(themes or self.config.generation.themes)
        if not available_themes:
            available_themes = sorted(self.generator.available_themes())
        for _ in range(count):
            if self._stop_flag.is_set():
                break
            self._wait_if_paused()
            theme = available_themes[self._seed_cursor % len(available_themes)]
            case = self.generator.generate_case(
                seed=self._seed_cursor,
                theme=theme,
                traces_output_dir=traces_dir,
            )
            self._seed_cursor += 1
            cases.append(case)
        return cases

    def run_cycle(self, *, case_count: int | None = None, themes: list[str] | None = None) -> dict[str, Any]:
        if self._stop_flag.is_set():
            return {"stopped": True, "reason": "stop requested before cycle"}

        count = int(case_count or self.config.generation.max_cases_per_cycle)
        cycle_started = time.time()
        cases = self._generate_cases(count=count, themes=themes)
        enabled_tiers = self._enabled_tiers()

        case_state: dict[str, dict[str, Any]] = {
            case.case_id: {"case": case, "reviews": []} for case in cases
        }
        pending = list(cases)
        theme_counters: dict[str, int] = defaultdict(int)
        tier_counters: dict[str, int] = defaultdict(int)
        status_counters: dict[str, int] = defaultdict(int)
        priority_counters: dict[str, int] = defaultdict(int)
        signal_code_counters: dict[str, int] = defaultdict(int)
        gap_code_counters: dict[str, int] = defaultdict(int)
        processed_cases: list[dict[str, Any]] = []
        all_latencies_ms: list[float] = []
        prompt_eval_counts: list[int] = []
        behavioral_review_count = 0
        infra_review_count = 0
        coherent_ordinary_count = 0

        for tier_name in enabled_tiers:
            if not pending or self._stop_flag.is_set():
                break
            self._set_status(
                {
                    "stage": "reviewing",
                    "tier": tier_name,
                    "pending_cases": len(pending),
                    "total_cases": len(cases),
                    "active_workers": self.config.tiers[tier_name].max_parallel_workers,
                    "queue_size": len(pending),
                    "behavioral_review_cases": behavioral_review_count,
                    "infra_review_cases": infra_review_count,
                    "coherent_ordinary_cases": coherent_ordinary_count,
                }
            )
            tier_results = self._run_tier_workers(tier_name=tier_name, cases=pending)
            next_pending: list[GeneratedCase] = []
            for item in tier_results:
                case_state[item.case.case_id]["reviews"].append(item.review)
                theme_counters[item.case.theme] += 1
                tier_counters[tier_name] += 1
                status_counters[item.review.status] += 1
                all_latencies_ms.append(float(item.review.latency_ms))
                if isinstance(item.review.prompt_eval_count, int):
                    prompt_eval_counts.append(item.review.prompt_eval_count)

                if self.config.diagnostic_mode:
                    self.retention.record_call_diagnostics(case=item.case, review=item.review)

                if item.review.status != SEMANTIC_STATUS:
                    self.retention.record_failure(case=item.case, review=item.review)
                    infra_review_count += 1
                    self.retention.record_infra_review(
                        case=item.case,
                        reviews=case_state[item.case.case_id]["reviews"],
                        triage_reason=f"infrastructure_or_schema_failure:{item.review.status}",
                    )
                    processed_cases.append(
                        {
                            "case_id": item.case.case_id,
                            "seed": item.case.seed,
                            "theme": item.case.theme,
                            "scenario_family": item.case.scenario_family,
                            "status": item.review.status,
                            "action": "infra_review",
                            "overall_reading": None,
                            "priority": None,
                            "signal_codes": [],
                            "gap_codes": [],
                            "triage_reason": f"infrastructure_or_schema_failure:{item.review.status}",
                        }
                    )
                    continue

                decision = decide_triage(
                    review_json=item.review.parsed_json or {},
                    tier_name=tier_name,
                    config=self.config,
                )
                if item.review.parsed_json is not None:
                    item.review.parsed_json["human_review_priority"] = decision.normalized_priority
                    priority_counters[decision.normalized_priority] += 1
                    suspicious_segments = item.review.parsed_json.get("suspicious_segments")
                    if isinstance(suspicious_segments, list):
                        for segment in suspicious_segments:
                            if not isinstance(segment, dict):
                                continue
                            signal_code = str(segment.get("signal_code", "")).strip()
                            if signal_code:
                                signal_code_counters[signal_code] += 1
                    gaps = item.review.parsed_json.get("likely_observability_gaps")
                    if isinstance(gaps, list):
                        for gap in gaps:
                            if not isinstance(gap, dict):
                                continue
                            gap_code = str(gap.get("gap_code", "")).strip()
                            if gap_code:
                                gap_code_counters[gap_code] += 1
                self.retention.record_semantic_review(case=item.case, review=item.review)
                parsed_json = item.review.parsed_json or {}
                signal_codes: list[str] = []
                suspicious_segments = parsed_json.get("suspicious_segments")
                if isinstance(suspicious_segments, list):
                    for segment in suspicious_segments:
                        if isinstance(segment, dict):
                            code = str(segment.get("signal_code", "")).strip()
                            if code:
                                signal_codes.append(code)
                gap_codes: list[str] = []
                gaps = parsed_json.get("likely_observability_gaps")
                if isinstance(gaps, list):
                    for gap in gaps:
                        if isinstance(gap, dict):
                            code = str(gap.get("gap_code", "")).strip()
                            if code:
                                gap_codes.append(code)
                if decision.action == "close":
                    coherent_ordinary_count += 1
                    self.retention.record_ordinary(
                        case=item.case,
                        reviews=case_state[item.case.case_id]["reviews"],
                        triage_reason=decision.reason,
                    )
                elif decision.action == "behavioral_review":
                    behavioral_review_count += 1
                    self.retention.record_behavioral_review(
                        case=item.case,
                        reviews=case_state[item.case.case_id]["reviews"],
                        triage_reason=decision.reason,
                    )
                elif decision.action == "infra_review":
                    infra_review_count += 1
                    self.retention.record_infra_review(
                        case=item.case,
                        reviews=case_state[item.case.case_id]["reviews"],
                        triage_reason=decision.reason,
                    )
                elif decision.action == "escalate":
                    next_pending.append(item.case)
                processed_cases.append(
                    {
                        "case_id": item.case.case_id,
                        "seed": item.case.seed,
                        "theme": item.case.theme,
                        "scenario_family": item.case.scenario_family,
                        "status": item.review.status,
                        "action": decision.action,
                        "overall_reading": parsed_json.get("overall_reading"),
                        "priority": parsed_json.get("human_review_priority"),
                        "signal_codes": signal_codes,
                        "gap_codes": gap_codes,
                        "triage_reason": decision.reason,
                    }
                )
            pending = next_pending

        for case in pending:
            infra_review_count += 1
            self.retention.record_infra_review(
                case=case,
                reviews=case_state[case.case_id]["reviews"],
                triage_reason="exhausted_tiers_without_close",
            )
            processed_cases.append(
                {
                    "case_id": case.case_id,
                    "seed": case.seed,
                    "theme": case.theme,
                    "scenario_family": case.scenario_family,
                    "status": "exhausted_tiers_without_close",
                    "action": "infra_review",
                    "overall_reading": None,
                    "priority": None,
                    "signal_codes": [],
                    "gap_codes": [],
                    "triage_reason": "exhausted_tiers_without_close",
                }
            )

        duration_s = round(time.time() - cycle_started, 3)
        avg_latency_ms = round(sum(all_latencies_ms) / len(all_latencies_ms), 3) if all_latencies_ms else 0.0
        prompt_eval_distribution = {
            "count": len(prompt_eval_counts),
            "min": min(prompt_eval_counts) if prompt_eval_counts else None,
            "max": max(prompt_eval_counts) if prompt_eval_counts else None,
            "avg": round(sum(prompt_eval_counts) / len(prompt_eval_counts), 3)
            if prompt_eval_counts
            else None,
            "values": sorted(prompt_eval_counts),
        }
        summary = {
            "cycle_duration_s": duration_s,
            "generated_cases": len(cases),
            "coherent_ordinary_cases": coherent_ordinary_count,
            "behavioral_review_cases": behavioral_review_count,
            "infra_review_cases": infra_review_count,
            # Backward-compatible aliases:
            "closed_cases": coherent_ordinary_count,
            "suspicious_cases": behavioral_review_count,
            "per_theme_reviews": dict(theme_counters),
            "per_tier_reviews": dict(tier_counters),
            "per_status_reviews": dict(status_counters),
            "priority_distribution": dict(priority_counters),
            "top_signal_code_counts": dict(
                sorted(signal_code_counters.items(), key=lambda item: (-item[1], item[0]))[:10]
            ),
            "top_gap_code_counts": dict(
                sorted(gap_code_counters.items(), key=lambda item: (-item[1], item[0]))[:10]
            ),
            "avg_latency_ms": avg_latency_ms,
            "prompt_eval_count_distribution": prompt_eval_distribution,
            "diagnostic_mode": self.config.diagnostic_mode,
            "model_health": self.health(),
            "stop_requested": self._stop_flag.is_set(),
            "processed_cases": processed_cases,
        }
        self._set_status({"stage": "idle", **summary})
        return summary

    def run_sequential_diagnostics(
        self,
        *,
        tier_name: str = "tier1",
        case_count: int = 1,
        themes: list[str] | None = None,
    ) -> dict[str, Any]:
        if tier_name not in self.config.tiers:
            raise ValueError(f"unknown tier_name={tier_name!r}")
        original_diagnostic_mode = self.config.diagnostic_mode
        original_tier_enabled = {
            key: tier.enabled for key, tier in self.config.tiers.items()
        }
        original_workers = {
            key: tier.max_parallel_workers for key, tier in self.config.tiers.items()
        }
        try:
            self.config.diagnostic_mode = True
            for key, tier in self.config.tiers.items():
                tier.enabled = key == tier_name
                if key == tier_name:
                    tier.max_parallel_workers = 1
            summary = self.run_cycle(case_count=case_count, themes=themes)
            summary["sequential_diagnostic_mode"] = True
            summary["sequential_tier"] = tier_name
            return summary
        finally:
            self.config.diagnostic_mode = original_diagnostic_mode
            for key, enabled in original_tier_enabled.items():
                self.config.tiers[key].enabled = enabled
            for key, workers in original_workers.items():
                self.config.tiers[key].max_parallel_workers = workers

    def run_forever(self, *, cycle_interval_seconds: float = 0.2) -> None:
        while not self._stop_flag.is_set():
            self.run_cycle()
            elapsed = 0.0
            while elapsed < cycle_interval_seconds and not self._stop_flag.is_set():
                self._wait_if_paused()
                time.sleep(0.05)
                elapsed += 0.05
