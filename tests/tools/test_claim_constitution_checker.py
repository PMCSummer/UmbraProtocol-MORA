from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.claim_constitution_checker import run_claim_constitution_checker


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_minimal_artifacts(root: Path) -> None:
    _write(root / "src/substrate/ap01_subject_action_publication/__init__.py", "")
    _write(root / "src/substrate/acp01_internal_action_candidate_production/policy.py", "")
    _write(root / "experiments/embodied_playground/models.py", "")
    _write(root / "experiments/embodied_playground/grid_world.py", "")
    _write(root / "experiments/embodied_playground/subject_bridge.py", "")
    _write(root / "experiments/embodied_playground/falsifiers.py", "")


def _run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "tools" / "claim_constitution_checker.py"
    return subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_claim_constitution_authorizes_current_bounded_proto_subject_claim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/note.md", "bounded proto-subject architecture")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=True,
    )

    joined = "\n".join(report.authorized_claims).lower()
    assert "bounded proto-subject" in joined
    assert "internal action-candidate production" in joined


def test_claim_constitution_rejects_consciousness_proven_claim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/claim.md", "We have consciousness proven in this build.")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert any(item.finding_type == "forbidden_vocabulary" for item in report.claim_findings)


def test_claim_constitution_allows_consciousness_adjacent_cautious_language(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(
        tmp_path / "docs/agent/claim.md",
        "This is not proof of consciousness, but consciousness-adjacent functional indicators.",
    )

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert not any(item.finding_type == "forbidden_vocabulary" for item in report.claim_findings)


def test_claim_constitution_rejects_l8_without_baseline_artifact(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/claim.md", "Stage is externally benchmarked and cross-backend proven.")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert any(item.finding_type == "missing_external_artifact" for item in report.claim_findings)


def test_claim_constitution_rejects_closed_claim_with_todo_allowed_claim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    payload = {
        "status": "closed",
        "allowed_claim": "TODO allowed_claim",
        "validation_state": "planned",
    }
    _write(tmp_path / "tracker/claim.json", json.dumps(payload, ensure_ascii=False))

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=True,
        scan_docs=False,
        scan_experiments=False,
    )

    assert any(item.finding_type == "closed_with_todo_allowed_claim" for item in report.claim_findings)


def test_claim_constitution_rejects_claim_blocked_by_nonempty_on_closed_status(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    payload = {
        "status": "closed",
        "allowed_claim": "L5 bounded loop",
        "claim_blocked_by": ["P8"],
        "validation_state": "implemented",
    }
    _write(tmp_path / "tracker/claim.json", json.dumps(payload, ensure_ascii=False))

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=True,
        scan_docs=False,
        scan_experiments=False,
    )

    assert any(item.finding_type == "closed_with_claim_blockers" for item in report.claim_findings)


def test_claim_constitution_rejects_acp01_planner_overclaim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/acp01.md", "ACP01 planning and open-ended strategy are implemented.")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert any(item.finding_type == "stage_overclaim_acp01_planner" for item in report.claim_findings)


def test_claim_constitution_rejects_ap01_execution_overclaim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/ap01.md", "AP01 executes actions and AP01 world mutation is complete.")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert any(item.finding_type == "stage_overclaim_ap01_execution" for item in report.claim_findings)


def test_claim_constitution_json_output_has_required_sections(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    proc = _run_cli(tmp_path, "--json")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    required = {
        "constitution_version",
        "scanned_paths",
        "skipped_paths",
        "claim_findings",
        "authorized_claims",
        "blocked_claims",
        "overclaim_findings",
        "missing_evidence_findings",
        "advisory_findings",
        "safe_context_mentions",
        "ignored_non_claim_surface_mentions",
        "summary_counts",
    }
    assert required.issubset(set(payload.keys()))


def test_claim_constitution_fail_on_overclaim_exit_code(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/bad.md", "consciousness proven")

    proc = _run_cli(tmp_path, "--fail-on-overclaim", "--scan-docs")
    assert proc.returncode != 0


def test_claim_constitution_report_mentions_near_defensible_claims(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=False,
        scan_experiments=False,
    )
    advisory = "\n".join(item.evidence for item in report.advisory_findings).lower()
    assert "cross-backend portability" in advisory
    assert "self/world boundary" in advisory


def test_claim_constitution_does_not_require_already_planned_world_action_selector_as_new_recommendation(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=False,
        scan_experiments=False,
    )
    joined = "\n".join(item.evidence for item in report.advisory_findings).lower()
    assert "world action selector" not in joined
    assert "gui" not in joined


def test_checker_default_scan_excludes_tests_and_checker_source_from_hard_claim_surface(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "tests/tools/noise.md", "consciousness proven")
    _write(tmp_path / "tools/claim_constitution_checker.py", "consciousness proven")
    _write(tmp_path / "docs/agent/ok.md", "bounded proto-subject")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=True,
        scan_docs=True,
        scan_experiments=True,
    )

    assert all(not item.path.startswith("tests/") for item in report.claim_findings)
    assert all(item.path != "tools/claim_constitution_checker.py" for item in report.claim_findings)


def test_checker_ignores_pycache_and_generated_artifacts(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/__pycache__/bad.pyc", "consciousness proven")
    _write(tmp_path / "docs/agent/generated/report.pdf", "consciousness proven")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert not report.claim_findings
    assert any("generated_or_cache" in item for item in report.skipped_paths)


def test_checker_still_scans_docs_agent_and_adr_claim_surfaces(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/claim.md", "consciousness proven")
    _write(tmp_path / "adr/claim.md", "consciousness proven")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    paths = {item.path for item in report.claim_findings}
    assert "docs/agent/claim.md" in paths
    assert "adr/claim.md" in paths


def test_checker_does_not_flag_forbidden_phrase_inside_forbidden_examples_section(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(
        tmp_path / "docs/agent/gov.md",
        "# Forbidden patterns\nDo not claim consciousness proven.",
    )

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert not report.claim_findings
    assert any(item.evidence == "consciousness proven" for item in report.safe_context_mentions)


def test_checker_does_not_flag_forbidden_phrase_inside_code_block(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(
        tmp_path / "docs/agent/gov.md",
        "```text\nconsciousness proven\n```",
    )

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert not report.claim_findings
    assert report.safe_context_mentions


def test_checker_allows_negated_consciousness_claim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(
        tmp_path / "docs/agent/gov.md",
        "This does not prove consciousness proven status.",
    )

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert not report.claim_findings


def test_checker_flags_affirmative_consciousness_claim_in_normal_claim_section(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/claims.md", "# Current claims\nWe are consciousness proven now.")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    assert any(item.finding_type == "forbidden_vocabulary" for item in report.claim_findings)


def test_checker_authorized_claims_are_reported_even_when_advisories_exist(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=False,
        scan_experiments=False,
    )

    assert report.authorized_claims
    assert report.advisory_findings


def test_checker_hard_findings_include_path_line_reason_and_context(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/claim.md", "# Claims\nconsciousness proven")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=False,
        scan_docs=True,
        scan_experiments=False,
    )

    finding = next(item for item in report.claim_findings if item.finding_type == "forbidden_vocabulary")
    assert finding.path == "docs/agent/claim.md"
    assert finding.line == 2
    assert finding.section
    assert finding.message


def test_checker_default_repo_scan_has_no_self_referential_governance_noise(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/GOVERNANCE/mora_claim_constitution.md", "# Forbidden language\nDo not claim consciousness proven")
    _write(tmp_path / "tests/tools/noise.py", "consciousness proven")
    _write(tmp_path / "tools/claim_constitution_checker.py", "consciousness proven")

    report = run_claim_constitution_checker(
        repo_root=tmp_path,
        scan_roadmap=True,
        scan_docs=True,
        scan_experiments=True,
    )

    assert report.summary_counts["hard_violations"] == 0


def test_fail_on_overclaim_exits_zero_for_safe_governance_examples(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/GOVERNANCE/gov.md", "# Forbidden language\nDo not claim consciousness proven")

    proc = _run_cli(tmp_path, "--scan-docs", "--fail-on-overclaim")
    assert proc.returncode == 0


def test_fail_on_overclaim_exits_nonzero_for_real_claim_surface_overclaim(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/claim.md", "# Current claims\nconsciousness proven")

    proc = _run_cli(tmp_path, "--scan-docs", "--fail-on-overclaim")
    assert proc.returncode != 0


def test_json_output_separates_safe_context_and_ignored_mentions(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "docs/agent/GOVERNANCE/gov.md", "# Forbidden patterns\nDo not claim consciousness proven")
    _write(tmp_path / "experiments/__pycache__/noise.pyc", "consciousness proven")

    proc = _run_cli(tmp_path, "--scan-docs", "--scan-experiments", "--json")
    payload = json.loads(proc.stdout)

    assert "safe_context_mentions" in payload
    assert "ignored_non_claim_surface_mentions" in payload


def test_json_output_lists_skipped_paths(tmp_path: Path) -> None:
    _seed_minimal_artifacts(tmp_path)
    _write(tmp_path / "experiments/__pycache__/noise.pyc", "x")

    proc = _run_cli(tmp_path, "--scan-experiments", "--json")
    payload = json.loads(proc.stdout)

    assert "skipped_paths" in payload
    assert any("generated_or_cache" in item for item in payload["skipped_paths"])
