from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from substrate.observability.collector import TickTraceBundle
from substrate.observability.utils import to_jsonable


def _json_dumps(payload: Any) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=True, sort_keys=True, indent=2) + "\n"


def write_trace_bundle(
    *,
    bundle: TickTraceBundle,
    integrity_report: dict[str, Any],
    output_root: str | Path,
) -> dict[str, str]:
    root = Path(output_root)
    trace_dir = root / bundle.trace_id
    snapshots_dir = trace_dir / "module_snapshots"
    diffs_dir = trace_dir / "diffs"
    trace_dir.mkdir(parents=True, exist_ok=True)
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    diffs_dir.mkdir(parents=True, exist_ok=True)

    events_path = trace_dir / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as fh:
        for event in bundle.events:
            fh.write(json.dumps(to_jsonable(event), ensure_ascii=True, sort_keys=True) + "\n")

    causal_edges_path = trace_dir / "causal_edges.json"
    causal_edges_path.write_text(_json_dumps(bundle.causal_edges), encoding="utf-8")

    for module, payload in sorted(bundle.module_snapshots.items()):
        compact_path = snapshots_dir / f"{module}.compact.json"
        deep_path = snapshots_dir / f"{module}.deep.json"
        compact_path.write_text(_json_dumps(payload.get("compact", {})), encoding="utf-8")
        deep_path.write_text(_json_dumps(payload.get("deep", {})), encoding="utf-8")

    for module, module_diff in sorted(bundle.diffs.items()):
        diff_path = diffs_dir / f"{module}.semantic_diff.json"
        diff_path.write_text(_json_dumps(module_diff), encoding="utf-8")

    summary_path = trace_dir / "compact_summary.json"
    summary_payload = {
        **bundle.compact_summary,
        "modules_with_snapshots": sorted(bundle.module_snapshots.keys()),
        "modules_with_diffs": sorted(bundle.diffs.keys()),
    }
    summary_path.write_text(_json_dumps(summary_payload), encoding="utf-8")

    manifest_path = trace_dir / "tick_manifest.json"
    manifest_payload = {
        "tick_id": bundle.tick_id,
        "trace_id": bundle.trace_id,
        "event_count": len(bundle.events),
        "module_snapshot_count": len(bundle.module_snapshots),
        "diff_count": sum(
            len(report.get("records", []))
            for report in bundle.diffs.values()
            if isinstance(report, dict)
        ),
        "causal_edge_count": len(bundle.causal_edges),
        "integrity": integrity_report,
        "files": {
            "events": str(events_path),
            "causal_edges": str(causal_edges_path),
            "summary": str(summary_path),
            "module_snapshots_dir": str(snapshots_dir),
            "diffs_dir": str(diffs_dir),
        },
    }
    manifest_path.write_text(_json_dumps(manifest_payload), encoding="utf-8")

    return {
        "trace_dir": str(trace_dir),
        "manifest_path": str(manifest_path),
        "events_path": str(events_path),
        "causal_edges_path": str(causal_edges_path),
        "summary_path": str(summary_path),
        "snapshots_dir": str(snapshots_dir),
        "diffs_dir": str(diffs_dir),
    }
