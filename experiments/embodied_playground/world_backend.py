from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from experiments.embodied_playground.action_space import (
    build_action_space_frame,
    default_interaction_surfaces,
)
from experiments.embodied_playground.effects import build_effect_from_envelope
from experiments.embodied_playground.models import (
    ActionEffectFrame,
    ActionSpaceFrame,
    BodyPostureStatus,
    BodyState,
    CorrelationStatus,
    EffectStatus,
    EvalOnlyWorldTruth,
    InventoryKnowledgeStatus,
    InventoryState,
    ObservationFrame,
    Orientation,
    PublishedActionEnvelope,
    PublicWorldSnapshot,
    WorldObjectKind,
    WorldObjectObservation,
)
from experiments.embodied_playground.observation import build_observation_frame, to_public_snapshot


@runtime_checkable
class WorldBackend(Protocol):
    def reset(self, seed: int | None, scenario_config: object | None = None) -> object: ...
    def observe(self, subject_id: str) -> ObservationFrame: ...
    def action_space(self, subject_id: str) -> ActionSpaceFrame: ...
    def submit_action(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame: ...
    def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot: ...
    def eval_snapshot(self) -> EvalOnlyWorldTruth: ...


@dataclass(slots=True)
class ContractOnlyWorldBackend:
    tick_index: int = 0
    _last_subject_id: str = "subject_a"

    def reset(self, seed: int | None, scenario_config: object | None = None) -> dict[str, object]:
        self.tick_index = 0
        self._last_subject_id = "subject_a"
        return {"seed": seed, "scenario_config": scenario_config, "reset": True}

    def observe(self, subject_id: str) -> ObservationFrame:
        self._last_subject_id = subject_id
        action_space = self.action_space(subject_id)
        body = BodyState(
            subject_id=subject_id,
            body_ref=f"{subject_id}:body",
            location_ref="location:origin",
            orientation=Orientation.UNKNOWN,
            posture_status=BodyPostureStatus.READY,
            hand_slot=None,
            held_item_ref=None,
            actuator_status="available",
            sensor_profile=("vision",),
        )
        inventory = InventoryState(
            inventory_ref=f"{subject_id}:inventory",
            owner_subject_id=subject_id,
            capacity_slots=8,
            used_slots=0,
            item_refs=(),
            item_counts={},
            knowledge_status=InventoryKnowledgeStatus.EMPTY,
        )
        visible_objects = (
            WorldObjectObservation(
                object_ref="object:aperture",
                object_kind=WorldObjectKind.APERTURE,
                display_label="aperture",
                location_ref="location:center",
                relation_to_subject="ahead",
                observable_properties={"state": "open"},
                source_authority="world_backend_public_observation",
                claim_not_fact_marker=False,
            ),
        )
        return build_observation_frame(
            observation_id=f"obs:{subject_id}:{self.tick_index}",
            subject_id=subject_id,
            tick_index=self.tick_index,
            body_state=body,
            inventory_state=inventory,
            visible_objects=visible_objects,
            action_space=action_space,
            previous_effect_refs=(),
            world_time_ref=f"time:{self.tick_index}",
        )

    def action_space(self, subject_id: str) -> ActionSpaceFrame:
        return build_action_space_frame(
            frame_id=f"as:{subject_id}:{self.tick_index}",
            subject_id=subject_id,
            tick_index=self.tick_index,
            available_surfaces=default_interaction_surfaces(subject_id),
        )

    def submit_action(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        self.tick_index += 1
        return build_effect_from_envelope(
            effect_id=f"effect:{envelope.envelope_id}:{self.tick_index}",
            subject_id=envelope.subject_id,
            tick_index=self.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.UNKNOWN,
            body_delta={},
            inventory_delta={},
            world_delta_public={},
            observed_result_refs=("effect:unknown",),
        )

    def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot:
        return to_public_snapshot(self.observe(subject_id))

    def eval_snapshot(self) -> EvalOnlyWorldTruth:
        return EvalOnlyWorldTruth(
            snapshot_id=f"eval:{self._last_subject_id}:{self.tick_index}",
            tick_index=self.tick_index,
            hidden_objects=({"object_ref": "hidden:1"},),
            hidden_inventory={"subject_b": {"food": 2}},
            true_recipe_table={"sample_recipe": {"in": ("x",), "out": ("y",)}},
            expected_outcome=None,
            scenario_labels=(),
        )
