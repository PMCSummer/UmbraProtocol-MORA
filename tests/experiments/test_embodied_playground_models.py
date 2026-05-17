from __future__ import annotations

from dataclasses import asdict
import pytest

from experiments.embodied_playground.models import (
    AP01RequestRef,
    ActionSpaceFrame,
    AvailableInteractionSurface,
    BodyPostureStatus,
    BodyState,
    CorrelationStatus,
    EffectStatus,
    EvalOnlyWorldTruth,
    InteractionSurfaceKind,
    InventoryKnowledgeStatus,
    InventoryState,
    ObservationFrame,
    Orientation,
    PublishedActionEnvelope,
    PublicWorldSnapshot,
    WorldObjectKind,
    WorldObjectObservation,
    ActionEffectFrame,
)


def _surface() -> AvailableInteractionSurface:
    return AvailableInteractionSurface(
        surface_ref="surface:movement",
        surface_kind=InteractionSurfaceKind.MOVEMENT,
        target_ref=None,
        action_kinds=("move_forward", "turn_left"),
        constraints=("movement_may_be_blocked",),
        affordance_hint_refs=("hint:movement",),
        source_authority="world_backend_public_surface",
    )


def _body(subject_id: str) -> BodyState:
    return BodyState(
        subject_id=subject_id,
        body_ref=f"{subject_id}:body",
        location_ref="location:origin",
        orientation=Orientation.NORTH,
        posture_status=BodyPostureStatus.READY,
        hand_slot=None,
        held_item_ref=None,
        actuator_status="available",
    )


def _inventory(subject_id: str) -> InventoryState:
    return InventoryState(
        inventory_ref=f"{subject_id}:inventory",
        owner_subject_id=subject_id,
        capacity_slots=10,
        used_slots=0,
        item_refs=(),
        item_counts={},
        knowledge_status=InventoryKnowledgeStatus.EMPTY,
    )


def test_models_construct_and_are_asdict_serializable() -> None:
    subject_id = "subject_a"
    body = _body(subject_id)
    inventory = _inventory(subject_id)
    obj = WorldObjectObservation(
        object_ref="object:station",
        object_kind=WorldObjectKind.STATION,
        display_label="station",
        location_ref="location:center",
        relation_to_subject="ahead",
        observable_properties={"state": "visible"},
        source_authority="world_backend_public_observation",
        claim_not_fact_marker=False,
    )
    action_space = ActionSpaceFrame(
        frame_id="as:1",
        subject_id=subject_id,
        tick_index=1,
        available_surfaces=(_surface(),),
        allowed_action_kinds_from_body=("move_forward", "turn_left"),
        body_constraints=(),
    )
    observation = ObservationFrame(
        observation_id="obs:1",
        subject_id=subject_id,
        tick_index=1,
        body_state=body,
        inventory_state=inventory,
        visible_objects=(obj,),
        action_space=action_space,
        previous_effect_refs=(),
        world_time_ref="t:1",
        source_authority="world_backend_public_observation",
    )
    snapshot = PublicWorldSnapshot(
        snapshot_id="pub:1",
        subject_id=subject_id,
        tick_index=1,
        visible_body_state=body,
        visible_inventory_state=inventory,
        visible_objects=(obj,),
        visible_surfaces=(_surface(),),
        public_effect_refs=(),
    )
    eval_truth = EvalOnlyWorldTruth(snapshot_id="eval:1", tick_index=1, expected_outcome="only_eval")
    envelope = PublishedActionEnvelope(
        envelope_id="env:1",
        subject_id=subject_id,
        ap01_request_ref="ap01_request:1",
        action_kind="inspect",
        target_ref="object:station",
        args={"distance": 1},
        intended_effect="inspection",
        source_tick_ref="tick:1",
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:obs",),
        affordance_binding_refs=("A04:bind",),
    )
    effect = ActionEffectFrame(
        effect_id="effect:1",
        subject_id=subject_id,
        tick_index=1,
        request_ref="ap01:req:1",
        envelope_ref="env:1",
        action_kind="inspect",
        target_ref="object:station",
        effect_status=EffectStatus.UNKNOWN,
        body_delta={},
        inventory_delta={},
        world_delta_public={},
        observed_result_refs=("result:unknown",),
        correlation_status=CorrelationStatus.CORRELATED_TO_REQUEST,
    )

    assert body.hidden_truth_excluded is True
    assert inventory.hidden_truth_excluded is True
    assert observation.eval_only_excluded is True
    assert snapshot.hidden_truth_excluded is True
    assert eval_truth.must_never_enter_subject_visible is True
    assert envelope.submitted_to_world is False
    assert envelope.executed_by_world is False
    assert asdict(effect)["action_kind"] == "inspect"
    assert asdict(observation)["action_space"]["action_space_is_permission"] is False
    assert envelope.ap01_request_id == "ap01_request:1"


def test_inventory_state_distinguishes_empty_unknown_full() -> None:
    empty = InventoryState(
        inventory_ref="inv:empty",
        owner_subject_id="s",
        capacity_slots=4,
        used_slots=0,
        item_refs=(),
        item_counts={},
        knowledge_status=InventoryKnowledgeStatus.EMPTY,
    )
    unknown = InventoryState(
        inventory_ref="inv:unknown",
        owner_subject_id="s",
        capacity_slots=4,
        used_slots=0,
        item_refs=(),
        item_counts={},
        knowledge_status=InventoryKnowledgeStatus.UNKNOWN,
    )
    full = InventoryState(
        inventory_ref="inv:full",
        owner_subject_id="s",
        capacity_slots=4,
        used_slots=4,
        item_refs=("item:a",),
        item_counts={"item:a": 4},
        knowledge_status=InventoryKnowledgeStatus.FULL,
    )
    assert empty.knowledge_status == InventoryKnowledgeStatus.EMPTY
    assert unknown.knowledge_status == InventoryKnowledgeStatus.UNKNOWN
    assert full.knowledge_status == InventoryKnowledgeStatus.FULL


def test_published_action_envelope_requires_constrained_ap01_request_ref() -> None:
    with pytest.raises(ValueError):
        PublishedActionEnvelope(
            envelope_id="env:bad",
            subject_id="subject_a",
            ap01_request_ref="request",
            action_kind="inspect",
            target_ref="object:station",
            args={"distance": 1},
            intended_effect="inspection",
            source_tick_ref="tick:1",
            source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
            permission_refs=("W04:permit",),
            evidence_refs=("W01:obs",),
            affordance_binding_refs=("A04:bind",),
        )


def test_published_action_envelope_rejects_scenario_like_ap01_ref() -> None:
    with pytest.raises(ValueError):
        PublishedActionEnvelope(
            envelope_id="env:bad2",
            subject_id="subject_a",
            ap01_request_ref="ap01_request:scenario_id:blocked_aperture",
            action_kind="inspect",
            target_ref="object:station",
            args={"distance": 1},
            intended_effect="inspection",
            source_tick_ref="tick:1",
            source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
            permission_refs=("W04:permit",),
            evidence_refs=("W01:obs",),
            affordance_binding_refs=("A04:bind",),
        )


def test_valid_ap01_request_ref_preserves_boundary_flags() -> None:
    request_ref = AP01RequestRef(request_ref="ap01_request:valid-1")
    envelope = PublishedActionEnvelope(
        envelope_id="env:ok",
        subject_id="subject_a",
        ap01_request_ref=request_ref,
        action_kind="inspect",
        target_ref="object:station",
        args={"distance": 1},
        intended_effect="inspection",
        source_tick_ref="tick:1",
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:obs",),
        affordance_binding_refs=("A04:bind",),
    )
    assert envelope.ap01_request_id == "ap01_request:valid-1"
    assert envelope.request_boundary_preserved is True
    assert envelope.submitted_to_world is False
    assert envelope.executed_by_world is False
