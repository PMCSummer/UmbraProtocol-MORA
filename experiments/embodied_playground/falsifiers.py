from __future__ import annotations

import inspect
from dataclasses import asdict
from typing import Any

from experiments.embodied_playground.action_space import (
    FORBIDDEN_ADAPTER_LOCKIN_ACTION_FIELDS,
)
from experiments.embodied_playground.models import (
    AP01RequestRef,
    ActionEffectFrame,
    ActionSpaceFrame,
    CorrelationStatus,
    EffectStatus,
    EvalOnlyWorldTruth,
    ObservationFrame,
    PublishedActionEnvelope,
    PublicWorldSnapshot,
)


FORBIDDEN_EVAL_KEYS: tuple[str, ...] = (
    "expected_outcome",
    "scenario_labels",
    "eval_label",
    "harness_truth",
)


def _flat(value: object) -> str:
    return str(value).lower()


def hidden_truth_leakage(
    observation: ObservationFrame,
    snapshot: PublicWorldSnapshot,
) -> bool:
    if not observation.hidden_truth_excluded or not snapshot.hidden_truth_excluded:
        return True
    payload = _flat(asdict(observation)) + _flat(asdict(snapshot))
    return (
        "hidden_inventory" in payload
        or "hidden_objects" in payload
        or "true_recipe_table" in payload
        or "must_never_enter_subject_visible': false" in payload
    )


def eval_label_leakage(observation: ObservationFrame, action_space: ActionSpaceFrame, effect: ActionEffectFrame) -> bool:
    payload = _flat(asdict(observation)) + _flat(asdict(action_space)) + _flat(asdict(effect))
    return any(token in payload for token in FORBIDDEN_EVAL_KEYS)


def action_space_as_permission(action_space: ActionSpaceFrame) -> bool:
    if action_space.action_space_is_permission or action_space.action_space_is_selection or action_space.action_space_is_execution:
        return True
    return any(surface.is_permission for surface in action_space.available_surfaces)


def action_without_ap01_envelope(effect: ActionEffectFrame) -> bool:
    if effect.correlation_status == CorrelationStatus.CORRELATED_TO_REQUEST:
        return not effect.request_ref or not effect.envelope_ref
    return False


def request_as_execution(envelope: PublishedActionEnvelope) -> bool:
    return envelope.submitted_to_world or envelope.executed_by_world


def request_as_success_or_completion(envelope: object) -> bool:
    if not isinstance(envelope, PublishedActionEnvelope):
        return True
    if envelope.submitted_to_world or envelope.executed_by_world:
        return True
    if not envelope.request_boundary_preserved:
        return True
    if not envelope.no_hidden_truth_used or not envelope.no_eval_only_used or not envelope.no_scenario_label_used:
        return True
    if isinstance(envelope.ap01_request_ref, AP01RequestRef):
        if envelope.ap01_request_ref.source != "ap01":
            return True
        if not envelope.ap01_request_ref.boundary_preserved or not envelope.ap01_request_ref.must_wait_for_effect:
            return True
    prohibited_fields = ("completion", "success", "world_change")
    for field_name in envelope.__dataclass_fields__.keys():
        if any(token in field_name.lower() for token in prohibited_fields):
            return True
    return False


def effect_without_correlation(effect: ActionEffectFrame) -> bool:
    effect_status = str(getattr(effect.effect_status, "value", effect.effect_status))
    if effect_status in {
        EffectStatus.SUCCEEDED.value,
        EffectStatus.FAILED.value,
        EffectStatus.BLOCKED.value,
        EffectStatus.PARTIAL.value,
    }:
        status = str(getattr(effect.correlation_status, "value", effect.correlation_status))
        if status == CorrelationStatus.CORRELATED_TO_REQUEST.value:
            return not effect.request_ref or not effect.envelope_ref
        return status not in {
            CorrelationStatus.PASSIVE_WORLD_EVENT.value,
            CorrelationStatus.AMBIGUOUS.value,
            CorrelationStatus.MISSING_REQUEST.value,
        }
    return False


def effect_success_without_correlation(effect: ActionEffectFrame) -> bool:
    return effect_without_correlation(effect)


def inventory_delta_without_effect(
    previous_inventory_state: dict[str, int],
    current_inventory_state: dict[str, int],
    effect: ActionEffectFrame | None,
) -> bool:
    if previous_inventory_state == current_inventory_state:
        return False
    return effect is None


def body_delta_without_effect(
    previous_location_ref: str,
    current_location_ref: str,
    effect: ActionEffectFrame | None,
) -> bool:
    if previous_location_ref == current_location_ref:
        return False
    return effect is None


def movement_without_effect(previous_location_ref: str, current_location_ref: str, effect: ActionEffectFrame | None) -> bool:
    return body_delta_without_effect(previous_location_ref, current_location_ref, effect)


def hidden_recipe_visible(observation: ObservationFrame) -> bool:
    payload = _flat(asdict(observation))
    return "true_recipe_table" in payload


def hidden_map_leak(observation: ObservationFrame, snapshot: PublicWorldSnapshot, hidden_object_ref: str) -> bool:
    payload = _flat(asdict(observation)) + _flat(asdict(snapshot))
    return hidden_object_ref.lower() in payload


def eval_truth_leak(observation: ObservationFrame, snapshot: PublicWorldSnapshot) -> bool:
    return hidden_truth_leakage(observation, snapshot) or any(
        token in (_flat(asdict(observation)) + _flat(asdict(snapshot)))
        for token in FORBIDDEN_EVAL_KEYS
    )


def backend_selects_action(backend: object) -> bool:
    cls = backend if inspect.isclass(backend) else type(backend)
    for method_name in dir(backend):
        lowered = method_name.lower()
        if any(token in lowered for token in ("choose_action", "select_action", "decide_action", "plan_action")):
            return True
    method_contract = {
        "observe": ("ObservationFrame", None),
        "action_space": ("ActionSpaceFrame", None),
        "submit_action": ("ActionEffectFrame", "PublishedActionEnvelope"),
        "public_snapshot": ("PublicWorldSnapshot", None),
    }
    for method_name, (return_ann, arg_ann) in method_contract.items():
        method = getattr(cls, method_name, None)
        if method is None or not callable(method):
            return True
        signature = inspect.signature(method)
        if arg_ann is not None:
            params = list(signature.parameters.values())
            if len(params) < 2:
                return True
            envelope_param = params[1]
            if arg_ann not in str(envelope_param.annotation):
                return True
        if return_ann not in str(signature.return_annotation):
            return True
        if method_name in {"observe", "action_space", "public_snapshot"}:
            if "PublishedActionEnvelope" in str(signature.return_annotation) or "AP01" in str(signature.return_annotation):
                return True
    # Runtime structural checks: backend must not output selected actions from
    # observation/action-space/snapshot surfaces and must not mutate world state
    # on read-only surfaces.
    try:
        observe_1 = getattr(backend, "observe")("subject_a")
        action_space_1 = getattr(backend, "action_space")("subject_a")
        snapshot_1 = getattr(backend, "public_snapshot")("subject_a")
    except Exception:
        return True

    if not isinstance(observe_1, ObservationFrame):
        return True
    if not isinstance(action_space_1, ActionSpaceFrame):
        return True
    if not isinstance(snapshot_1, PublicWorldSnapshot):
        return True
    if any(isinstance(v, PublishedActionEnvelope) for v in (observe_1, action_space_1, snapshot_1)):
        return True

    try:
        observe_2 = getattr(backend, "observe")("subject_a")
        action_space_2 = getattr(backend, "action_space")("subject_a")
        snapshot_2 = getattr(backend, "public_snapshot")("subject_a")
    except Exception:
        return True

    # Read-only surfaces must not advance or mutate world state by themselves.
    if observe_1.tick_index != observe_2.tick_index:
        return True
    if snapshot_1.tick_index != snapshot_2.tick_index:
        return True
    if action_space_1.tick_index != action_space_2.tick_index:
        return True
    if observe_1.body_state.location_ref != observe_2.body_state.location_ref:
        return True
    if observe_1.inventory_state.item_counts != observe_2.inventory_state.item_counts:
        return True
    if snapshot_1.visible_inventory_state.item_counts != snapshot_2.visible_inventory_state.item_counts:
        return True
    if snapshot_1.visible_body_state.location_ref != snapshot_2.visible_body_state.location_ref:
        return True
    return False


def backend_chooses_action(backend: object) -> bool:
    return backend_selects_action(backend)


def minecraft_specific_leak(model_type: type[Any]) -> bool:
    fields = getattr(model_type, "__dataclass_fields__", {})
    return any(field_name in fields for field_name in FORBIDDEN_ADAPTER_LOCKIN_ACTION_FIELDS)


def grid_specific_lockin(model_type: type[Any]) -> bool:
    fields = getattr(model_type, "__dataclass_fields__", {})
    has_location_ref = "location_ref" in fields
    has_forced_xy = "x" in fields and "y" in fields
    return has_forced_xy and not has_location_ref


def ap01_boundary_missing(envelope: PublishedActionEnvelope) -> bool:
    request_ref = envelope.ap01_request_ref.request_ref if isinstance(envelope.ap01_request_ref, AP01RequestRef) else str(envelope.ap01_request_ref)
    return (not request_ref) or (not envelope.request_boundary_preserved)


def ap01_request_boundary_lost(envelope: PublishedActionEnvelope) -> bool:
    return ap01_boundary_missing(envelope)


def scenario_id_action_selection(payload: object) -> bool:
    markers = (
        "scenario_id",
        "scenario:",
        "test_name",
        "expected_outcome",
        "gui_label",
        "eval_only",
        "hidden_truth",
        "select_action_by_scenario",
        "scenario_to_action",
    )
    decision_keys = (
        "action_kind",
        "target_ref",
        "args",
        "intended_effect",
        "source_tick_ref",
        "source_phase_refs",
        "permission_refs",
        "evidence_refs",
        "affordance_binding_refs",
        "constraints",
        "source_authority",
    )
    docs_only_keys = {"docs", "markdown", "note", "description", "readme"}

    if isinstance(payload, PublishedActionEnvelope):
        envelope_values = (
            payload.action_kind,
            payload.target_ref,
            payload.args,
            payload.intended_effect,
            payload.source_tick_ref,
            payload.source_phase_refs,
            payload.permission_refs,
            payload.evidence_refs,
            payload.affordance_binding_refs,
            payload.ap01_request_id,
        )
        serialized = _flat(envelope_values)
        return any(marker in serialized for marker in markers)

    if isinstance(payload, ActionSpaceFrame):
        serialized = _flat(
            (
                payload.allowed_action_kinds_from_body,
                payload.body_constraints,
                tuple(surface.constraints for surface in payload.available_surfaces),
                payload.frame_id,
            )
        )
        return any(marker in serialized for marker in markers)

    if isinstance(payload, (ObservationFrame, ActionEffectFrame, PublicWorldSnapshot)):
        serialized = _flat(asdict(payload))
        return any(marker in serialized for marker in markers)

    if isinstance(payload, dict):
        keys = set(payload.keys())
        if keys and keys.issubset(docs_only_keys):
            return False
        for key in decision_keys:
            if key in payload and any(marker in _flat(payload[key]) for marker in markers):
                return True
        return any(marker in _flat(payload) for marker in ("scenario_to_action", "select_action_by_scenario"))

    serialized = _flat(payload)
    return "scenario_to_action" in serialized or "select_action_by_scenario" in serialized


def movement_through_wall(
    *,
    was_blocked_by_wall: bool,
    previous_location_ref: str,
    current_location_ref: str,
    effect: ActionEffectFrame,
) -> bool:
    if not was_blocked_by_wall:
        return False
    if previous_location_ref != current_location_ref:
        return True
    status = str(getattr(effect.effect_status, "value", effect.effect_status))
    return status == EffectStatus.SUCCEEDED.value


def pickup_without_proximity(*, pickup_succeeded: bool, target_reachable: bool) -> bool:
    return pickup_succeeded and (not target_reachable)


def pickup_without_capacity(*, pickup_succeeded: bool, capacity_available: bool) -> bool:
    return pickup_succeeded and (not capacity_available)


def drop_without_inventory_item(*, drop_succeeded: bool, had_item_before: bool) -> bool:
    return drop_succeeded and (not had_item_before)


def station_use_without_visibility_or_proximity(*, use_station_succeeded: bool, station_visible: bool, station_reachable: bool) -> bool:
    return use_station_succeeded and ((not station_visible) or (not station_reachable))


def station_result_without_input(*, station_output_produced: bool, station_input_available: bool) -> bool:
    return station_output_produced and (not station_input_available)


def recipe_result_in_p2(effect: ActionEffectFrame) -> bool:
    payload = _flat(effect.world_delta_public) + _flat(effect.observed_result_refs)
    return any(token in payload for token in ("crafted", "refined", "recipe_output", "filter_output"))


def observation_as_effect(observation: ObservationFrame) -> bool:
    payload = _flat(asdict(observation))
    return any(token in payload for token in ("body_delta", "inventory_delta", "effect_status", "world_delta_public"))


def public_snapshot_contains_eval_truth(snapshot: PublicWorldSnapshot) -> bool:
    payload = _flat(asdict(snapshot))
    return any(token in payload for token in ("hidden_inventory", "hidden_objects", "true_recipe_table", "expected_outcome", "scenario_labels"))


def station_visible_as_usable(*, station_visible: bool, use_station_succeeded: bool, station_reachable: bool, input_available: bool) -> bool:
    return station_visible and use_station_succeeded and ((not station_reachable) or (not input_available))


def invalid_envelope_effect_invariant(effect: ActionEffectFrame) -> bool:
    effect_status = str(getattr(effect.effect_status, "value", effect.effect_status))
    correlation_status = str(getattr(effect.correlation_status, "value", effect.correlation_status))
    if effect_status not in {EffectStatus.BLOCKED.value, EffectStatus.FAILED.value}:
        return True
    if correlation_status != CorrelationStatus.INVALID.value:
        return True
    if effect.request_ref is not None:
        return True
    if effect.envelope_ref is not None:
        return True
    if bool(effect.body_delta):
        return True
    if bool(effect.inventory_delta):
        return True
    if bool(effect.world_delta_public):
        return True
    return False


def validate_public_eval_separation(
    observation: ObservationFrame,
    snapshot: PublicWorldSnapshot,
    eval_truth: EvalOnlyWorldTruth,
) -> bool:
    if hidden_truth_leakage(observation, snapshot):
        return False
    if not eval_truth.must_never_enter_subject_visible:
        return False
    return True
