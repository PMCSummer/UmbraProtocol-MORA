from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMPARISON_VERSION = "turn_audit_paired_contrast_v2"
ARTIFACT_VERSION_PREFIX = "turn_audit_artifact_v1"
UNRESOLVED_TOKEN = "UNRESOLVED_FOR_V1"
REQUIRED_ARTIFACT_SECTIONS: tuple[str, ...] = (
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
STRUCTURAL_UNRESOLVED_CODES = {
    "PRE_EXECUTION_DISPATCH_REJECTION",
    "MANDATORY_CHECKPOINT_COVERAGE_INCOMPLETE",
}
PATH_AFFECTING_ALLOWED = {"CONFIRMED", "NOT_CONFIRMED", "UNRESOLVED"}


def _unresolved_entry(
    *,
    code: str,
    message: str,
    blocking_surface: str,
    severity: str,
    impacted_sections: list[str],
    requires_non_v1_extension: bool,
) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "blocking_surface": blocking_surface,
        "severity": severity,
        "impacted_sections": impacted_sections,
        "requires_non_v1_extension": requires_non_v1_extension,
    }


def _load_artifact_forgiving(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, object]]]:
    unresolved: list[dict[str, object]] = []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        unresolved.append(
            _unresolved_entry(
                code="ARTIFACT_READ_ERROR",
                message=f"failed to read or parse artifact: {exc}",
                blocking_surface=str(path),
                severity="high",
                impacted_sections=["baseline_ref", "perturbation_ref", "path_affecting_assessment"],
                requires_non_v1_extension=False,
            )
        )
        return None, unresolved

    if not isinstance(raw, dict):
        unresolved.append(
            _unresolved_entry(
                code="ARTIFACT_NOT_OBJECT",
                message="artifact JSON root is not an object",
                blocking_surface=str(path),
                severity="high",
                impacted_sections=["baseline_ref", "perturbation_ref", "path_affecting_assessment"],
                requires_non_v1_extension=False,
            )
        )
        return None, unresolved

    metadata = raw.get("artifact_metadata")
    version = metadata.get("artifact_version") if isinstance(metadata, dict) else None
    if not isinstance(version, str) or not version.startswith(ARTIFACT_VERSION_PREFIX):
        unresolved.append(
            _unresolved_entry(
                code="ARTIFACT_VERSION_INCOMPATIBLE",
                message="artifact version is not v1-compatible",
                blocking_surface=f"{path}:artifact_metadata.artifact_version",
                severity="high",
                impacted_sections=["comparison_metadata", "path_affecting_assessment"],
                requires_non_v1_extension=False,
            )
        )

    missing_sections = [name for name in REQUIRED_ARTIFACT_SECTIONS if name not in raw]
    if missing_sections:
        unresolved.append(
            _unresolved_entry(
                code="ARTIFACT_MISSING_SECTIONS",
                message="artifact is structurally incomplete for v1 comparison: " + ", ".join(missing_sections),
                blocking_surface=str(path),
                severity="high",
                impacted_sections=missing_sections,
                requires_non_v1_extension=False,
            )
        )

    return raw, unresolved


def _get(data: dict[str, Any] | None, dotted: str, default: Any = UNRESOLVED_TOKEN) -> Any:
    if not isinstance(data, dict):
        return default
    current: Any = data
    for token in dotted.split("."):
        if not isinstance(current, dict) or token not in current:
            return default
        current = current[token]
    return current


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _changed(path: str, baseline: dict[str, Any] | None, perturbation: dict[str, Any] | None) -> dict[str, Any]:
    b = _get(baseline, path)
    p = _get(perturbation, path)
    return {
        "field_path": path,
        "baseline": b,
        "perturbation": p,
        "changed": _canonical(b) != _canonical(p),
    }


def _list_changed(path: str, baseline: dict[str, Any] | None, perturbation: dict[str, Any] | None) -> dict[str, Any]:
    b = _get(baseline, path, [])
    p = _get(perturbation, path, [])
    if not isinstance(b, list):
        b = [b]
    if not isinstance(p, list):
        p = [p]
    return {
        "field_path": path,
        "baseline": b,
        "perturbation": p,
        "changed": _canonical(b) != _canonical(p),
    }


def _compare_context_flags(
    baseline: dict[str, Any] | None,
    perturbation: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    b_ctx = _get(baseline, "input_summary.context_flags", {})
    p_ctx = _get(perturbation, "input_summary.context_flags", {})
    if not isinstance(b_ctx, dict):
        b_ctx = {}
    if not isinstance(p_ctx, dict):
        p_ctx = {}
    changed: list[dict[str, Any]] = []
    for key in sorted(set(b_ctx) | set(p_ctx)):
        b = b_ctx.get(key, UNRESOLVED_TOKEN)
        p = p_ctx.get(key, UNRESOLVED_TOKEN)
        if _canonical(b) != _canonical(p):
            changed.append(
                {
                    "field_path": f"input_summary.context_flags.{key}",
                    "baseline": b,
                    "perturbation": p,
                    "changed": True,
                }
            )
    return changed


def _compare_checkpoint_object(
    checkpoint_id: str,
    path: str,
    baseline: dict[str, Any] | None,
    perturbation: dict[str, Any] | None,
) -> dict[str, Any]:
    b = _get(baseline, path)
    p = _get(perturbation, path)
    b_status = b.get("status", UNRESOLVED_TOKEN) if isinstance(b, dict) else b
    p_status = p.get("status", UNRESOLVED_TOKEN) if isinstance(p, dict) else p
    b_action = b.get("applied_action", UNRESOLVED_TOKEN) if isinstance(b, dict) else UNRESOLVED_TOKEN
    p_action = p.get("applied_action", UNRESOLVED_TOKEN) if isinstance(p, dict) else UNRESOLVED_TOKEN
    changed = (_canonical(b_status) != _canonical(p_status)) or (_canonical(b_action) != _canonical(p_action))
    return {
        "checkpoint_id": checkpoint_id,
        "baseline_status": b_status,
        "perturbation_status": p_status,
        "baseline_applied_action": b_action,
        "perturbation_applied_action": p_action,
        "changed": changed,
    }


def _compare_marker_group(
    group_name: str,
    baseline: dict[str, Any] | None,
    perturbation: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    b = _get(baseline, f"uncertainty_and_fallbacks.{group_name}", {})
    p = _get(perturbation, f"uncertainty_and_fallbacks.{group_name}", {})
    if not isinstance(b, dict):
        b = {}
    if not isinstance(p, dict):
        p = {}
    diffs: list[dict[str, Any]] = []
    for key in sorted(set(b) | set(p)):
        bv = b.get(key, UNRESOLVED_TOKEN)
        pv = p.get(key, UNRESOLVED_TOKEN)
        if _canonical(bv) != _canonical(pv):
            diffs.append(
                {
                    "field_path": f"uncertainty_and_fallbacks.{group_name}.{key}",
                    "baseline": bv,
                    "perturbation": pv,
                    "changed": True,
                }
            )
    return diffs


def _compare_phase_map(
    field_path: str,
    baseline: dict[str, Any] | None,
    perturbation: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    b = _get(baseline, field_path, {})
    p = _get(perturbation, field_path, {})
    if not isinstance(b, dict):
        b = {}
    if not isinstance(p, dict):
        p = {}
    out: list[dict[str, Any]] = []
    for phase in sorted(set(b) | set(p)):
        bv = b.get(phase, UNRESOLVED_TOKEN)
        pv = p.get(phase, UNRESOLVED_TOKEN)
        if _canonical(bv) != _canonical(pv):
            out.append(
                {
                    "field_path": f"{field_path}.{phase}",
                    "baseline": bv,
                    "perturbation": pv,
                    "changed": True,
                }
            )
    return out


def _artifact_is_structurally_incomplete(artifact: dict[str, Any] | None) -> bool:
    if artifact is None:
        return True
    if any(section not in artifact for section in REQUIRED_ARTIFACT_SECTIONS):
        return True
    accepted = _get(artifact, "route_and_scope.accepted")
    final_outcome = _get(artifact, "final_outcome.final_execution_outcome")
    if accepted is False:
        return True
    if final_outcome == UNRESOLVED_TOKEN:
        return True
    unresolved_entries = _get(artifact, "unresolved", [])
    if isinstance(unresolved_entries, list):
        for entry in unresolved_entries:
            if isinstance(entry, dict) and entry.get("code") in STRUCTURAL_UNRESOLVED_CODES:
                return True
    return False


def _build_pair_slug(baseline_path: Path, perturbation_path: Path) -> str:
    b = baseline_path.stem
    p = perturbation_path.stem
    return f"{b}__vs__{p}".replace(" ", "_")


def build_comparison_artifact(
    *,
    baseline_path: str | Path,
    perturbation_path: str | Path,
) -> dict[str, Any]:
    b_path = Path(baseline_path)
    p_path = Path(perturbation_path)
    baseline, b_unresolved = _load_artifact_forgiving(b_path)
    perturbation, p_unresolved = _load_artifact_forgiving(p_path)
    unresolved: list[dict[str, object]] = [*b_unresolved, *p_unresolved]

    baseline_ref = {
        "artifact_path": str(b_path),
        "artifact_version": _get(baseline, "artifact_metadata.artifact_version"),
        "case_id": _get(baseline, "input_summary.tick_input.case_id"),
        "load_status": "loaded" if baseline is not None else "failed",
    }
    perturbation_ref = {
        "artifact_path": str(p_path),
        "artifact_version": _get(perturbation, "artifact_metadata.artifact_version"),
        "case_id": _get(perturbation, "input_summary.tick_input.case_id"),
        "load_status": "loaded" if perturbation is not None else "failed",
    }

    input_differences = {
        "changed_fields": [
            _changed("input_summary.tick_input.case_id", baseline, perturbation),
            _changed("input_summary.tick_input.energy", baseline, perturbation),
            _changed("input_summary.tick_input.cognitive", baseline, perturbation),
            _changed("input_summary.tick_input.safety", baseline, perturbation),
            _changed("input_summary.tick_input.unresolved_preference", baseline, perturbation),
            _changed("input_summary.route_class_requested", baseline, perturbation),
        ],
        "context_flag_differences": _compare_context_flags(baseline, perturbation),
    }

    route_and_scope_differences = {
        "changed_fields": [
            _changed("route_and_scope.accepted", baseline, perturbation),
            _changed("route_and_scope.lawful_production_route", baseline, perturbation),
            _changed("route_and_scope.route_class", baseline, perturbation),
            _changed("route_and_scope.route_binding_consequence", baseline, perturbation),
            _list_changed("route_and_scope.decision_restrictions", baseline, perturbation),
            _list_changed("route_and_scope.runtime_order", baseline, perturbation),
        ]
    }

    explicit_checkpoint_diffs = [
        _compare_checkpoint_object(
            "rt01.epistemic_admission_checkpoint",
            "checkpoints.epistemic_admission_checkpoint",
            baseline,
            perturbation,
        ),
        _compare_checkpoint_object(
            "rt01.shared_runtime_domain_checkpoint",
            "checkpoints.shared_runtime_domain_checkpoint",
            baseline,
            perturbation,
        ),
        _compare_checkpoint_object(
            "rt01.downstream_obedience_checkpoint",
            "checkpoints.downstream_obedience_checkpoint",
            baseline,
            perturbation,
        ),
        _compare_checkpoint_object(
            "rt01.outcome_resolution_checkpoint",
            "checkpoints.outcome_resolution_checkpoint",
            baseline,
            perturbation,
        ),
    ]
    checkpoint_differences = {
        "changed_fields": [
            _changed("checkpoints.checkpoint_coverage_complete", baseline, perturbation),
            _list_changed("checkpoints.missing_mandatory_checkpoint_ids", baseline, perturbation),
            _list_changed("checkpoints.blocked_checkpoint_ids", baseline, perturbation),
            _list_changed("checkpoints.enforced_detour_checkpoint_ids", baseline, perturbation),
        ],
        "explicit_checkpoint_differences": explicit_checkpoint_diffs,
    }

    restriction_differences = {
        "changed_fields": [
            _list_changed(
                "restrictions_and_forbidden_shortcuts.dispatch_restrictions",
                baseline,
                perturbation,
            ),
            _list_changed(
                "restrictions_and_forbidden_shortcuts.downstream_gate_restrictions",
                baseline,
                perturbation,
            ),
            _list_changed(
                "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions",
                baseline,
                perturbation,
            ),
        ],
        "phase_restriction_differences": _compare_phase_map(
            "restrictions_and_forbidden_shortcuts.phase_restrictions",
            baseline,
            perturbation,
        ),
        "phase_forbidden_shortcut_differences": _compare_phase_map(
            "restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts",
            baseline,
            perturbation,
        ),
    }

    epistemic_differences = {
        "changed_fields": [
            _changed("phase_surfaces.epistemics.epistemic_status", baseline, perturbation),
            _changed("phase_surfaces.epistemics.epistemic_should_abstain", baseline, perturbation),
            _changed("phase_surfaces.epistemics.epistemic_claim_strength", baseline, perturbation),
            _list_changed(
                "phase_surfaces.epistemics.epistemic_allowance_restrictions",
                baseline,
                perturbation,
            ),
            _changed(
                "checkpoints.epistemic_admission_checkpoint.status",
                baseline,
                perturbation,
            ),
            _changed(
                "checkpoints.epistemic_admission_checkpoint.applied_action",
                baseline,
                perturbation,
            ),
        ],
    }

    regulation_differences = {
        "changed_fields": [
            _changed("phase_surfaces.regulation.regulation_override_scope", baseline, perturbation),
            _changed(
                "phase_surfaces.regulation.regulation_no_strong_override_claim",
                baseline,
                perturbation,
            ),
            _changed("phase_surfaces.regulation.regulation_gate_accepted", baseline, perturbation),
            _changed("phase_surfaces.regulation.regulation_pressure_level", baseline, perturbation),
            _changed("phase_surfaces.regulation.regulation_escalation_stage", baseline, perturbation),
            _changed(
                "checkpoints.shared_runtime_domain_checkpoint.status",
                baseline,
                perturbation,
            ),
            _changed(
                "checkpoints.shared_runtime_domain_checkpoint.applied_action",
                baseline,
                perturbation,
            ),
            _list_changed(
                "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions",
                baseline,
                perturbation,
            ),
        ],
    }

    uncertainty_differences = {
        "changed_fields": [
            _changed("uncertainty_and_fallbacks.abstain", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.abstain_reason", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.downstream_obedience_status", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.downstream_obedience_fallback", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.epistemic_should_abstain", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.epistemic_claim_strength", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.epistemic_unknown_reason", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.epistemic_conflict_reason", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.epistemic_abstain_reason", baseline, perturbation),
            _changed(
                "uncertainty_and_fallbacks.regulation_no_strong_override_claim",
                baseline,
                perturbation,
            ),
            _changed("uncertainty_and_fallbacks.regulation_gate_accepted", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.regulation_pressure_level", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.regulation_escalation_stage", baseline, perturbation),
            _changed("uncertainty_and_fallbacks.regulation_override_scope", baseline, perturbation),
        ],
        "uncertainty_marker_differences": _compare_marker_group(
            "uncertainty_markers",
            baseline,
            perturbation,
        ),
        "no_safe_marker_differences": _compare_marker_group(
            "no_safe_markers",
            baseline,
            perturbation,
        ),
        "degraded_marker_differences": _compare_marker_group(
            "degraded_markers",
            baseline,
            perturbation,
        ),
    }

    outcome_differences = {
        "changed_fields": [
            _changed("final_outcome.final_execution_outcome", baseline, perturbation),
            _changed("final_outcome.execution_stance", baseline, perturbation),
            _changed("final_outcome.active_execution_mode", baseline, perturbation),
            _changed("final_outcome.repair_needed", baseline, perturbation),
            _changed("final_outcome.revalidation_needed", baseline, perturbation),
            _changed("final_outcome.halt_reason", baseline, perturbation),
            _changed("final_outcome.persist_transition_accepted", baseline, perturbation),
        ]
    }

    verdict_differences = {
        "changed_fields": [
            _changed("verdicts.mechanistic_integrity.status", baseline, perturbation),
            _changed("verdicts.claim_honesty.status", baseline, perturbation),
            _changed("verdicts.path_affecting_sensitivity.status", baseline, perturbation),
            _changed("verdicts.overall.status", baseline, perturbation),
        ]
    }

    signal_outcome_changed = _get(baseline, "final_outcome.final_execution_outcome") != _get(
        perturbation, "final_outcome.final_execution_outcome"
    )
    signal_stance_changed = _get(baseline, "final_outcome.execution_stance") != _get(
        perturbation, "final_outcome.execution_stance"
    )
    b_mode = _get(baseline, "final_outcome.active_execution_mode")
    p_mode = _get(perturbation, "final_outcome.active_execution_mode")
    signal_mode_available = b_mode != UNRESOLVED_TOKEN and p_mode != UNRESOLVED_TOKEN
    signal_mode_changed = signal_mode_available and (b_mode != p_mode)
    signal_route_binding_changed = _get(
        baseline, "route_and_scope.route_binding_consequence"
    ) != _get(perturbation, "route_and_scope.route_binding_consequence")
    signal_epistemic_status_changed = _changed(
        "phase_surfaces.epistemics.epistemic_status", baseline, perturbation
    )["changed"]
    signal_epistemic_should_abstain_changed = _changed(
        "phase_surfaces.epistemics.epistemic_should_abstain", baseline, perturbation
    )["changed"]
    signal_epistemic_claim_strength_changed = _changed(
        "phase_surfaces.epistemics.epistemic_claim_strength", baseline, perturbation
    )["changed"]
    signal_epistemic_allowance_restrictions_changed = _list_changed(
        "phase_surfaces.epistemics.epistemic_allowance_restrictions", baseline, perturbation
    )["changed"]
    signal_epistemic_checkpoint_changed = (
        _changed("checkpoints.epistemic_admission_checkpoint.status", baseline, perturbation)["changed"]
        or _changed(
            "checkpoints.epistemic_admission_checkpoint.applied_action",
            baseline,
            perturbation,
        )["changed"]
    )
    signal_regulation_override_scope_changed = _changed(
        "phase_surfaces.regulation.regulation_override_scope", baseline, perturbation
    )["changed"]
    signal_regulation_no_strong_override_changed = _changed(
        "phase_surfaces.regulation.regulation_no_strong_override_claim", baseline, perturbation
    )["changed"]
    signal_regulation_gate_changed = _changed(
        "phase_surfaces.regulation.regulation_gate_accepted", baseline, perturbation
    )["changed"]
    signal_regulation_pressure_changed = _changed(
        "phase_surfaces.regulation.regulation_pressure_level", baseline, perturbation
    )["changed"]
    signal_regulation_escalation_changed = _changed(
        "phase_surfaces.regulation.regulation_escalation_stage", baseline, perturbation
    )["changed"]
    signal_shared_runtime_checkpoint_changed = (
        _changed("checkpoints.shared_runtime_domain_checkpoint.status", baseline, perturbation)["changed"]
        or _changed(
            "checkpoints.shared_runtime_domain_checkpoint.applied_action",
            baseline,
            perturbation,
        )["changed"]
    )
    signal_regulation_gate_restrictions_changed = _list_changed(
        "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions",
        baseline,
        perturbation,
    )["changed"]
    signal_checkpoint_consequence_changed = (
        _list_changed("checkpoints.blocked_checkpoint_ids", baseline, perturbation)["changed"]
        or _list_changed("checkpoints.enforced_detour_checkpoint_ids", baseline, perturbation)["changed"]
        or signal_epistemic_checkpoint_changed
        or signal_shared_runtime_checkpoint_changed
        or any(row["changed"] for row in explicit_checkpoint_diffs)
    )
    signal_restriction_envelope_changed = (
        restriction_differences["changed_fields"][0]["changed"]
        or restriction_differences["changed_fields"][1]["changed"]
        or restriction_differences["changed_fields"][2]["changed"]
        or bool(restriction_differences["phase_restriction_differences"])
        or signal_epistemic_allowance_restrictions_changed
        or signal_regulation_gate_restrictions_changed
    )
    epistemic_surface_signal_changed = any(
        (
            signal_epistemic_status_changed,
            signal_epistemic_should_abstain_changed,
            signal_epistemic_claim_strength_changed,
            signal_epistemic_allowance_restrictions_changed,
        )
    )
    epistemic_signal_changed = epistemic_surface_signal_changed or signal_epistemic_checkpoint_changed
    regulation_surface_signal_changed = any(
        (
            signal_regulation_override_scope_changed,
            signal_regulation_no_strong_override_changed,
            signal_regulation_gate_changed,
            signal_regulation_pressure_changed,
            signal_regulation_escalation_changed,
        )
    )
    regulation_signal_changed = any(
        (
            regulation_surface_signal_changed,
            signal_shared_runtime_checkpoint_changed,
            signal_regulation_gate_restrictions_changed,
        )
    )
    epistemic_or_regulation_changed = epistemic_signal_changed or regulation_signal_changed

    epistemic_load_bearing_consequence_changed = any(
        (
            signal_epistemic_checkpoint_changed,
            signal_checkpoint_consequence_changed,
            signal_restriction_envelope_changed,
            signal_mode_changed,
            signal_outcome_changed,
            signal_stance_changed,
        )
    )
    regulation_load_bearing_consequence_changed = any(
        (
            signal_shared_runtime_checkpoint_changed,
            signal_regulation_gate_restrictions_changed,
            signal_checkpoint_consequence_changed,
            signal_restriction_envelope_changed,
            signal_mode_changed,
            signal_outcome_changed,
            signal_stance_changed,
        )
    )
    epistemic_path_affecting_confirmed = (
        epistemic_signal_changed and epistemic_load_bearing_consequence_changed
    )
    regulation_path_affecting_confirmed = (
        regulation_signal_changed and regulation_load_bearing_consequence_changed
    )

    primary_causal_signals: list[str] = []
    if signal_epistemic_checkpoint_changed:
        primary_causal_signals.append("checkpoints.epistemic_admission_checkpoint")
    if signal_shared_runtime_checkpoint_changed:
        primary_causal_signals.append("checkpoints.shared_runtime_domain_checkpoint")
    if signal_regulation_gate_restrictions_changed:
        primary_causal_signals.append("restrictions_and_forbidden_shortcuts.regulation_gate_restrictions")
    if signal_restriction_envelope_changed and (
        "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions"
        not in primary_causal_signals
    ):
        primary_causal_signals.append("restrictions_and_forbidden_shortcuts")
    if signal_mode_changed:
        primary_causal_signals.append("final_outcome.active_execution_mode")
    if signal_outcome_changed:
        primary_causal_signals.append("final_outcome.final_execution_outcome")
    if signal_stance_changed:
        primary_causal_signals.append("final_outcome.execution_stance")
    if signal_route_binding_changed:
        primary_causal_signals.append("route_and_scope.route_binding_consequence")

    non_load_bearing_differences: list[str] = []
    if epistemic_signal_changed and not epistemic_load_bearing_consequence_changed:
        non_load_bearing_differences.append("epistemic_surface_only")
    if regulation_signal_changed and not regulation_load_bearing_consequence_changed:
        non_load_bearing_differences.append("regulation_surface_only")

    if not signal_mode_available:
        unresolved.append(
            _unresolved_entry(
                code="ACTIVE_EXECUTION_MODE_NOT_EXPOSED",
                message="active_execution_mode is not exposed in one or both compared artifacts",
                blocking_surface="final_outcome.active_execution_mode",
                severity="low",
                impacted_sections=["outcome_differences", "path_affecting_assessment"],
                requires_non_v1_extension=False,
            )
        )

    baseline_structural = _artifact_is_structurally_incomplete(baseline)
    perturbation_structural = _artifact_is_structurally_incomplete(perturbation)
    structurally_incomplete = baseline_structural or perturbation_structural
    if baseline_structural:
        unresolved.append(
            _unresolved_entry(
                code="BASELINE_ARTIFACT_STRUCTURALLY_INCOMPLETE",
                message="baseline artifact does not expose complete load-bearing path evidence for paired assessment",
                blocking_surface="baseline_ref.artifact_path",
                severity="high",
                impacted_sections=["path_affecting_assessment", "baseline_ref"],
                requires_non_v1_extension=False,
            )
        )
    if perturbation_structural:
        unresolved.append(
            _unresolved_entry(
                code="PERTURBATION_ARTIFACT_STRUCTURALLY_INCOMPLETE",
                message="perturbation artifact does not expose complete load-bearing path evidence for paired assessment",
                blocking_surface="perturbation_ref.artifact_path",
                severity="high",
                impacted_sections=["path_affecting_assessment", "perturbation_ref"],
                requires_non_v1_extension=False,
            )
        )
    path_affecting_signals = {
        "final_execution_outcome_changed": signal_outcome_changed,
        "execution_stance_changed": signal_stance_changed,
        "active_execution_mode_changed": signal_mode_changed,
        "checkpoint_consequence_changed": signal_checkpoint_consequence_changed,
        "route_binding_consequence_changed": signal_route_binding_changed,
        "restriction_envelope_changed": signal_restriction_envelope_changed,
        "epistemic_status_changed": signal_epistemic_status_changed,
        "epistemic_should_abstain_changed": signal_epistemic_should_abstain_changed,
        "epistemic_claim_strength_changed": signal_epistemic_claim_strength_changed,
        "epistemic_allowance_restrictions_changed": signal_epistemic_allowance_restrictions_changed,
        "epistemic_admission_checkpoint_changed": signal_epistemic_checkpoint_changed,
        "epistemic_signal_changed": epistemic_signal_changed,
        "epistemic_load_bearing_consequence_changed": epistemic_load_bearing_consequence_changed,
        "epistemic_path_affecting_confirmed": epistemic_path_affecting_confirmed,
        "regulation_override_scope_changed": signal_regulation_override_scope_changed,
        "regulation_no_strong_override_claim_changed": signal_regulation_no_strong_override_changed,
        "regulation_gate_accepted_changed": signal_regulation_gate_changed,
        "regulation_pressure_level_changed": signal_regulation_pressure_changed,
        "regulation_escalation_stage_changed": signal_regulation_escalation_changed,
        "shared_runtime_domain_checkpoint_changed": signal_shared_runtime_checkpoint_changed,
        "regulation_gate_restrictions_changed": signal_regulation_gate_restrictions_changed,
        "regulation_signal_changed": regulation_signal_changed,
        "regulation_load_bearing_consequence_changed": regulation_load_bearing_consequence_changed,
        "regulation_path_affecting_confirmed": regulation_path_affecting_confirmed,
    }
    if structurally_incomplete:
        status = "UNRESOLVED"
        reasons = [
            "baseline or perturbation artifact is structurally incomplete; path-affecting confirmation is bounded",
        ]
    elif epistemic_path_affecting_confirmed or regulation_path_affecting_confirmed:
        status = "CONFIRMED"
        reasons = [
            "epistemic/regulation signals changed with explicit checkpoint/restriction/mode/outcome consequence",
        ]
    elif epistemic_or_regulation_changed:
        status = "NOT_CONFIRMED"
        reasons = [
            "epistemic/regulation surface differences are present but no load-bearing contour consequence is evidenced",
        ]
    else:
        status = "NOT_CONFIRMED"
        reasons = [
            "input or narrative differences did not produce load-bearing path change",
        ]
    if status not in PATH_AFFECTING_ALLOWED:
        status = "UNRESOLVED"

    comparison = {
        "comparison_metadata": {
            "comparison_version": COMPARISON_VERSION,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "comparison_mode": "paired_contrast_v2",
        },
        "baseline_ref": baseline_ref,
        "perturbation_ref": perturbation_ref,
        "input_differences": input_differences,
        "route_and_scope_differences": route_and_scope_differences,
        "checkpoint_differences": checkpoint_differences,
        "epistemic_differences": epistemic_differences,
        "regulation_differences": regulation_differences,
        "restriction_differences": restriction_differences,
        "uncertainty_differences": uncertainty_differences,
        "outcome_differences": outcome_differences,
        "verdict_differences": verdict_differences,
        "path_affecting_assessment": {
            "status": status,
            "reasons": reasons,
            "signals": path_affecting_signals,
            "primary_causal_signals": primary_causal_signals,
            "non_load_bearing_differences": non_load_bearing_differences,
            "structurally_incomplete": structurally_incomplete,
        },
        "unresolved": unresolved,
    }
    return comparison


def _fmt_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _fmt_list(value: Any) -> str:
    if isinstance(value, list):
        if not value:
            return "[]"
        return ", ".join(str(item) for item in value)
    return _fmt_scalar(value)


def render_comparison_markdown(comparison: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Pair summary")
    lines.append(
        "- baseline artifact: "
        f"`{_fmt_scalar(_get(comparison, 'baseline_ref.artifact_path'))}` "
        "(field: baseline_ref.artifact_path)"
    )
    lines.append(
        "- perturbation artifact: "
        f"`{_fmt_scalar(_get(comparison, 'perturbation_ref.artifact_path'))}` "
        "(field: perturbation_ref.artifact_path)"
    )
    lines.append(
        "- comparison version: "
        f"`{_fmt_scalar(_get(comparison, 'comparison_metadata.comparison_version'))}` "
        "(field: comparison_metadata.comparison_version)"
    )
    lines.append(
        "- path-affecting assessment: "
        f"`{_fmt_scalar(_get(comparison, 'path_affecting_assessment.status'))}` "
        "(field: path_affecting_assessment.status)"
    )

    sections = (
        ("## Input differences", "input_differences.changed_fields"),
        ("## Route / legality / scope differences", "route_and_scope_differences.changed_fields"),
        ("## Critical checkpoint differences", "checkpoint_differences.changed_fields"),
        ("## Epistemic differences", "epistemic_differences.changed_fields"),
        ("## Regulation differences", "regulation_differences.changed_fields"),
        ("## Restrictions / forbidden shortcut differences", "restriction_differences.changed_fields"),
        ("## Uncertainty / degraded / unresolved differences", "uncertainty_differences.changed_fields"),
        ("## Final outcome differences", "outcome_differences.changed_fields"),
        ("## Verdict differences", "verdict_differences.changed_fields"),
    )
    for title, path in sections:
        lines.append("")
        lines.append(title)
        rows = _get(comparison, path, [])
        if not isinstance(rows, list):
            lines.append(f"- {UNRESOLVED_TOKEN} (field: {path})")
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- "
                f"`{_fmt_scalar(row.get('field_path', UNRESOLVED_TOKEN))}`"
                f": baseline=`{_fmt_scalar(row.get('baseline', UNRESOLVED_TOKEN))}`"
                f", perturbation=`{_fmt_scalar(row.get('perturbation', UNRESOLVED_TOKEN))}`"
                f", changed=`{_fmt_scalar(row.get('changed', UNRESOLVED_TOKEN))}`"
            )

        if path == "input_differences.changed_fields":
            context_rows = _get(comparison, "input_differences.context_flag_differences", [])
            lines.append("")
            lines.append("Context flag differences:")
            if isinstance(context_rows, list) and context_rows:
                for row in context_rows:
                    lines.append(
                        "- "
                        f"`{_fmt_scalar(row.get('field_path', UNRESOLVED_TOKEN))}`"
                        f": baseline=`{_fmt_scalar(row.get('baseline', UNRESOLVED_TOKEN))}`"
                        f", perturbation=`{_fmt_scalar(row.get('perturbation', UNRESOLVED_TOKEN))}`"
                    )
            else:
                lines.append("- none")

        if path == "checkpoint_differences.changed_fields":
            explicit_rows = _get(comparison, "checkpoint_differences.explicit_checkpoint_differences", [])
            lines.append("")
            lines.append("Explicit checkpoints:")
            if isinstance(explicit_rows, list):
                for row in explicit_rows:
                    lines.append(
                        "- "
                        f"`{_fmt_scalar(row.get('checkpoint_id', UNRESOLVED_TOKEN))}`"
                        f": baseline_status=`{_fmt_scalar(row.get('baseline_status', UNRESOLVED_TOKEN))}`"
                        f", perturbation_status=`{_fmt_scalar(row.get('perturbation_status', UNRESOLVED_TOKEN))}`"
                        f", baseline_action=`{_fmt_scalar(row.get('baseline_applied_action', UNRESOLVED_TOKEN))}`"
                        f", perturbation_action=`{_fmt_scalar(row.get('perturbation_applied_action', UNRESOLVED_TOKEN))}`"
                        f", changed=`{_fmt_scalar(row.get('changed', UNRESOLVED_TOKEN))}`"
                    )

        if path == "restriction_differences.changed_fields":
            phase_rows = _get(comparison, "restriction_differences.phase_restriction_differences", [])
            shortcut_rows = _get(comparison, "restriction_differences.phase_forbidden_shortcut_differences", [])
            lines.append("")
            lines.append("Per-phase restriction differences:")
            if isinstance(phase_rows, list) and phase_rows:
                for row in phase_rows:
                    lines.append(
                        "- "
                        f"`{_fmt_scalar(row.get('field_path', UNRESOLVED_TOKEN))}`"
                        f": baseline=`{_fmt_scalar(row.get('baseline', UNRESOLVED_TOKEN))}`"
                        f", perturbation=`{_fmt_scalar(row.get('perturbation', UNRESOLVED_TOKEN))}`"
                    )
            else:
                lines.append("- none")
            lines.append("Per-phase forbidden shortcut differences:")
            if isinstance(shortcut_rows, list) and shortcut_rows:
                for row in shortcut_rows:
                    lines.append(
                        "- "
                        f"`{_fmt_scalar(row.get('field_path', UNRESOLVED_TOKEN))}`"
                        f": baseline=`{_fmt_scalar(row.get('baseline', UNRESOLVED_TOKEN))}`"
                        f", perturbation=`{_fmt_scalar(row.get('perturbation', UNRESOLVED_TOKEN))}`"
                    )
            else:
                lines.append("- none")

        if path == "uncertainty_differences.changed_fields":
            for sub_path, header in (
                ("uncertainty_differences.uncertainty_marker_differences", "Uncertainty marker differences"),
                ("uncertainty_differences.no_safe_marker_differences", "No-safe marker differences"),
                ("uncertainty_differences.degraded_marker_differences", "Degraded marker differences"),
            ):
                rows2 = _get(comparison, sub_path, [])
                lines.append(header + ":")
                if isinstance(rows2, list) and rows2:
                    for row in rows2:
                        lines.append(
                            "- "
                            f"`{_fmt_scalar(row.get('field_path', UNRESOLVED_TOKEN))}`"
                            f": baseline=`{_fmt_scalar(row.get('baseline', UNRESOLVED_TOKEN))}`"
                            f", perturbation=`{_fmt_scalar(row.get('perturbation', UNRESOLVED_TOKEN))}`"
                        )
                else:
                    lines.append("- none")

    lines.append("")
    lines.append("## Path-affecting assessment")
    lines.append(
        "- status: "
        f"`{_fmt_scalar(_get(comparison, 'path_affecting_assessment.status'))}` "
        "(field: path_affecting_assessment.status)"
    )
    lines.append(
        "- reasons: "
        f"{_fmt_list(_get(comparison, 'path_affecting_assessment.reasons', []))} "
        "(field: path_affecting_assessment.reasons)"
    )
    lines.append(
        "- primary causal signals: "
        f"{_fmt_list(_get(comparison, 'path_affecting_assessment.primary_causal_signals', []))} "
        "(field: path_affecting_assessment.primary_causal_signals)"
    )
    lines.append(
        "- non-load-bearing differences: "
        f"{_fmt_list(_get(comparison, 'path_affecting_assessment.non_load_bearing_differences', []))} "
        "(field: path_affecting_assessment.non_load_bearing_differences)"
    )
    signals = _get(comparison, "path_affecting_assessment.signals", {})
    lines.append("Load-bearing signals:")
    if isinstance(signals, dict):
        for key in sorted(signals):
            lines.append(f"- `{key}`: `{_fmt_scalar(signals[key])}` (field: path_affecting_assessment.signals.{key})")
    else:
        lines.append(f"- {UNRESOLVED_TOKEN}")

    lines.append("")
    lines.append("## Unresolved boundaries")
    unresolved = _get(comparison, "unresolved", [])
    if isinstance(unresolved, list) and unresolved:
        for entry in unresolved:
            if not isinstance(entry, dict):
                lines.append(f"- `{_fmt_scalar(entry)}`")
                continue
            lines.append(
                "- "
                f"`{_fmt_scalar(entry.get('code', UNRESOLVED_TOKEN))}`"
                f": {_fmt_scalar(entry.get('message', UNRESOLVED_TOKEN))}"
                f" | blocking_surface=`{_fmt_scalar(entry.get('blocking_surface', UNRESOLVED_TOKEN))}`"
                f" | severity=`{_fmt_scalar(entry.get('severity', UNRESOLVED_TOKEN))}`"
            )
    elif isinstance(unresolved, list):
        lines.append("- []")
    else:
        lines.append(f"- {UNRESOLVED_TOKEN}")

    return "\n".join(lines).rstrip() + "\n"


def write_comparison_outputs(
    *,
    comparison: dict[str, Any],
    baseline_path: Path,
    perturbation_path: Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    slug = _build_pair_slug(baseline_path, perturbation_path)
    json_path = out / f"{slug}.comparison.json"
    md_path = out / f"{slug}.comparison.md"
    json_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    md_path.write_text(render_comparison_markdown(comparison), encoding="utf-8")
    return json_path, md_path


def compare_artifacts(
    *,
    baseline_path: str | Path,
    perturbation_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    b = Path(baseline_path)
    p = Path(perturbation_path)
    comparison = build_comparison_artifact(
        baseline_path=b,
        perturbation_path=p,
    )
    json_path, md_path = write_comparison_outputs(
        comparison=comparison,
        baseline_path=b,
        perturbation_path=p,
        output_dir=output_dir,
    )
    return {
        "comparison_json_path": str(json_path),
        "comparison_markdown_path": str(md_path),
        "comparison": comparison,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turn Audit Paired Contrast Mode v2")
    parser.add_argument("--baseline", required=True, help="baseline artifact json path")
    parser.add_argument("--perturbation", required=True, help="perturbation artifact json path")
    parser.add_argument("--output-dir", required=True, help="output directory for comparison files")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = compare_artifacts(
        baseline_path=args.baseline,
        perturbation_path=args.perturbation,
        output_dir=args.output_dir,
    )
    status = _get(result["comparison"], "path_affecting_assessment.status")
    print(f"comparison_json={result['comparison_json_path']}")
    print(f"comparison_markdown={result['comparison_markdown_path']}")
    print(f"path_affecting_assessment={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
