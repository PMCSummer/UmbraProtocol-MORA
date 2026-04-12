from __future__ import annotations

import json
import shutil
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

    def __post_init__(self) -> None:
        self.active_dir = self.root / "active"
        self.suspicious_dir = self.root / "suspicious"
        self.summaries_dir = self.root / "summaries"
        self.logs_dir = self.root / "logs"
        for directory in (
            self.active_dir,
            self.suspicious_dir,
            self.summaries_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

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
            "overall_reading": latest.parsed_json.get("overall_reading"),
            "priority": latest.parsed_json.get("human_review_priority"),
            "confidence": latest.parsed_json.get("confidence"),
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
                        "parsed_json": item.parsed_json,
                        "raw_text": item.raw_text,
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
            "priority": reviews[-1].parsed_json.get("human_review_priority"),
            "overall_reading": reviews[-1].parsed_json.get("overall_reading"),
            "tier": reviews[-1].tier,
            "model": reviews[-1].model,
            "triage_reason": triage_reason,
            "artifact_dir": str(dst),
        }
        _append_jsonl(self.summaries_dir / "suspicious_cases.jsonl", index_row)
        return dst
