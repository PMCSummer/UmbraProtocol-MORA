from __future__ import annotations

import json
import math
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reviewer.config import ReviewerPipelineConfig
from reviewer.pipeline import LocalStatelessReviewerPipeline


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True))
        handle.write("\n")


def _clamp_rate(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(slots=True)
class FamilyAssignment:
    family: str
    seed: int
    index: int


class DiversityScheduler:
    def __init__(
        self,
        *,
        families: list[str],
        base_seed: int,
        total_target: int,
        mode: str,
        weights: dict[str, float],
        quotas: dict[str, int],
        min_share: dict[str, float],
        max_share: dict[str, float],
        max_same_family_streak: int,
        state: dict[str, Any] | None = None,
    ) -> None:
        if not families:
            raise ValueError("families must not be empty")
        self.families = list(dict.fromkeys(families))
        self.base_seed = int(base_seed)
        self.total_target = max(1, int(total_target))
        self.mode = str(mode)
        self.weights = {f: max(0.0, float(weights.get(f, 1.0))) for f in self.families}
        self.quotas = {f: max(0, int(quotas.get(f, 0))) for f in self.families if f in quotas}
        self.min_share = {f: _clamp_rate(min_share.get(f, 0.0)) for f in self.families}
        self.max_share = {f: _clamp_rate(max_share.get(f, 1.0)) for f in self.families}
        self.max_same_family_streak = max(1, int(max_same_family_streak))
        self.index = 0
        self.round_robin_index = 0
        self.last_family: str | None = None
        self.last_streak = 0
        self.counts: Counter[str] = Counter({f: 0 for f in self.families})
        if state:
            self.index = int(state.get("index", 0))
            self.round_robin_index = int(state.get("round_robin_index", 0))
            self.last_family = state.get("last_family")
            self.last_streak = int(state.get("last_streak", 0))
            for f in self.families:
                self.counts[f] = int(dict(state.get("counts", {})).get(f, 0))

    def export_state(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "round_robin_index": self.round_robin_index,
            "last_family": self.last_family,
            "last_streak": self.last_streak,
            "counts": dict(self.counts),
        }

    def _required_min(self, family: str) -> int:
        return int(math.ceil(self.min_share.get(family, 0.0) * self.total_target))

    def _quota_reached(self, family: str) -> bool:
        quota = self.quotas.get(family)
        return quota is not None and self.counts[family] >= quota

    def _share_blocked(self, family: str, processed: int) -> bool:
        limit = self.max_share.get(family, 1.0)
        return limit < 1.0 and ((self.counts[family] + 1) / float(max(1, processed + 1))) > limit

    def _eligible(self, processed: int) -> list[str]:
        eligible = [f for f in self.families if not self._quota_reached(f)]
        if not eligible:
            return []
        filtered = [f for f in eligible if not self._share_blocked(f, processed)]
        if filtered:
            eligible = filtered
        if self.last_family and self.last_streak >= self.max_same_family_streak and len(eligible) > 1:
            alt = [f for f in eligible if f != self.last_family]
            if alt:
                eligible = alt
        return eligible

    def _pick_family(self, eligible: list[str]) -> str:
        deficits = sorted(
            ((self._required_min(f) - self.counts[f], f) for f in eligible),
            key=lambda item: (-item[0], item[1]),
        )
        if deficits and deficits[0][0] > 0:
            return deficits[0][1]
        if self.mode == "weighted":
            weights = [self.weights.get(f, 1.0) for f in eligible]
            total = sum(weights)
            if total <= 0:
                return sorted(eligible)[0]
            cursor = ((self.base_seed * 1315423911 + self.index * 2654435761) & 0xFFFFFFFF) / float(
                0xFFFFFFFF
            )
            cutoff = cursor * total
            acc = 0.0
            for f, w in zip(eligible, weights):
                acc += w
                if cutoff <= acc:
                    return f
            return eligible[-1]
        start = self.round_robin_index % len(self.families)
        for offset in range(len(self.families)):
            candidate = self.families[(start + offset) % len(self.families)]
            if candidate in eligible:
                self.round_robin_index = (start + offset + 1) % len(self.families)
                return candidate
        return sorted(eligible)[0]

    def next_assignment(self, processed: int) -> FamilyAssignment | None:
        eligible = self._eligible(processed)
        if not eligible:
            return None
        family = self._pick_family(eligible)
        return FamilyAssignment(family=family, seed=self.base_seed + self.index, index=self.index)

    def commit(self, assignment: FamilyAssignment) -> None:
        self.counts[assignment.family] += 1
        self.index += 1
        if self.last_family == assignment.family:
            self.last_streak += 1
        else:
            self.last_family = assignment.family
            self.last_streak = 1


class NightRunController:
    def __init__(self, *, pipeline: LocalStatelessReviewerPipeline, config: ReviewerPipelineConfig) -> None:
        self.pipeline = pipeline
        self.config = config
        self.root = Path(config.artifacts_root).expanduser().resolve() / "runs"
        self.root.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_id: str) -> Path:
        path = self.root / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _paths(self, run_id: str) -> dict[str, Path]:
        run_dir = self._run_dir(run_id)
        return {
            "run_dir": run_dir,
            "checkpoint": run_dir / "checkpoint.json",
            "heartbeat": run_dir / "heartbeat.json",
            "schedule": run_dir / "schedule.jsonl",
            "events": run_dir / "events.jsonl",
            "warnings": run_dir / "warnings.jsonl",
            "summary_json": run_dir / "run_summary.json",
            "summary_md": run_dir / "run_summary.md",
        }

    def _init_state(self, run_id: str, mode: str, families: list[str], max_cases: int) -> dict[str, Any]:
        return {
            "run_id": run_id,
            "mode": mode,
            "status": "running",
            "started_at": _iso_now(),
            "stop_reason": None,
            "max_cases": int(max_cases),
            "completed_cases": 0,
            "base_seed": int(self.config.generation.base_seed),
            "next_seed": int(self.config.generation.base_seed),
            "completed_case_ids": [],
            "families": list(families),
            "scheduler_state": {},
            "consecutive_infra_failures": 0,
            "per_family_counts": {},
            "per_status_counts": {},
            "per_overall_reading_counts": {},
            "per_priority_counts": {},
            "behavioral_by_family": {},
            "infra_by_family": {},
            "signal_code_counts_overall": {},
            "gap_code_counts_overall": {},
            "signal_code_counts_by_family": {},
            "gap_code_counts_by_family": {},
            "warnings": [],
            "warmup": {
                "enabled": bool(self.config.night_run.warmup.enabled),
                "case_count": int(self.config.night_run.warmup.case_count),
                "processed": 0,
                "infra_failures": 0,
                "parse_failures": 0,
                "completed": False,
            },
            "elapsed_seconds": 0.0,
        }

    def _write_checkpoint(self, state: dict[str, Any], path: Path) -> None:
        state["updated_at"] = _iso_now()
        path.write_text(json.dumps(state, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")

    def _write_heartbeat(self, state: dict[str, Any], path: Path, phase: str) -> None:
        payload = {
            "run_id": state["run_id"],
            "timestamp": _iso_now(),
            "phase": phase,
            "status": state["status"],
            "completed_cases": state["completed_cases"],
            "max_cases": state["max_cases"],
            "next_seed": state["next_seed"],
            "stop_reason": state["stop_reason"],
            "per_family_counts": state["per_family_counts"],
            "per_status_counts": state["per_status_counts"],
        }
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")

    def _warn(self, state: dict[str, Any], warnings_path: Path, code: str, details: dict[str, Any]) -> None:
        row = {"timestamp": _iso_now(), "code": code, "details": details}
        state["warnings"].append(row)
        _append_jsonl(warnings_path, row)

    def _collect_outcome(self, summary: dict[str, Any]) -> dict[str, Any]:
        processed = summary.get("processed_cases")
        if isinstance(processed, list) and processed:
            return dict(processed[0])
        return {"status": "pipeline_missing_processed_case", "action": "infra_review"}

    def _update_state_counts(self, state: dict[str, Any], outcome: dict[str, Any]) -> None:
        family = str(outcome.get("scenario_family") or outcome.get("theme") or "unknown")
        status = str(outcome.get("status") or "unknown")
        action = str(outcome.get("action") or "unknown")
        reading = outcome.get("overall_reading")
        priority = outcome.get("priority")
        signals = [str(x) for x in list(outcome.get("signal_codes") or []) if str(x).strip()]
        gaps = [str(x) for x in list(outcome.get("gap_codes") or []) if str(x).strip()]

        for key, bucket, value in (
            (family, "per_family_counts", 1),
            (status, "per_status_counts", 1),
        ):
            d = dict(state[bucket]); d[key] = int(d.get(key, 0)) + value; state[bucket] = d
        if reading is not None:
            d = dict(state["per_overall_reading_counts"]); k = str(reading); d[k] = int(d.get(k, 0)) + 1; state["per_overall_reading_counts"] = d
        if priority is not None:
            d = dict(state["per_priority_counts"]); k = str(priority); d[k] = int(d.get(k, 0)) + 1; state["per_priority_counts"] = d
        if action == "behavioral_review":
            d = dict(state["behavioral_by_family"]); d[family] = int(d.get(family, 0)) + 1; state["behavioral_by_family"] = d
        if action == "infra_review":
            d = dict(state["infra_by_family"]); d[family] = int(d.get(family, 0)) + 1; state["infra_by_family"] = d

        overall_signal = Counter(dict(state["signal_code_counts_overall"])); overall_signal.update(signals); state["signal_code_counts_overall"] = dict(overall_signal)
        overall_gap = Counter(dict(state["gap_code_counts_overall"])); overall_gap.update(gaps); state["gap_code_counts_overall"] = dict(overall_gap)
        sf = defaultdict(Counter, {k: Counter(dict(v)) for k, v in dict(state["signal_code_counts_by_family"]).items()}); sf[family].update(signals); state["signal_code_counts_by_family"] = {k: dict(v) for k, v in sf.items()}
        gf = defaultdict(Counter, {k: Counter(dict(v)) for k, v in dict(state["gap_code_counts_by_family"]).items()}); gf[family].update(gaps); state["gap_code_counts_by_family"] = {k: dict(v) for k, v in gf.items()}

    def _top(self, counts: dict[str, int], limit: int = 10) -> dict[str, int]:
        return dict(sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))[:limit])

    def _write_summary(self, state: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
        signal_by_family = {f: self._top(dict(v), 10) for f, v in dict(state["signal_code_counts_by_family"]).items()}
        gap_by_family = {f: self._top(dict(v), 10) for f, v in dict(state["gap_code_counts_by_family"]).items()}
        summary = {
            "run_id": state["run_id"],
            "mode": state["mode"],
            "status": state["status"],
            "stop_reason": state["stop_reason"],
            "started_at": state["started_at"],
            "finished_at": _iso_now(),
            "duration_seconds": float(state.get("elapsed_seconds", 0.0)),
            "total_cases": state["completed_cases"],
            "max_cases": state["max_cases"],
            "per_family_counts": dict(state["per_family_counts"]),
            "per_overall_reading_counts": dict(state["per_overall_reading_counts"]),
            "per_priority_counts": dict(state["per_priority_counts"]),
            "behavioral_review_counts_by_family": dict(state["behavioral_by_family"]),
            "infra_review_counts_by_family": dict(state["infra_by_family"]),
            "top_signal_code_counts_overall": self._top(dict(state["signal_code_counts_overall"]), 20),
            "top_signal_code_counts_by_family": signal_by_family,
            "top_gap_code_counts_overall": self._top(dict(state["gap_code_counts_overall"]), 20),
            "top_gap_code_counts_by_family": gap_by_family,
            "rolling_drift_warnings": list(state["warnings"]),
        }
        paths["summary_json"].write_text(
            json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        md = [
            f"# Run Summary: {summary['run_id']}",
            "",
            f"- status: `{summary['status']}`",
            f"- stop_reason: `{summary['stop_reason']}`",
            f"- total_cases: `{summary['total_cases']}`",
            f"- duration_seconds: `{summary['duration_seconds']:.3f}`",
            "",
            "## Per Family",
            json.dumps(summary["per_family_counts"], ensure_ascii=False, indent=2),
            "",
            "## Per Reading",
            json.dumps(summary["per_overall_reading_counts"], ensure_ascii=False, indent=2),
            "",
            "## Per Priority",
            json.dumps(summary["per_priority_counts"], ensure_ascii=False, indent=2),
            "",
            "## Behavioral By Family",
            json.dumps(summary["behavioral_review_counts_by_family"], ensure_ascii=False, indent=2),
            "",
            "## Infra By Family",
            json.dumps(summary["infra_review_counts_by_family"], ensure_ascii=False, indent=2),
            "",
            "## Top Signal Codes",
            json.dumps(summary["top_signal_code_counts_overall"], ensure_ascii=False, indent=2),
            "",
            "## Top Gap Codes",
            json.dumps(summary["top_gap_code_counts_overall"], ensure_ascii=False, indent=2),
            "",
        ]
        if summary["rolling_drift_warnings"]:
            md += ["## Warnings", json.dumps(summary["rolling_drift_warnings"], ensure_ascii=False, indent=2), ""]
        paths["summary_md"].write_text("\n".join(md), encoding="utf-8")
        summary["run_summary_json_path"] = str(paths["summary_json"])
        summary["run_summary_md_path"] = str(paths["summary_md"])
        return summary

    def _rolling_rates(self, window: deque[dict[str, Any]]) -> dict[str, float]:
        if not window:
            return {"infra": 0.0, "behavioral": 0.0, "coherent": 0.0, "insufficient": 0.0}
        total = float(len(window))
        return {
            "infra": sum(1 for x in window if x.get("infra")) / total,
            "behavioral": sum(1 for x in window if x.get("behavioral")) / total,
            "coherent": sum(1 for x in window if x.get("coherent")) / total,
            "insufficient": sum(1 for x in window if x.get("insufficient")) / total,
        }

    def _dominance(self, values: list[str]) -> float:
        if not values:
            return 0.0
        c = Counter(values)
        return c.most_common(1)[0][1] / float(len(values))

    def _load_resume_state(self, run_id: str, checkpoint_path: Path) -> dict[str, Any]:
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"checkpoint not found: {checkpoint_path}")
        state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if "base_seed" not in state:
            state["base_seed"] = int(state.get("next_seed", self.config.generation.base_seed))
        state["status"] = "running"
        return state

    def run(
        self,
        *,
        mode: str,
        run_id: str | None = None,
        max_cases: int | None = None,
        max_duration_seconds: int | None = None,
        themes: list[str] | None = None,
        resume: bool = False,
    ) -> dict[str, Any]:
        if mode not in {"batch", "long"}:
            raise ValueError(f"unsupported mode={mode!r}")
        resolved_run_id = run_id or f"{self.config.night_run.run_id_prefix}-{int(time.time())}"
        paths = self._paths(resolved_run_id)
        if resume:
            state = self._load_resume_state(resolved_run_id, paths["checkpoint"])
        else:
            families = list(dict.fromkeys(themes or list(self.config.generation.themes)))
            if not families:
                families = sorted(self.pipeline.generator.available_themes())
            target = int(self.config.night_run.batch_case_count) if mode == "batch" else int(self.config.night_run.guardrails.max_case_count)
            if max_cases is not None:
                target = int(max_cases)
            state = self._init_state(resolved_run_id, mode, families, target)

        guardrails = self.config.night_run.guardrails
        duration_limit = int(max_duration_seconds) if max_duration_seconds is not None else int(guardrails.max_duration_seconds)
        start_epoch = time.time() - float(state.get("elapsed_seconds", 0.0))

        scheduler = DiversityScheduler(
            families=list(state["families"]),
            base_seed=int(state.get("base_seed", state["next_seed"])),
            total_target=int(state["max_cases"]),
            mode=str(self.config.night_run.scheduler.mode),
            weights=dict(self.config.night_run.scheduler.family_weights),
            quotas=dict(self.config.night_run.scheduler.family_quotas),
            min_share=dict(self.config.night_run.scheduler.family_min_share),
            max_share=dict(self.config.night_run.scheduler.family_max_share),
            max_same_family_streak=max(int(self.config.night_run.scheduler.max_same_family_streak), int(guardrails.max_repeated_same_family_streak)),
            state=dict(state.get("scheduler_state", {})),
        )

        rolling = deque(maxlen=max(5, int(guardrails.rolling_window_size)))
        last_checkpoint_cases = int(state.get("completed_cases", 0))
        last_heartbeat = 0.0

        while True:
            if int(state["completed_cases"]) >= int(state["max_cases"]):
                state["status"] = "completed"; state["stop_reason"] = "max_case_count_reached"; break
            if time.time() - start_epoch >= duration_limit:
                state["status"] = "stopped"; state["stop_reason"] = "max_duration_reached"; break

            assignment = scheduler.next_assignment(int(state["completed_cases"]))
            if assignment is None:
                state["status"] = "stopped"; state["stop_reason"] = "scheduler_exhausted"; break
            _append_jsonl(paths["schedule"], {"timestamp": _iso_now(), "schedule_index": assignment.index, "family": assignment.family, "seed": assignment.seed})
            self.pipeline.set_seed_cursor(assignment.seed)
            cycle_summary = self.pipeline.run_cycle(case_count=1, themes=[assignment.family])
            outcome = self._collect_outcome(cycle_summary)
            case_id = str(outcome.get("case_id"))
            seen = set(state.get("completed_case_ids", []))
            if case_id and case_id not in {"None", ""} and case_id in seen:
                self._warn(state, paths["warnings"], "duplicate_case_id_skipped", {"case_id": case_id})
                scheduler.commit(assignment); state["next_seed"] = assignment.seed + 1
                continue
            if case_id and case_id not in {"None", ""}:
                seen.add(case_id); state["completed_case_ids"] = sorted(seen)

            scheduler.commit(assignment)
            state["scheduler_state"] = scheduler.export_state()
            state["next_seed"] = assignment.seed + 1
            state["completed_cases"] = int(state["completed_cases"]) + 1
            self._update_state_counts(state, outcome)
            _append_jsonl(paths["events"], {"timestamp": _iso_now(), "assignment": {"family": assignment.family, "seed": assignment.seed, "schedule_index": assignment.index}, "outcome": outcome})

            status = str(outcome.get("status") or "unknown")
            action = str(outcome.get("action") or "unknown")
            reading = str(outcome.get("overall_reading") or "")
            signals = [str(x) for x in list(outcome.get("signal_codes") or [])]
            gaps = [str(x) for x in list(outcome.get("gap_codes") or [])]
            is_infra = action == "infra_review" or status != "semantic_review_completed"
            is_behavioral = action == "behavioral_review"
            is_coherent = reading in {"coherent_bounded_caution", "coherent_abstention_or_revalidation"}
            is_insufficient = reading == "insufficient_evidence"
            if is_infra:
                state["consecutive_infra_failures"] = int(state["consecutive_infra_failures"]) + 1
            else:
                state["consecutive_infra_failures"] = 0
            rolling.append({"infra": is_infra, "behavioral": is_behavioral, "coherent": is_coherent, "insufficient": is_insufficient, "signal_codes": signals, "gap_codes": gaps})

            warmup = dict(state.get("warmup", {}))
            if bool(warmup.get("enabled")) and not bool(warmup.get("completed")):
                warmup["processed"] = int(warmup.get("processed", 0)) + 1
                if is_infra:
                    warmup["infra_failures"] = int(warmup.get("infra_failures", 0)) + 1
                if status == "parse_error":
                    warmup["parse_failures"] = int(warmup.get("parse_failures", 0)) + 1
                if int(warmup["infra_failures"]) > int(self.config.night_run.warmup.max_infra_failures):
                    state["status"] = "stopped"; state["stop_reason"] = "warmup_infra_failure_guardrail"
                if int(warmup["parse_failures"]) > int(self.config.night_run.warmup.max_parse_failures):
                    state["status"] = "stopped"; state["stop_reason"] = "warmup_parse_failure_guardrail"
                if int(warmup["processed"]) >= int(self.config.night_run.warmup.case_count):
                    warmup["completed"] = True
                state["warmup"] = warmup

            rates = self._rolling_rates(rolling)
            if int(state["consecutive_infra_failures"]) >= int(guardrails.max_consecutive_infra_failures):
                state["status"] = "stopped"; state["stop_reason"] = "max_consecutive_infra_failures_guardrail"
            if rates["infra"] >= float(guardrails.max_rolling_infra_failure_rate):
                state["status"] = "stopped"; state["stop_reason"] = "max_rolling_infra_failure_rate_guardrail"

            if rates["behavioral"] >= float(guardrails.max_rolling_behavioral_flag_rate):
                action_mode = str(guardrails.rolling_behavioral_rate_action).lower()
                self._warn(state, paths["warnings"], "rolling_behavioral_rate_guardrail", {"rolling_behavioral_rate": rates["behavioral"], "threshold": float(guardrails.max_rolling_behavioral_flag_rate), "action": action_mode})
                if action_mode == "stop":
                    state["status"] = "stopped"; state["stop_reason"] = "rolling_behavioral_rate_guardrail_stop"
                elif action_mode == "pause":
                    state["status"] = "paused"; state["stop_reason"] = "rolling_behavioral_rate_guardrail_pause"

            if rates["insufficient"] >= float(guardrails.warn_insufficient_evidence_rate):
                self._warn(state, paths["warnings"], "insufficient_evidence_rate_warning", {"rate": rates["insufficient"], "threshold": float(guardrails.warn_insufficient_evidence_rate)})
            signal_dom = self._dominance([code for item in rolling for code in list(item.get("signal_codes") or [])])
            if signal_dom >= float(guardrails.warn_signal_code_dominance):
                self._warn(state, paths["warnings"], "signal_code_dominance_warning", {"rate": signal_dom, "threshold": float(guardrails.warn_signal_code_dominance)})
            gap_dom = self._dominance([code for item in rolling for code in list(item.get("gap_codes") or [])])
            if gap_dom >= float(guardrails.warn_gap_code_dominance):
                self._warn(state, paths["warnings"], "gap_code_dominance_warning", {"rate": gap_dom, "threshold": float(guardrails.warn_gap_code_dominance)})

            family_counts = dict(state["per_family_counts"])
            if family_counts:
                largest_share = max(family_counts.values()) / float(sum(family_counts.values()))
                if largest_share >= float(guardrails.warn_family_imbalance_share):
                    self._warn(state, paths["warnings"], "family_imbalance_warning", {"largest_share": largest_share, "threshold": float(guardrails.warn_family_imbalance_share)})

            if guardrails.max_ordinary_storage_mb is not None:
                ordinary = Path(self.config.artifacts_root).expanduser().resolve() / "summaries" / "ordinary_cases.jsonl"
                ordinary_mb = (ordinary.stat().st_size / float(1024 * 1024)) if ordinary.exists() else 0.0
                if ordinary_mb >= float(guardrails.max_ordinary_storage_mb):
                    state["status"] = "stopped"; state["stop_reason"] = "ordinary_storage_budget_guardrail"
                    self._warn(state, paths["warnings"], "ordinary_storage_budget_guardrail", {"ordinary_storage_mb": ordinary_mb, "threshold_mb": float(guardrails.max_ordinary_storage_mb)})

            now = time.time()
            if now - last_heartbeat >= max(1, int(guardrails.heartbeat_interval_seconds)):
                self._write_heartbeat(state, paths["heartbeat"], "running")
                last_heartbeat = now
            if int(state["completed_cases"]) - last_checkpoint_cases >= max(1, int(guardrails.checkpoint_interval_cases)):
                state["elapsed_seconds"] = time.time() - start_epoch
                self._write_checkpoint(state, paths["checkpoint"])
                last_checkpoint_cases = int(state["completed_cases"])
            if state["status"] in {"paused", "stopped"}:
                break

        if state["status"] == "running":
            state["status"] = "completed"; state["stop_reason"] = "completed"
        state["elapsed_seconds"] = time.time() - start_epoch
        self._write_heartbeat(state, paths["heartbeat"], "finalizing")
        self._write_checkpoint(state, paths["checkpoint"])
        return self._write_summary(state, paths)
