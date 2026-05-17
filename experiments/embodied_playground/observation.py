from __future__ import annotations

from experiments.embodied_playground.models import (
    ActionSpaceFrame,
    BodyState,
    InventoryState,
    ObservationFrame,
    PublicWorldSnapshot,
    WorldObjectObservation,
)


def build_observation_frame(
    *,
    observation_id: str,
    subject_id: str,
    tick_index: int,
    body_state: BodyState,
    inventory_state: InventoryState,
    visible_objects: tuple[WorldObjectObservation, ...],
    action_space: ActionSpaceFrame,
    previous_effect_refs: tuple[str, ...] = (),
    world_time_ref: str | None = None,
    source_authority: str = "world_backend_public_observation",
) -> ObservationFrame:
    return ObservationFrame(
        observation_id=observation_id,
        subject_id=subject_id,
        tick_index=tick_index,
        body_state=body_state,
        inventory_state=inventory_state,
        visible_objects=visible_objects,
        action_space=action_space,
        previous_effect_refs=previous_effect_refs,
        world_time_ref=world_time_ref,
        source_authority=source_authority,
    )


def to_public_snapshot(frame: ObservationFrame) -> PublicWorldSnapshot:
    return PublicWorldSnapshot(
        snapshot_id=f"public:{frame.observation_id}",
        subject_id=frame.subject_id,
        tick_index=frame.tick_index,
        visible_body_state=frame.body_state,
        visible_inventory_state=frame.inventory_state,
        visible_objects=frame.visible_objects,
        visible_surfaces=frame.action_space.available_surfaces,
        public_effect_refs=frame.previous_effect_refs,
    )
