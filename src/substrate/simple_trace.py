from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.runtime_topology.models import RuntimeDispatchResult
from substrate.runtime_topology.telemetry import runtime_dispatch_snapshot
from substrate.subject_tick import SubjectTickInput
from substrate.subject_tick.telemetry import subject_tick_result_snapshot
from substrate.t01_semantic_field.telemetry import t01_active_field_snapshot
from substrate.t02_relation_binding.telemetry import t02_constrained_scene_snapshot
from substrate.t03_hypothesis_competition.telemetry import t03_hypothesis_competition_snapshot
from substrate.t04_attention_schema.telemetry import t04_attention_schema_snapshot
from substrate.world_adapter.telemetry import world_adapter_result_snapshot
from substrate.world_entry_contract.telemetry import world_entry_contract_snapshot

TRACE_STEP_ALLOWED = {"enter", "decision", "exit", "blocked"}

MODULE_ORDER: tuple[str, ...] = (
    "world_adapter",
    "world_entry_contract",
    "runtime_topology",
    "epistemics",
    "regulation",
    "t01_semantic_field",
    "t02_relation_binding",
    "t03_hypothesis_competition",
    "t04_attention_schema",
    "downstream_obedience",
    "subject_tick",
)

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
        "forbidden_claim_classes",
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
        "classification_basis",
    ),
    "regulation": (
        "confidence",
        "dominant_axis",
        "active_axes",
        "coping_mode",
        "claim_strength",
        "partial_known_reason",
        "abstain_reason",
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
        "open_slots",
        "convergence_status",
        "nonconvergence_preserved",
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
        "blocked_reason",
        "restrictions",
    ),
    "subject_tick": (
        "final_execution_outcome",
        "active_execution_mode",
        "abstain",
        "abstain_reason",
        "materialized_output",
    ),
}

_MODULE_FIELD_PATHS: dict[str, dict[str, tuple[str, ...]]] = {
    "world_adapter": {
        "adapter_presence": ("world_adapter", "state", "adapter_presence"),
        "adapter_available": ("world_adapter", "state", "adapter_available"),
        "adapter_degraded": ("world_adapter", "state", "adapter_degraded"),
        "world_link_status": ("world_adapter", "state", "world_link_status"),
        "effect_status": ("world_adapter", "state", "effect_status"),
        "world_grounded_transition_allowed": (
            "world_adapter",
            "gate",
            "world_grounded_transition_allowed",
        ),
        "effect_feedback_correlated": (
            "world_adapter",
            "gate",
            "effect_feedback_correlated",
        ),
    },
    "world_entry_contract": {
        "world_presence_mode": ("world_entry_contract", "episode", "world_presence_mode"),
        "observation_basis_present": (
            "world_entry_contract",
            "episode",
            "observation_basis_present",
        ),
        "action_trace_present": ("world_entry_contract", "episode", "action_trace_present"),
        "effect_basis_present": ("world_entry_contract", "episode", "effect_basis_present"),
        "effect_feedback_correlated": (
            "world_entry_contract",
            "episode",
            "effect_feedback_correlated",
        ),
        "w01_admission_ready": (
            "world_entry_contract",
            "w01_admission",
            "admission_ready",
        ),
        "forbidden_claim_classes": ("world_entry_contract", "forbidden_claim_classes"),
    },
    "runtime_topology": {
        "route_class": ("runtime_topology", "decision", "route_class"),
        "accepted": ("runtime_topology", "decision", "accepted"),
        "route_binding_consequence": (
            "runtime_topology",
            "decision",
            "route_binding_consequence",
        ),
        "runtime_entry": ("runtime_topology", "bundle", "runtime_entry"),
        "reason": ("runtime_topology", "decision", "reason"),
    },
    "epistemics": {
        "epistemic_status": ("epistemics", "unit", "status"),
        "claim_strength": ("epistemics", "allowance", "claim_strength"),
        "should_abstain": ("epistemics", "allowance", "should_abstain"),
        "can_treat_as_observation": (
            "epistemics",
            "allowance",
            "can_treat_as_observation",
        ),
        "classification_basis": ("epistemics", "unit", "classification_basis"),
    },
    "regulation": {
        "confidence": ("regulation", "state", "confidence"),
        "dominant_axis": ("regulation", "tradeoff", "dominant_axis"),
        "active_axes": ("regulation", "tradeoff", "active_axes"),
        "coping_mode": ("regulation", "bias", "coping_mode"),
        "claim_strength": ("regulation", "bias", "claim_strength"),
        "partial_known_reason": ("regulation", "telemetry", "partial_known_reason"),
        "abstain_reason": ("regulation", "telemetry", "abstain_reason"),
    },
    "t01_semantic_field": {
        "scene_status": ("t01_semantic_field", "state", "scene_status"),
        "unresolved_slots_count": ("t01_semantic_field", "telemetry", "unresolved_slots_count"),
        "pre_verbal_consumer_ready": (
            "t01_semantic_field",
            "gate",
            "pre_verbal_consumer_ready",
        ),
        "no_clean_scene_commit": ("t01_semantic_field", "gate", "no_clean_scene_commit"),
    },
    "t02_relation_binding": {
        "scene_status": ("t02_relation_binding", "state", "scene_status"),
        "no_clean_binding_commit": ("t02_relation_binding", "gate", "no_clean_binding_commit"),
        "pre_verbal_constraint_consumer_ready": (
            "t02_relation_binding",
            "gate",
            "pre_verbal_constraint_consumer_ready",
        ),
        "raw_vs_propagated_distinct": (
            "subject_tick",
            "state",
            "t02_raw_vs_propagated_distinct",
        ),
    },
    "t03_hypothesis_competition": {
        "leader": ("t03_hypothesis_competition", "state", "publication_frontier", "current_leader"),
        "conflict_count": (
            "t03_hypothesis_competition",
            "telemetry",
            "tied_competitor_count",
        ),
        "open_slots": (
            "t03_hypothesis_competition",
            "state",
            "publication_frontier",
            "open_slots",
        ),
        "convergence_status": ("t03_hypothesis_competition", "state", "convergence_status"),
        "nonconvergence_preserved": (
            "t03_hypothesis_competition",
            "gate",
            "nonconvergence_preserved",
        ),
    },
    "t04_attention_schema": {
        "attention_owner": ("t04_attention_schema", "state", "attention_owner"),
        "focus_mode": ("t04_attention_schema", "state", "focus_mode"),
        "reportability_status": ("t04_attention_schema", "state", "reportability_status"),
        "focus_ownership_consumer_ready": (
            "t04_attention_schema",
            "gate",
            "focus_ownership_consumer_ready",
        ),
    },
    "downstream_obedience": {
        "accepted": ("downstream_obedience", "accepted"),
        "usability_class": ("downstream_obedience", "usability_class"),
        "blocked_reason": ("downstream_obedience", "reason"),
        "restrictions": ("downstream_obedience", "restrictions"),
    },
    "subject_tick": {
        "final_execution_outcome": ("subject_tick", "state", "final_execution_outcome"),
        "active_execution_mode": ("subject_tick", "state", "active_execution_mode"),
        "abstain": ("subject_tick", "abstain"),
        "abstain_reason": ("subject_tick", "abstain_reason"),
        "materialized_output": ("subject_tick", "downstream_gate", "accepted"),
    },
}

_MODULE_BLOCKED_RULES: dict[str, tuple[tuple[tuple[str, ...], bool], ...]] = {
    "world_adapter": (
        (("world_adapter", "gate", "world_grounded_transition_allowed"), False),
        (("world_adapter", "abstain"), True),
    ),
    "world_entry_contract": (
        (("world_entry_contract", "w01_admission", "admission_ready"), False),
    ),
    "runtime_topology": (
        (("runtime_topology", "decision", "accepted"), False),
    ),
    "epistemics": (
        (("epistemics", "allowance", "should_abstain"), True),
    ),
    "t01_semantic_field": (
        (("t01_semantic_field", "gate", "no_clean_scene_commit"), True),
    ),
    "t02_relation_binding": (
        (("t02_relation_binding", "gate", "no_clean_binding_commit"), True),
    ),
    "t03_hypothesis_competition": (
        (("t03_hypothesis_competition", "gate", "convergence_consumer_ready"), False),
    ),
    "t04_attention_schema": (
        (("t04_attention_schema", "gate", "focus_ownership_consumer_ready"), False),
    ),
    "downstream_obedience": (
        (("downstream_obedience", "accepted"), False),
    ),
    "subject_tick": (
        (("subject_tick", "abstain"), True),
    ),
}

_trace_output_root = Path("artifacts") / "simple_tick_trace"
_tick_orders: dict[str, int] = {}
_initialized_ticks: set[str] = set()


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


def get_tick_trace_path(tick_id: str) -> Path:
    return _trace_output_root / f"{tick_id}.jsonl"


def _ensure_tick_file(tick_id: str) -> Path:
    path = get_tick_trace_path(tick_id)
    if tick_id not in _initialized_ticks:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        _initialized_ticks.add(tick_id)
        _tick_orders[tick_id] = 0
    return path


def _prepare_tick_trace(tick_id: str) -> Path:
    path = get_tick_trace_path(tick_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    _initialized_ticks.add(tick_id)
    _tick_orders[tick_id] = 0
    return path


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


def _value_at_path(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        if key not in current:
            return None
        current = current[key]
    return current


def _build_snapshot_map(result: RuntimeDispatchResult) -> dict[str, dict[str, Any]]:
    if result.subject_tick_result is None:
        raise ValueError("subject_tick_result is required")
    subject_tick = result.subject_tick_result
    return {
        "runtime_topology": _to_jsonable(runtime_dispatch_snapshot(result)),
        "world_adapter": _to_jsonable(world_adapter_result_snapshot(subject_tick.world_adapter_result)),
        "world_entry_contract": _to_jsonable(world_entry_contract_snapshot(subject_tick.world_entry_result)),
        "epistemics": _to_jsonable(subject_tick.epistemic_result),
        "regulation": _to_jsonable(subject_tick.regulation_result),
        "t01_semantic_field": _to_jsonable(t01_active_field_snapshot(subject_tick.t01_result)),
        "t02_relation_binding": _to_jsonable(t02_constrained_scene_snapshot(subject_tick.t02_result)),
        "t03_hypothesis_competition": _to_jsonable(
            t03_hypothesis_competition_snapshot(subject_tick.t03_result)
        ),
        "t04_attention_schema": _to_jsonable(t04_attention_schema_snapshot(subject_tick.t04_result)),
        "downstream_obedience": _to_jsonable(subject_tick.downstream_gate),
        "subject_tick": _to_jsonable(subject_tick_result_snapshot(subject_tick)),
    }


def extract_module_values(module: str, snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if module not in MODULE_ALLOWED_FIELDS:
        raise ValueError(f"unknown module: {module}")
    field_specs = _MODULE_FIELD_PATHS[module]
    values: dict[str, Any] = {}
    for field in MODULE_ALLOWED_FIELDS[module]:
        path = field_specs[field]
        source = path[0]
        payload = snapshots.get(source, {})
        values[field] = _value_at_path(payload, path[1:])
    return values


def _blocked_note(module: str, snapshots: dict[str, dict[str, Any]]) -> str | None:
    rules = _MODULE_BLOCKED_RULES.get(module, ())
    for path, expected in rules:
        source = path[0]
        payload = snapshots.get(source, {})
        actual = _value_at_path(payload, path[1:])
        if actual is expected:
            return f"{'.'.join(path[1:])}={str(actual).lower()}"
    return None


def emit_simple_tick_trace(
    *,
    tick_id: str,
    snapshots: dict[str, dict[str, Any]],
    output_root: str | Path,
) -> dict[str, Any]:
    set_trace_output_root(output_root)
    trace_path = _prepare_tick_trace(tick_id)
    for module in MODULE_ORDER:
        empty_values = {field: None for field in MODULE_ALLOWED_FIELDS[module]}
        trace_emit(tick_id, module, "enter", empty_values, note="module_enter")
        decision_values = extract_module_values(module, snapshots)
        trace_emit(tick_id, module, "decision", decision_values)
        blocked_note = _blocked_note(module, snapshots)
        if blocked_note is not None:
            trace_emit(tick_id, module, "blocked", decision_values, note=blocked_note)
        trace_emit(tick_id, module, "exit", decision_values, note="module_exit")
    return {
        "tick_id": tick_id,
        "trace_path": str(trace_path),
        "event_count": _tick_orders.get(tick_id, 0),
    }


def write_simple_trace_for_dispatch_result(
    *,
    result: RuntimeDispatchResult,
    output_root: str | Path,
) -> dict[str, Any]:
    if result.subject_tick_result is None:
        raise ValueError("subject_tick_result is required")
    tick_id = result.subject_tick_result.state.tick_id
    snapshots = _build_snapshot_map(result)
    return emit_simple_tick_trace(
        tick_id=tick_id,
        snapshots=snapshots,
        output_root=output_root,
    )


def run_tick_and_write_simple_trace(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool,
    output_root: str | Path,
    route_class: str = "production_contour",
) -> dict[str, Any]:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=SubjectTickInput(
                case_id=case_id,
                energy=energy,
                cognitive=cognitive,
                safety=safety,
                unresolved_preference=unresolved_preference,
            ),
            route_class=RuntimeRouteClass(route_class),
        )
    )
    return write_simple_trace_for_dispatch_result(
        result=result,
        output_root=output_root,
    )
