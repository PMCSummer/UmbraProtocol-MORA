from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from experiments.embodied_playground.body_action_proof import BodyActionProofRun

_SCENARIO_MARKERS: tuple[str, ...] = (
    "scenario:",
    "scenario_id",
    "test_label",
    "select_action_by_scenario",
    "scenario_to_action",
)
_OVERCLAIM_TERMS: tuple[str, ...] = (
    "planning",
    "general autonomy",
    "consciousness",
    "human-like motor control",
    "motor intelligence",
    "understands physical space",
)
_CAUTION_GUARDS: tuple[str, ...] = (
    "no planning",
    "not planning",
    "no general autonomy",
    "not general autonomy",
    "does not prove autonomy",
    "no consciousness",
    "not consciousness",
    "does not prove consciousness",
    "no human-like motor control",
    "not human-like motor control",
)


def manual_provider_used_in_internal_body_action(run: BodyActionProofRun) -> bool:
    return run.manual_provider_used or any(step.manual_candidate_input for step in run.bridge_run.steps)


def internal_pickup_without_basis(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_pickup_step(step):
            continue
        payload = step.subject_tick_surface_payload
        has_drive = bool(_drive_refs_from_step(step))
        has_visible_object = bool(payload.get("visible_objects"))
        has_surface = _surface_supports_action(payload, "pickup")
        has_proximity = _capability_present(step, "capability:proximity:")
        has_capacity = _capability_present(step, "capability:inventory_capacity")
        if not (has_drive and has_visible_object and has_surface and has_proximity and has_capacity):
            return True
    return False


def internal_move_without_body_basis(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_action_kind(step, "move_forward"):
            continue
        payload = step.subject_tick_surface_payload
        body = payload.get("body", {})
        has_body = bool(body.get("body_ref")) and bool(body.get("location_ref"))
        has_surface = _surface_supports_action(payload, "move_forward")
        if not has_body or not has_surface:
            return True
    return False


def internal_turn_without_body_basis(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not (_is_action_kind(step, "turn_left") or _is_action_kind(step, "turn_right")):
            continue
        payload = step.subject_tick_surface_payload
        body = payload.get("body", {})
        has_body = bool(body.get("body_ref")) and bool(body.get("orientation"))
        has_surface = _surface_supports_action(payload, "turn_left") or _surface_supports_action(payload, "turn_right")
        if not has_body or not has_surface:
            return True
    return False


def internal_drop_without_inventory_basis(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_action_kind(step, "drop"):
            continue
        payload = step.subject_tick_surface_payload
        inventory = payload.get("inventory", {})
        item_counts = inventory.get("item_counts", {})
        has_inventory_item = any(int(v) > 0 for v in item_counts.values()) if isinstance(item_counts, dict) else False
        if not has_inventory_item:
            return True
    return False


def body_delta_without_effect(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not step.world_effect_payload:
            continue
        body_delta = dict(step.world_effect_payload.get("body_delta", {}))
        if body_delta and not step.world_effect_id:
            return True
    return False


def inventory_delta_without_effect(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not step.world_effect_payload:
            continue
        inventory_delta = dict(step.world_effect_payload.get("inventory_delta", {}))
        if inventory_delta and not step.world_effect_id:
            return True
    return False


def world_object_delta_without_effect(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not step.world_effect_payload:
            continue
        world_delta = dict(step.world_effect_payload.get("world_delta_public", {}))
        if world_delta and not step.world_effect_id:
            return True
    return False


def movement_through_wall_as_success(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_action_kind(step, "move_forward"):
            continue
        if step.world_effect_status != "blocked":
            continue
        payload = step.world_effect_payload or {}
        body_delta = dict(payload.get("body_delta", {}))
        if body_delta:
            return True
    return False


def pickup_without_proximity_basis(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_pickup_step(step):
            continue
        if step.ap01_published_request_count <= 0:
            continue
        if not _capability_present(step, "capability:proximity:"):
            return True
    return False


def pickup_without_capacity_basis(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_pickup_step(step):
            continue
        if step.ap01_published_request_count <= 0:
            continue
        if not _capability_present(step, "capability:inventory_capacity"):
            return True
    return False


def pickup_hidden_eval_object(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_pickup_step(step):
            continue
        envelope_payload = step.envelope_payload or {}
        target_ref = str(envelope_payload.get("target_ref", "")).lower()
        if any(marker in target_ref for marker in ("hidden", "eval", "private", "scenario:")):
            return True
    return False


def visible_object_alone_pickup(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_pickup_step(step):
            continue
        if step.ap01_published_request_count <= 0:
            continue
        if not _drive_refs_from_step(step):
            return True
    return False


def drive_alone_pickup(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not _is_pickup_step(step):
            continue
        if step.ap01_published_request_count <= 0:
            continue
        payload = step.subject_tick_surface_payload
        has_visible = bool(payload.get("visible_objects"))
        has_surface = _surface_supports_action(payload, "pickup")
        if not has_visible or not has_surface:
            return True
    return False


def action_space_alone_body_action(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if step.ap01_published_request_count <= 0:
            continue
        payload = step.subject_tick_surface_payload
        if not payload.get("visible_objects") and not _drive_refs_from_step(step):
            return True
    return False


def request_as_body_effect(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        envelope_payload = step.envelope_payload or {}
        if isinstance(envelope_payload, dict):
            if any(
                key in envelope_payload
                for key in ("body_delta", "inventory_delta", "world_delta_public")
            ):
                return True
        if step.ap01_published_request_count > 0 and step.world_submission_attempted and step.world_effect_payload is None:
            return True
    return False


def effect_as_completion_oracle(run: BodyActionProofRun) -> bool:
    claim_text = f"{run.claim_boundary}".lower()
    if any(term in claim_text for term in _OVERCLAIM_TERMS) and not any(
        guard in claim_text for guard in _CAUTION_GUARDS
    ):
        return True
    for step in run.bridge_run.steps:
        envelope_payload = step.envelope_payload or {}
        if isinstance(envelope_payload, dict):
            completion_keys = ("completion", "completion_claim", "competence", "autonomy_claim")
            if any(key in envelope_payload for key in completion_keys):
                return True
        verdict_value = str(step.verdict.value).lower()
        if "completion" in verdict_value or "competence" in verdict_value or "autonomy" in verdict_value:
            return True
    return False


def scenario_label_body_action_selection(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        envelope_payload = step.envelope_payload or {}
        action_kind = str(envelope_payload.get("action_kind", "")).lower() if isinstance(envelope_payload, dict) else ""
        target_ref = str(envelope_payload.get("target_ref", "")).lower() if isinstance(envelope_payload, dict) else ""
        args = envelope_payload.get("args", {}) if isinstance(envelope_payload, dict) else {}
        evidence_refs = tuple(envelope_payload.get("evidence_refs", ())) if isinstance(envelope_payload, dict) else ()
        candidate_source = str(step.candidate_source).lower()
        reason_codes = tuple(str(item).lower() for item in getattr(step, "ap01_decision_reason_codes", ()))
        decision_fields: tuple[str, ...] = (
            action_kind,
            target_ref,
            candidate_source,
            str(args).lower(),
            str(evidence_refs).lower(),
            str(reason_codes).lower(),
        )
        if any(any(marker in value for marker in _SCENARIO_MARKERS) for value in decision_fields):
            return True
    return False


def body_action_bypasses_ap01(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if not step.world_submission_attempted:
            continue
        if (
            step.ap01_published_request_count <= 0
            or not step.ap01_request_ref
            or not step.envelope_ref
        ):
            return True
    return False


def acp01_executes_body_action(run: BodyActionProofRun) -> bool:
    for step in run.bridge_run.steps:
        if step.world_submission_attempted and step.candidate_source == "none":
            return True
        envelope_payload = step.envelope_payload or {}
        if isinstance(envelope_payload, dict) and any(
            key in envelope_payload for key in ("executed", "world_submission", "body_delta", "inventory_delta", "world_delta_public")
        ):
            return True
    return False


def p10_report_overclaims(report_text: str) -> bool:
    lowered = report_text.lower()
    if any(guard in lowered for guard in _CAUTION_GUARDS):
        return False
    return any(token in lowered for token in _OVERCLAIM_TERMS)


def run_p10_falsifier_suite(run: BodyActionProofRun, *, report_text: str = "") -> dict[str, bool]:
    return {
        "manual_provider_used_in_internal_body_action": manual_provider_used_in_internal_body_action(run),
        "internal_pickup_without_basis": internal_pickup_without_basis(run),
        "internal_move_without_body_basis": internal_move_without_body_basis(run),
        "internal_turn_without_body_basis": internal_turn_without_body_basis(run),
        "internal_drop_without_inventory_basis": internal_drop_without_inventory_basis(run),
        "body_delta_without_effect": body_delta_without_effect(run),
        "inventory_delta_without_effect": inventory_delta_without_effect(run),
        "world_object_delta_without_effect": world_object_delta_without_effect(run),
        "movement_through_wall_as_success": movement_through_wall_as_success(run),
        "pickup_without_proximity_basis": pickup_without_proximity_basis(run),
        "pickup_without_capacity_basis": pickup_without_capacity_basis(run),
        "pickup_hidden_eval_object": pickup_hidden_eval_object(run),
        "visible_object_alone_pickup": visible_object_alone_pickup(run),
        "drive_alone_pickup": drive_alone_pickup(run),
        "action_space_alone_body_action": action_space_alone_body_action(run),
        "request_as_body_effect": request_as_body_effect(run),
        "effect_as_completion_oracle": effect_as_completion_oracle(run),
        "scenario_label_body_action_selection": scenario_label_body_action_selection(run),
        "body_action_bypasses_ap01": body_action_bypasses_ap01(run),
        "acp01_executes_body_action": acp01_executes_body_action(run),
        "p10_report_overclaims": p10_report_overclaims(report_text),
    }


def _is_pickup_step(step: object) -> bool:
    return _is_action_kind(step, "pickup")


def _is_action_kind(step: object, action_kind: str) -> bool:
    envelope_payload = getattr(step, "envelope_payload", None) or {}
    if isinstance(envelope_payload, dict):
        return str(envelope_payload.get("action_kind", "")).lower() == action_kind.lower()
    return False


def _surface_supports_action(payload: dict[str, object], action_kind: str) -> bool:
    action_space = payload.get("action_space", {})
    surfaces = action_space.get("available_surfaces", ()) if isinstance(action_space, dict) else ()
    for surface in surfaces if isinstance(surfaces, Iterable) else ():
        if not isinstance(surface, dict):
            continue
        actions = tuple(surface.get("action_kinds", ()))
        if action_kind in actions:
            return True
    return False


def _drive_refs_from_step(step: object) -> tuple[str, ...]:
    envelope_payload = getattr(step, "envelope_payload", None) or {}
    if not isinstance(envelope_payload, dict):
        return ()
    evidence_refs = tuple(envelope_payload.get("evidence_refs", ()))
    return tuple(str(item) for item in evidence_refs if str(item).startswith("drive:"))


def _capability_present(step: object, prefix: str) -> bool:
    envelope_payload = getattr(step, "envelope_payload", None) or {}
    if not isinstance(envelope_payload, dict):
        return False
    evidence_refs = tuple(envelope_payload.get("evidence_refs", ()))
    lowered_prefix = prefix.lower()
    return any(str(item).lower().startswith(lowered_prefix) for item in evidence_refs)
