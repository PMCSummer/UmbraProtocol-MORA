from __future__ import annotations

from experiments.embodied_playground.models import (
    ActionSpaceFrame,
    AvailableInteractionSurface,
    InteractionSurfaceKind,
)


BACKEND_NEUTRAL_ACTION_KINDS: tuple[str, ...] = (
    "wait",
    "turn_left",
    "turn_right",
    "move_forward",
    "move_backward",
    "strafe_left",
    "strafe_right",
    "inspect",
    "pickup",
    "drop",
    "interact",
    "use_station",
    "communicate",
)


FORBIDDEN_ADAPTER_LOCKIN_ACTION_FIELDS: tuple[str, ...] = (
    "block_id",
    "hotbar_slot",
    "crafting_table_id",
)


def build_action_space_frame(
    *,
    frame_id: str,
    subject_id: str,
    tick_index: int,
    available_surfaces: tuple[AvailableInteractionSurface, ...],
    body_constraints: tuple[str, ...] = (),
) -> ActionSpaceFrame:
    allowed_action_kinds = tuple(
        sorted(
            {
                action_kind
                for surface in available_surfaces
                for action_kind in surface.action_kinds
                if action_kind in BACKEND_NEUTRAL_ACTION_KINDS
            }
        )
    )
    return ActionSpaceFrame(
        frame_id=frame_id,
        subject_id=subject_id,
        tick_index=tick_index,
        available_surfaces=available_surfaces,
        allowed_action_kinds_from_body=allowed_action_kinds,
        body_constraints=body_constraints,
    )


def default_interaction_surfaces(subject_id: str) -> tuple[AvailableInteractionSurface, ...]:
    return (
        AvailableInteractionSurface(
            surface_ref=f"{subject_id}:surface:movement",
            surface_kind=InteractionSurfaceKind.MOVEMENT,
            target_ref=None,
            action_kinds=("move_forward", "turn_left", "turn_right"),
            constraints=("movement_may_be_blocked",),
            affordance_hint_refs=("hint:movement",),
            source_authority="world_backend_public_surface",
        ),
        AvailableInteractionSurface(
            surface_ref=f"{subject_id}:surface:pickup",
            surface_kind=InteractionSurfaceKind.PICKUP,
            target_ref="object:nearby",
            action_kinds=("pickup",),
            constraints=("target_required", "inventory_space_required"),
            affordance_hint_refs=("hint:pickup",),
            source_authority="world_backend_public_surface",
        ),
        AvailableInteractionSurface(
            surface_ref=f"{subject_id}:surface:interact",
            surface_kind=InteractionSurfaceKind.INTERACT,
            target_ref="station:visible",
            action_kinds=("inspect", "interact", "use_station"),
            constraints=("target_required",),
            affordance_hint_refs=("hint:interaction",),
            source_authority="world_backend_public_surface",
        ),
    )
