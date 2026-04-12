from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from reviewer.config import ReviewerPipelineConfig
from reviewer.models import GeneratedCase, ReviewCallResult
from reviewer.night_run import NightRunController
from reviewer.retention import ArtifactRetentionManager


FAMILIES = [
    "world_absence_poverty",
    "epistemic_fragility",
    "regulation_mode_validity_pressure",
    "ownership_self_prediction_instability",
    "memory_narrative_temptation",
]


class _FakeGenerator:
    def available_themes(self) -> set[str]:
        return set(FAMILIES)


class _FakePipeline:
    def __init__(self, fn: Callable[[int, str], dict[str, object]]) -> None:
        self._fn = fn
        self._seed = 0
        self.generator = _FakeGenerator()

    def set_seed_cursor(self, seed: int) -> None:
        self._seed = int(seed)

    def run_cycle(self, *, case_count: int | None = None, themes: list[str] | None = None) -> dict[str, object]:
        family = str((themes or [FAMILIES[0]])[0])
        outcome = dict(self._fn(self._seed, family))
        outcome.setdefault("case_id", f"{family}-seed-{self._seed}")
        outcome.setdefault("seed", self._seed)
        outcome.setdefault("theme", family)
        outcome.setdefault("scenario_family", family)
        outcome.setdefault("status", "semantic_review_completed")
        outcome.setdefault("action", "close")
        outcome.setdefault("overall_reading", "coherent_bounded_caution")
        outcome.setdefault("priority", "low")
        outcome.setdefault("signal_codes", [])
        outcome.setdefault("gap_codes", [])
        outcome.setdefault("triage_reason", "fake")
        return {"processed_cases": [outcome]}


def _cfg(tmp_path: Path) -> ReviewerPipelineConfig:
    cfg = ReviewerPipelineConfig.default()
    cfg.artifacts_root = str((tmp_path / "artifacts").resolve())
    cfg.night_run.warmup.enabled = False
    cfg.night_run.guardrails.heartbeat_interval_seconds = 1
    cfg.night_run.guardrails.checkpoint_interval_cases = 1
    cfg.night_run.guardrails.max_case_count = 20
    cfg.night_run.guardrails.max_rolling_infra_failure_rate = 1.0
    cfg.night_run.guardrails.max_rolling_behavioral_flag_rate = 1.0
    return cfg


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_balanced_scheduler_behavior_across_families(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.scheduler.mode = "balanced_round_robin"
    controller = NightRunController(pipeline=_FakePipeline(lambda seed, family: {}), config=cfg)
    summary = controller.run(mode="batch", max_cases=10, themes=FAMILIES, run_id="run-balanced")
    counts = summary["per_family_counts"]
    assert sum(counts.values()) == 10
    values = list(counts.values())
    assert max(values) - min(values) <= 1


def test_per_family_quota_enforcement(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.scheduler.family_quotas = {
        "world_absence_poverty": 2,
        "epistemic_fragility": 1,
    }
    controller = NightRunController(pipeline=_FakePipeline(lambda seed, family: {}), config=cfg)
    summary = controller.run(
        mode="long",
        max_cases=8,
        themes=["world_absence_poverty", "epistemic_fragility"],
        run_id="run-quota",
    )
    assert summary["status"] == "stopped"
    assert summary["stop_reason"] == "scheduler_exhausted"
    assert summary["per_family_counts"]["world_absence_poverty"] <= 2
    assert summary["per_family_counts"]["epistemic_fragility"] <= 1


def test_deterministic_seed_schedule_reproducibility(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.scheduler.mode = "weighted"
    cfg.night_run.scheduler.family_weights = {FAMILIES[0]: 3.0, FAMILIES[1]: 1.0}
    controller = NightRunController(pipeline=_FakePipeline(lambda seed, family: {}), config=cfg)
    controller.run(mode="batch", max_cases=12, themes=FAMILIES, run_id="run-repro-a")
    controller.run(mode="batch", max_cases=12, themes=FAMILIES, run_id="run-repro-b")
    p = Path(cfg.artifacts_root) / "runs"
    a = _read_jsonl(p / "run-repro-a" / "schedule.jsonl")
    b = _read_jsonl(p / "run-repro-b" / "schedule.jsonl")
    assert [(x["family"], x["seed"]) for x in a] == [(x["family"], x["seed"]) for x in b]


def test_checkpoint_save_load_and_resume_without_duplicates(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.guardrails.max_rolling_behavioral_flag_rate = 0.0
    cfg.night_run.guardrails.rolling_behavioral_rate_action = "pause"

    def first(seed: int, family: str) -> dict[str, object]:
        return {"action": "behavioral_review", "priority": "medium"}

    controller = NightRunController(pipeline=_FakePipeline(first), config=cfg)
    summary1 = controller.run(mode="batch", max_cases=3, themes=FAMILIES, run_id="run-resume")
    assert summary1["status"] == "paused"
    checkpoint = Path(cfg.artifacts_root) / "runs" / "run-resume" / "checkpoint.json"
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["completed_cases"] == 1

    cfg.night_run.guardrails.max_rolling_behavioral_flag_rate = 1.0
    cfg.night_run.guardrails.rolling_behavioral_rate_action = "warn"
    controller2 = NightRunController(pipeline=_FakePipeline(lambda seed, family: {}), config=cfg)
    summary2 = controller2.run(mode="batch", run_id="run-resume", resume=True)
    state2 = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert summary2["total_cases"] == 3
    assert len(state2["completed_case_ids"]) == 3
    assert len(set(state2["completed_case_ids"])) == 3


def test_behavioral_infra_separation_bookkeeping(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    def fn(seed: int, family: str) -> dict[str, object]:
        if seed % 3 == 0:
            return {"action": "close", "overall_reading": "coherent_bounded_caution", "priority": "low"}
        if seed % 3 == 1:
            return {"action": "behavioral_review", "overall_reading": "likely_behavioral_problem", "priority": "medium"}
        return {"action": "infra_review", "status": "parse_error"}

    controller = NightRunController(pipeline=_FakePipeline(fn), config=cfg)
    summary = controller.run(mode="batch", max_cases=9, themes=FAMILIES, run_id="run-bookkeeping")
    assert sum(summary["behavioral_review_counts_by_family"].values()) == 3
    assert sum(summary["infra_review_counts_by_family"].values()) == 3


def test_heartbeat_and_summary_artifacts_exist(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    controller = NightRunController(pipeline=_FakePipeline(lambda seed, family: {}), config=cfg)
    summary = controller.run(mode="batch", max_cases=4, themes=FAMILIES, run_id="run-artifacts")
    run_dir = Path(cfg.artifacts_root) / "runs" / "run-artifacts"
    assert (run_dir / "heartbeat.json").exists()
    assert (run_dir / "checkpoint.json").exists()
    assert (run_dir / "run_summary.json").exists()
    assert (run_dir / "run_summary.md").exists()
    assert summary["status"] in {"completed", "stopped", "paused"}


def test_guardrail_trigger_behavior(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.guardrails.max_consecutive_infra_failures = 2
    cfg.night_run.guardrails.max_rolling_infra_failure_rate = 2.0

    def fn(seed: int, family: str) -> dict[str, object]:
        return {"action": "infra_review", "status": "parse_error"}

    controller = NightRunController(pipeline=_FakePipeline(fn), config=cfg)
    summary = controller.run(mode="long", max_cases=10, themes=FAMILIES, run_id="run-infra-guard")
    assert summary["status"] == "stopped"
    assert summary["stop_reason"] == "max_consecutive_infra_failures_guardrail"


def test_drift_warning_generation(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.guardrails.warn_signal_code_dominance = 0.3
    cfg.night_run.guardrails.warn_gap_code_dominance = 0.3
    cfg.night_run.guardrails.warn_family_imbalance_share = 0.9

    def fn(seed: int, family: str) -> dict[str, object]:
        return {
            "action": "behavioral_review",
            "overall_reading": "plausible_but_needs_review",
            "priority": "medium",
            "signal_codes": ["t03_honest_nonconvergence"],
            "gap_codes": ["unclear_resolution_step"],
        }

    controller = NightRunController(pipeline=_FakePipeline(fn), config=cfg)
    summary = controller.run(mode="batch", max_cases=6, themes=FAMILIES, run_id="run-drift")
    warning_codes = {row["code"] for row in summary["rolling_drift_warnings"]}
    assert "signal_code_dominance_warning" in warning_codes
    assert "gap_code_dominance_warning" in warning_codes


def test_warmup_phase_guardrail(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.night_run.warmup.enabled = True
    cfg.night_run.warmup.case_count = 3
    cfg.night_run.warmup.max_infra_failures = 0
    cfg.night_run.warmup.max_parse_failures = 10
    cfg.night_run.guardrails.max_rolling_infra_failure_rate = 2.0

    def fn(seed: int, family: str) -> dict[str, object]:
        return {"action": "infra_review", "status": "parse_error"}

    controller = NightRunController(pipeline=_FakePipeline(fn), config=cfg)
    summary = controller.run(mode="long", max_cases=10, themes=FAMILIES, run_id="run-warmup-stop")
    assert summary["status"] == "stopped"
    assert summary["stop_reason"] == "warmup_infra_failure_guardrail"


def test_ordinary_retention_discipline_for_large_run() -> None:
    root = Path(__file__).resolve().parents[2] / "artifacts" / "reviewer" / "tmp-retention-test"
    if root.exists():
        for item in sorted(root.glob("**/*"), reverse=True):
            if item.is_file():
                item.unlink(missing_ok=True)
        for item in sorted(root.glob("**/*"), reverse=True):
            if item.is_dir():
                item.rmdir()
    root.mkdir(parents=True, exist_ok=True)
    policy = ReviewerPipelineConfig.default().retention
    policy.keep_non_suspicious_trace = False
    manager = ArtifactRetentionManager(root=root, policy=policy)
    trace = root / "active" / "trace.jsonl"
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text("{}", encoding="utf-8")
    case = GeneratedCase(
        case_id="retention-case",
        seed=1,
        theme="epistemic_fragility",
        scenario_family="epistemic_fragility",
        scenario_intent="intent",
        paired_with=None,
        key_tension_axis=("axis",),
        what_to_inspect_in_trace=("subject_tick",),
        why_this_case_exists="test",
        trace_path=str(trace),
        generation_params={},
    )
    review = ReviewCallResult(
        tier="tier1",
        model="gemma3:4b",
        case_id="retention-case",
        status="semantic_review_completed",
        endpoint="/api/chat",
        request_payload={},
        raw_http_response_body="{}",
        extracted_text="{}",
        response_field_used="message.content",
        thinking_present=False,
        prompt_eval_count=1,
        eval_count=1,
        latency_ms=1.0,
        timeout=False,
        retry_count=0,
        parsed_json={"overall_reading": "coherent_bounded_caution", "human_review_priority": "low", "confidence": 0.9},
        schema_warnings=(),
        nonfatal_warnings=(),
        error_message=None,
        model_case_id=None,
    )
    manager.record_ordinary(case=case, reviews=[review], triage_reason="ordinary")
    assert not trace.exists()
    assert (root / "summaries" / "ordinary_cases.jsonl").exists()
