from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

try:
    from substrate.ap01_subject_action_publication import AP01DecisionStatus, AP01SubjectActionRequestPacket
    from substrate.subject_tick import SubjectTickContext, SubjectTickInput
    from substrate.subject_tick.update import execute_subject_tick
    from substrate.world_adapter.models import (
        WorldActionPacket,
        WorldAdapterInput,
        WorldEffectObservationPacket,
        WorldObservationPacket,
    )
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from substrate.ap01_subject_action_publication import AP01DecisionStatus, AP01SubjectActionRequestPacket
    from substrate.subject_tick import SubjectTickContext, SubjectTickInput
    from substrate.subject_tick.update import execute_subject_tick
    from substrate.world_adapter.models import (
        WorldActionPacket,
        WorldAdapterInput,
        WorldEffectObservationPacket,
        WorldObservationPacket,
    )

from experiments.embodied_playground.bridge_trace import (
    BridgeTickRecord,
    BridgeVerdict,
    SubjectWorldBridgeConfig,
    SubjectWorldBridgeRun,
)
from experiments.embodied_playground.candidate_provider import CandidateProvider
from experiments.embodied_playground.grid_world import GridWorldBackend, build_grid_world_backend
from experiments.embodied_playground.models import (
    AP01RequestRef,
    ActionEffectFrame,
    ObservationFrame,
    PublishedActionEnvelope,
)


def run_subject_world_bridge(
    *,
    scenario_id: str,
    config: SubjectWorldBridgeConfig,
    candidate_provider: CandidateProvider | None = None,
    backend: GridWorldBackend | None = None,
) -> SubjectWorldBridgeRun:
    world = backend or build_grid_world_backend(scenario_id=scenario_id, subject_id=config.subject_id)

    records: list[BridgeTickRecord] = []
    world_submissions_count = 0
    world_effect_count = 0
    no_candidate_no_execution_count = 0
    rejected_multiple_requests_count = 0
    subject_tick_used_any = False

    prior_action_packet: WorldActionPacket | None = None
    prior_effect_packet: WorldEffectObservationPacket | None = None

    for bridge_tick_index in range(1, config.max_ticks + 1):
        observation_before = world.observe(config.subject_id)
        action_space_before = world.action_space(config.subject_id)

        candidate_set = None
        manual_candidate_input = False
        if candidate_provider is not None and config.allow_manual_candidate_provider:
            candidate_set = candidate_provider.provide_candidates(
                bridge_tick_index=bridge_tick_index,
                observation=observation_before,
                action_space=action_space_before,
            )
            manual_candidate_input = candidate_set is not None

        tick_input, tick_context, subject_tick_surface_payload = _build_subject_tick_surfaces(
            bridge_tick_index=bridge_tick_index,
            observation=observation_before,
            action_packet=prior_action_packet,
            effect_packet=prior_effect_packet,
            candidate_set=candidate_set,
        )

        tick_result = None
        subject_tick_used = False
        subject_tick_result_ref: str | None = None
        try:
            tick_result = execute_subject_tick(tick_input, tick_context)
            subject_tick_used = True
            subject_tick_used_any = True
            subject_tick_result_ref = tick_result.state.tick_id
        except Exception as exc:
            observation_after = world.observe(config.subject_id)
            records.append(
                BridgeTickRecord(
                    bridge_tick_index=bridge_tick_index,
                    world_tick_before=observation_before.tick_index,
                    observation_id=observation_before.observation_id,
                    observation_previous_effect_refs=observation_before.previous_effect_refs,
                    subject_tick_surface_payload=subject_tick_surface_payload,
                    action_space_frame_id=action_space_before.frame_id,
                    subject_tick_used=subject_tick_used,
                    subject_tick_result_ref=subject_tick_result_ref,
                    ap01_candidate_count=0,
                    ap01_published_request_count=0,
                    ap01_blocked_count=0,
                    ap01_revalidation_required_count=0,
                    ap01_unsafe_basis_count=0,
                    ap01_request_ref=None,
                    envelope_created=False,
                    envelope_ref=None,
                    envelope_payload=None,
                    world_submission_attempted=False,
                    world_effect_id=None,
                    world_effect_status=None,
                    correlation_status=None,
                    world_effect_payload=None,
                    world_tick_after=observation_after.tick_index,
                    next_observation_id=observation_after.observation_id,
                    hidden_eval_excluded=True,
                    direct_phase_calls_detected=False,
                    bridge_chose_action=False,
                    manual_candidate_input=manual_candidate_input,
                    autonomous_action_selection=False,
                    verdict=BridgeVerdict.BRIDGE_ERROR,
                    subject_tick_error=str(exc),
                )
            )
            no_candidate_no_execution_count += 1
            continue

        ap01_result = tick_result.ap01_result
        telemetry = ap01_result.telemetry
        published_requests = ap01_result.published_requests

        envelope: PublishedActionEnvelope | None = None
        world_effect: ActionEffectFrame | None = None
        world_submission_attempted = False

        if config.execute_world_actions:
            if len(published_requests) == 1:
                request = published_requests[0]
                if _request_is_publishable(ap01_result.decisions, request.request_id):
                    envelope = _published_request_to_envelope(
                        subject_id=config.subject_id,
                        request=request,
                        bridge_tick_index=bridge_tick_index,
                    )
                    world_effect = world.submit_action(envelope)
                    world_submission_attempted = True
                    world_submissions_count += 1
                    world_effect_count += 1
                    prior_action_packet = _action_packet_from_envelope(envelope)
                    prior_effect_packet = _effect_packet_from_effect(world_effect)
            elif len(published_requests) > 1 and config.reject_multiple_published_requests:
                rejected_multiple_requests_count += 1
            elif len(published_requests) == 0:
                no_candidate_no_execution_count += 1
        else:
            if len(published_requests) == 0:
                no_candidate_no_execution_count += 1

        observation_after = world.observe(config.subject_id)

        if world_effect is not None:
            verdict = BridgeVerdict.WORLD_EFFECT_OBSERVED
        elif len(published_requests) > 1 and config.reject_multiple_published_requests:
            verdict = BridgeVerdict.MULTIPLE_REQUESTS_REJECTED
        else:
            verdict = _verdict_from_decisions(ap01_result.decisions)

        record = BridgeTickRecord(
            bridge_tick_index=bridge_tick_index,
            world_tick_before=observation_before.tick_index,
            observation_id=observation_before.observation_id,
            observation_previous_effect_refs=observation_before.previous_effect_refs,
            subject_tick_surface_payload=subject_tick_surface_payload,
            action_space_frame_id=action_space_before.frame_id,
            subject_tick_used=subject_tick_used,
            subject_tick_result_ref=subject_tick_result_ref,
            ap01_candidate_count=telemetry.candidate_count,
            ap01_published_request_count=telemetry.published_request_count,
            ap01_blocked_count=telemetry.blocked_count,
            ap01_revalidation_required_count=telemetry.revalidation_required_count,
            ap01_unsafe_basis_count=telemetry.unsafe_basis_count,
            ap01_request_ref=(published_requests[0].request_id if len(published_requests) == 1 else None),
            envelope_created=envelope is not None,
            envelope_ref=(envelope.envelope_id if envelope is not None else None),
            envelope_payload=(asdict(envelope) if envelope is not None else None),
            world_submission_attempted=world_submission_attempted,
            world_effect_id=(world_effect.effect_id if world_effect is not None else None),
            world_effect_status=(
                str(getattr(world_effect.effect_status, "value", world_effect.effect_status))
                if world_effect is not None
                else None
            ),
            correlation_status=(
                str(getattr(world_effect.correlation_status, "value", world_effect.correlation_status))
                if world_effect is not None
                else None
            ),
            world_effect_payload=(asdict(world_effect) if world_effect is not None else None),
            world_tick_after=observation_after.tick_index,
            next_observation_id=observation_after.observation_id,
            hidden_eval_excluded=True,
            direct_phase_calls_detected=False,
            bridge_chose_action=False,
            manual_candidate_input=manual_candidate_input,
            autonomous_action_selection=False,
            verdict=verdict,
        )
        records.append(record)

    final_observation = world.observe(config.subject_id)
    eval_only_payload: dict[str, object] | None = None
    if config.include_eval_only:
        eval_only_payload = asdict(world.eval_snapshot())

    return SubjectWorldBridgeRun(
        run_id=f"bridge-run:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        subject_id=config.subject_id,
        bridge_stage="p3_subject_world_bridge",
        steps=tuple(records),
        final_observation_id=final_observation.observation_id,
        subject_tick_used_any=subject_tick_used_any,
        world_submissions_count=world_submissions_count,
        world_effect_count=world_effect_count,
        no_candidate_no_execution_count=no_candidate_no_execution_count,
        rejected_multiple_requests_count=rejected_multiple_requests_count,
        hidden_eval_excluded=True,
        autonomous_action_selection=False,
        eval_only=eval_only_payload,
    )


def _request_is_publishable(decisions: tuple[Any, ...], request_id: str) -> bool:
    for decision in decisions:
        if decision.published_request is None:
            continue
        if decision.published_request.request_id != request_id:
            continue
        return decision.decision_status is AP01DecisionStatus.PUBLISHED
    return False


def _verdict_from_decisions(decisions: tuple[Any, ...]) -> BridgeVerdict:
    if not decisions:
        return BridgeVerdict.NO_CANDIDATE_NO_EXECUTION
    statuses = {decision.decision_status for decision in decisions}
    if AP01DecisionStatus.PUBLISHED in statuses:
        return BridgeVerdict.REQUEST_PUBLISHED_AND_SUBMITTED
    if AP01DecisionStatus.BLOCKED in statuses:
        return BridgeVerdict.REQUEST_BLOCKED_NO_EXECUTION
    if AP01DecisionStatus.REVALIDATION_REQUIRED in statuses:
        return BridgeVerdict.REQUEST_REVALIDATION_NO_EXECUTION
    if AP01DecisionStatus.UNSAFE_BASIS in statuses:
        return BridgeVerdict.UNSAFE_CANDIDATE_REJECTED
    return BridgeVerdict.NO_CANDIDATE_NO_EXECUTION


def _published_request_to_envelope(
    *,
    subject_id: str,
    request: AP01SubjectActionRequestPacket,
    bridge_tick_index: int,
) -> PublishedActionEnvelope:
    return PublishedActionEnvelope(
        envelope_id=f"bridge:envelope:{bridge_tick_index}:{request.request_id}",
        subject_id=subject_id,
        ap01_request_ref=AP01RequestRef(request_ref=f"ap01_request:{request.request_id}"),
        action_kind=request.action_kind,
        target_ref=request.target_ref,
        args=dict(request.args),
        intended_effect=request.intended_effect,
        source_tick_ref=request.source_tick_ref,
        source_phase_refs=request.source_phase_refs,
        permission_refs=request.permission_refs,
        evidence_refs=request.evidence_refs,
        affordance_binding_refs=request.affordance_binding_refs,
        request_boundary_preserved=True,
        submitted_to_world=False,
        executed_by_world=False,
        no_hidden_truth_used=request.no_hidden_truth_used,
        no_eval_only_used=request.no_eval_only_used,
        no_scenario_label_used=request.no_scenario_label_used,
    )


def _action_packet_from_envelope(envelope: PublishedActionEnvelope) -> WorldActionPacket:
    return WorldActionPacket(
        action_id=envelope.envelope_id,
        action_kind=envelope.action_kind,
        target_ref=envelope.target_ref or "target:none",
        requested_at=datetime.now(tz=timezone.utc).isoformat(),
        payload_ref=envelope.ap01_request_id,
        provenance="embodied_playground.subject_world_bridge",
    )


def _effect_packet_from_effect(effect: ActionEffectFrame) -> WorldEffectObservationPacket:
    effect_status = str(getattr(effect.effect_status, "value", effect.effect_status))
    return WorldEffectObservationPacket(
        effect_id=effect.effect_id,
        action_id=effect.envelope_ref or "action:none",
        effect_kind=effect_status,
        observed_at=datetime.now(tz=timezone.utc).isoformat(),
        success=effect_status == "succeeded",
        source_ref="grid_world_backend",
        provenance="embodied_playground.subject_world_bridge",
    )


def _build_subject_tick_surfaces(
    *,
    bridge_tick_index: int,
    observation: ObservationFrame,
    action_packet: WorldActionPacket | None,
    effect_packet: WorldEffectObservationPacket | None,
    candidate_set: Any,
) -> tuple[SubjectTickInput, SubjectTickContext, dict[str, object]]:
    public_payload = _build_public_subject_tick_surface_payload(observation)
    observed_at = observation.world_time_ref or datetime.now(tz=timezone.utc).isoformat()
    world_adapter_input = WorldAdapterInput(
        adapter_presence=True,
        adapter_available=True,
        adapter_degraded=False,
        observation_packet=WorldObservationPacket(
            observation_id=observation.observation_id,
            observation_kind="embodied_observation_frame",
            source_ref=observation.source_authority,
            observed_at=observed_at,
            payload_ref=observation.observation_id,
            provenance="embodied_playground.grid_world_backend",
        ),
        action_packet=action_packet,
        effect_packet=effect_packet,
        source_lineage=("embodied_playground.p3.subject_bridge",),
        reason="p3_subject_world_bridge_world_adapter_input",
    )

    tick_input = SubjectTickInput(
        case_id=f"epg_p3_bridge_tick_{bridge_tick_index}",
        energy=70.0,
        cognitive=55.0,
        safety=70.0,
        unresolved_preference=False,
        epistemic_content=json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
        epistemic_source_id=f"observation:{observation.observation_id}",
        epistemic_source_class="observation",
        epistemic_modality="sensor",
        epistemic_confidence_hint="high",
        epistemic_support_note=f"observation_ref:{observation.observation_id}",
    )
    tick_context = SubjectTickContext(
        world_adapter_input=world_adapter_input,
        ap01_action_publication_candidate_set=candidate_set,
        source_lineage=("embodied_playground.p3.subject_bridge",),
    )
    return tick_input, tick_context, public_payload


def _build_public_subject_tick_surface_payload(observation: ObservationFrame) -> dict[str, object]:
    body = observation.body_state
    inventory = observation.inventory_state
    action_space = observation.action_space
    visible_objects = tuple(
        {
            "object_ref": obj.object_ref,
            "object_kind": str(getattr(obj.object_kind, "value", obj.object_kind)),
            "location_ref": obj.location_ref,
            "relation_to_subject": obj.relation_to_subject,
            "observable_properties": dict(obj.observable_properties),
        }
        for obj in observation.visible_objects
    )
    available_surfaces = tuple(
        {
            "surface_ref": surface.surface_ref,
            "surface_kind": str(getattr(surface.surface_kind, "value", surface.surface_kind)),
            "target_ref": surface.target_ref,
            "action_kinds": tuple(surface.action_kinds),
            "constraints": tuple(surface.constraints),
        }
        for surface in action_space.available_surfaces
    )
    return {
        "surface_schema_version": "p3_public_observation_v1",
        "observation_id": observation.observation_id,
        "world_time_ref": observation.world_time_ref,
        "source_authority": observation.source_authority,
        "hidden_eval_excluded": True,
        "body": {
            "body_ref": body.body_ref,
            "location_ref": body.location_ref,
            "orientation": str(getattr(body.orientation, "value", body.orientation)),
            "posture_status": str(getattr(body.posture_status, "value", body.posture_status)),
            "actuator_status": str(getattr(body.actuator_status, "value", body.actuator_status)),
        },
        "inventory": {
            "inventory_ref": inventory.inventory_ref,
            "used_slots": inventory.used_slots,
            "capacity_slots": inventory.capacity_slots,
            "item_refs": tuple(inventory.item_refs),
            "item_counts": dict(inventory.item_counts),
        },
        "visible_objects": visible_objects,
        "action_space": {
            "frame_id": action_space.frame_id,
            "allowed_action_kinds_from_body": tuple(action_space.allowed_action_kinds_from_body),
            "available_surfaces": available_surfaces,
            "action_space_is_permission": action_space.action_space_is_permission,
            "action_space_is_selection": action_space.action_space_is_selection,
            "action_space_is_execution": action_space.action_space_is_execution,
        },
        "previous_effect_refs": tuple(observation.previous_effect_refs),
    }
