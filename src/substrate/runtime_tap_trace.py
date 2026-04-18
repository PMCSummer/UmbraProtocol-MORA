from __future__ import annotations

import json
from contextvars import ContextVar, Token
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

TRACE_STEP_ALLOWED = {"enter", "decision", "blocked", "exit"}

MODULE_ALLOWED_FIELDS: dict[str, tuple[str, ...]] = {
    "world_adapter": (
        "adapter_presence",
        "adapter_available",
        "adapter_degraded",
        "world_link_status",
        "effect_status",
        "world_grounded_transition_allowed",
        "effect_feedback_correlated",
    ),
    "world_entry_contract": (
        "world_presence_mode",
        "observation_basis_present",
        "action_trace_present",
        "effect_basis_present",
        "effect_feedback_correlated",
        "w01_admission_ready",
    ),
    "runtime_topology": (
        "route_class",
        "accepted",
        "route_binding_consequence",
        "runtime_entry",
        "reason",
    ),
    "epistemics": (
        "epistemic_status",
        "claim_strength",
        "should_abstain",
        "can_treat_as_observation",
    ),
    "regulation": (
        "pressure_level",
        "escalation_stage",
        "override_scope",
        "gate_accepted",
        "dominant_axis",
        "claim_strength",
    ),
    "c01_stream_kernel": (
        "stream_state",
        "kernel_ready",
        "stream_load",
        "kernel_blocked",
        "active_stream_count",
    ),
    "c02_tension_scheduler": (
        "tension_level",
        "scheduler_state",
        "pressure_binding",
        "tension_blocked",
        "schedule_ready",
    ),
    "c03_stream_diversification": (
        "diversification_state",
        "active_branches",
        "branch_pressure",
        "diversification_blocked",
        "diversification_ready",
    ),
    "c04_mode_arbitration": (
        "selected_mode",
        "mode_source",
        "mode_conflict_present",
        "arbitration_stable",
        "handoff_ready",
    ),
    "c05_temporal_validity": (
        "validity_status",
        "legality_class",
        "revalidation_required",
        "temporal_blocked",
        "validity_ready",
    ),
    "world_seam_enforcement": (
        "world_transition_allowed",
        "seam_blocked",
        "seam_block_reason",
        "world_grounded_ready",
    ),
    "bounded_outcome_resolution": (
        "bounded_outcome_class",
        "output_allowed",
        "materialization_mode",
        "bounded_reason",
        "outcome_ready",
    ),
    "s01_efference_copy": (
        "efference_available",
        "trace_ready",
        "action_projection_present",
        "efference_blocked",
    ),
    "s02_prediction_boundary": (
        "prediction_boundary_status",
        "boundary_integrity",
        "boundary_blocked",
        "prediction_ready",
    ),
    "s03_ownership_weighted_learning": (
        "ownership_status",
        "ownership_confidence",
        "learning_weight_applied",
        "ownership_blocked",
    ),
    "s04_interoceptive_self_binding": (
        "strong_bound_count",
        "weak_bound_count",
        "contested_count",
        "provisional_count",
        "no_stable_core_claim",
        "strongest_binding_strength",
        "contamination_detected",
        "rebinding_event",
        "stale_binding_drop_count",
    ),
    "s05_multi_cause_attribution_factorization": (
        "dominant_slot_count",
        "residual_share",
        "residual_class",
        "underdetermined_split",
        "contamination_present",
        "temporal_misalignment_present",
        "reattribution_happened",
        "downstream_route_class",
        "factorization_consumer_ready",
        "learning_route_ready",
    ),
    "o01_other_entity_model": (
        "entity_count",
        "current_user_model_ready",
        "third_party_models_active",
        "stable_claim_count",
        "temporary_hypothesis_count",
        "contradiction_count",
        "knowledge_boundary_known_count",
        "projection_guard_triggered",
        "no_safe_state_claim",
        "downstream_consumer_ready",
    ),
    "o02_intersubjective_allostasis": (
        "interaction_mode",
        "predicted_other_load",
        "predicted_self_load",
        "repair_pressure",
        "other_model_reliance_status",
        "boundary_protection_status",
        "no_safe_regulation_claim",
        "other_load_underconstrained",
        "self_other_constraint_conflict",
        "downstream_consumer_ready",
    ),
    "o03_strategy_class_evaluation": (
        "strategy_class",
        "hidden_divergence_band",
        "asymmetry_exploitation_band",
        "dependency_risk_band",
        "entropy_burden_band",
        "no_safe_classification",
        "strategy_underconstrained",
        "downstream_consumer_ready",
    ),
    "p01_project_formation": (
        "active_project_count",
        "candidate_project_count",
        "suspended_project_count",
        "arbitration_count",
        "conflicting_authority",
        "blocked_pending_grounding",
        "no_safe_project_formation",
        "project_handoff_ready",
        "prompt_local_capture_risk",
        "downstream_consumer_ready",
    ),
    "o04_rupture_hostility_coercion": (
        "dynamic_type",
        "rupture_status",
        "severity_band",
        "certainty_band",
        "directionality_kind",
        "leverage_surface",
        "legitimacy_hint_status",
        "coercion_candidate_count",
        "hostility_candidate_count",
        "no_safe_dynamic_claim",
        "dependency_model_underconstrained",
        "downstream_consumer_ready",
    ),
    "r05_appraisal_sovereign_protective_regulation": (
        "protective_mode",
        "authority_level",
        "trigger_count",
        "inhibited_surface_count",
        "override_active",
        "release_pending",
        "regulation_conflict",
        "insufficient_basis_for_override",
        "downstream_consumer_ready",
        "project_override_active",
    ),
    "s_minimal_contour": (
        "minimal_self_status",
        "minimal_self_ready",
        "contour_blocked",
    ),
    "a_line_normalization": (
        "normalization_status",
        "normalized_ready",
        "normalization_blocked",
        "normalization_scope",
    ),
    "m_minimal": (
        "minimal_memory_status",
        "memory_ready",
        "memory_blocked",
    ),
    "n_minimal": (
        "minimal_narrative_status",
        "narrative_ready",
        "narrative_blocked",
    ),
    "t01_semantic_field": (
        "scene_status",
        "unresolved_slots_count",
        "pre_verbal_consumer_ready",
        "no_clean_scene_commit",
    ),
    "t02_relation_binding": (
        "scene_status",
        "no_clean_binding_commit",
        "pre_verbal_constraint_consumer_ready",
        "raw_vs_propagated_distinct",
    ),
    "t03_hypothesis_competition": (
        "leader",
        "conflict_count",
        "open_slot_count",
        "convergence_status",
        "nonconvergence_preserved",
        "no_viable_leader",
        "nonconvergence_basis",
    ),
    "t04_attention_schema": (
        "attention_owner",
        "focus_mode",
        "reportability_status",
        "focus_ownership_consumer_ready",
    ),
    "downstream_obedience": (
        "accepted",
        "usability_class",
        "top_restrictions",
        "blocked_reason",
        "restriction_count",
    ),
    "subject_tick": (
        "output_kind",
        "final_execution_outcome",
        "active_execution_mode",
        "abstain",
        "abstain_reason",
        "materialized_output",
    ),
}

_trace_output_root = Path("artifacts") / "simple_tick_trace"
_tick_orders: dict[str, int] = {}
_initialized_ticks: set[str] = set()
_active_tick_id: ContextVar[str | None] = ContextVar("runtime_tap_trace.active_tick_id", default=None)


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, Enum):
        return _to_jsonable(value.value)
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [_to_jsonable(item) for item in sorted(value, key=lambda item: str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def set_trace_output_root(path: str | Path) -> None:
    global _trace_output_root
    _trace_output_root = Path(path)


def reset_trace_state() -> None:
    _tick_orders.clear()
    _initialized_ticks.clear()
    _active_tick_id.set(None)


def derive_tick_id(case_id: str, *, prior_tick_index: int | None = None) -> str:
    tick_index = 1 if prior_tick_index is None else prior_tick_index + 1
    return f"subject-tick-{case_id}-{tick_index}"


def get_tick_trace_path(tick_id: str) -> Path:
    return _trace_output_root / f"{tick_id}.jsonl"


def _prepare_tick_trace(tick_id: str) -> Path:
    path = get_tick_trace_path(tick_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    _initialized_ticks.add(tick_id)
    _tick_orders[tick_id] = 0
    return path


def _ensure_tick_file(tick_id: str) -> Path:
    if tick_id not in _initialized_ticks:
        return _prepare_tick_trace(tick_id)
    return get_tick_trace_path(tick_id)


def start_tick_trace(*, tick_id: str, output_root: str | Path) -> Token[str | None]:
    set_trace_output_root(output_root)
    _prepare_tick_trace(tick_id)
    return _active_tick_id.set(tick_id)


def activate_tick_trace(*, tick_id: str, output_root: str | Path) -> Token[str | None]:
    return start_tick_trace(tick_id=tick_id, output_root=output_root)


def deactivate_tick_trace(token: Token[str | None]) -> None:
    _active_tick_id.reset(token)


def finish_tick_trace(*, tick_id: str) -> dict[str, Any]:
    return {
        "tick_id": tick_id,
        "trace_path": str(get_tick_trace_path(tick_id)),
        "event_count": _tick_orders.get(tick_id, 0),
    }


def trace_emit(
    tick_id: str,
    module: str,
    step: str,
    values: dict[str, Any],
    note: str | None = None,
) -> dict[str, Any]:
    if step not in TRACE_STEP_ALLOWED:
        raise ValueError(f"invalid step: {step}")
    if module not in MODULE_ALLOWED_FIELDS:
        raise ValueError(f"unknown module: {module}")
    if not isinstance(values, dict):
        raise TypeError("values must be dict")

    allowed = set(MODULE_ALLOWED_FIELDS[module])
    extra = sorted(str(field) for field in values if field not in allowed)
    if extra:
        raise ValueError(f"module {module} emitted non-allowlisted fields: {', '.join(extra)}")

    path = _ensure_tick_file(tick_id)
    order = _tick_orders[tick_id]
    event = {
        "tick_id": tick_id,
        "order": order,
        "module": module,
        "step": step,
        "values": _to_jsonable(values),
        "note": None if note is None else str(note),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True))
        handle.write("\n")
    _tick_orders[tick_id] = order + 1
    return event


def trace_emit_active(
    module: str,
    step: str,
    values: dict[str, Any],
    note: str | None = None,
) -> dict[str, Any] | None:
    tick_id = _active_tick_id.get()
    if tick_id is None:
        return None
    return trace_emit(tick_id=tick_id, module=module, step=step, values=values, note=note)
