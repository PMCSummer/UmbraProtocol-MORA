from __future__ import annotations

import argparse
import json
from bisect import bisect_right
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

CONSTITUTION_VERSION = "p6-claim-constitution-v1"

DANGEROUS_PHRASES = (
    "consciousness proven",
    "real consciousness",
    "agi achieved",
    "fully autonomous subject",
    "true artificial subject",
    "human-level consciousness",
    "sentient",
    "self-aware proven",
)

EXTERNAL_STRONG_CLAIM_PHRASES = (
    "externally benchmarked",
    "externally validated",
    "cross-domain robust",
    "cross-backend proven",
    "subjecthood evidence",
    "consciousness-adjacent evidence",
)

EXTERNAL_ARTIFACT_MARKERS = (
    "baseline artifact",
    "baseline_report",
    "benchmark_report",
    "ablation_report",
    "trace_bundle",
    "external_review_bundle",
    "cross_backend_run",
    "artifact:",
)

AP01_EXECUTION_OVERCLAIM_MARKERS = (
    "ap01 executes",
    "ap01 execution",
    "ap01 mutates world",
    "ap01 world mutation",
    "ap01 submits to world",
)

ACP01_PLANNER_OVERCLAIM_MARKERS = (
    "acp01 planner",
    "acp01 planning",
    "open-ended strategy",
    "autonomous strategy",
    "best action selector",
    "acp01 chooses best",
)

NEAR_DEFENSIBLE_CLAIMS = (
    "load-bearing architecture versus simpler baselines",
    "self/world boundary under perturbation",
    "calibrated internal uncertainty/residue report",
    "delayed/confounded learning",
    "cross-backend portability",
)

NOT_DEFENSIBLE_YET = (
    "full autonomy",
    "open-ended planning",
    "strong artificial subjecthood",
    "consciousness proof",
    "general AGI",
    "robust real-world intelligence",
)

SAFE_SECTION_MARKERS = (
    "forbidden language",
    "forbidden patterns",
    "forbidden claim patterns",
    "examples of overclaim",
    "not allowed",
    "do not claim",
    "hard violations",
    "evidence requirements",
    "required evidence",
    "dangerous vocabulary",
)

SAFE_LINE_MARKERS = (
    "must not claim",
    "do not claim",
    "forbidden phrase",
    "example overclaim",
    "not allowed",
    "dangerous vocabulary",
)

CLAIM_TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}

GENERATED_OR_BINARY_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".zip",
    ".bin",
}


@dataclass(frozen=True)
class ClaimFinding:
    severity: str
    finding_type: str
    path: str
    message: str
    evidence: str
    line: int | None = None
    section: str | None = None


@dataclass
class ClaimConstitutionReport:
    constitution_version: str
    scanned_paths: list[str]
    skipped_paths: list[str] = field(default_factory=list)
    claim_findings: list[ClaimFinding] = field(default_factory=list)
    authorized_claims: list[str] = field(default_factory=list)
    blocked_claims: list[str] = field(default_factory=list)
    overclaim_findings: list[ClaimFinding] = field(default_factory=list)
    missing_evidence_findings: list[ClaimFinding] = field(default_factory=list)
    advisory_findings: list[ClaimFinding] = field(default_factory=list)
    safe_context_mentions: list[ClaimFinding] = field(default_factory=list)
    ignored_non_claim_surface_mentions: list[ClaimFinding] = field(default_factory=list)
    summary_counts: dict[str, int] = field(default_factory=dict)

    def finalize(self) -> None:
        self.summary_counts = {
            "hard_violations": sum(1 for item in self.claim_findings if item.severity == "hard"),
            "overclaims": len(self.overclaim_findings),
            "missing_evidence": len(self.missing_evidence_findings),
            "advisories": len(self.advisory_findings),
            "safe_context_mentions": len(self.safe_context_mentions),
            "ignored_non_claim_surface_mentions": len(self.ignored_non_claim_surface_mentions),
            "authorized_claims": len(self.authorized_claims),
            "blocked_claims": len(self.blocked_claims),
        }

    def as_json(self) -> dict[str, object]:
        return {
            "constitution_version": self.constitution_version,
            "scanned_paths": self.scanned_paths,
            "skipped_paths": self.skipped_paths,
            "claim_findings": [asdict(item) for item in self.claim_findings],
            "authorized_claims": self.authorized_claims,
            "blocked_claims": self.blocked_claims,
            "overclaim_findings": [asdict(item) for item in self.overclaim_findings],
            "missing_evidence_findings": [asdict(item) for item in self.missing_evidence_findings],
            "advisory_findings": [asdict(item) for item in self.advisory_findings],
            "safe_context_mentions": [asdict(item) for item in self.safe_context_mentions],
            "ignored_non_claim_surface_mentions": [asdict(item) for item in self.ignored_non_claim_surface_mentions],
            "summary_counts": self.summary_counts,
        }


@dataclass(frozen=True)
class _ClaimCandidate:
    path: Path
    rel: str


@dataclass(frozen=True)
class _SkippedPath:
    path: Path
    rel: str
    reason: str


def _normalized_rel(path: Path, repo_root: Path) -> str:
    return str(path.relative_to(repo_root)).replace("\\", "/")


def _is_generated_or_cache_path(rel: str, suffix: str) -> bool:
    segments = rel.split("/")
    if any(seg in {"__pycache__", ".pytest_cache", "build", "dist", "cache", "tmp", "temp"} for seg in segments):
        return True
    if suffix in GENERATED_OR_BINARY_EXTENSIONS:
        return True
    return False


def _is_non_claim_surface(rel: str) -> bool:
    if rel.startswith("tests/"):
        return True
    if rel == "tools/claim_constitution_checker.py":
        return True
    if rel.startswith("tools/__pycache__/"):
        return True
    return False


def _is_claim_surface_path(rel: str, *, scan_roadmap: bool, scan_docs: bool, scan_experiments: bool) -> bool:
    if scan_roadmap and (rel.startswith("tracker/") or rel.startswith("roadmap/")):
        return True
    if scan_docs and (rel.startswith("docs/") or rel.startswith("adr/")):
        return True
    if scan_docs and (rel.lower() == "readme.md" or rel.lower().startswith("readme.")):
        return True
    if scan_experiments and rel.startswith("experiments/"):
        return True
    return False


def _iter_claim_surfaces(
    repo_root: Path,
    *,
    scan_roadmap: bool,
    scan_docs: bool,
    scan_experiments: bool,
    include_non_claim_surfaces: bool,
) -> tuple[list[_ClaimCandidate], list[_SkippedPath]]:
    roots: list[Path] = []
    if scan_roadmap:
        for rel in ("tracker", "roadmap"):
            base = repo_root / rel
            if base.exists():
                roots.append(base)
    if scan_docs:
        for rel in ("docs", "adr"):
            base = repo_root / rel
            if base.exists():
                roots.append(base)
        for name in ("README.md", "README.MD", "readme.md"):
            path = repo_root / name
            if path.exists():
                roots.append(path)
    if scan_experiments:
        base = repo_root / "experiments"
        if base.exists():
            roots.append(base)

    discovered: dict[str, Path] = {}
    for base in roots:
        if base.is_file():
            discovered[_normalized_rel(base, repo_root)] = base
            continue
        for path in base.rglob("*"):
            if path.is_file():
                discovered[_normalized_rel(path, repo_root)] = path

    candidates: list[_ClaimCandidate] = []
    skipped: list[_SkippedPath] = []

    for rel in sorted(discovered.keys()):
        path = discovered[rel]
        suffix = path.suffix.lower()

        if not _is_claim_surface_path(rel, scan_roadmap=scan_roadmap, scan_docs=scan_docs, scan_experiments=scan_experiments):
            skipped.append(_SkippedPath(path=path, rel=rel, reason="outside_claim_surface"))
            continue

        if _is_generated_or_cache_path(rel, suffix):
            skipped.append(_SkippedPath(path=path, rel=rel, reason="generated_or_cache"))
            continue

        if _is_non_claim_surface(rel) and not include_non_claim_surfaces:
            skipped.append(_SkippedPath(path=path, rel=rel, reason="non_claim_surface"))
            continue

        if suffix and suffix not in CLAIM_TEXT_EXTENSIONS:
            skipped.append(_SkippedPath(path=path, rel=rel, reason="unsupported_format"))
            continue

        candidates.append(_ClaimCandidate(path=path, rel=rel))

    return candidates, skipped


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for idx, ch in enumerate(text):
        if ch == "\n":
            starts.append(idx + 1)
    return starts


def _index_to_line(starts: list[int], idx: int) -> int:
    return bisect_right(starts, idx)


def _build_context_maps(text: str) -> tuple[list[str], list[bool], list[str], list[bool]]:
    lines = text.splitlines()
    sections: list[str] = []
    in_code_flags: list[bool] = []
    safe_flags: list[bool] = []

    current_section = "document"
    in_code = False
    safe_section = False

    table_forbidden_column = False

    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        lower = stripped.lower()

        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_flags.append(in_code)
            sections.append(current_section)
            safe_flags.append(True)
            in_code = not in_code
            continue

        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip() or current_section
            current_section = heading
            safe_section = any(marker in heading.lower() for marker in SAFE_SECTION_MARKERS)
            table_forbidden_column = False

        if "|" in stripped and "forbidden language" in lower:
            table_forbidden_column = True
        elif table_forbidden_column and idx > 0 and not stripped.startswith("|"):
            table_forbidden_column = False

        line_safe = (
            in_code
            or safe_section
            or table_forbidden_column
            or any(marker in lower for marker in SAFE_LINE_MARKERS)
        )

        in_code_flags.append(in_code)
        sections.append(current_section)
        safe_flags.append(line_safe)

    return lines, in_code_flags, sections, safe_flags


def _negated_around(text: str, phrase: str, idx: int) -> bool:
    window = text[max(0, idx - 120) : min(len(text), idx + len(phrase) + 120)]
    neg_markers = (
        "not ",
        "not proof",
        "no proof",
        "without proof",
        "does not prove",
        "doesn't prove",
        "must not claim",
        "do not claim",
        "не ",
        "не доказ",
    )
    return any(marker in window for marker in neg_markers)


def _record_safe_context(
    report: ClaimConstitutionReport,
    *,
    rel: str,
    marker: str,
    line: int,
    section: str,
    reason: str,
) -> None:
    report.safe_context_mentions.append(
        ClaimFinding(
            severity="safe",
            finding_type="safe_context_mention",
            path=rel,
            message=reason,
            evidence=marker,
            line=line,
            section=section,
        )
    )


def _contains_any(text: str, markers: Iterable[str]) -> str | None:
    for marker in markers:
        if marker in text:
            return marker
    return None


def _find_occurrences(text: str, marker: str) -> Iterable[int]:
    start = 0
    while True:
        idx = text.find(marker, start)
        if idx < 0:
            return
        yield idx
        start = idx + len(marker)


def _add_hard_finding(
    report: ClaimConstitutionReport,
    *,
    finding_type: str,
    rel: str,
    message: str,
    evidence: str,
    line: int | None,
    section: str | None,
    as_overclaim: bool,
    as_missing: bool,
) -> None:
    finding = ClaimFinding(
        severity="hard",
        finding_type=finding_type,
        path=rel,
        message=message,
        evidence=evidence,
        line=line,
        section=section,
    )
    report.claim_findings.append(finding)
    if as_overclaim:
        report.overclaim_findings.append(finding)
    if as_missing:
        report.missing_evidence_findings.append(finding)


def _scan_text_claims(report: ClaimConstitutionReport, rel: str, text: str) -> None:
    lowered = text.lower()
    starts = _line_starts(lowered)
    lines, _, sections, safe_flags = _build_context_maps(lowered)

    for phrase in DANGEROUS_PHRASES:
        for idx in _find_occurrences(lowered, phrase):
            line = _index_to_line(starts, idx)
            section = sections[line - 1] if line - 1 < len(sections) else "document"
            if line - 1 < len(safe_flags) and safe_flags[line - 1]:
                _record_safe_context(
                    report,
                    rel=rel,
                    marker=phrase,
                    line=line,
                    section=section,
                    reason="Forbidden vocabulary mention appears in safe context (forbidden/examples/code/negation section)",
                )
                continue
            if _negated_around(lowered, phrase, idx):
                _record_safe_context(
                    report,
                    rel=rel,
                    marker=phrase,
                    line=line,
                    section=section,
                    reason="Forbidden vocabulary mention explicitly negated",
                )
                continue

            _add_hard_finding(
                report,
                finding_type="forbidden_vocabulary",
                rel=rel,
                message="Forbidden overclaim vocabulary without safe-context exemption",
                evidence=phrase,
                line=line,
                section=section,
                as_overclaim=True,
                as_missing=False,
            )

    for marker in AP01_EXECUTION_OVERCLAIM_MARKERS:
        for idx in _find_occurrences(lowered, marker):
            line = _index_to_line(starts, idx)
            section = sections[line - 1] if line - 1 < len(sections) else "document"
            if line - 1 < len(safe_flags) and safe_flags[line - 1]:
                _record_safe_context(
                    report,
                    rel=rel,
                    marker=marker,
                    line=line,
                    section=section,
                    reason="AP01 overclaim marker appears in safe context",
                )
                continue

            _add_hard_finding(
                report,
                finding_type="stage_overclaim_ap01_execution",
                rel=rel,
                message="AP01 overclaimed as execution/world mutation authority",
                evidence=marker,
                line=line,
                section=section,
                as_overclaim=True,
                as_missing=False,
            )

    for marker in ACP01_PLANNER_OVERCLAIM_MARKERS:
        for idx in _find_occurrences(lowered, marker):
            line = _index_to_line(starts, idx)
            section = sections[line - 1] if line - 1 < len(sections) else "document"
            if line - 1 < len(safe_flags) and safe_flags[line - 1]:
                _record_safe_context(
                    report,
                    rel=rel,
                    marker=marker,
                    line=line,
                    section=section,
                    reason="ACP01 planner marker appears in safe context",
                )
                continue

            _add_hard_finding(
                report,
                finding_type="stage_overclaim_acp01_planner",
                rel=rel,
                message="ACP01 overclaimed as planner/open-ended selector",
                evidence=marker,
                line=line,
                section=section,
                as_overclaim=True,
                as_missing=False,
            )

    artifact_marker_present = _contains_any(lowered, EXTERNAL_ARTIFACT_MARKERS) is not None
    for phrase in EXTERNAL_STRONG_CLAIM_PHRASES:
        for idx in _find_occurrences(lowered, phrase):
            line = _index_to_line(starts, idx)
            section = sections[line - 1] if line - 1 < len(sections) else "document"
            if line - 1 < len(safe_flags) and safe_flags[line - 1]:
                _record_safe_context(
                    report,
                    rel=rel,
                    marker=phrase,
                    line=line,
                    section=section,
                    reason="External-claim marker appears in safe context",
                )
                continue
            if artifact_marker_present:
                continue
            _add_hard_finding(
                report,
                finding_type="missing_external_artifact",
                rel=rel,
                message="Strong external/cross-domain claim without artifact support",
                evidence=phrase,
                line=line,
                section=section,
                as_overclaim=False,
                as_missing=True,
            )


def _iter_dict_nodes(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _iter_dict_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_dict_nodes(item)


def _closedish(node: dict[str, Any]) -> bool:
    combined = " ".join(str(node.get(key, "")).lower() for key in ("status", "claim_state", "maturity"))
    markers = (
        "closed",
        "sealed",
        "mature",
        "implemented",
        "externally_benchmarked",
        "l8",
        "l9",
        "l10",
    )
    return any(marker in combined for marker in markers)


def _todoish(value: Any) -> bool:
    text = str(value or "").lower()
    return any(token in text for token in ("todo", "tbd", "fixme", "allowed_claim"))


def _incomplete_validation(value: Any) -> bool:
    text = str(value or "").lower()
    bad = ("incomplete", "planned", "pending", "not_started", "unverified", "claim_gate", "todo")
    return any(token in text for token in bad)


def _scan_structured_claims(report: ClaimConstitutionReport, rel: str, payload: Any) -> None:
    for node in _iter_dict_nodes(payload):
        if not _closedish(node):
            continue

        allowed_claim = node.get("allowed_claim", "")
        claim_blocked_by = node.get("claim_blocked_by", [])
        validation_state = node.get("validation_state", "")

        if _todoish(allowed_claim):
            _add_hard_finding(
                report,
                finding_type="closed_with_todo_allowed_claim",
                rel=rel,
                message="Closed/mature claim contains TODO/TBD in allowed_claim",
                evidence=str(allowed_claim),
                line=None,
                section="structured_claim",
                as_overclaim=False,
                as_missing=True,
            )

        blockers = claim_blocked_by if isinstance(claim_blocked_by, list) else [claim_blocked_by]
        blockers = [str(item).strip() for item in blockers if str(item).strip()]
        if blockers:
            _add_hard_finding(
                report,
                finding_type="closed_with_claim_blockers",
                rel=rel,
                message="Closed/mature claim has non-empty claim_blocked_by",
                evidence=", ".join(blockers),
                line=None,
                section="structured_claim",
                as_overclaim=False,
                as_missing=True,
            )

        if _incomplete_validation(validation_state):
            _add_hard_finding(
                report,
                finding_type="closed_with_incomplete_validation",
                rel=rel,
                message="Closed/mature claim has incomplete validation_state",
                evidence=str(validation_state),
                line=None,
                section="structured_claim",
                as_overclaim=False,
                as_missing=True,
            )


def _scan_file(report: ClaimConstitutionReport, candidate: _ClaimCandidate) -> None:
    text = _read_text(candidate.path)
    _scan_text_claims(report, candidate.rel, text)

    if candidate.path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return
        _scan_structured_claims(report, candidate.rel, payload)


def _scan_ignored_noise(report: ClaimConstitutionReport, skipped: list[_SkippedPath]) -> None:
    markers = (
        *DANGEROUS_PHRASES,
        *AP01_EXECUTION_OVERCLAIM_MARKERS,
        *ACP01_PLANNER_OVERCLAIM_MARKERS,
        *EXTERNAL_STRONG_CLAIM_PHRASES,
    )
    for item in skipped:
        if item.reason not in {"non_claim_surface", "generated_or_cache"}:
            continue
        if item.path.suffix.lower() in GENERATED_OR_BINARY_EXTENSIONS:
            continue
        try:
            text = _read_text(item.path).lower()
        except Exception:
            continue
        marker = _contains_any(text, markers)
        if marker is None:
            continue
        report.ignored_non_claim_surface_mentions.append(
            ClaimFinding(
                severity="ignored",
                finding_type="ignored_non_claim_surface",
                path=item.rel,
                message=f"Potential claim marker ignored because path is {item.reason}",
                evidence=marker,
            )
        )


def _detect_authorized_claims(repo_root: Path) -> tuple[list[str], list[str], list[ClaimFinding]]:
    def exists(rel: str) -> bool:
        return (repo_root / rel).exists()

    authorized: list[str] = []
    blocked: list[str] = []
    advisories: list[ClaimFinding] = []

    if exists("src/substrate/ap01_subject_action_publication"):
        authorized.append("MORA supports subject-owned bounded action publication (request != execution).")
    if exists("experiments/embodied_playground/models.py"):
        authorized.append("MORA supports a typed universal embodied world API contract.")
    if exists("experiments/embodied_playground/grid_world.py"):
        authorized.append("MORA supports a bounded embodied action/effect loop in controlled GridWorld.")
    if exists("experiments/embodied_playground/subject_bridge.py"):
        authorized.append("MORA supports subject_tick-centered world bridge orchestration with AP01-gated submission.")
    if exists("src/substrate/acp01_internal_action_candidate_production/policy.py"):
        authorized.append("MORA supports internal action-candidate production under typed public basis with AP01 publication authority preserved.")
    if exists("experiments/embodied_playground/falsifiers.py"):
        authorized.append("MORA supports anti-shortcut falsifier discipline across request/effect/visibility boundaries.")

    if authorized:
        authorized.append("MORA supports a bounded proto-subject contour claim, not consciousness proof.")

    blocked.extend(NOT_DEFENSIBLE_YET)

    for claim in NEAR_DEFENSIBLE_CLAIMS:
        advisories.append(
            ClaimFinding(
                severity="advisory",
                finding_type="near_defensible",
                path="governance/claim_ladder",
                message="Near-defensible claim requires additional evidence stages",
                evidence=claim,
            )
        )

    return authorized, blocked, advisories


def run_claim_constitution_checker(
    *,
    repo_root: Path,
    scan_roadmap: bool,
    scan_docs: bool,
    scan_experiments: bool,
    include_non_claim_surfaces: bool = False,
) -> ClaimConstitutionReport:
    report = ClaimConstitutionReport(
        constitution_version=CONSTITUTION_VERSION,
        scanned_paths=[],
    )

    candidates, skipped = _iter_claim_surfaces(
        repo_root,
        scan_roadmap=scan_roadmap,
        scan_docs=scan_docs,
        scan_experiments=scan_experiments,
        include_non_claim_surfaces=include_non_claim_surfaces,
    )

    report.scanned_paths = [item.rel for item in candidates]
    report.skipped_paths = [f"{item.rel} [{item.reason}]" for item in skipped]

    for candidate in candidates:
        _scan_file(report, candidate)

    _scan_ignored_noise(report, skipped)

    authorized, blocked, advisories = _detect_authorized_claims(repo_root)
    report.authorized_claims.extend(authorized)
    report.blocked_claims.extend(blocked)
    report.advisory_findings.extend(advisories)
    report.finalize()
    return report


def _format_human(report: ClaimConstitutionReport, *, include_advisory: bool) -> str:
    lines: list[str] = []
    lines.append(f"Claim Constitution Checker [{report.constitution_version}]")
    lines.append(f"Scanned files: {len(report.scanned_paths)}")
    lines.append(f"Skipped files: {len(report.skipped_paths)}")
    lines.append("")

    lines.append("Authorized claims:")
    for item in report.authorized_claims:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("Blocked / not-yet-defensible claims:")
    for item in report.blocked_claims:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("Hard findings:")
    hard = [item for item in report.claim_findings if item.severity == "hard"]
    if not hard:
        lines.append("- none")
    else:
        for item in hard:
            location = f"{item.path}:{item.line}" if item.line else item.path
            section = f" section={item.section}" if item.section else ""
            lines.append(f"- [{item.finding_type}] {location}{section}: {item.message} :: {item.evidence}")

    if include_advisory:
        lines.append("")
        lines.append("Advisory findings:")
        if not report.advisory_findings:
            lines.append("- none")
        else:
            for item in report.advisory_findings:
                lines.append(f"- [{item.finding_type}] {item.evidence}")

    lines.append("")
    lines.append("Summary counts:")
    for key, value in report.summary_counts.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MORA Claim Constitution checker")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--include-advisory", action="store_true", help="Include advisory section in text output")
    parser.add_argument("--fail-on-overclaim", action="store_true", help="Exit nonzero on hard overclaim violations")
    parser.add_argument("--scan-roadmap", action="store_true", help="Scan roadmap/tracker claim surfaces")
    parser.add_argument("--scan-docs", action="store_true", help="Scan docs/adr/readme claim surfaces")
    parser.add_argument("--scan-experiments", action="store_true", help="Scan experiments claim surfaces")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    enabled = args.scan_roadmap or args.scan_docs or args.scan_experiments
    scan_roadmap = args.scan_roadmap or not enabled
    scan_docs = args.scan_docs or not enabled
    scan_experiments = args.scan_experiments or not enabled

    repo_root = Path(args.repo_root).resolve()
    report = run_claim_constitution_checker(
        repo_root=repo_root,
        scan_roadmap=scan_roadmap,
        scan_docs=scan_docs,
        scan_experiments=scan_experiments,
    )

    if args.json:
        print(json.dumps(report.as_json(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_format_human(report, include_advisory=args.include_advisory))

    if args.fail_on_overclaim and report.summary_counts.get("hard_violations", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
