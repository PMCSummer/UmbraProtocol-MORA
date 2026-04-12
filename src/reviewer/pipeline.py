from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reviewer.api_client import OllamaClient
from reviewer.case_generator import SeededCaseGenerator
from reviewer.config import ReviewerPipelineConfig, TierConfig
from reviewer.models import (
    GeneratedCase,
    ReviewCallResult,
    ReviewerSchemaError,
    extract_first_json_object,
    validate_reviewer_output,
)
from reviewer.queue import CaseWorkQueue
from reviewer.retention import ArtifactRetentionManager
from reviewer.triage import decide_triage

MODULE_GLOSSARY = {
    "world_adapter": "external world seam availability and effect feedback",
    "world_entry_contract": "world claim admissibility and W01 readiness",
    "epistemics": "source/modality/confidence grounding discipline",
    "regulation": "pressure and override gate shaping",
    "c04_mode_arbitration": "mode selection and arbitration stability",
    "c05_temporal_validity": "legality/revalidation pressure on reuse",
    "s01_efference_copy": "action projection vs observed change comparison",
    "s02_prediction_boundary": "self/world seam boundary and integrity",
    "s03_ownership_weighted_learning": "ownership-weighted update routing",
    "m_minimal": "minimal memory claim safety",
    "n_minimal": "minimal narrative commitment safety",
    "bounded_outcome_resolution": "bounded outcome class before subject output",
    "subject_tick": "final execution outcome and materialization mode",
}

MODULE_FILE_MAPPING = {
    "subject_tick": "src/substrate/subject_tick/update.py",
    "world_adapter": "src/substrate/world_adapter/adapter.py",
    "world_entry_contract": "src/substrate/world_entry_contract/policy.py",
    "epistemics": "src/substrate/epistemics/grounding.py",
    "regulation": "src/substrate/viability_control/update.py",
    "c04_mode_arbitration": "src/substrate/mode_arbitration/update.py",
    "c05_temporal_validity": "src/substrate/temporal_validity/update.py",
}


@dataclass(frozen=True, slots=True)
class _TierCaseResult:
    case: GeneratedCase
    review: ReviewCallResult


def _default_review_payload(*, case_id: str, reason: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "overall_reading": "insufficient_evidence",
        "confidence": 0.0,
        "behavior_summary": [],
        "coherent_segments": [],
        "suspicious_segments": [],
        "likely_observability_gaps": [],
        "paired_case_comparison": {
            "used": False,
            "paired_case_id": None,
            "main_behavior_shift": "",
            "is_shift_plausible": False,
            "notes": "",
        },
        "human_review_priority": "high",
        "code_focus_candidates": [],
        "final_note": reason,
    }


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
        prompt_name = {
            "tier1": "v1_tier1_prefilter.md",
            "tier2": "v1_tier2_main.md",
            "tier3": "v1_tier3_second_opinion.md",
        }[tier_name]
        path = Path(self.config.prompt_dir).expanduser().resolve() / prompt_name
        template = path.read_text(encoding="utf-8")
        self._prompt_cache[tier_name] = template
        return template

    def _build_review_prompt(self, *, tier_name: str, case: GeneratedCase) -> str:
        trace_text = Path(case.trace_path).read_text(encoding="utf-8")
        package = {
            "case_id": case.case_id,
            "theme": case.theme,
            "scenario_family": case.scenario_family,
            "scenario_intent": case.scenario_intent,
            "key_tension_axis": list(case.key_tension_axis),
            "what_to_inspect_in_trace": list(case.what_to_inspect_in_trace),
            "paired_case_id": case.paired_with,
            "generation_params": case.generation_params,
            "module_glossary": MODULE_GLOSSARY,
            "module_file_mapping": MODULE_FILE_MAPPING,
            "trace_jsonl": trace_text,
        }
        template = self._load_prompt_template(tier_name)
        return f"{template}\n\nREVIEW_PACKAGE_JSON:\n{json.dumps(package, ensure_ascii=True)}"

    def _review_case(self, *, tier_name: str, tier_config: TierConfig, case: GeneratedCase) -> ReviewCallResult:
        # Stateless guarantee: each call builds standalone prompt and never reuses prior model context.
        prompt = self._build_review_prompt(tier_name=tier_name, case=case)
        try:
            raw = self.client.generate(model=tier_config.model, prompt=prompt)
            parsed = extract_first_json_object(raw)
            parsed = validate_reviewer_output(parsed, expected_case_id=case.case_id)
            return ReviewCallResult(
                tier=tier_name,
                model=tier_config.model,
                raw_text=raw,
                parsed_json=parsed,
            )
        except Exception as exc:  # noqa: BLE001
            fallback = _default_review_payload(case_id=case.case_id, reason=str(exc))
            return ReviewCallResult(
                tier=tier_name,
                model=tier_config.model,
                raw_text="",
                parsed_json=fallback,
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
        suspicious_count = 0
        closed_count = 0

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
                    "suspicious_count": suspicious_count,
                    "closed_count": closed_count,
                }
            )
            tier_results = self._run_tier_workers(tier_name=tier_name, cases=pending)
            next_pending: list[GeneratedCase] = []
            for item in tier_results:
                case_state[item.case.case_id]["reviews"].append(item.review)
                theme_counters[item.case.theme] += 1
                tier_counters[tier_name] += 1
                decision = decide_triage(
                    review_json=item.review.parsed_json,
                    tier_name=tier_name,
                    config=self.config,
                )
                if decision.action == "close":
                    closed_count += 1
                    self.retention.record_ordinary(
                        case=item.case,
                        reviews=case_state[item.case.case_id]["reviews"],
                        triage_reason=decision.reason,
                    )
                elif decision.action == "freeze":
                    suspicious_count += 1
                    self.retention.record_suspicious(
                        case=item.case,
                        reviews=case_state[item.case.case_id]["reviews"],
                        triage_reason=decision.reason,
                    )
                elif decision.action == "escalate":
                    next_pending.append(item.case)
            pending = next_pending

        # If any case still pending after the last enabled tier, freeze it for human review.
        for case in pending:
            suspicious_count += 1
            self.retention.record_suspicious(
                case=case,
                reviews=case_state[case.case_id]["reviews"],
                triage_reason="exhausted_tiers_without_close",
            )

        duration_s = round(time.time() - cycle_started, 3)
        summary = {
            "cycle_duration_s": duration_s,
            "generated_cases": len(cases),
            "closed_cases": closed_count,
            "suspicious_cases": suspicious_count,
            "per_theme_reviews": dict(theme_counters),
            "per_tier_reviews": dict(tier_counters),
            "model_health": self.health(),
            "stop_requested": self._stop_flag.is_set(),
        }
        self._set_status({"stage": "idle", **summary})
        return summary

    def run_forever(self, *, cycle_interval_seconds: float = 0.2) -> None:
        while not self._stop_flag.is_set():
            self.run_cycle()
            elapsed = 0.0
            while elapsed < cycle_interval_seconds and not self._stop_flag.is_set():
                self._wait_if_paused()
                time.sleep(0.05)
                elapsed += 0.05

