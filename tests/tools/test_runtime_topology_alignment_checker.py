from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools import runtime_topology_alignment_checker as checker


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _mk_min_repo(tmp_path: Path, *, with_docs: bool = True) -> Path:
    repo = tmp_path / "repo"
    _write(
        repo / "src/substrate/subject_tick/update.py",
        "\n".join(
            [
                "def execute_subject_tick():",
                "    build_w01_bounded_world_loop()",
                "    build_w02_regularity_extraction()",
                "    build_w03_schema_consolidation()",
                "    build_w04_applicability_gating()",
                "    build_w05_predictive_prior_injection()",
                "    build_w06_error_driven_revision()",
                "    build_acp01_internal_action_candidates()",
                "    build_ap01_subject_action_publication()",
            ]
        ),
    )
    _write(repo / "src/substrate/subject_tick/models.py", "class SubjectTickResult: ...")
    _write(
        repo / "src/substrate/runtime_topology/policy.py",
        "\n".join(
            [
                "rt01_subject_tick_contour",
                "world_adapter.observation",
                "world_adapter.action",
                "world_adapter.effect_feedback",
            ]
        ),
    )
    _write(repo / "src/substrate/runtime_tap_trace.py", "def trace_emit(): ...")
    _write(
        repo / "experiments/embodied_playground/subject_bridge.py",
        "\n".join(
            [
                "world.observe(subject_id)",
                "execute_subject_tick(tick_input, tick_context)",
                "_build_public_subject_tick_surface_payload(observation)",
                "_envelope_from_request(request, subject_id)",
                "PublishedActionEnvelope(...)",
                "world.submit_action(envelope)",
                "ActionEffectFrame(...)",
                "_effect_packet_from_effect(effect)",
                "next_observation = world.observe(subject_id)",
                "previous_effect_refs = ['effect:1']",
            ]
        ),
    )
    _write(repo / "experiments/embodied_playground/bridge_trace.py", "bridge trace model")
    _write(repo / "experiments/embodied_playground/falsifiers.py", "falsifiers")
    if with_docs:
        _write(
            repo / "docs/agent/EXPERIMENTS/p4.md",
            "\n".join(
                [
                    "ACP01 candidate production",
                    "AP01 publication authority",
                    "candidate != request",
                    "request != execution",
                    "effect != completion",
                    "public != eval/private",
                    "acp01 runs before ap01",
                    "world backend external",
                    "next observation effect feedback",
                    "subject-visible observation",
                    "PublishedActionEnvelope from AP01 request",
                    "W01 W02 W03 W04 W05 W06",
                    "ActionEffectFrame feedback",
                ]
            ),
        )
        _write(repo / "docs/adr/ADR-ACP01.md", "ACP01 candidate production only")
        _write(repo / "docs/adr/ADR-AP01.md", "AP01 publication authority only")
        _write(repo / "docs/seams/RT01.seam.md", "subject_tick contour")
    return repo


def test_topology_checker_imports() -> None:
    assert checker.CHECKER_VERSION.startswith("p7-runtime-topology-alignment")


def test_topology_checker_reports_required_sections_json(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    report = checker.run_alignment_checker(repo, include_advisory=True)
    data = report.as_json()
    for key in (
        "checker_version",
        "scanned_paths",
        "executed_seams",
        "represented_seams",
        "missing_seams",
        "partial_seams",
        "ordering_findings",
        "authority_boundary_findings",
        "consumer_obligation_findings",
        "advisory_findings",
        "summary_counts",
    ):
        assert key in data


def test_topology_checker_detects_acp01_ap01_ordering(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    report = checker.run_alignment_checker(repo)
    finding = next(f for f in report.ordering_findings if f.finding_type == "acp01_ap01_ordering")
    assert finding.severity == "ok"


def test_topology_checker_flags_missing_executed_seam(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path, with_docs=False)
    report = checker.run_alignment_checker(repo)
    assert report.summary_counts["missing_seams"] > 0


def test_topology_checker_accepts_documented_executed_seam(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path, with_docs=True)
    report = checker.run_alignment_checker(repo)
    seam_ids = {row["seam_id"] for row in report.represented_seams}
    assert "ap01_subject_action_publication" in seam_ids
    assert "acp01_internal_candidate_production" in seam_ids


def test_topology_checker_flags_candidate_request_execution_conflation(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    _write(repo / "docs/agent/GOVERNANCE/bad.md", "ACP01 executes and AP01 mutates world.")
    report = checker.run_alignment_checker(repo)
    assert any(f.finding_type == "authority_conflation" for f in report.authority_boundary_findings)


def test_topology_checker_flags_bridge_world_authority_conflation(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    _write(repo / "docs/agent/GOVERNANCE/bad_bridge.md", "bridge chooses action for subject")
    report = checker.run_alignment_checker(repo)
    assert any((f.evidence or "").lower() == "bridge chooses action" for f in report.authority_boundary_findings)


def test_topology_checker_reports_consumer_obligations(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    report = checker.run_alignment_checker(repo)
    assert report.summary_counts["obligation_hard_findings"] == 0


def test_topology_checker_fail_on_missing_exit_code(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path, with_docs=False)
    cmd = [
        sys.executable,
        "tools/runtime_topology_alignment_checker.py",
        "--repo-root",
        str(repo),
        "--fail-on-missing",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert result.returncode == 1


def test_topology_checker_default_repo_scan_no_src_or_experiment_mutation(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    before = {p: p.read_text(encoding="utf-8") for p in repo.rglob("*.py")}
    _ = checker.run_alignment_checker(repo)
    after = {p: p.read_text(encoding="utf-8") for p in repo.rglob("*.py")}
    assert before == after


def test_topology_checker_current_acp01_and_ap01_are_not_missing() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    report = checker.run_alignment_checker(repo_root, include_advisory=True)
    missing = {row["seam_id"] for row in report.missing_seams}
    assert "acp01_internal_candidate_production" not in missing
    assert "ap01_subject_action_publication" not in missing


def test_topology_checker_outputs_p7_claim_calibration(tmp_path: Path) -> None:
    repo = _mk_min_repo(tmp_path)
    report = checker.run_alignment_checker(repo)
    text = checker._format_report(report)
    assert "does not prove cognition" in text.lower()
    assert "formal/executable architecture matching" in text.lower()
