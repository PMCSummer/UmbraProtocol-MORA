from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CHECKER_VERSION = "p7-runtime-topology-alignment-v1"


@dataclass(frozen=True)
class Finding:
    finding_type: str
    severity: str
    seam_id: str | None
    message: str
    path: str | None = None
    evidence: str | None = None


@dataclass(frozen=True)
class SeamSpec:
    seam_id: str
    seam_name: str
    expected_owner: str
    expected_authority: str
    required_when: str
    executed_patterns: tuple[str, ...]
    represented_patterns: tuple[str, ...]
    consumer_obligations: tuple[str, ...]
    forbidden_authority_patterns: tuple[str, ...] = ()
    expected_order_after: tuple[str, ...] = ()
    expected_order_before: tuple[str, ...] = ()


@dataclass
class AlignmentReport:
    checker_version: str
    scanned_paths: list[str]
    executed_seams: list[dict[str, Any]]
    represented_seams: list[dict[str, Any]]
    missing_seams: list[dict[str, Any]]
    partial_seams: list[dict[str, Any]]
    ordering_findings: list[Finding]
    authority_boundary_findings: list[Finding]
    consumer_obligation_findings: list[Finding]
    advisory_findings: list[Finding]
    summary_counts: dict[str, int] = field(default_factory=dict)

    def finalize(self) -> None:
        self.summary_counts = {
            "executed_seams": len(self.executed_seams),
            "represented_seams": len(self.represented_seams),
            "missing_seams": len(self.missing_seams),
            "partial_seams": len(self.partial_seams),
            "ordering_hard_findings": sum(1 for f in self.ordering_findings if f.severity == "hard"),
            "authority_hard_findings": sum(
                1 for f in self.authority_boundary_findings if f.severity == "hard"
            ),
            "obligation_hard_findings": sum(
                1 for f in self.consumer_obligation_findings if f.severity == "hard"
            ),
            "advisories": len(self.advisory_findings),
        }

    def as_json(self) -> dict[str, Any]:
        return {
            "checker_version": self.checker_version,
            "scanned_paths": self.scanned_paths,
            "executed_seams": self.executed_seams,
            "represented_seams": self.represented_seams,
            "missing_seams": self.missing_seams,
            "partial_seams": self.partial_seams,
            "ordering_findings": [asdict(x) for x in self.ordering_findings],
            "authority_boundary_findings": [asdict(x) for x in self.authority_boundary_findings],
            "consumer_obligation_findings": [asdict(x) for x in self.consumer_obligation_findings],
            "advisory_findings": [asdict(x) for x in self.advisory_findings],
            "summary_counts": self.summary_counts,
        }


def _default_registry() -> list[SeamSpec]:
    return [
        SeamSpec(
            seam_id="subject_tick_entry",
            seam_name="Subject tick entry",
            expected_owner="RT01",
            expected_authority="subject execution spine",
            required_when="scan_subject_tick",
            executed_patterns=("def execute_subject_tick(",),
            represented_patterns=("rt01_subject_tick_contour", "subject_tick"),
            consumer_obligations=(),
        ),
        SeamSpec(
            seam_id="w01_claim_fact_boundary",
            seam_name="W01 world admission",
            expected_owner="W01",
            expected_authority="world admission gate",
            required_when="scan_subject_tick",
            executed_patterns=("build_w01_bounded_world_loop",),
            represented_patterns=("W01", "w01"),
            consumer_obligations=("candidate != request",),
        ),
        SeamSpec(
            seam_id="w02_regularities",
            seam_name="W02 regularity extraction",
            expected_owner="W02",
            expected_authority="regularity extraction",
            required_when="scan_subject_tick",
            executed_patterns=("build_w02_regularity_extraction",),
            represented_patterns=("W02", "w02"),
            consumer_obligations=("request != execution",),
        ),
        SeamSpec(
            seam_id="w03_schema_prior",
            seam_name="W03 schema consolidation",
            expected_owner="W03",
            expected_authority="schema prior",
            required_when="scan_subject_tick",
            executed_patterns=("build_w03_schema_consolidation",),
            represented_patterns=("W03", "w03"),
            consumer_obligations=("effect != completion",),
        ),
        SeamSpec(
            seam_id="w04_applicability_gate",
            seam_name="W04 applicability gating",
            expected_owner="W04",
            expected_authority="applicability gate",
            required_when="scan_subject_tick",
            executed_patterns=("build_w04_applicability_gating",),
            represented_patterns=("W04", "w04"),
            consumer_obligations=("public != eval/private",),
        ),
        SeamSpec(
            seam_id="w05_prediction_permission_separation",
            seam_name="W05 predicted vs permitted",
            expected_owner="W05",
            expected_authority="permission separation",
            required_when="scan_subject_tick",
            executed_patterns=("build_w05_predictive_prior_injection",),
            represented_patterns=("W05", "w05"),
            consumer_obligations=("request != execution",),
        ),
        SeamSpec(
            seam_id="w06_residue_revision_boundary",
            seam_name="W06 revision boundary",
            expected_owner="W06",
            expected_authority="revision routing",
            required_when="scan_subject_tick",
            executed_patterns=("build_w06_error_driven_revision",),
            represented_patterns=("W06", "w06"),
            consumer_obligations=("effect != completion",),
        ),
        SeamSpec(
            seam_id="acp01_internal_candidate_production",
            seam_name="ACP01 candidate production",
            expected_owner="ACP01",
            expected_authority="candidate production only",
            required_when="scan_subject_tick",
            executed_patterns=("build_acp01_internal_action_candidates",),
            represented_patterns=("ACP01", "candidate production"),
            consumer_obligations=("candidate != request", "public != eval/private"),
            forbidden_authority_patterns=(
                "acp01 executes",
                "acp01 submit_action",
                "acp01 creates publishedactionenvelope",
            ),
            expected_order_before=("ap01_subject_action_publication",),
        ),
        SeamSpec(
            seam_id="ap01_subject_action_publication",
            seam_name="AP01 publication",
            expected_owner="AP01",
            expected_authority="publication authority only",
            required_when="scan_subject_tick",
            executed_patterns=("build_ap01_subject_action_publication",),
            represented_patterns=("AP01", "publication authority"),
            consumer_obligations=("request != execution", "effect != completion"),
            forbidden_authority_patterns=(
                "ap01 executes world",
                "ap01 mutates world",
                "ap01 submit_action",
            ),
            expected_order_after=("acp01_internal_candidate_production",),
        ),
        SeamSpec(
            seam_id="bridge_public_observation_projection",
            seam_name="Bridge public observation projection",
            expected_owner="P3 bridge",
            expected_authority="public payload projection",
            required_when="scan_embodied_bridge",
            executed_patterns=("_build_public_subject_tick_surface_payload", "world.observe("),
            represented_patterns=("subject-visible", "observation"),
            consumer_obligations=("public != eval/private",),
        ),
        SeamSpec(
            seam_id="bridge_ap01_envelope_wrapping",
            seam_name="Bridge AP01 envelope wrapping",
            expected_owner="P3 bridge",
            expected_authority="wrap AP01 request only",
            required_when="scan_embodied_bridge",
            executed_patterns=("_envelope_from_request", "PublishedActionEnvelope"),
            represented_patterns=("PublishedActionEnvelope", "AP01 request"),
            consumer_obligations=("candidate != request", "request != execution"),
            forbidden_authority_patterns=("bridge chooses action",),
        ),
        SeamSpec(
            seam_id="world_backend_external_execution",
            seam_name="World backend external execution",
            expected_owner="P2 world backend",
            expected_authority="world mutation outside subject",
            required_when="scan_embodied_bridge",
            executed_patterns=("world.submit_action(",),
            represented_patterns=("world backend", "external"),
            consumer_obligations=("request != execution",),
        ),
        SeamSpec(
            seam_id="action_effect_feedback",
            seam_name="Action effect feedback",
            expected_owner="P2/P3",
            expected_authority="feedback only",
            required_when="scan_embodied_bridge",
            executed_patterns=("ActionEffectFrame", "_effect_packet_from_effect"),
            represented_patterns=("ActionEffectFrame", "feedback"),
            consumer_obligations=("effect != completion",),
        ),
        SeamSpec(
            seam_id="next_observation_effect_feedback",
            seam_name="Next observation effect feedback",
            expected_owner="P3 bridge",
            expected_authority="carry previous effect refs",
            required_when="scan_embodied_bridge",
            executed_patterns=("previous_effect_refs", "next_observation"),
            represented_patterns=("next observation", "effect feedback"),
            consumer_obligations=("effect != completion", "public != eval/private"),
        ),
    ]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _load_scan_targets(
    repo_root: Path,
    *,
    scan_subject_tick: bool,
    scan_embodied_bridge: bool,
    scan_docs: bool,
) -> tuple[dict[str, str], list[str]]:
    targets: list[Path] = []
    if scan_subject_tick:
        targets.extend(
            [
                repo_root / "src/substrate/subject_tick/update.py",
                repo_root / "src/substrate/subject_tick/models.py",
            ]
        )
    targets.append(repo_root / "src/substrate/runtime_topology/policy.py")
    targets.append(repo_root / "src/substrate/runtime_tap_trace.py")
    if scan_embodied_bridge:
        targets.extend(
            [
                repo_root / "experiments/embodied_playground/subject_bridge.py",
                repo_root / "experiments/embodied_playground/bridge_trace.py",
                repo_root / "experiments/embodied_playground/falsifiers.py",
            ]
        )
    if scan_docs:
        for folder in ("docs/agent", "docs/adr", "docs/seams"):
            base = repo_root / folder
            if base.exists():
                targets.extend([p for p in base.rglob("*.md") if p.is_file()])

    texts: dict[str, str] = {}
    scanned: list[str] = []
    for path in targets:
        if not path.exists() or not path.is_file():
            continue
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        if rel in texts:
            continue
        texts[rel] = _read_text(path)
        scanned.append(rel)
    return texts, sorted(scanned)


def _contains_all(text_blob: str, patterns: tuple[str, ...]) -> bool:
    lowered = text_blob.lower()
    return all(pattern.lower() in lowered for pattern in patterns)


def _contains_any(text_blob: str, patterns: tuple[str, ...]) -> bool:
    lowered = text_blob.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def _find_first_path_with_pattern(texts: dict[str, str], pattern: str) -> str | None:
    needle = pattern.lower()
    for path, content in texts.items():
        if needle in content.lower():
            return path
    return None


def _first_runtime_call_line(lines: list[str], token: str) -> int | None:
    for idx, line in enumerate(lines, start=1):
        low = line.lower()
        if token.lower() in low and "(" in low and "import " not in low:
            return idx
    return None


def _build_report(
    repo_root: Path,
    *,
    scan_subject_tick: bool,
    scan_embodied_bridge: bool,
    scan_docs: bool,
    include_advisory: bool,
    registry: list[SeamSpec] | None = None,
) -> AlignmentReport:
    seam_registry = list(_default_registry() if registry is None else registry)
    texts, scanned_paths = _load_scan_targets(
        repo_root,
        scan_subject_tick=scan_subject_tick,
        scan_embodied_bridge=scan_embodied_bridge,
        scan_docs=scan_docs,
    )
    full_blob = "\n".join(texts.values())

    executed_seams: list[dict[str, Any]] = []
    represented_seams: list[dict[str, Any]] = []
    missing_seams: list[dict[str, Any]] = []
    partial_seams: list[dict[str, Any]] = []
    ordering_findings: list[Finding] = []
    authority_findings: list[Finding] = []
    obligation_findings: list[Finding] = []
    advisory_findings: list[Finding] = []

    seam_index: dict[str, dict[str, Any]] = {}
    for spec in seam_registry:
        active = (spec.required_when == "scan_subject_tick" and scan_subject_tick) or (
            spec.required_when == "scan_embodied_bridge" and scan_embodied_bridge
        ) or spec.required_when not in {"scan_subject_tick", "scan_embodied_bridge"}
        if not active:
            continue

        executed = _contains_any(full_blob, spec.executed_patterns)
        represented_hits = [p for p in spec.represented_patterns if _contains_any(full_blob, (p,))]
        represented = len(represented_hits) == len(spec.represented_patterns)
        partial = bool(represented_hits) and not represented

        seam_row = {
            "seam_id": spec.seam_id,
            "seam_name": spec.seam_name,
            "expected_owner": spec.expected_owner,
            "expected_authority": spec.expected_authority,
            "executed": executed,
            "represented": represented,
            "represented_hits": represented_hits,
        }
        seam_index[spec.seam_id] = seam_row

        if executed:
            executed_seams.append(seam_row)
            if represented:
                represented_seams.append(seam_row)
            elif partial:
                partial_seams.append(seam_row)
            else:
                missing_seams.append(seam_row)

        if spec.forbidden_authority_patterns:
            for phrase in spec.forbidden_authority_patterns:
                found_path = _find_first_path_with_pattern(texts, phrase)
                if found_path is not None:
                    authority_findings.append(
                        Finding(
                            finding_type="authority_conflation",
                            severity="hard",
                            seam_id=spec.seam_id,
                            message="Forbidden authority phrase found",
                            path=found_path,
                            evidence=phrase,
                        )
                    )

        for obligation in spec.consumer_obligations:
            if not _contains_any(full_blob, (obligation,)):
                obligation_findings.append(
                    Finding(
                        finding_type="missing_consumer_obligation",
                        severity="advisory",
                        seam_id=spec.seam_id,
                        message="Consumer obligation phrase not found in scanned topology/docs",
                        evidence=obligation,
                    )
                )

    acp_line = None
    ap_line = None
    st_path = "src/substrate/subject_tick/update.py"
    if st_path in texts:
        lines = texts[st_path].splitlines()
        acp_line = _first_runtime_call_line(lines, "build_acp01_internal_action_candidates")
        ap_line = _first_runtime_call_line(lines, "build_ap01_subject_action_publication")
    if acp_line is not None and ap_line is not None:
        if acp_line < ap_line:
            ordering_findings.append(
                Finding(
                    finding_type="acp01_ap01_ordering",
                    severity="ok",
                    seam_id="acp01_internal_candidate_production",
                    message="ACP01 appears before AP01 in subject_tick runtime path",
                    path=st_path,
                    evidence=f"acp01_line={acp_line}, ap01_line={ap_line}",
                )
            )
        else:
            ordering_findings.append(
                Finding(
                    finding_type="acp01_ap01_ordering",
                    severity="hard",
                    seam_id="acp01_internal_candidate_production",
                    message="ACP01 does not appear before AP01 in subject_tick runtime path",
                    path=st_path,
                    evidence=f"acp01_line={acp_line}, ap01_line={ap_line}",
                )
            )
    else:
        ordering_findings.append(
            Finding(
                finding_type="acp01_ap01_ordering",
                severity="hard",
                seam_id="acp01_internal_candidate_production",
                message="Unable to confirm ACP01/AP01 ordering from subject_tick runtime path",
                path=st_path if st_path in texts else None,
            )
        )

    rep_phrase = "acp01 runs before ap01"
    if not _contains_any(full_blob, (rep_phrase, "acp01 before ap01", "acp01 -> ap01")):
        ordering_findings.append(
            Finding(
                finding_type="ordering_representation_gap",
                severity="advisory",
                seam_id="acp01_internal_candidate_production",
                message="ACP01->AP01 ordering is executed but not explicitly phrased in docs/topology text",
                evidence="expected phrase similar to 'acp01 before ap01'",
            )
        )

    if include_advisory:
        for seam in partial_seams:
            advisory_findings.append(
                Finding(
                    finding_type="partial_representation",
                    severity="advisory",
                    seam_id=seam["seam_id"],
                    message="Executed seam has partial topology representation",
                    evidence=", ".join(seam["represented_hits"]),
                )
            )

    advisory_findings.extend(obligation_findings)

    report = AlignmentReport(
        checker_version=CHECKER_VERSION,
        scanned_paths=scanned_paths,
        executed_seams=sorted(executed_seams, key=lambda x: x["seam_id"]),
        represented_seams=sorted(represented_seams, key=lambda x: x["seam_id"]),
        missing_seams=sorted(missing_seams, key=lambda x: x["seam_id"]),
        partial_seams=sorted(partial_seams, key=lambda x: x["seam_id"]),
        ordering_findings=ordering_findings,
        authority_boundary_findings=authority_findings,
        consumer_obligation_findings=obligation_findings,
        advisory_findings=advisory_findings,
    )
    report.finalize()
    return report


def _format_report(report: AlignmentReport) -> str:
    lines: list[str] = []
    lines.append(f"Runtime Topology Alignment Checker [{report.checker_version}]")
    lines.append(f"Scanned files: {len(report.scanned_paths)}")
    lines.append("")
    lines.append(f"Executed seams: {report.summary_counts.get('executed_seams', 0)}")
    lines.append(f"Represented seams: {report.summary_counts.get('represented_seams', 0)}")
    lines.append(f"Missing seams: {report.summary_counts.get('missing_seams', 0)}")
    lines.append(f"Partial seams: {report.summary_counts.get('partial_seams', 0)}")
    lines.append("")
    if report.missing_seams:
        lines.append("Missing seams:")
        for seam in report.missing_seams:
            lines.append(f"- {seam['seam_id']}: {seam['seam_name']}")
        lines.append("")
    if report.partial_seams:
        lines.append("Partial seams:")
        for seam in report.partial_seams:
            hits = ", ".join(seam["represented_hits"])
            lines.append(f"- {seam['seam_id']} (hits: {hits})")
        lines.append("")
    lines.append("Ordering findings:")
    for finding in report.ordering_findings:
        sev = finding.severity.upper()
        lines.append(f"- [{sev}] {finding.finding_type}: {finding.message}")
    lines.append("")
    lines.append("Authority boundary findings:")
    if report.authority_boundary_findings:
        for finding in report.authority_boundary_findings:
            lines.append(f"- [HARD] {finding.seam_id}: {finding.message} ({finding.evidence})")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Consumer obligations:")
    if report.consumer_obligation_findings:
        for finding in report.consumer_obligation_findings:
            lines.append(f"- [{finding.severity}] {finding.seam_id}: missing '{finding.evidence}'")
    else:
        lines.append("- satisfied by scanned sources")
    lines.append("")
    lines.append("Claim calibration:")
    lines.append("- Topology alignment supports formal/executable architecture matching.")
    lines.append("- Topology alignment alone does not prove cognition, agency, or consciousness.")
    return "\n".join(lines)


def run_alignment_checker(
    repo_root: Path,
    *,
    include_advisory: bool = False,
    scan_subject_tick: bool = True,
    scan_embodied_bridge: bool = True,
    scan_docs: bool = True,
    registry: list[SeamSpec] | None = None,
) -> AlignmentReport:
    return _build_report(
        repo_root=repo_root,
        scan_subject_tick=scan_subject_tick,
        scan_embodied_bridge=scan_embodied_bridge,
        scan_docs=scan_docs,
        include_advisory=include_advisory,
        registry=registry,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="P7 Runtime Topology & Role Alignment checker")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--include-advisory", action="store_true", help="Include advisories")
    parser.add_argument("--fail-on-missing", action="store_true", help="Exit nonzero on hard missing seams")
    parser.add_argument("--scan-subject-tick", action="store_true", help="Scan subject_tick runtime contour")
    parser.add_argument("--scan-embodied-bridge", action="store_true", help="Scan embodied bridge contour")
    parser.add_argument("--scan-docs", action="store_true", help="Scan docs for representation evidence")
    args = parser.parse_args()

    scan_subject_tick = True if not any((args.scan_subject_tick, args.scan_embodied_bridge, args.scan_docs)) else args.scan_subject_tick
    scan_embodied_bridge = True if not any((args.scan_subject_tick, args.scan_embodied_bridge, args.scan_docs)) else args.scan_embodied_bridge
    scan_docs = True if not any((args.scan_subject_tick, args.scan_embodied_bridge, args.scan_docs)) else args.scan_docs

    report = run_alignment_checker(
        Path(args.repo_root).resolve(),
        include_advisory=args.include_advisory,
        scan_subject_tick=scan_subject_tick,
        scan_embodied_bridge=scan_embodied_bridge,
        scan_docs=scan_docs,
    )
    if args.json:
        print(json.dumps(report.as_json(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_format_report(report))

    hard_findings = (
        report.summary_counts.get("missing_seams", 0)
        + report.summary_counts.get("ordering_hard_findings", 0)
        + report.summary_counts.get("authority_hard_findings", 0)
    )
    if args.fail_on_missing and hard_findings > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
