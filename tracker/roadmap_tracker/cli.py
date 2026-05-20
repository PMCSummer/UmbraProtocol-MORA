from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import Phase, RoadmapModel


def _norm_code(value: str) -> str:
    return str(value or "").strip().upper()


def _json_pretty(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _load_model(roadmap_path: Path) -> RoadmapModel:
    if not roadmap_path.exists():
        raise FileNotFoundError(f"Roadmap JSON not found: {roadmap_path}")
    raw = json.loads(roadmap_path.read_text(encoding="utf-8-sig"))
    return RoadmapModel.from_json(raw)


def _phase_duplicates(model: RoadmapModel) -> list[str]:
    seen: set[str] = set()
    dup: list[str] = []
    for phase in model.phases:
        code = _norm_code(phase.code)
        if code in seen and code not in dup:
            dup.append(code)
        seen.add(code)
    return dup


def _phase_code_set(model: RoadmapModel) -> set[str]:
    return {_norm_code(phase.code) for phase in model.phases}


@dataclass(frozen=True)
class _ValidationSummary:
    schema_version: int
    phase_count: int
    evidence_count: int
    graph_node_count: int
    graph_edge_count: int
    duplicate_count: int
    seam_violation_count: int
    ok: bool


def _validate_model(model: RoadmapModel) -> _ValidationSummary:
    duplicates = _phase_duplicates(model)
    model.rebuild_phase_bindings()
    _ = model.to_json_text()
    seam_violations = model.seam_relation_consistency_violations()
    archive = model.archive_metrics()
    ok = not duplicates and not seam_violations
    return _ValidationSummary(
        schema_version=model.schema_version,
        phase_count=len(model.phases),
        evidence_count=archive.get("evidence", 0),
        graph_node_count=archive.get("nodes", 0),
        graph_edge_count=archive.get("edges", 0),
        duplicate_count=len(duplicates),
        seam_violation_count=len(seam_violations),
        ok=ok,
    )


def _print_validation(summary: _ValidationSummary) -> None:
    print(f"schema_version: {summary.schema_version}")
    print(f"phase_count: {summary.phase_count}")
    print(f"evidence_count: {summary.evidence_count}")
    print(f"graph_node_count: {summary.graph_node_count}")
    print(f"graph_edge_count: {summary.graph_edge_count}")
    print(f"duplicate_count: {summary.duplicate_count}")
    print(f"seam_violation_count: {summary.seam_violation_count}")
    print(f"result: {'OK' if summary.ok else 'FAIL'}")


def _build_phase_payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": _norm_code(args.code),
        "title": args.title.strip(),
        "track": (args.track or "build").strip(),
        "line": (args.line or "misc").strip(),
        "after": (_norm_code(args.after) if args.after else None),
        "status": (args.status or "later").strip(),
        "status_source": "cli",
        "spec": {
            "objective": args.desc.strip(),
            "includes": [],
            "rationale": "",
            "excludes": [],
        },
        "notes": "",
        "conceptually_after": [_norm_code(item) for item in (args.conceptually_after or []) if _norm_code(item)],
        "validation_state": "planned",
        "claim_state": (args.claim_state or "hypothesis").strip(),
        "maturity": (args.maturity or "L1_theoretical_only").strip(),
        "risk_tags": [item.strip() for item in (args.risk_tag or []) if item.strip()],
        "knowledge_card": {
            "functional_role": args.desc.strip(),
            "why_exists": "",
            "inputs": [],
            "outputs": [],
            "authority": "",
            "forbidden_shortcuts": [],
            "uncertainty_policy": "",
            "observables": [],
            "failure_modes": [],
            "falsifiers": [],
            "tests": [],
        },
        "related_node_ids": [],
    }
    if args.implemented_after:
        payload["implemented_after"] = _norm_code(args.implemented_after)
    if args.priority_bucket:
        payload["priority_bucket"] = args.priority_bucket.strip()
    if args.claim_role:
        payload["claim_role"] = args.claim_role.strip()
    return payload


def _build_phase_payload_from_item(item: dict[str, Any]) -> dict[str, Any]:
    code = _norm_code(item.get("code", ""))
    title = str(item.get("title", "")).strip()
    desc = str(item.get("desc", item.get("description", ""))).strip()
    if not code or not title or not desc:
        raise ValueError("Each bulk entry requires non-empty code/title/desc")

    conceptually_after_raw = item.get("conceptually_after", [])
    if isinstance(conceptually_after_raw, str):
        conceptually_after = [_norm_code(conceptually_after_raw)] if _norm_code(conceptually_after_raw) else []
    else:
        conceptually_after = [_norm_code(x) for x in (conceptually_after_raw or []) if _norm_code(x)]

    risk_tags_raw = item.get("risk_tag", item.get("risk_tags", []))
    if isinstance(risk_tags_raw, str):
        risk_tags = [risk_tags_raw.strip()] if risk_tags_raw.strip() else []
    else:
        risk_tags = [str(x).strip() for x in (risk_tags_raw or []) if str(x).strip()]

    payload: dict[str, Any] = {
        "code": code,
        "title": title,
        "track": str(item.get("track", "build")).strip() or "build",
        "line": str(item.get("line", "misc")).strip() or "misc",
        "after": (_norm_code(item.get("after")) if item.get("after") else None),
        "status": str(item.get("status", "later")).strip() or "later",
        "status_source": "cli",
        "spec": {
            "objective": desc,
            "includes": [],
            "rationale": "",
            "excludes": [],
        },
        "notes": "",
        "conceptually_after": conceptually_after,
        "validation_state": "planned",
        "claim_state": str(item.get("claim_state", "hypothesis")).strip() or "hypothesis",
        "maturity": str(item.get("maturity", "L1_theoretical_only")).strip() or "L1_theoretical_only",
        "risk_tags": risk_tags,
        "knowledge_card": {
            "functional_role": desc,
            "why_exists": "",
            "inputs": [],
            "outputs": [],
            "authority": "",
            "forbidden_shortcuts": [],
            "uncertainty_policy": "",
            "observables": [],
            "failure_modes": [],
            "falsifiers": [],
            "tests": [],
        },
        "related_node_ids": [],
    }
    if item.get("implemented_after") is not None and str(item.get("implemented_after")).strip():
        payload["implemented_after"] = _norm_code(str(item.get("implemented_after")))
    if item.get("priority_bucket") is not None and str(item.get("priority_bucket")).strip():
        payload["priority_bucket"] = str(item.get("priority_bucket")).strip()
    if item.get("claim_role") is not None and str(item.get("claim_role")).strip():
        payload["claim_role"] = str(item.get("claim_role")).strip()
    return payload


def _warn_missing_refs(model: RoadmapModel, payload: dict[str, Any]) -> list[str]:
    known = _phase_code_set(model)
    warnings: list[str] = []
    after = _norm_code(payload.get("after", "") or "")
    if after and after not in known:
        warnings.append(f"after ref not found: {after}")
    for code in payload.get("conceptually_after", []) or []:
        n = _norm_code(code)
        if n and n not in known:
            warnings.append(f"conceptually_after ref not found: {n}")
    implemented_after = _norm_code(payload.get("implemented_after", "") or "")
    if implemented_after and implemented_after not in known:
        warnings.append(f"implemented_after ref not found: {implemented_after}")
    return warnings


def _backup_path(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return path.with_name(f"{path.name}.bak.{stamp}")


def _write_model_with_backup(model: RoadmapModel, path: Path) -> Path:
    backup = _backup_path(path)
    shutil.copy2(path, backup)
    model.save(path)
    return backup


def cmd_validate(args: argparse.Namespace) -> int:
    model = _load_model(Path(args.roadmap))
    summary = _validate_model(model)
    _print_validation(summary)
    return 0 if summary.ok else 1


def cmd_show(args: argparse.Namespace) -> int:
    model = _load_model(Path(args.roadmap))
    phase = model.get_phase(args.code)
    if phase is None:
        print(f"Phase not found: {args.code}", file=sys.stderr)
        return 1
    print(_json_pretty(phase.to_dict()))
    return 0


def cmd_todo(args: argparse.Namespace) -> int:
    model = _load_model(Path(args.roadmap))
    phase = model.get_phase(args.code)
    if phase is None:
        print(f"Phase not found: {args.code}", file=sys.stderr)
        return 1
    print(_json_pretty(phase.to_todo_dict()))
    return 0


def cmd_add_phase(args: argparse.Namespace) -> int:
    roadmap_path = Path(args.roadmap)
    model = _load_model(roadmap_path)
    payload = _build_phase_payload_from_args(args)
    code = _norm_code(payload["code"])
    if model.get_phase(code) is not None:
        print(f"Duplicate phase code: {code}", file=sys.stderr)
        return 1

    warnings = _warn_missing_refs(model, payload)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    phase = Phase.from_dict(payload)
    before = len(model.phases)
    print("dry_run:" if not args.write else "write:")
    print(_json_pretty(phase.to_dict()))
    print(f"phase_count_before: {before}")
    print(f"phase_count_after: {before + 1}")

    if not args.write:
        return 0

    model.phases.append(phase)
    model.rebuild_phase_bindings()
    backup = _write_model_with_backup(model, roadmap_path)
    reloaded = _load_model(roadmap_path)
    summary = _validate_model(reloaded)
    print(f"backup: {backup}")
    _print_validation(summary)
    return 0 if summary.ok else 1


def cmd_bulk_add(args: argparse.Namespace) -> int:
    roadmap_path = Path(args.roadmap)
    model = _load_model(roadmap_path)
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input JSON not found: {input_path}", file=sys.stderr)
        return 1
    raw = json.loads(input_path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, list):
        print("bulk-add input must be a JSON list", file=sys.stderr)
        return 1

    payloads: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            print(f"bulk-add item #{idx} must be object", file=sys.stderr)
            return 1
        payload = _build_phase_payload_from_item(item)
        code = _norm_code(payload["code"])
        if code in seen_codes:
            print(f"Duplicate code in input: {code}", file=sys.stderr)
            return 1
        seen_codes.add(code)
        payloads.append(payload)

    existing_codes = _phase_code_set(model)
    overlap = sorted(code for code in seen_codes if code in existing_codes)
    if overlap:
        print(f"Codes already exist in roadmap: {', '.join(overlap)}", file=sys.stderr)
        return 1

    all_warnings: list[str] = []
    phases: list[Phase] = []
    for payload in payloads:
        all_warnings.extend(_warn_missing_refs(model, payload))
        phases.append(Phase.from_dict(payload))
    for warning in all_warnings:
        print(f"warning: {warning}", file=sys.stderr)

    before = len(model.phases)
    print("dry_run:" if not args.write else "write:")
    print(f"bulk_count: {len(phases)}")
    print("codes:")
    for phase in phases:
        print(f"- {phase.code}")
    print(f"phase_count_before: {before}")
    print(f"phase_count_after: {before + len(phases)}")

    if not args.write:
        return 0

    model.phases.extend(phases)
    model.rebuild_phase_bindings()
    backup = _write_model_with_backup(model, roadmap_path)
    reloaded = _load_model(roadmap_path)
    summary = _validate_model(reloaded)
    print(f"backup: {backup}")
    _print_validation(summary)
    return 0 if summary.ok else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="roadmap_tracker.cli", description="Roadmap JSON CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate roadmap JSON")
    p_validate.add_argument("--roadmap", required=True, help="Path to roadmap JSON")
    p_validate.set_defaults(func=cmd_validate)

    p_show = sub.add_parser("show", help="Show one phase as JSON")
    p_show.add_argument("--roadmap", required=True, help="Path to roadmap JSON")
    p_show.add_argument("--code", required=True, help="Phase code")
    p_show.set_defaults(func=cmd_show)

    p_todo = sub.add_parser("todo", help="Show one phase TODO template as JSON")
    p_todo.add_argument("--roadmap", required=True, help="Path to roadmap JSON")
    p_todo.add_argument("--code", required=True, help="Phase code")
    p_todo.set_defaults(func=cmd_todo)

    p_add = sub.add_parser("add-phase", help="Add one phase skeleton (dry-run by default)")
    p_add.add_argument("--roadmap", required=True, help="Path to roadmap JSON")
    p_add.add_argument("--code", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--desc", required=True)
    p_add.add_argument("--after")
    p_add.add_argument("--track", default="build", choices=("build", "frontier", "refinement"))
    p_add.add_argument("--line", default="misc")
    p_add.add_argument("--status", default="later", choices=("later", "proposed", "next", "current", "closed"))
    p_add.add_argument("--priority-bucket")
    p_add.add_argument("--claim-role")
    p_add.add_argument("--claim-state", default="hypothesis")
    p_add.add_argument("--maturity", default="L1_theoretical_only")
    p_add.add_argument("--risk-tag", action="append", default=[])
    p_add.add_argument("--conceptually-after", action="append", default=[])
    p_add.add_argument("--implemented-after")
    p_add.add_argument("--write", action="store_true")
    p_add.set_defaults(func=cmd_add_phase)

    p_bulk = sub.add_parser("bulk-add", help="Bulk add phase skeletons from JSON list (dry-run by default)")
    p_bulk.add_argument("--roadmap", required=True, help="Path to roadmap JSON")
    p_bulk.add_argument("--input", required=True, help="Path to input JSON list")
    p_bulk.add_argument("--write", action="store_true")
    p_bulk.set_defaults(func=cmd_bulk_add)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
