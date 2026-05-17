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
FORBIDDEN_PRIVATE_EVAL_BASIS_MARKERS: tuple[str, ...] = (
    "eval_only",
    "private_world",
    "private_map",
    "hidden_truth",
    "hidden_map",
    "hidden_object",
    "hidden_inventory",
    "full_map",
    "expected_outcome",
)
FORBIDDEN_SCENARIO_ACTION_BASIS_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "scenario_to_action",
    "select_action_by_scenario",
    "test_name",
    "test_case",
    "demo_case",
    "gui_label",
    "manual_action",
    "expected_outcome",
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


def bridge_calls_w_modules_directly(source_text: str) -> bool:
    lowered = source_text.lower()
    forbidden_tokens = (
        "substrate.w01",
        "substrate.w02",
        "substrate.w03",
        "substrate.w04",
        "substrate.w05",
        "substrate.w06",
        "substrate.a01",
        "substrate.a02",
        "substrate.a03",
        "substrate.a04",
        "substrate.p01",
        "substrate.p02",
        "substrate.p03",
        "substrate.p04",
        "substrate.s01",
        "substrate.s02",
        "substrate.s03",
        "substrate.s04",
        "substrate.s05",
    )
    if "execute_subject_tick" not in lowered:
        return True
    return any(token in lowered for token in forbidden_tokens)


def ap01_policy_called_directly_by_bridge(source_text: str) -> bool:
    lowered = source_text.lower()
    if "execute_subject_tick" not in lowered:
        return True
    return "build_ap01_subject_action_publication" in lowered


def world_executes_without_subject_request(
    *,
    world_submission_attempted: bool,
    ap01_published_request_count: int,
) -> bool:
    return world_submission_attempted and ap01_published_request_count <= 0


def action_space_as_action_request(
    *,
    action_space_available: bool,
    ap01_published_request_count: int,
    world_submission_attempted: bool,
) -> bool:
    if not action_space_available:
        return False
    if ap01_published_request_count > 0:
        return False
    return world_submission_attempted


def eval_truth_fed_to_subject_tick(payload: object) -> bool:
    forbidden = ("hidden_objects", "hidden_inventory", "true_recipe_table", "expected_outcome", "scenario_labels", "eval_only")
    if isinstance(payload, dict):
        payload_keys = set(payload.keys())
        if payload_keys:
            allowed_surface_keys = {
                "surface_schema_version",
                "observation_id",
                "world_time_ref",
                "source_authority",
                "hidden_eval_excluded",
                "body",
                "inventory",
                "visible_objects",
                "action_space",
                "previous_effect_refs",
            }
            if payload_keys - allowed_surface_keys:
                extra = payload_keys - allowed_surface_keys
                if any(any(marker in key for marker in forbidden) for key in extra):
                    return True
        return any(marker in _flat(payload) for marker in forbidden)
    text = _flat(payload)
    return any(token in text for token in forbidden)


def hidden_map_fed_to_subject_tick(payload: object, hidden_object_ref: str) -> bool:
    return hidden_object_ref.lower() in _flat(payload)


def raw_action_submitted_to_world(submission_input: object) -> bool:
    return not isinstance(submission_input, PublishedActionEnvelope)


def invalid_ap01_decision_submitted(
    *,
    decision_statuses: tuple[str, ...],
    world_submission_attempted: bool,
) -> bool:
    if not world_submission_attempted:
        return False
    allowed = {"published"}
    return not set(decision_statuses).issubset(allowed)


def multiple_requests_auto_selected(
    *,
    published_request_count: int,
    world_submission_attempted: bool,
    reject_multiple_published_requests: bool,
) -> bool:
    if published_request_count <= 1:
        return False
    return world_submission_attempted or (not reject_multiple_published_requests)


def effect_not_correlated_to_request(effect: ActionEffectFrame | None) -> bool:
    if effect is None:
        return False
    status = str(getattr(effect.correlation_status, "value", effect.correlation_status))
    if status != CorrelationStatus.CORRELATED_TO_REQUEST.value:
        return True
    return not effect.request_ref or not effect.envelope_ref


def effect_not_fed_to_next_observation(
    *,
    effect_id: str | None,
    next_previous_effect_refs: tuple[str, ...],
) -> bool:
    if effect_id is None:
        return False
    return effect_id not in next_previous_effect_refs


def observation_mutates_world(*, world_tick_before: int, world_tick_after_observe_only: int) -> bool:
    return world_tick_after_observe_only != world_tick_before


def no_candidate_executes_action(
    *,
    ap01_candidate_count: int,
    world_submission_attempted: bool,
) -> bool:
    return ap01_candidate_count == 0 and world_submission_attempted


def request_as_success_or_completion_bridge(
    *,
    envelope_created: bool,
    world_effect_status: str | None,
    bridge_claims_completion: bool,
) -> bool:
    if bridge_claims_completion and world_effect_status is None:
        return True
    return envelope_created and bridge_claims_completion and world_effect_status != "succeeded"


def world_effect_as_competence_oracle(
    *,
    world_effect_status: str | None,
    bridge_claims_autonomy: bool,
) -> bool:
    return bool(world_effect_status) and bridge_claims_autonomy


def subject_tick_not_used(
    subject_tick_used: bool | None = None,
    *,
    ap01_published_request_count: int = 0,
    envelope_created: bool = False,
    world_submission_attempted: bool = False,
    world_effect_id: str | None = None,
    subject_tick_result_ref: str | None = None,
    record: object | None = None,
) -> bool:
    if record is not None:
        subject_tick_used = bool(getattr(record, "subject_tick_used", False))
        ap01_published_request_count = int(getattr(record, "ap01_published_request_count", 0))
        envelope_created = bool(getattr(record, "envelope_created", False))
        world_submission_attempted = bool(getattr(record, "world_submission_attempted", False))
        world_effect_id = getattr(record, "world_effect_id", None)
        subject_tick_result_ref = getattr(record, "subject_tick_result_ref", None)

    if subject_tick_used is None:
        return True

    # Preserve legacy boolean mode when no additional consistency context is supplied.
    if (
        ap01_published_request_count == 0
        and envelope_created is False
        and world_submission_attempted is False
        and world_effect_id is None
        and subject_tick_result_ref is None
    ):
        return not subject_tick_used

    active_downstream = (
        ap01_published_request_count > 0
        or envelope_created
        or world_submission_attempted
        or world_effect_id is not None
    )
    if active_downstream and not subject_tick_used:
        return True
    if subject_tick_used and not subject_tick_result_ref:
        return True
    return False


def candidate_provider_uses_hidden_or_eval(provider_trace_payload: object) -> bool:
    if isinstance(provider_trace_payload, dict):
        text = _flat(provider_trace_payload)
        return any(
            token in text
            for token in (
                "expected_outcome",
                "hidden_objects",
                "hidden_inventory",
                "scenario_to_action",
                "select_action_by_scenario",
            )
        )

    no_hidden = getattr(provider_trace_payload, "no_hidden_truth_used", True)
    no_eval = getattr(provider_trace_payload, "no_eval_only_used", True)
    no_scenario = getattr(provider_trace_payload, "no_scenario_label_used", True)
    if (not no_hidden) or (not no_eval) or (not no_scenario):
        return True

    text = _flat(provider_trace_payload)
    return any(
        token in text
        for token in (
            "expected_outcome",
            "hidden_objects",
            "hidden_inventory",
            "scenario_to_action",
            "select_action_by_scenario",
        )
    )


def public_trace_contains_eval_only(public_trace_payload: object) -> bool:
    forbidden = ("hidden_objects", "hidden_inventory", "true_recipe_table", "expected_outcome", "scenario_labels")
    if isinstance(public_trace_payload, dict):
        run_payload = public_trace_payload.get("run", public_trace_payload)
        if not isinstance(run_payload, dict):
            run_payload = {}
        eval_scope = run_payload.get("eval_only")
        for step in run_payload.get("steps", ()) if isinstance(run_payload.get("steps"), (list, tuple)) else ():
            if any(token in _flat(step) for token in forbidden):
                return True
        if eval_scope in (None, {}, (), []):
            return False
        if not isinstance(eval_scope, dict):
            return True
        return False

    eval_only_value = getattr(public_trace_payload, "eval_only", None)
    steps = getattr(public_trace_payload, "steps", ())
    for step in steps:
        if any(token in _flat(step) for token in forbidden):
            return True
    if eval_only_value in (None, {}, (), []):
        return False
    return not isinstance(eval_only_value, dict)


def bridge_directly_mutates_world(*, world_mutation_surface: str) -> bool:
    allowed = {"submit_action"}
    return world_mutation_surface not in allowed


def bridge_chooses_action_from_scenario_id(payload: object) -> bool:
    markers = ("scenario_id", "scenario:", "scenario_to_action", "select_action_by_scenario")

    def _contains_marker(value: object) -> bool:
        text = _flat(value)
        return any(marker in text for marker in markers)

    if isinstance(payload, dict):
        if "scenario_to_action" in payload or "select_action_by_scenario" in payload:
            return True
        for key in ("action_kind", "target_ref", "intended_effect", "args", "ap01_request_ref", "ap01_request_id"):
            if key in payload and _contains_marker(payload[key]):
                return True
        return False

    if hasattr(payload, "plans_by_tick"):
        plans_by_tick = getattr(payload, "plans_by_tick", {})
        for specs in plans_by_tick.values():
            for spec in specs:
                if _contains_marker(getattr(spec, "action_kind", "")):
                    return True
                if _contains_marker(getattr(spec, "target_ref", "")):
                    return True
                if _contains_marker(getattr(spec, "intended_effect", "")):
                    return True
                if _contains_marker(getattr(spec, "args", {})):
                    return True
        return False

    if hasattr(payload, "steps"):
        for step in getattr(payload, "steps", ()):
            envelope_payload = getattr(step, "envelope_payload", None)
            if envelope_payload and bridge_chooses_action_from_scenario_id(envelope_payload):
                return True
        return False

    return "scenario_to_action" in _flat(payload) or "select_action_by_scenario" in _flat(payload)


def candidate_from_scenario_id(candidate_payload: object) -> bool:
    sections = _decision_bearing_sections(candidate_payload)
    return _contains_forbidden_marker_in_sections(
        sections,
        markers=FORBIDDEN_SCENARIO_ACTION_BASIS_MARKERS,
        path_prefix="candidate_basis",
    )


def candidate_from_eval_or_private_data(candidate_payload: object) -> bool:
    sections = _decision_bearing_sections(candidate_payload)
    return _contains_forbidden_marker_in_sections(
        sections,
        markers=FORBIDDEN_PRIVATE_EVAL_BASIS_MARKERS,
        path_prefix="candidate_basis",
    )


def visible_object_alone_creates_pickup(
    *,
    has_visible_object_basis: bool,
    has_internal_drive_basis: bool,
    proposed_action_kind: str | None,
) -> bool:
    return has_visible_object_basis and (not has_internal_drive_basis) and proposed_action_kind == "pickup"


def drive_alone_creates_pickup(
    *,
    has_internal_drive_basis: bool,
    has_visible_object_basis: bool,
    has_action_surface_basis: bool,
    proposed_action_kind: str | None,
) -> bool:
    return (
        has_internal_drive_basis
        and (not has_visible_object_basis)
        and (not has_action_surface_basis)
        and proposed_action_kind == "pickup"
    )


def action_space_alone_creates_candidate(
    *,
    has_action_surface_basis: bool,
    has_internal_drive_basis: bool,
    has_visible_object_basis: bool,
    proposed_action_kind: str | None,
) -> bool:
    return (
        has_action_surface_basis
        and (not has_internal_drive_basis)
        and (not has_visible_object_basis)
        and proposed_action_kind is not None
    )


def pickup_without_proximity_basis(
    *,
    proposed_action_kind: str | None,
    proximity_basis_status: str | None,
) -> bool:
    if proposed_action_kind != "pickup":
        return False
    return proximity_basis_status not in {"available"}


def pickup_without_capacity_basis(
    *,
    proposed_action_kind: str | None,
    capacity_basis_status: str | None,
) -> bool:
    if proposed_action_kind != "pickup":
        return False
    return capacity_basis_status not in {"available"}


def pickup_when_capacity_blocked(
    *,
    proposed_action_kind: str | None,
    capacity_basis_status: str | None,
) -> bool:
    return proposed_action_kind == "pickup" and capacity_basis_status == "blocked"


def candidate_executes_world(payload: object) -> bool:
    text = _flat(payload)
    return "submit_action" in text or "world_effect" in text or "publishedactionenvelope" in text


def candidate_bypasses_ap01(
    *,
    candidate_proposed: bool,
    ap01_published_request_count: int,
    world_submission_attempted: bool,
) -> bool:
    return candidate_proposed and world_submission_attempted and ap01_published_request_count <= 0


def ap01_publication_without_acp01_basis(
    *,
    ap01_candidate_source: str,
    ap01_published_request_count: int,
    acp01_proposed_count: int,
) -> bool:
    return (
        ap01_candidate_source == "acp01_internal"
        and ap01_published_request_count > 0
        and acp01_proposed_count <= 0
    )


def previous_effect_as_success_oracle(
    *,
    only_previous_effect_basis: bool,
    proposed_action_kind: str | None,
) -> bool:
    return only_previous_effect_basis and proposed_action_kind is not None


def blocked_effect_auto_alternative_action(
    *,
    previous_effect_status: str | None,
    revalidation_required: bool,
    proposed_action_kind: str | None,
) -> bool:
    return (
        previous_effect_status in {"blocked", "failed"}
        and (not revalidation_required)
        and proposed_action_kind in {"turn_left", "turn_right", "move_forward", "move_backward"}
    )


def inspect_as_pickup_shortcut(
    *,
    previous_action_kind: str | None,
    current_action_kind: str | None,
    new_evidence_present: bool,
) -> bool:
    return previous_action_kind == "inspect" and current_action_kind == "pickup" and not new_evidence_present


def station_visibility_as_use_candidate(
    *,
    station_visible: bool,
    has_drive_basis: bool,
    has_capability_basis: bool,
    proposed_action_kind: str | None,
) -> bool:
    return station_visible and proposed_action_kind == "use_station" and ((not has_drive_basis) or (not has_capability_basis))


def recipe_or_automation_candidate_in_p4(proposed_action_kind: str | None) -> bool:
    return proposed_action_kind in {"craft", "refine", "filter", "research", "automation"}


def bridge_calls_acp01_policy_directly(source_text: str) -> bool:
    lowered = source_text.lower()
    if "execute_subject_tick" not in lowered:
        return True
    return "build_acp01_internal_action_candidates" in lowered


def manual_provider_used_in_internal_mode(
    *,
    use_internal_candidate_producer: bool,
    manual_candidate_input: bool,
) -> bool:
    return use_internal_candidate_producer and manual_candidate_input


def public_payload_eval_scope_violation(payload: object) -> bool:
    if not isinstance(payload, dict):
        return eval_truth_fed_to_subject_tick(payload)
    allowed_sections = {
        "surface_schema_version",
        "observation_id",
        "world_time_ref",
        "source_authority",
        "hidden_eval_excluded",
        "body",
        "inventory",
        "visible_objects",
        "action_space",
        "previous_effect_refs",
    }
    if any(key not in allowed_sections for key in payload):
        return True
    scoped_sections = {
        "body": {
            "body_ref": payload.get("body", {}).get("body_ref"),
            "location_ref": payload.get("body", {}).get("location_ref"),
            "orientation": payload.get("body", {}).get("orientation"),
            "posture_status": payload.get("body", {}).get("posture_status"),
            "actuator_status": payload.get("body", {}).get("actuator_status"),
        },
        "inventory": {
            "inventory_ref": payload.get("inventory", {}).get("inventory_ref"),
            "used_slots": payload.get("inventory", {}).get("used_slots"),
            "capacity_slots": payload.get("inventory", {}).get("capacity_slots"),
            "item_refs": payload.get("inventory", {}).get("item_refs"),
            "item_counts": payload.get("inventory", {}).get("item_counts"),
        },
        "visible_objects": payload.get("visible_objects", ()),
        "action_space": {
            "allowed_action_kinds_from_body": payload.get("action_space", {}).get("allowed_action_kinds_from_body"),
            "available_surfaces": payload.get("action_space", {}).get("available_surfaces"),
            "action_space_is_permission": payload.get("action_space", {}).get("action_space_is_permission"),
            "action_space_is_selection": payload.get("action_space", {}).get("action_space_is_selection"),
            "action_space_is_execution": payload.get("action_space", {}).get("action_space_is_execution"),
        },
        "previous_effect_refs": payload.get("previous_effect_refs", ()),
    }
    return _contains_forbidden_marker_in_sections(
        scoped_sections,
        markers=FORBIDDEN_PRIVATE_EVAL_BASIS_MARKERS + FORBIDDEN_SCENARIO_ACTION_BASIS_MARKERS,
        path_prefix="subject_tick_surface_payload",
    )


def candidate_without_provenance_refs(candidate_payload: object) -> bool:
    if isinstance(candidate_payload, dict):
        refs = candidate_payload.get("basis_refs")
        if not refs:
            return True
        text = _flat(refs)
        required = ("observation:", "drive:", "surface:", "capability:")
        return not all(token in text for token in required)
    text = _flat(candidate_payload)
    return "basis_refs" not in text


def _decision_bearing_sections(candidate_payload: object) -> dict[str, object]:
    if isinstance(candidate_payload, dict):
        decision_keys = {
            "candidate_id",
            "action_kind",
            "target_ref",
            "args",
            "intended_effect",
            "basis_refs",
            "missing_basis",
            "blocked_basis",
            "resource_or_goal_ref",
            "drive_kind",
            "drive_ref",
            "public_properties",
            "forbidden_basis_markers",
            "source_tick_ref",
            "source_phase_refs",
            "permission_refs",
            "evidence_refs",
            "affordance_binding_refs",
            "reason_codes",
            "visible_object_bases",
            "internal_drive_bases",
            "action_surface_bases",
            "capability_bases",
            "effect_feedback_bases",
            "candidate_set_for_ap01",
        }
        return {key: value for key, value in candidate_payload.items() if key in decision_keys}

    if hasattr(candidate_payload, "__dataclass_fields__"):
        serial = asdict(candidate_payload)
        return _decision_bearing_sections(serial)

    return {
        "raw": candidate_payload,
    }


def _contains_forbidden_marker_in_sections(
    sections: object,
    *,
    markers: tuple[str, ...],
    path_prefix: str,
) -> bool:
    return _scan_sections_for_markers(sections, markers=markers, path=path_prefix)


def _scan_sections_for_markers(value: object, *, markers: tuple[str, ...], path: str) -> bool:
    if value is None:
        return False
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in markers):
                return True
            if _scan_sections_for_markers(item, markers=markers, path=f"{path}.{key}"):
                return True
        return False
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(
            _scan_sections_for_markers(item, markers=markers, path=f"{path}[{idx}]")
            for idx, item in enumerate(value)
        )
    text = str(value).lower()
    return any(marker in text for marker in markers)
