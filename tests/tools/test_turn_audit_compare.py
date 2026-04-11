from __future__ import annotations

import json
from pathlib import Path

from tools.turn_audit import collect_turn_audit_artifact_to_disk
from tools.turn_audit_battery import run_turn_audit_battery
from tools.turn_audit_compare import compare_artifacts


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _gen_artifact(path: Path, **kwargs) -> dict:
    _, artifact = collect_turn_audit_artifact_to_disk(
        output_path=path,
        **kwargs,
    )
    return artifact


def _artifact_path_from_battery(index: dict, case_id: str) -> Path:
    matches = [item for item in index.get("cases", []) if item.get("case_id") == case_id]
    assert len(matches) == 1
    return Path(matches[0]["artifact_path"])


def test_compare_confirms_epistemic_load_bearing_difference(tmp_path) -> None:
    battery = run_turn_audit_battery(
        output_dir=tmp_path / "battery-epistemic",
        case_filter=[
            "bounded_clean_production_turn",
            "epistemic_unknown_abstain_detour",
        ],
    )
    index = _load(Path(battery["index_json_path"]))
    baseline = _artifact_path_from_battery(index, "bounded_clean_production_turn")
    perturb = _artifact_path_from_battery(index, "epistemic_unknown_abstain_detour")
    out = tmp_path / "cmp"

    result = compare_artifacts(
        baseline_path=baseline,
        perturbation_path=perturb,
        output_dir=out,
    )
    comparison = _load(Path(result["comparison_json_path"]))
    markdown = Path(result["comparison_markdown_path"]).read_text(encoding="utf-8")

    assert comparison["path_affecting_assessment"]["status"] == "CONFIRMED"
    signals = comparison["path_affecting_assessment"]["signals"]
    assert signals["epistemic_signal_changed"] is True
    assert signals["epistemic_load_bearing_consequence_changed"] is True
    assert signals["epistemic_path_affecting_confirmed"] is True
    assert signals["epistemic_admission_checkpoint_changed"] is True
    primary = comparison["path_affecting_assessment"]["primary_causal_signals"]
    assert "checkpoints.epistemic_admission_checkpoint" in primary
    assert "## Epistemic differences" in markdown
    assert "rt01.epistemic_admission_checkpoint" in markdown


def test_compare_confirms_regulation_load_bearing_difference(tmp_path) -> None:
    battery = run_turn_audit_battery(
        output_dir=tmp_path / "battery-regulation",
        case_filter=[
            "regulation_no_strong_override_claim_guard",
            "regulation_high_override_scope_detour",
        ],
    )
    index = _load(Path(battery["index_json_path"]))
    baseline_path = _artifact_path_from_battery(
        index,
        "regulation_no_strong_override_claim_guard",
    )
    perturb_path = _artifact_path_from_battery(
        index,
        "regulation_high_override_scope_detour",
    )
    out = tmp_path / "cmp"

    result = compare_artifacts(
        baseline_path=baseline_path,
        perturbation_path=perturb_path,
        output_dir=out,
    )
    comparison = _load(Path(result["comparison_json_path"]))
    markdown = Path(result["comparison_markdown_path"]).read_text(encoding="utf-8")

    assert comparison["path_affecting_assessment"]["status"] == "CONFIRMED"
    signals = comparison["path_affecting_assessment"]["signals"]
    assert signals["regulation_signal_changed"] is True
    assert signals["regulation_causal_surface_changed"] is True
    assert signals["regulation_direct_consequence_changed"] is True
    assert signals["regulation_load_bearing_consequence_changed"] is True
    assert signals["regulation_path_affecting_confirmed"] is True
    assert signals["shared_runtime_domain_checkpoint_changed"] is True
    support = comparison["regulation_path_affecting_support"]
    assert support["regulation_signal_changed"] is True
    assert support["regulation_load_bearing_consequence_changed"] is True
    assert support["regulation_path_affecting_confirmed"] is True
    assert isinstance(support["regulation_load_bearing_consequence_field_paths"], list)
    assert support["regulation_load_bearing_consequence_field_paths"]
    assert "## Regulation signal differences" in markdown
    assert "## Regulation observability differences" in markdown
    assert "## Regulation load-bearing consequences" in markdown
    unresolved_codes = {entry["code"] for entry in comparison["unresolved"] if isinstance(entry, dict)}
    assert "REGULATION_GATE_RESTRICTIONS_UNRESOLVED_IN_COMPARISON_INPUT" in unresolved_codes
    assert any(
        marker in comparison["path_affecting_assessment"]["primary_causal_signals"]
        for marker in (
            "checkpoints.shared_runtime_domain_checkpoint",
            "final_outcome.active_execution_mode",
            "final_outcome.final_execution_outcome",
        )
    )


def test_compare_does_not_fake_confirm_cosmetic_epistemic_regulation_difference(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    perturb_path = tmp_path / "perturb.json"
    out = tmp_path / "cmp"
    baseline = _gen_artifact(
        baseline_path,
        case_id="compare-cosmetic-baseline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    perturb = json.loads(json.dumps(baseline))
    perturb["input_summary"]["tick_input"]["case_id"] = "compare-cosmetic-perturb"
    perturb["phase_surfaces"]["epistemics"]["epistemic_status"] = "report_variant"
    perturb["phase_surfaces"]["regulation"]["regulation_pressure_level"] = 0.51
    _write(perturb_path, perturb)

    result = compare_artifacts(
        baseline_path=baseline_path,
        perturbation_path=perturb_path,
        output_dir=out,
    )
    comparison = _load(Path(result["comparison_json_path"]))

    assert comparison["path_affecting_assessment"]["status"] == "NOT_CONFIRMED"
    assert any(
        "epistemic/regulation surface differences are present" in reason
        for reason in comparison["path_affecting_assessment"]["reasons"]
    )
    assert comparison["path_affecting_assessment"]["signals"]["epistemic_status_changed"] is True
    assert "epistemic_surface_only" in comparison["path_affecting_assessment"]["non_load_bearing_differences"]


def test_compare_does_not_auto_confirm_observability_only_regulation_difference(tmp_path) -> None:
    baseline_path = tmp_path / "baseline-observability.json"
    perturb_path = tmp_path / "perturb-observability.json"
    out = tmp_path / "cmp-observability"
    baseline = _gen_artifact(
        baseline_path,
        case_id="compare-regulation-observability-baseline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    perturb = json.loads(json.dumps(baseline))
    perturb["phase_surfaces"]["regulation"]["effective_regulation_causal_reason"] = (
        "synthetic_observability_note_only"
    )
    perturb["phase_surfaces"]["regulation"]["effective_regulation_influence_source"] = (
        "shared_runtime_domain_precedence"
    )
    _write(perturb_path, perturb)

    result = compare_artifacts(
        baseline_path=baseline_path,
        perturbation_path=perturb_path,
        output_dir=out,
    )
    comparison = _load(Path(result["comparison_json_path"]))

    assert comparison["path_affecting_assessment"]["status"] == "NOT_CONFIRMED"
    signals = comparison["path_affecting_assessment"]["signals"]
    assert signals["regulation_observability_changed"] is True
    assert signals["regulation_signal_changed"] is False
    assert signals["regulation_load_bearing_consequence_changed"] is False
    support = comparison["regulation_path_affecting_support"]
    assert support["regulation_observability_changed"] is True
    assert support["regulation_load_bearing_consequence_changed"] is False
    assert support["regulation_path_affecting_confirmed"] is False
    assert "regulation_observability_only" in comparison["path_affecting_assessment"]["non_load_bearing_differences"]


def test_compare_marks_unresolved_for_structurally_incomplete_pair(tmp_path) -> None:
    baseline = tmp_path / "baseline.json"
    perturb = tmp_path / "perturb.json"
    out = tmp_path / "cmp"
    _gen_artifact(
        baseline,
        case_id="compare-unresolved-baseline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    _gen_artifact(
        perturb,
        case_id="compare-unresolved-perturb",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        route_class="helper_path",
    )

    result = compare_artifacts(
        baseline_path=baseline,
        perturbation_path=perturb,
        output_dir=out,
    )
    comparison = _load(Path(result["comparison_json_path"]))
    markdown = Path(result["comparison_markdown_path"]).read_text(encoding="utf-8")

    assert comparison["path_affecting_assessment"]["status"] == "UNRESOLVED"
    unresolved_codes = {entry["code"] for entry in comparison["unresolved"]}
    assert "PERTURBATION_ARTIFACT_STRUCTURALLY_INCOMPLETE" in unresolved_codes
    assert "## Unresolved boundaries" in markdown


def test_compare_backward_compat_without_regulation_observability_fields(tmp_path) -> None:
    baseline_path = tmp_path / "baseline-legacy.json"
    perturb_path = tmp_path / "perturb-legacy.json"
    out = tmp_path / "cmp-legacy"
    baseline = _gen_artifact(
        baseline_path,
        case_id="compare-legacy-regulation-baseline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    perturb = json.loads(json.dumps(baseline))
    perturb["input_summary"]["tick_input"]["case_id"] = "compare-legacy-regulation-perturb"

    for payload in (baseline, perturb):
        regulation = payload.get("phase_surfaces", {}).get("regulation", {})
        if isinstance(regulation, dict):
            regulation.pop("effective_regulation_shared_domain_source_surface", None)
            regulation.pop("effective_shared_runtime_domain_checkpoint_status", None)
            regulation.pop("effective_shared_runtime_domain_checkpoint_applied_action", None)
            regulation.pop("effective_regulation_path_consequence", None)
            regulation.pop("effective_regulation_causal_reason", None)
            regulation.pop("effective_regulation_influence_source", None)
            regulation.pop("effective_regulation_restriction_source", None)

    _write(baseline_path, baseline)
    _write(perturb_path, perturb)

    result = compare_artifacts(
        baseline_path=baseline_path,
        perturbation_path=perturb_path,
        output_dir=out,
    )
    comparison = _load(Path(result["comparison_json_path"]))
    markdown = Path(result["comparison_markdown_path"]).read_text(encoding="utf-8")

    assert comparison["path_affecting_assessment"]["status"] in {"NOT_CONFIRMED", "UNRESOLVED"}
    unresolved_codes = {entry["code"] for entry in comparison["unresolved"] if isinstance(entry, dict)}
    assert "REGULATION_OBSERVABILITY_FIELDS_PARTIALLY_EXPOSED" in unresolved_codes
    assert "## Regulation observability differences" in markdown
    assert "REGULATION_OBSERVABILITY_FIELDS_PARTIALLY_EXPOSED" in markdown


def test_compare_markdown_includes_regulation_and_epistemic_sections(tmp_path) -> None:
    baseline = tmp_path / "baseline.json"
    perturb = tmp_path / "perturb.json"
    out = tmp_path / "cmp"
    _gen_artifact(
        baseline,
        case_id="compare-markdown-baseline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    _gen_artifact(
        perturb,
        case_id="compare-markdown-perturb",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context_flags={"disable_gate_application": True},
    )

    result = compare_artifacts(
        baseline_path=baseline,
        perturbation_path=perturb,
        output_dir=out,
    )
    markdown = Path(result["comparison_markdown_path"]).read_text(encoding="utf-8")

    assert "## Epistemic differences" in markdown
    assert "## Regulation signal differences" in markdown
    assert "## Regulation observability differences" in markdown
    assert "## Regulation load-bearing consequences" in markdown
    assert "## Regulation differences" in markdown
    assert "rt01.shared_runtime_domain_checkpoint" in markdown
    assert "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions" in markdown
    assert "primary causal signals" in markdown
    assert "non-load-bearing differences" in markdown
    assert "regulation signal changed field paths" in markdown
    assert "regulation observability changed field paths" in markdown
    assert "regulation load-bearing consequence field paths" in markdown
