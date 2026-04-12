from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from substrate.observability.utils import to_jsonable
from substrate.runtime_topology.models import RuntimeDispatchResult
from substrate.runtime_topology.telemetry import runtime_dispatch_snapshot
from substrate.subject_tick.telemetry import subject_tick_result_snapshot
from substrate.t01_semantic_field.telemetry import t01_active_field_snapshot
from substrate.t02_relation_binding.telemetry import t02_constrained_scene_snapshot
from substrate.t03_hypothesis_competition.telemetry import t03_hypothesis_competition_snapshot
from substrate.t04_attention_schema.telemetry import t04_attention_schema_snapshot
from substrate.world_adapter.telemetry import world_adapter_result_snapshot
from substrate.world_entry_contract.telemetry import world_entry_contract_snapshot


@dataclass
class ModuleObservation:
    module: str
    stage: str
    local_pre_state: dict[str, Any] | None
    local_pre_state_available: bool
    local_pre_state_reason: str
    local_post_state: dict[str, Any]
    snapshot_state: dict[str, Any] | None
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    decision: dict[str, Any]
    constraints: dict[str, Any]
    failures: dict[str, Any]
    degradations: dict[str, Any]
    markers: dict[str, Any]
    provenance: dict[str, Any]
    ownership: dict[str, Any]
    event_class: str
    decision_raw: bool = False


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return to_jsonable(dict(value))
    return {}


def _value_at_path(snapshot: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = snapshot
    for token in path:
        if not isinstance(current, Mapping) or token not in current:
            return None
        current = current[token]
    return current


def _extract_path_mapping(snapshot: Mapping[str, Any], path: tuple[str, ...]) -> tuple[dict[str, Any], bool]:
    value = _value_at_path(snapshot, path)
    if value is None:
        return {}, False
    if isinstance(value, Mapping):
        return to_jsonable(dict(value)), False
    return {}, True


def _extract_constraints(
    snapshot: Mapping[str, Any],
    *,
    restrictions_path: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    if restrictions_path is None:
        return {}
    restrictions = _value_at_path(snapshot, restrictions_path)
    if isinstance(restrictions, (list, tuple)):
        return {"restrictions": list(restrictions)}
    return {}


def _extract_bool_fields(
    snapshot: Mapping[str, Any],
    *,
    paths: tuple[tuple[str, ...], ...],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in paths:
        value = _value_at_path(snapshot, path)
        if isinstance(value, bool):
            out[".".join(path)] = value
        elif isinstance(value, str):
            out[".".join(path)] = value
    return out


def _extract_provenance(snapshot: Mapping[str, Any], *, paths: tuple[tuple[str, ...], ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in paths:
        value = _value_at_path(snapshot, path)
        if value is not None:
            out[".".join(path)] = to_jsonable(value)
    return out


def extract_explicit_sections(module: str, snapshot: Mapping[str, Any]) -> dict[str, Any]:
    decision_raw = False
    decision: dict[str, Any] = {}
    constraints: dict[str, Any] = {}
    failures: dict[str, Any] = {}
    degradations: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    ownership: dict[str, Any] = {}

    if module == "runtime_topology":
        decision, decision_raw = _extract_path_mapping(snapshot, ("decision",))
        constraints = _extract_constraints(snapshot, restrictions_path=("decision", "restrictions"))
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("dispatch_lineage",),
                ("decision", "topology_ref"),
            ),
        )
    elif module == "world_adapter":
        decision, decision_raw = _extract_path_mapping(snapshot, ("gate",))
        constraints = _extract_constraints(snapshot, restrictions_path=("gate", "restrictions"))
        failures = _extract_bool_fields(
            snapshot,
            paths=(("abstain",), ("abstain_reason",)),
        )
        degradations = _extract_bool_fields(
            snapshot,
            paths=(("partial_known",), ("partial_known_reason",)),
        )
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("telemetry", "source_lineage"),
                ("telemetry", "emitted_at"),
            ),
        )
    elif module == "world_entry_contract":
        decision, decision_raw = _extract_path_mapping(snapshot, ("w01_admission",))
        constraints = _extract_constraints(snapshot, restrictions_path=("w01_admission", "restrictions"))
        degradations = _extract_bool_fields(
            snapshot,
            paths=(
                ("episode", "degraded"),
                ("episode", "incomplete"),
                ("telemetry", "degraded"),
                ("telemetry", "incomplete"),
            ),
        )
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("episode", "source_lineage"),
                ("telemetry", "emitted_at"),
            ),
        )
    elif module == "epistemics":
        decision, decision_raw = _extract_path_mapping(snapshot, ("allowance",))
        constraints = _extract_constraints(snapshot, restrictions_path=("allowance", "restrictions"))
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("telemetry", "source_lineage"),
                ("telemetry", "emitted_at"),
            ),
        )
    elif module == "regulation":
        decision, decision_raw = _extract_path_mapping(snapshot, ("tradeoff",))
        constraints = _extract_constraints(snapshot, restrictions_path=("tradeoff", "restrictions"))
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("telemetry", "source_lineage"),
                ("telemetry", "emitted_at"),
            ),
        )
    elif module in {
        "t01_semantic_field",
        "t02_relation_binding",
        "t03_hypothesis_competition",
        "t04_attention_schema",
    }:
        decision, decision_raw = _extract_path_mapping(snapshot, ("gate",))
        constraints = _extract_constraints(snapshot, restrictions_path=("gate", "restrictions"))
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("state", "source_lineage"),
                ("telemetry", "emitted_at"),
            ),
        )
        if module == "t04_attention_schema":
            owner_value = _value_at_path(snapshot, ("state", "attention_owner"))
            if owner_value is not None:
                ownership = {"state.attention_owner": owner_value}
    elif module == "downstream_obedience":
        explicit = {
            key: snapshot[key]
            for key in ("accepted", "usability_class", "restrictions", "reason", "state_ref")
            if key in snapshot
        }
        decision = to_jsonable(explicit)
        constraints = _extract_constraints(snapshot, restrictions_path=("restrictions",))
        provenance = _extract_provenance(snapshot, paths=(("state_ref",),))
    elif module == "subject_tick":
        decision, decision_raw = _extract_path_mapping(snapshot, ("downstream_gate",))
        constraints = _extract_constraints(snapshot, restrictions_path=("downstream_gate", "restrictions"))
        failures = _extract_bool_fields(
            snapshot,
            paths=(("abstain",), ("abstain_reason",)),
        )
        provenance = _extract_provenance(
            snapshot,
            paths=(
                ("telemetry", "source_lineage"),
                ("telemetry", "role_source_ref"),
                ("telemetry", "emitted_at"),
            ),
        )

    return {
        "decision": decision,
        "constraints": constraints,
        "failures": failures,
        "degradations": degradations,
        "provenance": provenance,
        "ownership": ownership,
        "decision_raw": decision_raw,
    }


def _extract_tick_input(result: RuntimeDispatchResult) -> dict[str, Any]:
    tick_input = result.request.tick_input
    return to_jsonable(
        {
            "case_id": tick_input.case_id,
            "energy": tick_input.energy,
            "cognitive": tick_input.cognitive,
            "safety": tick_input.safety,
            "unresolved_preference": tick_input.unresolved_preference,
            "route_class_requested": result.request.route_class.value,
        }
    )


def _mapping_value(snapshot: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = snapshot.get(key)
    if isinstance(value, Mapping):
        return value
    return {}


def _count(value: Any) -> int:
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    return 0


def _enum_or_raw(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _build_local_post_state(module: str, snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if module == "runtime_topology":
        decision = _mapping_value(snapshot, "decision")
        bundle = _mapping_value(snapshot, "bundle")
        tick_graph = _mapping_value(snapshot, "tick_graph")
        return {
            "decision": {
                "accepted": decision.get("accepted"),
                "lawful_production_route": decision.get("lawful_production_route"),
                "route_class": decision.get("route_class"),
                "route_binding_consequence": decision.get("route_binding_consequence"),
            },
            "bundle": {
                "runtime_entry": bundle.get("runtime_entry"),
                "contour_id": bundle.get("contour_id"),
                "execution_spine_phase": bundle.get("execution_spine_phase"),
            },
            "tick_graph": {
                "runtime_order_len": _count(tick_graph.get("runtime_order")),
                "mandatory_checkpoint_count": _count(
                    tick_graph.get("mandatory_checkpoint_ids")
                ),
            },
        }
    if module == "epistemics":
        unit = _mapping_value(snapshot, "unit")
        allowance = _mapping_value(snapshot, "allowance")
        telemetry = _mapping_value(snapshot, "telemetry")
        return {
            "unit": {
                "status": unit.get("status"),
                "confidence": unit.get("confidence"),
                "source_class": unit.get("source_class"),
                "modality": unit.get("modality"),
            },
            "allowance": {
                "can_treat_as_observation": allowance.get("can_treat_as_observation"),
                "should_abstain": allowance.get("should_abstain"),
                "claim_strength": allowance.get("claim_strength"),
                "restrictions_count": _count(allowance.get("restrictions")),
                "reason": allowance.get("reason"),
            },
            "telemetry": {
                "classification_basis": telemetry.get("classification_basis"),
                "downstream_claim_strength": telemetry.get("downstream_claim_strength"),
                "downstream_restrictions_count": _count(
                    telemetry.get("downstream_restrictions")
                ),
            },
        }
    if module == "regulation":
        state = _mapping_value(snapshot, "state")
        tradeoff = _mapping_value(snapshot, "tradeoff")
        bias = _mapping_value(snapshot, "bias")
        return {
            "state": {
                "confidence": state.get("confidence"),
                "tracked_axes_count": _count(state.get("needs")),
                "partial_known": state.get("partial_known") is not None,
                "abstention": state.get("abstention") is not None,
            },
            "tradeoff": {
                "dominant_axis": tradeoff.get("dominant_axis"),
                "active_axes_count": _count(tradeoff.get("active_axes")),
                "suppressed_axes_count": _count(tradeoff.get("suppressed_axes")),
                "reason": tradeoff.get("reason"),
            },
            "bias": {
                "coping_mode": bias.get("coping_mode"),
                "claim_strength": bias.get("claim_strength"),
                "restrictions_count": _count(bias.get("restrictions")),
                "reason": bias.get("reason"),
            },
        }
    if module == "t03_hypothesis_competition":
        state = _mapping_value(snapshot, "state")
        gate = _mapping_value(snapshot, "gate")
        frontier = _mapping_value(state, "publication_frontier")
        return {
            "state": {
                "competition_id": state.get("competition_id"),
                "convergence_status": state.get("convergence_status"),
                "current_leader_hypothesis_id": state.get("current_leader_hypothesis_id"),
                "provisional_frontrunner_hypothesis_id": state.get(
                    "provisional_frontrunner_hypothesis_id"
                ),
                "tied_competitor_count": _count(state.get("tied_competitor_ids")),
                "blocked_hypothesis_count": _count(state.get("blocked_hypothesis_ids")),
                "eliminated_hypothesis_count": _count(
                    state.get("eliminated_hypothesis_ids")
                ),
                "reactivated_hypothesis_count": _count(
                    state.get("reactivated_hypothesis_ids")
                ),
                "honest_nonconvergence": state.get("honest_nonconvergence"),
                "bounded_plurality": state.get("bounded_plurality"),
            },
            "gate": {
                "convergence_consumer_ready": gate.get("convergence_consumer_ready"),
                "frontier_consumer_ready": gate.get("frontier_consumer_ready"),
                "nonconvergence_preserved": gate.get("nonconvergence_preserved"),
                "restrictions_count": _count(gate.get("restrictions")),
            },
            "frontier": {
                "current_leader": frontier.get("current_leader"),
                "open_slots_count": _count(frontier.get("open_slots")),
                "unresolved_conflicts_count": _count(frontier.get("unresolved_conflicts")),
                "stability_status": frontier.get("stability_status"),
            },
        }
    if module == "downstream_obedience":
        return {
            "accepted": snapshot.get("accepted"),
            "usability_class": snapshot.get("usability_class"),
            "restrictions_count": _count(snapshot.get("restrictions")),
            "reason": snapshot.get("reason"),
            "state_ref": snapshot.get("state_ref"),
        }
    if module == "subject_tick":
        state = _mapping_value(snapshot, "state")
        downstream_gate = _mapping_value(snapshot, "downstream_gate")
        return {
            "state": {
                "tick_id": state.get("tick_id"),
                "tick_index": state.get("tick_index"),
                "active_execution_mode": state.get("active_execution_mode"),
                "execution_stance": state.get("execution_stance"),
                "final_execution_outcome": state.get("final_execution_outcome"),
                "c04_selected_mode": state.get("c04_selected_mode"),
                "c05_validity_action": state.get("c05_validity_action"),
                "world_link_status": state.get("world_link_status"),
                "world_grounded_transition_allowed": state.get(
                    "world_grounded_transition_allowed"
                ),
                "world_effect_feedback_correlated": state.get(
                    "world_effect_feedback_correlated"
                ),
                "t03_convergence_status": state.get("t03_convergence_status"),
                "t03_current_leader_hypothesis_id": state.get(
                    "t03_current_leader_hypothesis_id"
                ),
                "t03_honest_nonconvergence": state.get("t03_honest_nonconvergence"),
                "t03_bounded_plurality": state.get("t03_bounded_plurality"),
            },
            "downstream_gate": {
                "accepted": downstream_gate.get("accepted"),
                "usability_class": downstream_gate.get("usability_class"),
                "restrictions_count": _count(downstream_gate.get("restrictions")),
                "reason": downstream_gate.get("reason"),
            },
            "abstain": snapshot.get("abstain"),
            "abstain_reason": snapshot.get("abstain_reason"),
        }
    return _as_mapping(snapshot)


def _local_pre_state(
    *,
    module: str,
    tick_input: Mapping[str, Any],
    result: RuntimeDispatchResult,
) -> tuple[dict[str, Any] | None, bool, str]:
    context = result.request.context
    subject_tick = result.subject_tick_result
    if module == "runtime_topology":
        return (
            {
                "local_state": {
                    "decision": {
                        "accepted": None,
                        "lawful_production_route": None,
                        "route_class": result.request.route_class.value,
                        "route_binding_consequence": None,
                    },
                    "bundle": {
                        "runtime_entry": result.bundle.runtime_entry,
                        "contour_id": result.bundle.contour_id,
                        "execution_spine_phase": result.bundle.execution_spine_phase,
                    },
                    "tick_graph": {
                        "runtime_order_len": len(result.tick_graph.runtime_order),
                        "mandatory_checkpoint_count": len(
                            result.tick_graph.mandatory_checkpoint_ids
                        ),
                    },
                    "dispatch_request": dict(tick_input),
                }
            },
            True,
            "available",
        )
    if subject_tick is None:
        return None, False, "no_subject_tick_result"
    if module == "epistemics":
        return (
            {
                "local_state": {
                    "unit": {
                        "status": "pre_grounding_pending",
                        "confidence": tick_input.get("epistemic_confidence_hint"),
                        "source_class": tick_input.get("epistemic_source_class"),
                        "modality": tick_input.get("epistemic_modality"),
                    },
                    "allowance": {
                        "can_treat_as_observation": False,
                        "should_abstain": bool(
                            getattr(context, "require_epistemic_observation", False)
                        ),
                        "claim_strength": "pre_grounding_pending",
                        "restrictions_count": 0,
                        "reason": "pre_grounding_pending",
                    },
                    "telemetry": {
                        "classification_basis": "pre_grounding_pending",
                        "downstream_claim_strength": "pre_grounding_pending",
                        "downstream_restrictions_count": 0,
                    },
                }
            },
            True,
            "available",
        )
    if module == "regulation":
        prior_regulation_state = None if context is None else getattr(context, "prior_regulation_state", None)
        prior_needs = getattr(prior_regulation_state, "needs", ())
        prior_confidence = _enum_or_raw(getattr(prior_regulation_state, "confidence", None))
        return (
            {
                "local_state": {
                    "state": {
                        "confidence": prior_confidence,
                        "tracked_axes_count": len(prior_needs),
                        "partial_known": getattr(prior_regulation_state, "partial_known", None)
                        is not None,
                        "abstention": getattr(prior_regulation_state, "abstention", None)
                        is not None,
                    },
                    "tradeoff": {
                        "dominant_axis": None,
                        "active_axes_count": 0,
                        "suppressed_axes_count": 0,
                        "reason": "pre_regulation_pending",
                    },
                    "bias": {
                        "coping_mode": "pre_regulation_pending",
                        "claim_strength": "pre_regulation_pending",
                        "restrictions_count": 0,
                        "reason": "pre_regulation_pending",
                    },
                }
            },
            True,
            "available",
        )
    if module == "t03_hypothesis_competition":
        prior_state = None if context is None else getattr(context, "prior_subject_tick_state", None)
        return (
            {
                "local_state": {
                    "state": {
                        "competition_id": getattr(prior_state, "t03_competition_id", None),
                        "convergence_status": getattr(
                            prior_state, "t03_convergence_status", "pre_competition_pending"
                        ),
                        "current_leader_hypothesis_id": getattr(
                            prior_state, "t03_current_leader_hypothesis_id", None
                        ),
                        "provisional_frontrunner_hypothesis_id": getattr(
                            prior_state, "t03_provisional_frontrunner_hypothesis_id", None
                        ),
                        "tied_competitor_count": getattr(
                            prior_state, "t03_tied_competitor_count", 0
                        ),
                        "blocked_hypothesis_count": getattr(
                            prior_state, "t03_blocked_hypothesis_count", 0
                        ),
                        "eliminated_hypothesis_count": getattr(
                            prior_state, "t03_eliminated_hypothesis_count", 0
                        ),
                        "reactivated_hypothesis_count": getattr(
                            prior_state, "t03_reactivated_hypothesis_count", 0
                        ),
                        "honest_nonconvergence": getattr(
                            prior_state, "t03_honest_nonconvergence", None
                        ),
                        "bounded_plurality": getattr(prior_state, "t03_bounded_plurality", None),
                    },
                    "gate": {
                        "convergence_consumer_ready": None,
                        "frontier_consumer_ready": None,
                        "nonconvergence_preserved": None,
                        "restrictions_count": 0,
                    },
                    "frontier": {
                        "current_leader": getattr(
                            prior_state, "t03_publication_current_leader", None
                        ),
                        "open_slots_count": len(
                            getattr(prior_state, "t03_publication_open_slots", ()) or ()
                        ),
                        "unresolved_conflicts_count": len(
                            getattr(prior_state, "t03_publication_unresolved_conflicts", ())
                            or ()
                        ),
                        "stability_status": getattr(
                            prior_state, "t03_publication_stability_status", None
                        ),
                    },
                }
            },
            True,
            "available",
        )
    if module == "downstream_obedience":
        state = subject_tick.state
        return (
            {
                "local_state": {
                    "accepted": None,
                    "usability_class": None,
                    "restrictions_count": 0,
                    "reason": "pre_obedience_pending",
                    "state_ref": None,
                    "inputs": {
                        "active_execution_mode": state.active_execution_mode,
                        "c04_selected_mode": state.c04_selected_mode,
                        "c05_validity_action": state.c05_validity_action,
                        "world_entry_w01_admission_ready": state.world_entry_w01_admission_ready,
                        "t03_convergence_status": state.t03_convergence_status,
                        "t03_honest_nonconvergence": state.t03_honest_nonconvergence,
                        "t04_focus_ownership_consumer_required": (
                            state.t04_require_focus_ownership_consumer
                        ),
                    },
                }
            },
            True,
            "available",
        )
    if module == "subject_tick":
        prior_state = None if context is None else getattr(context, "prior_subject_tick_state", None)
        prior_outcome = None
        if prior_state is not None:
            prior_outcome = _enum_or_raw(getattr(prior_state, "final_execution_outcome", None))
        return (
            {
                "local_state": {
                    "state": {
                        "tick_id": getattr(prior_state, "tick_id", None),
                        "tick_index": getattr(prior_state, "tick_index", None),
                        "active_execution_mode": getattr(
                            prior_state, "active_execution_mode", None
                        ),
                        "execution_stance": _enum_or_raw(
                            getattr(prior_state, "execution_stance", None)
                        ),
                        "final_execution_outcome": prior_outcome,
                        "c04_selected_mode": None,
                        "c05_validity_action": None,
                        "world_link_status": None,
                        "world_grounded_transition_allowed": None,
                        "world_effect_feedback_correlated": None,
                        "t03_convergence_status": getattr(
                            prior_state, "t03_convergence_status", None
                        ),
                        "t03_current_leader_hypothesis_id": getattr(
                            prior_state, "t03_current_leader_hypothesis_id", None
                        ),
                        "t03_honest_nonconvergence": getattr(
                            prior_state, "t03_honest_nonconvergence", None
                        ),
                        "t03_bounded_plurality": getattr(
                            prior_state, "t03_bounded_plurality", None
                        ),
                    },
                    "downstream_gate": {
                        "accepted": None,
                        "usability_class": None,
                        "restrictions_count": 0,
                        "reason": "pre_subject_tick_pending",
                    },
                    "abstain": None,
                    "abstain_reason": None,
                }
            },
            True,
            "available",
        )
    return None, False, "no_local_pre_state"


def build_core_observations(result: RuntimeDispatchResult) -> list[ModuleObservation]:
    if result.subject_tick_result is None:
        raise ValueError("subject_tick_result is required to build observability core trace")
    subject_tick = result.subject_tick_result
    tick_input = _extract_tick_input(result)

    runtime_snapshot = to_jsonable(runtime_dispatch_snapshot(result))
    subject_snapshot = to_jsonable(subject_tick_result_snapshot(subject_tick))
    world_adapter_snapshot = to_jsonable(world_adapter_result_snapshot(subject_tick.world_adapter_result))
    world_entry_snapshot = to_jsonable(world_entry_contract_snapshot(subject_tick.world_entry_result))
    epistemics_snapshot = to_jsonable(subject_tick.epistemic_result)
    regulation_snapshot = to_jsonable(subject_tick.regulation_result)
    downstream_snapshot = to_jsonable(subject_tick.downstream_gate)
    t01_snapshot = to_jsonable(t01_active_field_snapshot(subject_tick.t01_result))
    t02_snapshot = to_jsonable(t02_constrained_scene_snapshot(subject_tick.t02_result))
    t03_snapshot = to_jsonable(t03_hypothesis_competition_snapshot(subject_tick.t03_result))
    t04_snapshot = to_jsonable(t04_attention_schema_snapshot(subject_tick.t04_result))

    module_snapshots: list[tuple[str, str, dict[str, Any], str]] = [
        ("runtime_topology", "dispatch", runtime_snapshot, "topology_routing"),
        ("world_adapter", "world", world_adapter_snapshot, "snapshot"),
        ("world_entry_contract", "world", world_entry_snapshot, "snapshot"),
        ("epistemics", "admission", epistemics_snapshot, "decision"),
        ("regulation", "shared_domain", regulation_snapshot, "decision"),
        ("t01_semantic_field", "semantic_field", t01_snapshot, "snapshot"),
        ("t02_relation_binding", "relation_binding", t02_snapshot, "snapshot"),
        ("t03_hypothesis_competition", "competition", t03_snapshot, "snapshot"),
        ("t04_attention_schema", "attention", t04_snapshot, "snapshot"),
        ("downstream_obedience", "gate", downstream_snapshot, "decision"),
        ("subject_tick", "execution_spine", subject_snapshot, "snapshot"),
    ]

    observations: list[ModuleObservation] = []
    for module_name, stage, deep_snapshot, event_class in module_snapshots:
        sections = extract_explicit_sections(module_name, _as_mapping(deep_snapshot))
        local_pre_state, local_pre_state_available, local_pre_state_reason = _local_pre_state(
            module=module_name,
            tick_input=tick_input,
            result=result,
        )
        post_state_projection = _build_local_post_state(module_name, _as_mapping(deep_snapshot))
        observations.append(
            ModuleObservation(
                module=module_name,
                stage=stage,
                local_pre_state=to_jsonable(local_pre_state) if local_pre_state is not None else None,
                local_pre_state_available=local_pre_state_available,
                local_pre_state_reason=local_pre_state_reason,
                local_post_state={"local_state": to_jsonable(post_state_projection)},
                snapshot_state=_as_mapping(deep_snapshot),
                inputs={"tick_input": tick_input},
                outputs={
                    "module": module_name,
                    "stage": stage,
                    "snapshot_keys": tuple(sorted(deep_snapshot.keys()))
                    if isinstance(deep_snapshot, dict)
                    else (),
                },
                decision=to_jsonable(sections["decision"]),
                constraints=to_jsonable(sections["constraints"]),
                failures=to_jsonable(sections["failures"]),
                degradations=to_jsonable(sections["degradations"]),
                markers={
                    "canonical_snapshot": True,
                    "module_adapter": "explicit_core_adapter",
                    "decision_raw": sections["decision_raw"],
                },
                provenance=to_jsonable(sections["provenance"]),
                ownership=to_jsonable(sections["ownership"]),
                event_class=event_class,
                decision_raw=bool(sections["decision_raw"]),
            )
        )
    return observations
