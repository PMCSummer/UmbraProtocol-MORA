from __future__ import annotations

import json
from pathlib import Path

from tools.turn_audit import collect_turn_audit_artifact
from tools.turn_audit_markdown import render_turn_audit_markdown_from_file


def _write_artifact(path: Path, artifact: dict) -> None:
    path.write_text(json.dumps(artifact, ensure_ascii=True, indent=2), encoding="utf-8")


def test_markdown_renderer_creates_clean_report_with_required_sections(tmp_path) -> None:
    artifact = collect_turn_audit_artifact(
        case_id="renderer-clean",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    artifact_path = tmp_path / "renderer-clean.json"
    _write_artifact(artifact_path, artifact)

    report_path, _ = render_turn_audit_markdown_from_file(artifact_path=artifact_path)
    assert report_path.exists()
    markdown = report_path.read_text(encoding="utf-8")

    assert "# Turn summary" in markdown
    assert "## Route / legality / scope" in markdown
    assert "## Critical checkpoints" in markdown
    assert "## Restrictions and forbidden shortcuts" in markdown
    assert "## Uncertainty / degraded / abstain / mixed / unresolved" in markdown
    assert "## Final execution outcome" in markdown
    assert "## Verdicts" in markdown
    assert "## Non-v1 / unresolved boundaries" in markdown

    assert "route class" in markdown
    assert "final execution outcome" in markdown
    assert "overall verdict" in markdown
    assert "mechanistic_integrity" in markdown
    assert "claim_honesty" in markdown
    assert "path_affecting_sensitivity" in markdown
    assert "epistemic status" in markdown
    assert "regulation pressure level" in markdown
    assert "regulation effective influence source" in markdown
    assert "regulation effective shared checkpoint status" in markdown
    assert "regulation effective shared checkpoint applied_action" in markdown
    assert "regulation effective path consequence" in markdown
    assert "regulation effective causal reason" in markdown
    assert "regulation effective restriction source" in markdown
    assert "rt01.epistemic_admission_checkpoint" in markdown
    assert "active execution mode" in markdown


def test_markdown_renderer_keeps_unresolved_visible(tmp_path) -> None:
    artifact = collect_turn_audit_artifact(
        case_id="renderer-unresolved",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        route_class="helper_path",
    )
    artifact_path = tmp_path / "renderer-unresolved.json"
    _write_artifact(artifact_path, artifact)

    report_path, _ = render_turn_audit_markdown_from_file(artifact_path=artifact_path)
    markdown = report_path.read_text(encoding="utf-8")

    assert "PRE_EXECUTION_DISPATCH_REJECTION" in markdown
    assert "UNRESOLVED_FOR_V1" in markdown
    assert (
        "REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD"
        in markdown
    )
    assert "regulation gate restrictions canonical field: `UNRESOLVED_FOR_V1`" in markdown
    assert "Unresolved entries from artifact" in markdown
    assert "Non-v1 / unresolved boundaries" in markdown


def test_markdown_renderer_keeps_explicit_empty_restrictions(tmp_path) -> None:
    artifact = collect_turn_audit_artifact(
        case_id="renderer-empty-restrictions",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    restrictions = artifact["restrictions_and_forbidden_shortcuts"]
    restrictions["dispatch_restrictions"] = []
    restrictions["downstream_gate_restrictions"] = []
    restrictions["epistemic_allowance_restrictions"] = []
    restrictions["regulation_gate_restrictions"] = []
    restrictions["phase_restrictions"] = {
        "s": [],
        "t01": [],
        "t02": "UNRESOLVED_FOR_V1",
    }
    restrictions["phase_forbidden_shortcuts"] = {
        "s": [],
        "t01": [],
    }

    artifact_path = tmp_path / "renderer-empty-restrictions.json"
    _write_artifact(artifact_path, artifact)

    report_path, _ = render_turn_audit_markdown_from_file(artifact_path=artifact_path)
    markdown = report_path.read_text(encoding="utf-8")

    assert "dispatch restrictions: [] (explicit empty list)" in markdown
    assert "downstream gate restrictions: [] (explicit empty list)" in markdown
    assert "epistemic allowance restrictions: [] (explicit empty list)" in markdown
    assert "regulation gate restrictions: [] (explicit empty list)" in markdown
    assert "`s`: [] (explicit empty list)" in markdown
    assert "`t01`: [] (explicit empty list)" in markdown


def test_markdown_renderer_handles_older_artifact_without_v2_fields(tmp_path) -> None:
    artifact = collect_turn_audit_artifact(
        case_id="renderer-backward-compat",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    artifact["phase_surfaces"].pop("epistemics", None)
    artifact["phase_surfaces"].pop("regulation", None)
    artifact["checkpoints"].pop("epistemic_admission_checkpoint", None)
    artifact["checkpoints"].pop("shared_runtime_domain_checkpoint", None)
    artifact["restrictions_and_forbidden_shortcuts"].pop("epistemic_allowance_restrictions", None)
    artifact["restrictions_and_forbidden_shortcuts"].pop("regulation_gate_restrictions", None)
    artifact["uncertainty_and_fallbacks"].pop("epistemic_should_abstain", None)
    artifact["uncertainty_and_fallbacks"].pop("epistemic_unknown_reason", None)
    artifact["uncertainty_and_fallbacks"].pop("epistemic_conflict_reason", None)
    artifact["uncertainty_and_fallbacks"].pop("epistemic_abstain_reason", None)
    artifact["final_outcome"].pop("active_execution_mode", None)

    artifact_path = tmp_path / "renderer-backward-compat.json"
    _write_artifact(artifact_path, artifact)
    report_path, _ = render_turn_audit_markdown_from_file(artifact_path=artifact_path)
    markdown = report_path.read_text(encoding="utf-8")

    assert "epistemic status: `UNRESOLVED_FOR_V1`" in markdown
    assert "regulation pressure level: `UNRESOLVED_FOR_V1`" in markdown
    assert "regulation effective influence source: `UNRESOLVED_FOR_V1`" in markdown
    assert "regulation effective path consequence: `UNRESOLVED_FOR_V1`" in markdown
    assert "rt01.epistemic_admission_checkpoint" in markdown
    assert "active execution mode: `UNRESOLVED_FOR_V1`" in markdown
