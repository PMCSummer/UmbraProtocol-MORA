from __future__ import annotations

from experiments.embodied_playground.action_space import (
    BACKEND_NEUTRAL_ACTION_KINDS,
    build_action_space_frame,
    default_interaction_surfaces,
)
from experiments.embodied_playground.models import InteractionSurfaceKind


def test_action_space_contains_movement_pickup_interact_surfaces() -> None:
    surfaces = default_interaction_surfaces("subject_a")
    kinds = {str(getattr(surface.surface_kind, "value", surface.surface_kind)) for surface in surfaces}
    assert InteractionSurfaceKind.MOVEMENT.value in kinds
    assert InteractionSurfaceKind.PICKUP.value in kinds
    assert InteractionSurfaceKind.INTERACT.value in kinds

    frame = build_action_space_frame(
        frame_id="as:subject_a:1",
        subject_id="subject_a",
        tick_index=1,
        available_surfaces=surfaces,
    )
    assert frame.action_space_is_permission is False
    assert frame.action_space_is_selection is False
    assert frame.action_space_is_execution is False
    assert frame.hidden_truth_excluded is True


def test_surface_availability_does_not_imply_permission() -> None:
    frame = build_action_space_frame(
        frame_id="as:subject_a:2",
        subject_id="subject_a",
        tick_index=2,
        available_surfaces=default_interaction_surfaces("subject_a"),
    )
    assert all(surface.is_permission is False for surface in frame.available_surfaces)


def test_action_space_action_kinds_are_backend_neutral() -> None:
    frame = build_action_space_frame(
        frame_id="as:subject_a:3",
        subject_id="subject_a",
        tick_index=3,
        available_surfaces=default_interaction_surfaces("subject_a"),
    )
    assert frame.allowed_action_kinds_from_body
    assert set(frame.allowed_action_kinds_from_body).issubset(set(BACKEND_NEUTRAL_ACTION_KINDS))
