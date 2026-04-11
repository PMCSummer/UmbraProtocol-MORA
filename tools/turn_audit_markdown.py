from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


UNRESOLVED_TOKEN = "UNRESOLVED_FOR_V1"
ARTIFACT_VERSION = "turn_audit_artifact_v1"
REQUIRED_TOP_LEVEL_SECTIONS: tuple[str, ...] = (
    "artifact_metadata",
    "input_summary",
    "route_and_scope",
    "phase_surfaces",
    "checkpoints",
    "restrictions_and_forbidden_shortcuts",
    "uncertainty_and_fallbacks",
    "final_outcome",
    "verdicts",
    "unresolved",
)


class ArtifactCompatibilityError(ValueError):
    pass


def _load_artifact(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ArtifactCompatibilityError("artifact must be a JSON object")
    metadata = raw.get("artifact_metadata")
    if not isinstance(metadata, dict):
        raise ArtifactCompatibilityError("missing artifact_metadata object")
    artifact_version = metadata.get("artifact_version")
    if not isinstance(artifact_version, str) or not artifact_version.startswith(ARTIFACT_VERSION):
        raise ArtifactCompatibilityError("artifact is not v1-compatible")
    return raw


def _get_path(payload: dict[str, Any], dotted: str, default: Any = UNRESOLVED_TOKEN) -> Any:
    current: Any = payload
    for token in dotted.split("."):
        if not isinstance(current, dict) or token not in current:
            return default
        current = current[token]
    return current


def _fmt_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _fmt_list(value: Any) -> str:
    if value == UNRESOLVED_TOKEN:
        return UNRESOLVED_TOKEN
    if not isinstance(value, list):
        return _fmt_scalar(value)
    if not value:
        return "[] (explicit empty list)"
    return ", ".join(str(item) for item in value)


def _append_missing_section_unresolved(lines: list[str], artifact: dict[str, Any]) -> None:
    missing = [name for name in REQUIRED_TOP_LEVEL_SECTIONS if name not in artifact]
    if not missing:
        return
    lines.append("")
    lines.append("## Structural unresolved")
    lines.append(
        "- missing top-level sections: "
        + ", ".join(missing)
        + " (field: root)"
    )


def _scope_rows(phase_surfaces: dict[str, Any]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for surface_name in sorted(phase_surfaces):
        surface_payload = phase_surfaces.get(surface_name)
        if not isinstance(surface_payload, dict):
            continue
        scope_payload = surface_payload.get("scope")
        if isinstance(scope_payload, dict):
            scope = _fmt_scalar(scope_payload.get("scope", UNRESOLVED_TOKEN))
            rt01_flag = _fmt_scalar(scope_payload.get("rt01_contour_only", UNRESOLVED_TOKEN))
            rows.append((surface_name, scope, rt01_flag))
            continue
        if isinstance(scope_payload, str):
            rt01_flag = _fmt_scalar(surface_payload.get("rt01_contour_only", UNRESOLVED_TOKEN))
            rows.append((surface_name, scope_payload, rt01_flag))
    return rows


def _render_turn_summary(lines: list[str], artifact: dict[str, Any], artifact_path: Path) -> None:
    lines.append("# Turn summary")
    lines.append(
        "- artifact path: "
        f"`{artifact_path}` "
        "(field: input artifact file)"
    )
    lines.append(
        "- artifact version: "
        f"`{_fmt_scalar(_get_path(artifact, 'artifact_metadata.artifact_version'))}` "
        "(field: artifact_metadata.artifact_version)"
    )
    lines.append(
        "- route class: "
        f"`{_fmt_scalar(_get_path(artifact, 'route_and_scope.route_class'))}` "
        "(field: route_and_scope.route_class)"
    )
    lines.append(
        "- route binding consequence: "
        f"`{_fmt_scalar(_get_path(artifact, 'route_and_scope.route_binding_consequence'))}` "
        "(field: route_and_scope.route_binding_consequence)"
    )
    lines.append(
        "- final execution outcome: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.final_execution_outcome'))}` "
        "(field: final_outcome.final_execution_outcome)"
    )
    lines.append(
        "- overall verdict: "
        f"`{_fmt_scalar(_get_path(artifact, 'verdicts.overall.status'))}` "
        "(field: verdicts.overall.status)"
    )
    lines.append(
        "- mechanistic_integrity: "
        f"`{_fmt_scalar(_get_path(artifact, 'verdicts.mechanistic_integrity.status'))}` "
        "(field: verdicts.mechanistic_integrity.status)"
    )
    lines.append(
        "- claim_honesty: "
        f"`{_fmt_scalar(_get_path(artifact, 'verdicts.claim_honesty.status'))}` "
        "(field: verdicts.claim_honesty.status)"
    )
    lines.append(
        "- path_affecting_sensitivity: "
        f"`{_fmt_scalar(_get_path(artifact, 'verdicts.path_affecting_sensitivity.status'))}` "
        "(field: verdicts.path_affecting_sensitivity.status)"
    )


def _render_route_legality_scope(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Route / legality / scope")
    lines.append(
        "- dispatch accepted: "
        f"`{_fmt_scalar(_get_path(artifact, 'route_and_scope.accepted'))}` "
        "(field: route_and_scope.accepted)"
    )
    lines.append(
        "- lawful production route: "
        f"`{_fmt_scalar(_get_path(artifact, 'route_and_scope.lawful_production_route'))}` "
        "(field: route_and_scope.lawful_production_route)"
    )
    lines.append(
        "- decision restrictions: "
        f"{_fmt_list(_get_path(artifact, 'route_and_scope.decision_restrictions', []))} "
        "(field: route_and_scope.decision_restrictions)"
    )
    lines.append(
        "- runtime order: "
        f"{_fmt_list(_get_path(artifact, 'route_and_scope.runtime_order', []))} "
        "(field: route_and_scope.runtime_order)"
    )
    mandatory = _get_path(artifact, "checkpoints.mandatory_checkpoint_ids", [])
    mandatory_count = len(mandatory) if isinstance(mandatory, list) else UNRESOLVED_TOKEN
    lines.append(
        "- mandatory checkpoint count: "
        f"`{mandatory_count}` "
        "(field: checkpoints.mandatory_checkpoint_ids)"
    )
    lines.append(
        "- epistemic status: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.epistemics.epistemic_status'))}` "
        "(field: phase_surfaces.epistemics.epistemic_status)"
    )
    lines.append(
        "- epistemic confidence: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.epistemics.epistemic_confidence'))}` "
        "(field: phase_surfaces.epistemics.epistemic_confidence)"
    )
    lines.append(
        "- epistemic source_class: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.epistemics.epistemic_source_class'))}` "
        "(field: phase_surfaces.epistemics.epistemic_source_class)"
    )
    lines.append(
        "- epistemic modality: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.epistemics.epistemic_modality'))}` "
        "(field: phase_surfaces.epistemics.epistemic_modality)"
    )
    lines.append(
        "- regulation pressure level: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.regulation_pressure_level'))}` "
        "(field: phase_surfaces.regulation.regulation_pressure_level)"
    )
    lines.append(
        "- regulation escalation stage: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.regulation_escalation_stage'))}` "
        "(field: phase_surfaces.regulation.regulation_escalation_stage)"
    )
    lines.append(
        "- regulation override scope: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.regulation_override_scope'))}` "
        "(field: phase_surfaces.regulation.regulation_override_scope)"
    )
    lines.append(
        "- regulation no_strong_override_claim: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.regulation_no_strong_override_claim'))}` "
        "(field: phase_surfaces.regulation.regulation_no_strong_override_claim)"
    )
    lines.append(
        "- regulation gate_accepted: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.regulation_gate_accepted'))}` "
        "(field: phase_surfaces.regulation.regulation_gate_accepted)"
    )
    lines.append(
        "- regulation source_state_ref: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.regulation_source_state_ref'))}` "
        "(field: phase_surfaces.regulation.regulation_source_state_ref)"
    )
    lines.append(
        "- regulation effective influence source: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_regulation_influence_source'))}` "
        "(field: phase_surfaces.regulation.effective_regulation_influence_source)"
    )
    lines.append(
        "- regulation effective shared-domain source surface: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_regulation_shared_domain_source_surface'))}` "
        "(field: phase_surfaces.regulation.effective_regulation_shared_domain_source_surface)"
    )
    lines.append(
        "- regulation effective shared checkpoint status: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_shared_runtime_domain_checkpoint_status'))}` "
        "(field: phase_surfaces.regulation.effective_shared_runtime_domain_checkpoint_status)"
    )
    lines.append(
        "- regulation effective shared checkpoint applied_action: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_shared_runtime_domain_checkpoint_applied_action'))}` "
        "(field: phase_surfaces.regulation.effective_shared_runtime_domain_checkpoint_applied_action)"
    )
    phase_surfaces = _get_path(artifact, "phase_surfaces", {})
    rows = _scope_rows(phase_surfaces if isinstance(phase_surfaces, dict) else {})
    lines.append("")
    lines.append("Scope table:")
    lines.append("| Surface | Scope | rt01_contour_only |")
    lines.append("| --- | --- | --- |")
    if not rows:
        lines.append(f"| {UNRESOLVED_TOKEN} | {UNRESOLVED_TOKEN} | {UNRESOLVED_TOKEN} |")
    else:
        for surface_name, scope, rt01_flag in rows:
            lines.append(f"| `{surface_name}` | `{scope}` | `{rt01_flag}` |")


def _render_checkpoints(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Critical checkpoints")
    lines.append(
        "- checkpoint coverage complete: "
        f"`{_fmt_scalar(_get_path(artifact, 'checkpoints.checkpoint_coverage_complete'))}` "
        "(field: checkpoints.checkpoint_coverage_complete)"
    )
    lines.append(
        "- missing mandatory checkpoint ids: "
        f"{_fmt_list(_get_path(artifact, 'checkpoints.missing_mandatory_checkpoint_ids', []))} "
        "(field: checkpoints.missing_mandatory_checkpoint_ids)"
    )
    lines.append(
        "- blocked checkpoint ids: "
        f"{_fmt_list(_get_path(artifact, 'checkpoints.blocked_checkpoint_ids', []))} "
        "(field: checkpoints.blocked_checkpoint_ids)"
    )
    lines.append(
        "- enforced detour checkpoint ids: "
        f"{_fmt_list(_get_path(artifact, 'checkpoints.enforced_detour_checkpoint_ids', []))} "
        "(field: checkpoints.enforced_detour_checkpoint_ids)"
    )

    lines.append("")
    lines.append("Explicit checkpoint rows:")
    lines.append("| Checkpoint | Status | Required action | Applied action | Reason |")
    lines.append("| --- | --- | --- | --- | --- |")
    for checkpoint_id, path in (
        ("rt01.epistemic_admission_checkpoint", "checkpoints.epistemic_admission_checkpoint"),
        ("rt01.shared_runtime_domain_checkpoint", "checkpoints.shared_runtime_domain_checkpoint"),
        ("rt01.downstream_obedience_checkpoint", "checkpoints.downstream_obedience_checkpoint"),
        ("rt01.outcome_resolution_checkpoint", "checkpoints.outcome_resolution_checkpoint"),
    ):
        payload = _get_path(artifact, path)
        if isinstance(payload, dict):
            lines.append(
                "| "
                f"`{checkpoint_id}` | "
                f"`{_fmt_scalar(payload.get('status', UNRESOLVED_TOKEN))}` | "
                f"`{_fmt_scalar(payload.get('required_action', UNRESOLVED_TOKEN))}` | "
                f"`{_fmt_scalar(payload.get('applied_action', UNRESOLVED_TOKEN))}` | "
                f"`{_fmt_scalar(payload.get('reason', UNRESOLVED_TOKEN))}` |"
            )
        else:
            lines.append(
                f"| `{checkpoint_id}` | `{_fmt_scalar(payload)}` | `{UNRESOLVED_TOKEN}` | "
                f"`{UNRESOLVED_TOKEN}` | `{UNRESOLVED_TOKEN}` |"
            )


def _render_restrictions(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Restrictions and forbidden shortcuts")
    lines.append(
        "- dispatch restrictions: "
        f"{_fmt_list(_get_path(artifact, 'restrictions_and_forbidden_shortcuts.dispatch_restrictions', []))} "
        "(field: restrictions_and_forbidden_shortcuts.dispatch_restrictions)"
    )
    lines.append(
        "- downstream gate restrictions: "
        f"{_fmt_list(_get_path(artifact, 'restrictions_and_forbidden_shortcuts.downstream_gate_restrictions', []))} "
        "(field: restrictions_and_forbidden_shortcuts.downstream_gate_restrictions)"
    )
    lines.append(
        "- epistemic allowance restrictions: "
        f"{_fmt_list(_get_path(artifact, 'restrictions_and_forbidden_shortcuts.epistemic_allowance_restrictions'))} "
        "(field: restrictions_and_forbidden_shortcuts.epistemic_allowance_restrictions)"
    )
    lines.append(
        "- regulation gate restrictions: "
        f"{_fmt_list(_get_path(artifact, 'restrictions_and_forbidden_shortcuts.regulation_gate_restrictions'))} "
        "(field: restrictions_and_forbidden_shortcuts.regulation_gate_restrictions)"
    )
    lines.append(
        "- t02 restrictions: "
        f"{_fmt_list(_get_path(artifact, 'restrictions_and_forbidden_shortcuts.t02_restrictions'))} "
        "(field: restrictions_and_forbidden_shortcuts.t02_restrictions)"
    )
    lines.append(
        "- regulation effective restriction source: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_regulation_restriction_source'))}` "
        "(field: phase_surfaces.regulation.effective_regulation_restriction_source)"
    )
    regulation_gate_restrictions = _get_path(
        artifact,
        "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions",
    )
    if regulation_gate_restrictions == UNRESOLVED_TOKEN:
        lines.append(
            "- regulation gate restrictions canonical field: "
            "`UNRESOLVED_FOR_V1` "
            "(evidence: unresolved[].code=REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD)"
        )
    t02_restrictions = _get_path(
        artifact,
        "restrictions_and_forbidden_shortcuts.t02_restrictions",
    )
    if t02_restrictions == UNRESOLVED_TOKEN:
        lines.append(
            "- t02 restrictions canonical field: "
            "`UNRESOLVED_FOR_V1` "
            "(evidence: unresolved[].code=T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD)"
        )

    lines.append("")
    lines.append("Per-phase restrictions:")
    phase_restrictions = _get_path(
        artifact,
        "restrictions_and_forbidden_shortcuts.phase_restrictions",
        {},
    )
    if isinstance(phase_restrictions, dict):
        for phase_name in sorted(phase_restrictions):
            lines.append(
                f"- `{phase_name}`: {_fmt_list(phase_restrictions.get(phase_name))} "
                f"(field: restrictions_and_forbidden_shortcuts.phase_restrictions.{phase_name})"
            )
    else:
        lines.append(f"- {UNRESOLVED_TOKEN} (field: restrictions_and_forbidden_shortcuts.phase_restrictions)")

    lines.append("")
    lines.append("Per-phase forbidden shortcuts:")
    phase_shortcuts = _get_path(
        artifact,
        "restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts",
        {},
    )
    if isinstance(phase_shortcuts, dict):
        for phase_name in sorted(phase_shortcuts):
            lines.append(
                f"- `{phase_name}`: {_fmt_list(phase_shortcuts.get(phase_name))} "
                f"(field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.{phase_name})"
            )
    else:
        lines.append(
            f"- {UNRESOLVED_TOKEN} (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts)"
        )


def _render_uncertainty(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Uncertainty / degraded / abstain / mixed / unresolved")
    lines.append(
        "- abstain: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.abstain'))}` "
        "(field: uncertainty_and_fallbacks.abstain)"
    )
    lines.append(
        "- abstain_reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.abstain_reason'))}` "
        "(field: uncertainty_and_fallbacks.abstain_reason)"
    )
    lines.append(
        "- epistemic_should_abstain: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.epistemic_should_abstain'))}` "
        "(field: uncertainty_and_fallbacks.epistemic_should_abstain)"
    )
    lines.append(
        "- epistemic_claim_strength: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.epistemic_claim_strength'))}` "
        "(field: uncertainty_and_fallbacks.epistemic_claim_strength)"
    )
    lines.append(
        "- epistemic_allowance_reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.epistemic_allowance_reason'))}` "
        "(field: uncertainty_and_fallbacks.epistemic_allowance_reason)"
    )
    lines.append(
        "- epistemic_unknown_reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.epistemic_unknown_reason'))}` "
        "(field: uncertainty_and_fallbacks.epistemic_unknown_reason)"
    )
    lines.append(
        "- epistemic_conflict_reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.epistemic_conflict_reason'))}` "
        "(field: uncertainty_and_fallbacks.epistemic_conflict_reason)"
    )
    lines.append(
        "- epistemic_abstain_reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.epistemic_abstain_reason'))}` "
        "(field: uncertainty_and_fallbacks.epistemic_abstain_reason)"
    )
    lines.append(
        "- regulation_no_strong_override_claim: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.regulation_no_strong_override_claim'))}` "
        "(field: uncertainty_and_fallbacks.regulation_no_strong_override_claim)"
    )
    lines.append(
        "- regulation_gate_accepted: "
        f"`{_fmt_scalar(_get_path(artifact, 'uncertainty_and_fallbacks.regulation_gate_accepted'))}` "
        "(field: uncertainty_and_fallbacks.regulation_gate_accepted)"
    )
    lines.append(
        "- regulation effective causal reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_regulation_causal_reason'))}` "
        "(field: phase_surfaces.regulation.effective_regulation_causal_reason)"
    )

    lines.append("")
    lines.append("Active uncertainty/no_safe/degraded markers:")
    found_any = False
    for group in ("uncertainty_markers", "no_safe_markers", "degraded_markers"):
        payload = _get_path(artifact, f"uncertainty_and_fallbacks.{group}", {})
        if not isinstance(payload, dict):
            lines.append(f"- `{group}`: {UNRESOLVED_TOKEN} (field: uncertainty_and_fallbacks.{group})")
            found_any = True
            continue
        for marker, value in payload.items():
            active = (value is True) or (isinstance(value, list) and len(value) > 0) or (value == UNRESOLVED_TOKEN)
            if active:
                lines.append(
                    f"- `{group}.{marker}`: `{_fmt_scalar(value)}` "
                    f"(field: uncertainty_and_fallbacks.{group}.{marker})"
                )
                found_any = True
    if not found_any:
        lines.append("- none (no active markers in artifact)")

    unresolved = _get_path(artifact, "unresolved", [])
    lines.append("")
    lines.append("Unresolved entries from artifact:")
    if isinstance(unresolved, list) and unresolved:
        for entry in unresolved:
            if isinstance(entry, dict):
                lines.append(
                    "- "
                    f"`{_fmt_scalar(entry.get('code', UNRESOLVED_TOKEN))}`: "
                    f"{_fmt_scalar(entry.get('message', UNRESOLVED_TOKEN))} "
                    "(field: unresolved[])"
                )
            else:
                lines.append(f"- `{_fmt_scalar(entry)}` (field: unresolved[])")
    elif isinstance(unresolved, list):
        lines.append("- [] (explicit empty list) (field: unresolved)")
    else:
        lines.append(f"- {UNRESOLVED_TOKEN} (field: unresolved)")


def _render_final_outcome(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Final execution outcome")
    lines.append(
        "- execution stance: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.execution_stance'))}` "
        "(field: final_outcome.execution_stance)"
    )
    lines.append(
        "- active execution mode: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.active_execution_mode'))}` "
        "(field: final_outcome.active_execution_mode)"
    )
    lines.append(
        "- repair_needed: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.repair_needed'))}` "
        "(field: final_outcome.repair_needed)"
    )
    lines.append(
        "- revalidation_needed: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.revalidation_needed'))}` "
        "(field: final_outcome.revalidation_needed)"
    )
    lines.append(
        "- halt_reason: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.halt_reason'))}` "
        "(field: final_outcome.halt_reason)"
    )
    lines.append(
        "- persist_transition_accepted: "
        f"`{_fmt_scalar(_get_path(artifact, 'final_outcome.persist_transition_accepted'))}` "
        "(field: final_outcome.persist_transition_accepted)"
    )
    lines.append(
        "- regulation effective path consequence: "
        f"`{_fmt_scalar(_get_path(artifact, 'phase_surfaces.regulation.effective_regulation_path_consequence'))}` "
        "(field: phase_surfaces.regulation.effective_regulation_path_consequence)"
    )


def _render_verdicts(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Verdicts")
    verdicts = _get_path(artifact, "verdicts", {})
    if not isinstance(verdicts, dict):
        lines.append(f"- {UNRESOLVED_TOKEN} (field: verdicts)")
        return
    for verdict_name in (
        "mechanistic_integrity",
        "claim_honesty",
        "path_affecting_sensitivity",
        "overall",
    ):
        payload = verdicts.get(verdict_name)
        lines.append("")
        lines.append(f"### {verdict_name}")
        if not isinstance(payload, dict):
            lines.append(f"- status: `{UNRESOLVED_TOKEN}` (field: verdicts.{verdict_name}.status)")
            lines.append(f"- reasons: `{UNRESOLVED_TOKEN}` (field: verdicts.{verdict_name}.reasons)")
            lines.append(
                f"- evidence_field_paths: `{UNRESOLVED_TOKEN}` "
                f"(field: verdicts.{verdict_name}.evidence_field_paths)"
            )
            continue
        lines.append(
            "- status: "
            f"`{_fmt_scalar(payload.get('status', UNRESOLVED_TOKEN))}` "
            f"(field: verdicts.{verdict_name}.status)"
        )
        lines.append(
            "- reasons: "
            f"{_fmt_list(payload.get('reasons', []))} "
            f"(field: verdicts.{verdict_name}.reasons)"
        )
        lines.append(
            "- evidence_field_paths: "
            f"{_fmt_list(payload.get('evidence_field_paths', []))} "
            f"(field: verdicts.{verdict_name}.evidence_field_paths)"
        )


def _render_boundaries(lines: list[str], artifact: dict[str, Any]) -> None:
    lines.append("")
    lines.append("## Non-v1 / unresolved boundaries")
    unresolved = _get_path(artifact, "unresolved", [])
    if isinstance(unresolved, list) and unresolved:
        lines.append("Unresolved entries:")
        for entry in unresolved:
            if not isinstance(entry, dict):
                lines.append(f"- `{_fmt_scalar(entry)}`")
                continue
            impacted = entry.get("impacted_sections", [])
            lines.append(
                "- "
                f"`{_fmt_scalar(entry.get('code', UNRESOLVED_TOKEN))}`"
                f" | severity=`{_fmt_scalar(entry.get('severity', UNRESOLVED_TOKEN))}`"
                f" | blocking_surface=`{_fmt_scalar(entry.get('blocking_surface', UNRESOLVED_TOKEN))}`"
                f" | impacted={_fmt_list(impacted)}"
                f" | requires_non_v1_extension=`{_fmt_scalar(entry.get('requires_non_v1_extension', UNRESOLVED_TOKEN))}`"
            )
    elif isinstance(unresolved, list):
        lines.append("- unresolved: [] (explicit empty list)")
    else:
        lines.append(f"- unresolved: {UNRESOLVED_TOKEN}")

    non_v1_exclusions = artifact.get("non_v1_exclusions")
    if non_v1_exclusions is None:
        lines.append("- non-v1 exclusions: UNRESOLVED_FOR_V1 (field not present in artifact)")
    else:
        lines.append(f"- non-v1 exclusions: {_fmt_list(non_v1_exclusions)}")

    lines.append(
        "- boundary note: report is rendered strictly from artifact JSON and does not extend beyond artifact scope"
    )


def render_turn_audit_markdown(
    *,
    artifact: dict[str, Any],
    artifact_path: Path,
) -> str:
    lines: list[str] = []
    _render_turn_summary(lines, artifact, artifact_path)
    _render_route_legality_scope(lines, artifact)
    _render_checkpoints(lines, artifact)
    _render_restrictions(lines, artifact)
    _render_uncertainty(lines, artifact)
    _render_final_outcome(lines, artifact)
    _render_verdicts(lines, artifact)
    _render_boundaries(lines, artifact)
    _append_missing_section_unresolved(lines, artifact)
    return "\n".join(lines).rstrip() + "\n"


def _default_markdown_path(artifact_path: Path) -> Path:
    if artifact_path.suffix.lower() == ".json":
        return artifact_path.with_suffix(".md")
    return artifact_path.parent / f"{artifact_path.name}.md"


def render_turn_audit_markdown_from_file(
    *,
    artifact_path: str | Path,
    output_markdown_path: str | Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    artifact_file = Path(artifact_path)
    artifact = _load_artifact(artifact_file)
    report = render_turn_audit_markdown(artifact=artifact, artifact_path=artifact_file)
    output_file = Path(output_markdown_path) if output_markdown_path is not None else _default_markdown_path(artifact_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding="utf-8")
    return output_file, artifact


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turn Audit Markdown Renderer v1")
    parser.add_argument("--artifact", required=True, help="path to turn audit artifact JSON v1")
    parser.add_argument("--output", help="optional output markdown path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    output_path, artifact = render_turn_audit_markdown_from_file(
        artifact_path=args.artifact,
        output_markdown_path=args.output,
    )
    overall = _fmt_scalar(_get_path(artifact, "verdicts.overall.status"))
    print(f"input_artifact={Path(args.artifact)}")
    print(f"output_markdown={output_path}")
    print(f"overall_verdict={overall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
