from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from experiments.embodied_playground.action_space import BACKEND_NEUTRAL_ACTION_KINDS, build_action_space_frame
from experiments.embodied_playground.effects import build_effect_from_envelope
from experiments.embodied_playground.models import (
    ActionEffectFrame,
    ActionSpaceFrame,
    ActuatorStatus,
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
)
from experiments.embodied_playground.observation import build_observation_frame, to_public_snapshot
from experiments.embodied_playground.scenarios import GridWorldScenarioConfig, build_grid_world_scenario
from experiments.embodied_playground.validation import validate_published_action_envelope
from experiments.embodied_playground.world_backend import WorldBackend


class GridDirection(str, Enum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"


class GridCellKind(str, Enum):
    EMPTY = "empty"
    WALL = "wall"
    WATER_SOURCE = "water_source"
    STATION = "station"
    APERTURE = "aperture"
    OBSTACLE = "obstacle"


@dataclass(frozen=True, slots=True)
class GridPosition:
    x: int
    y: int


@dataclass(slots=True)
class GridItem:
    item_ref: str
    item_kind: str
    position: GridPosition
    quantity: int
    observable_properties: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class GridStation:
    station_ref: str
    position: GridPosition
    station_kind: str
    required_input_refs: tuple[str, ...] = ()
    blocked_reason: str | None = None
    visible: bool = True


@dataclass(slots=True)
class GridWorldState:
    width: int
    height: int
    walls: set[tuple[int, int]]
    subject_position: GridPosition
    subject_orientation: GridDirection
    inventory_capacity: int
    inventory_counts: dict[str, int]
    items: dict[str, GridItem]
    stations: dict[str, GridStation]
    water_sources: dict[str, GridPosition]
    tick_index: int = 0
    last_effects: list[ActionEffectFrame] = field(default_factory=list)


_TARGET_REQUIRED_ACTIONS: set[str] = {"pickup", "drop", "interact", "use_station"}


class GridWorldBackend(WorldBackend):
    def __init__(self, scenario_id: str = "empty_room_presence", subject_id: str = "subject_a") -> None:
        self.subject_id = subject_id
        self._scenario_id = scenario_id
        self._scenario_config: GridWorldScenarioConfig = build_grid_world_scenario(scenario_id)
        self._state: GridWorldState = self._state_from_config(self._scenario_config)

    def reset(self, seed: int | None, scenario_config: object | None = None) -> dict[str, object]:
        _ = seed
        if scenario_config is None:
            self._scenario_config = build_grid_world_scenario(self._scenario_id)
        elif isinstance(scenario_config, GridWorldScenarioConfig):
            self._scenario_config = scenario_config
            self._scenario_id = scenario_config.scenario_id
        elif isinstance(scenario_config, dict) and "scenario_id" in scenario_config:
            scenario_id = str(scenario_config["scenario_id"])
            self._scenario_id = scenario_id
            self._scenario_config = build_grid_world_scenario(scenario_id)
        else:
            raise ValueError("GridWorldBackend.reset expects GridWorldScenarioConfig or {'scenario_id': ...}")
        self._state = self._state_from_config(self._scenario_config)
        return {"reset": True, "scenario_id": self._scenario_id}

    def observe(self, subject_id: str) -> ObservationFrame:
        self._assert_subject(subject_id)
        return build_observation_frame(
            observation_id=f"obs:{self._scenario_id}:{self._state.tick_index}",
            subject_id=subject_id,
            tick_index=self._state.tick_index,
            body_state=self._body_state(),
            inventory_state=self._inventory_state(),
            visible_objects=self._visible_objects(),
            action_space=self.action_space(subject_id),
            previous_effect_refs=tuple(effect.effect_id for effect in self._state.last_effects[-3:]),
            world_time_ref=f"grid_tick:{self._state.tick_index}",
            source_authority="grid_world_public_observation",
        )

    def action_space(self, subject_id: str) -> ActionSpaceFrame:
        self._assert_subject(subject_id)
        surfaces: list[AvailableInteractionSurface] = [
            AvailableInteractionSurface(
                surface_ref=f"{subject_id}:surface:movement",
                surface_kind=InteractionSurfaceKind.MOVEMENT,
                target_ref=None,
                action_kinds=("move_forward", "move_backward", "turn_left", "turn_right", "wait"),
                constraints=("out_of_bounds_blocked", "wall_blocked"),
                affordance_hint_refs=("grid:movement",),
                source_authority="grid_world_public_surface",
            ),
            AvailableInteractionSurface(
                surface_ref=f"{subject_id}:surface:inspect",
                surface_kind=InteractionSurfaceKind.INSPECT,
                target_ref=None,
                action_kinds=("inspect",),
                constraints=("visible_target_optional",),
                affordance_hint_refs=("grid:inspect",),
                source_authority="grid_world_public_surface",
            ),
        ]
        if self._visible_item_refs():
            surfaces.append(
                AvailableInteractionSurface(
                    surface_ref=f"{subject_id}:surface:pickup",
                    surface_kind=InteractionSurfaceKind.PICKUP,
                    target_ref="item:visible",
                    action_kinds=("pickup",),
                    constraints=("target_required", "adjacent_or_same_cell", "inventory_capacity_required"),
                    affordance_hint_refs=("grid:pickup",),
                    source_authority="grid_world_public_surface",
                )
            )
        if self._inventory_used_slots() > 0:
            surfaces.append(
                AvailableInteractionSurface(
                    surface_ref=f"{subject_id}:surface:drop",
                    surface_kind=InteractionSurfaceKind.DROP,
                    target_ref="item:inventory",
                    action_kinds=("drop",),
                    constraints=("target_required", "inventory_item_required"),
                    affordance_hint_refs=("grid:drop",),
                    source_authority="grid_world_public_surface",
                )
            )
        if self._visible_station_refs() or self._visible_water_refs():
            surfaces.append(
                AvailableInteractionSurface(
                    surface_ref=f"{subject_id}:surface:interact",
                    surface_kind=InteractionSurfaceKind.INTERACT,
                    target_ref="object:visible",
                    action_kinds=("interact", "use_station"),
                    constraints=("target_required", "adjacent_required"),
                    affordance_hint_refs=("grid:interact",),
                    source_authority="grid_world_public_surface",
                )
            )
        return build_action_space_frame(
            frame_id=f"as:{self._scenario_id}:{self._state.tick_index}",
            subject_id=subject_id,
            tick_index=self._state.tick_index,
            available_surfaces=tuple(surfaces),
            body_constraints=(),
        )

    def submit_action(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        self._state.tick_index += 1
        if not isinstance(envelope, PublishedActionEnvelope):
            return self._invalid_effect(reason="published_action_envelope_required", action_kind="invalid_envelope")
        if envelope.subject_id != self.subject_id:
            return self._invalid_effect(reason="subject_mismatch", action_kind=envelope.action_kind)
        try:
            validate_published_action_envelope(envelope)
        except Exception:
            return self._invalid_effect(reason="invalid_ap01_boundary", action_kind=envelope.action_kind)
        if envelope.action_kind not in BACKEND_NEUTRAL_ACTION_KINDS:
            return self._blocked_effect(envelope, blocked_reason="unknown_action_kind")
        if envelope.action_kind in _TARGET_REQUIRED_ACTIONS and not envelope.target_ref:
            return self._blocked_effect(envelope, blocked_reason="target_required")

        handler = getattr(self, f"_do_{envelope.action_kind}", None)
        if handler is None:
            return self._blocked_effect(envelope, blocked_reason="action_not_supported_in_p2")
        effect = handler(envelope)
        self._state.last_effects.append(effect)
        return effect

    def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot:
        self._assert_subject(subject_id)
        return to_public_snapshot(self.observe(subject_id))

    def eval_snapshot(self) -> EvalOnlyWorldTruth:
        hidden_objects = tuple(
            {
                "object_ref": obj_ref,
                "object_kind": kind,
                "location_ref": self._location_ref(GridPosition(*pos)),
            }
            for obj_ref, kind, pos in self._scenario_config.hidden_objects_eval_only
        )
        return EvalOnlyWorldTruth(
            snapshot_id=f"eval:{self._scenario_id}:{self._state.tick_index}",
            tick_index=self._state.tick_index,
            hidden_objects=hidden_objects,
            hidden_inventory={},
            true_recipe_table={},
            expected_outcome=None,
            scenario_labels=(f"scenario:{self._scenario_id}",),
        )

    def _do_wait(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.NO_EFFECT,
            observed_result_refs=("grid:wait",),
        )

    def _do_turn_left(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        old = self._state.subject_orientation
        self._state.subject_orientation = {
            GridDirection.NORTH: GridDirection.WEST,
            GridDirection.WEST: GridDirection.SOUTH,
            GridDirection.SOUTH: GridDirection.EAST,
            GridDirection.EAST: GridDirection.NORTH,
        }[old]
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.SUCCEEDED,
            body_delta={"orientation_from": old.value, "orientation_to": self._state.subject_orientation.value},
            observed_result_refs=("grid:turned_left",),
        )

    def _do_turn_right(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        old = self._state.subject_orientation
        self._state.subject_orientation = {
            GridDirection.NORTH: GridDirection.EAST,
            GridDirection.EAST: GridDirection.SOUTH,
            GridDirection.SOUTH: GridDirection.WEST,
            GridDirection.WEST: GridDirection.NORTH,
        }[old]
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.SUCCEEDED,
            body_delta={"orientation_from": old.value, "orientation_to": self._state.subject_orientation.value},
            observed_result_refs=("grid:turned_right",),
        )

    def _do_move_forward(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        return self._move_with_scale(envelope, scale=1)

    def _do_move_backward(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        return self._move_with_scale(envelope, scale=-1)

    def _move_with_scale(self, envelope: PublishedActionEnvelope, scale: int) -> ActionEffectFrame:
        dx, dy = self._direction_delta(self._state.subject_orientation)
        target = GridPosition(self._state.subject_position.x + (dx * scale), self._state.subject_position.y + (dy * scale))
        if not self._within_bounds(target):
            return self._blocked_effect(envelope, blocked_reason="out_of_bounds")
        if (target.x, target.y) in self._state.walls:
            return self._blocked_effect(envelope, blocked_reason="wall_blocked")
        old_pos = self._state.subject_position
        self._state.subject_position = target
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.SUCCEEDED,
            body_delta={
                "location_from": self._location_ref(old_pos),
                "location_to": self._location_ref(target),
            },
            observed_result_refs=("grid:moved",),
        )

    def _do_inspect(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        visible_refs = {obj.object_ref for obj in self._visible_objects()}
        target = envelope.target_ref
        if target and target not in visible_refs:
            return self._blocked_effect(envelope, blocked_reason="target_not_visible")
        result_refs = (f"inspect:{target or 'local'}",)
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.SUCCEEDED,
            observed_result_refs=result_refs,
        )

    def _do_pickup(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        target_ref = envelope.target_ref or ""
        item = self._state.items.get(target_ref)
        if item is None or item.quantity <= 0:
            return self._blocked_effect(envelope, blocked_reason="target_item_missing")
        if not self._is_reachable(item.position):
            return self._blocked_effect(envelope, blocked_reason="target_not_reachable")
        if self._inventory_used_slots() >= self._state.inventory_capacity and target_ref not in self._state.inventory_counts:
            return self._blocked_effect(envelope, blocked_reason="inventory_full")
        self._state.inventory_counts[target_ref] = self._state.inventory_counts.get(target_ref, 0) + 1
        item.quantity -= 1
        if item.quantity <= 0:
            del self._state.items[target_ref]
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.SUCCEEDED,
            inventory_delta={"added": {target_ref: 1}},
            world_delta_public={"removed_items": [target_ref]},
            observed_result_refs=("grid:pickup_succeeded",),
        )

    def _do_drop(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        target_ref = envelope.target_ref or ""
        if self._state.inventory_counts.get(target_ref, 0) <= 0:
            return self._blocked_effect(envelope, blocked_reason="inventory_item_missing")
        self._state.inventory_counts[target_ref] -= 1
        if self._state.inventory_counts[target_ref] <= 0:
            del self._state.inventory_counts[target_ref]
        existing = self._state.items.get(target_ref)
        if existing is None:
            self._state.items[target_ref] = GridItem(
                item_ref=target_ref,
                item_kind="item",
                position=self._state.subject_position,
                quantity=1,
                observable_properties={"dropped": True},
            )
        else:
            existing.quantity += 1
            existing.position = self._state.subject_position
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.SUCCEEDED,
            inventory_delta={"removed": {target_ref: 1}},
            world_delta_public={"dropped_items": [target_ref], "drop_location": self._location_ref(self._state.subject_position)},
            observed_result_refs=("grid:drop_succeeded",),
        )

    def _do_interact(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        target = envelope.target_ref or ""
        if target in self._state.stations:
            station = self._state.stations[target]
            if not self._is_reachable(station.position):
                return self._blocked_effect(envelope, blocked_reason="station_not_reachable")
            return build_effect_from_envelope(
                effect_id=self._effect_id(envelope),
                subject_id=self.subject_id,
                tick_index=self._state.tick_index,
                envelope=envelope,
                effect_status=EffectStatus.NO_EFFECT,
                observed_result_refs=("grid:station_visible",),
            )
        if target in self._state.water_sources:
            if not self._is_reachable(self._state.water_sources[target]):
                return self._blocked_effect(envelope, blocked_reason="water_not_reachable")
            return build_effect_from_envelope(
                effect_id=self._effect_id(envelope),
                subject_id=self.subject_id,
                tick_index=self._state.tick_index,
                envelope=envelope,
                effect_status=EffectStatus.NO_EFFECT,
                observed_result_refs=("grid:water_source_observed",),
            )
        return self._blocked_effect(envelope, blocked_reason="target_not_interactable")

    def _do_use_station(self, envelope: PublishedActionEnvelope) -> ActionEffectFrame:
        target = envelope.target_ref or ""
        station = self._state.stations.get(target)
        if station is None:
            return self._blocked_effect(envelope, blocked_reason="station_missing")
        if not self._is_reachable(station.position):
            return self._blocked_effect(envelope, blocked_reason="station_not_reachable")
        if station.blocked_reason:
            return self._blocked_effect(envelope, blocked_reason=station.blocked_reason)
        missing_inputs = [item_ref for item_ref in station.required_input_refs if self._state.inventory_counts.get(item_ref, 0) <= 0]
        if missing_inputs:
            return self._blocked_effect(envelope, blocked_reason="station_input_missing")
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.PARTIAL,
            partial_reason="not_implemented_recipe",
            observed_result_refs=("grid:station_input_seen", "grid:recipe_execution_not_available_in_p2"),
        )

    def _blocked_effect(self, envelope: PublishedActionEnvelope, blocked_reason: str) -> ActionEffectFrame:
        return build_effect_from_envelope(
            effect_id=self._effect_id(envelope),
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            envelope=envelope,
            effect_status=EffectStatus.BLOCKED,
            blocked_reason=blocked_reason,
            observed_result_refs=(f"grid:block:{blocked_reason}",),
        )

    def _invalid_effect(self, reason: str, action_kind: str) -> ActionEffectFrame:
        effect = ActionEffectFrame(
            effect_id=f"effect:invalid:{self._scenario_id}:{self._state.tick_index}",
            subject_id=self.subject_id,
            tick_index=self._state.tick_index,
            request_ref=None,
            envelope_ref=None,
            action_kind=action_kind,
            target_ref=None,
            effect_status=EffectStatus.BLOCKED,
            body_delta={},
            inventory_delta={},
            world_delta_public={},
            observed_result_refs=(f"grid:invalid:{reason}",),
            blocked_reason=reason,
            correlation_status=CorrelationStatus.INVALID,
        )
        self._state.last_effects.append(effect)
        return effect

    def _body_state(self) -> BodyState:
        return BodyState(
            subject_id=self.subject_id,
            body_ref=f"{self.subject_id}:body",
            location_ref=self._location_ref(self._state.subject_position),
            orientation=Orientation(self._state.subject_orientation.value),
            posture_status=BodyPostureStatus.READY,
            hand_slot=None,
            held_item_ref=None,
            actuator_status=ActuatorStatus.AVAILABLE,
            visible_range=float(self._scenario_config.visibility_range),
            sensor_profile=("vision",),
        )

    def _inventory_state(self) -> InventoryState:
        used_slots = self._inventory_used_slots()
        if used_slots == 0:
            status = InventoryKnowledgeStatus.EMPTY
        elif used_slots >= self._state.inventory_capacity:
            status = InventoryKnowledgeStatus.FULL
        else:
            status = InventoryKnowledgeStatus.VISIBLE
        item_refs = tuple(sorted(item_ref for item_ref, qty in self._state.inventory_counts.items() if qty > 0))
        return InventoryState(
            inventory_ref=f"{self.subject_id}:inventory",
            owner_subject_id=self.subject_id,
            capacity_slots=self._state.inventory_capacity,
            used_slots=used_slots,
            item_refs=item_refs,
            item_counts={ref: self._state.inventory_counts[ref] for ref in item_refs},
            knowledge_status=status,
        )

    def _visible_objects(self) -> tuple[WorldObjectObservation, ...]:
        objects: list[WorldObjectObservation] = []
        for x, y in sorted(self._state.walls):
            pos = GridPosition(x, y)
            if self._is_visible(pos):
                objects.append(
                    WorldObjectObservation(
                        object_ref=f"wall:{x}:{y}",
                        object_kind=WorldObjectKind.OBSTACLE,
                        display_label="wall",
                        location_ref=self._location_ref(pos),
                        relation_to_subject=self._relation_to_subject(pos),
                        observable_properties={"cell_kind": GridCellKind.WALL.value},
                        source_authority="grid_world_public_observation",
                        claim_not_fact_marker=False,
                    )
                )
        for item in sorted(self._state.items.values(), key=lambda i: i.item_ref):
            if item.quantity > 0 and self._is_visible(item.position):
                objects.append(
                    WorldObjectObservation(
                        object_ref=item.item_ref,
                        object_kind=WorldObjectKind.ITEM,
                        display_label=item.item_ref,
                        location_ref=self._location_ref(item.position),
                        relation_to_subject=self._relation_to_subject(item.position),
                        observable_properties={"quantity": item.quantity, **item.observable_properties},
                        source_authority="grid_world_public_observation",
                        claim_not_fact_marker=False,
                    )
                )
        for station in sorted(self._state.stations.values(), key=lambda s: s.station_ref):
            if station.visible and self._is_visible(station.position):
                objects.append(
                    WorldObjectObservation(
                        object_ref=station.station_ref,
                        object_kind=WorldObjectKind.STATION,
                        display_label=station.station_kind,
                        location_ref=self._location_ref(station.position),
                        relation_to_subject=self._relation_to_subject(station.position),
                        observable_properties={
                            "required_input_refs": station.required_input_refs,
                            "blocked_reason": station.blocked_reason,
                        },
                        source_authority="grid_world_public_observation",
                        claim_not_fact_marker=False,
                    )
                )
        for source_ref, pos in sorted(self._state.water_sources.items()):
            if self._is_visible(pos):
                objects.append(
                    WorldObjectObservation(
                        object_ref=source_ref,
                        object_kind=WorldObjectKind.FLUID_SOURCE,
                        display_label="water_source",
                        location_ref=self._location_ref(pos),
                        relation_to_subject=self._relation_to_subject(pos),
                        observable_properties={"water_visible": True},
                        source_authority="grid_world_public_observation",
                        claim_not_fact_marker=False,
                    )
                )
        return tuple(objects)

    def _state_from_config(self, config: GridWorldScenarioConfig) -> GridWorldState:
        stations = {
            station_ref: GridStation(
                station_ref=station_ref,
                position=GridPosition(*pos),
                station_kind="station",
                required_input_refs=required_inputs,
                blocked_reason=blocked_reason,
            )
            for station_ref, pos, required_inputs, blocked_reason in config.stations
        }
        items = {
            item_ref: GridItem(
                item_ref=item_ref,
                item_kind=item_kind,
                position=GridPosition(*pos),
                quantity=quantity,
                observable_properties={"item_kind": item_kind},
            )
            for item_ref, item_kind, pos, quantity in config.items
        }
        water_sources = {source_ref: GridPosition(*pos) for source_ref, pos in config.water_sources}
        return GridWorldState(
            width=config.width,
            height=config.height,
            walls=set(config.walls),
            subject_position=GridPosition(*config.subject_start),
            subject_orientation=GridDirection(config.subject_orientation),
            inventory_capacity=config.inventory_capacity,
            inventory_counts={item_ref: qty for item_ref, qty in config.initial_inventory},
            items=items,
            stations=stations,
            water_sources=water_sources,
            tick_index=0,
            last_effects=[],
        )

    def _direction_delta(self, direction: GridDirection) -> tuple[int, int]:
        if direction == GridDirection.NORTH:
            return (0, -1)
        if direction == GridDirection.EAST:
            return (1, 0)
        if direction == GridDirection.SOUTH:
            return (0, 1)
        return (-1, 0)

    def _location_ref(self, pos: GridPosition) -> str:
        return f"grid:{pos.x},{pos.y}"

    def _within_bounds(self, pos: GridPosition) -> bool:
        return 0 <= pos.x < self._state.width and 0 <= pos.y < self._state.height

    def _is_visible(self, pos: GridPosition) -> bool:
        distance = abs(pos.x - self._state.subject_position.x) + abs(pos.y - self._state.subject_position.y)
        return distance <= self._scenario_config.visibility_range

    def _is_reachable(self, pos: GridPosition) -> bool:
        distance = abs(pos.x - self._state.subject_position.x) + abs(pos.y - self._state.subject_position.y)
        return distance <= 1

    def _relation_to_subject(self, pos: GridPosition) -> str:
        distance = abs(pos.x - self._state.subject_position.x) + abs(pos.y - self._state.subject_position.y)
        if distance == 0:
            return "same_cell"
        if distance == 1:
            return "adjacent"
        return "visible_far"

    def _visible_item_refs(self) -> tuple[str, ...]:
        return tuple(sorted(item.item_ref for item in self._state.items.values() if item.quantity > 0 and self._is_visible(item.position)))

    def _visible_station_refs(self) -> tuple[str, ...]:
        return tuple(sorted(station.station_ref for station in self._state.stations.values() if station.visible and self._is_visible(station.position)))

    def _visible_water_refs(self) -> tuple[str, ...]:
        return tuple(sorted(source_ref for source_ref, pos in self._state.water_sources.items() if self._is_visible(pos)))

    def _inventory_used_slots(self) -> int:
        return sum(1 for quantity in self._state.inventory_counts.values() if quantity > 0)

    def _effect_id(self, envelope: PublishedActionEnvelope) -> str:
        return f"effect:{self._scenario_id}:{envelope.envelope_id}:{self._state.tick_index}"

    def _assert_subject(self, subject_id: str) -> None:
        if subject_id != self.subject_id:
            raise ValueError(f"GridWorldBackend supports only configured subject_id={self.subject_id}")


def build_grid_world_backend(scenario_id: str, subject_id: str = "subject_a") -> GridWorldBackend:
    return GridWorldBackend(scenario_id=scenario_id, subject_id=subject_id)


def make_published_action_envelope(
    *,
    subject_id: str,
    action_kind: str,
    target_ref: str | None = None,
    args: dict[str, Any] | None = None,
    request_ref: str = "ap01_request:demo",
    source_tick_ref: str = "tick:demo",
) -> PublishedActionEnvelope:
    return PublishedActionEnvelope(
        envelope_id=f"env:{subject_id}:{action_kind}",
        subject_id=subject_id,
        ap01_request_ref=request_ref,
        action_kind=action_kind,
        target_ref=target_ref,
        args=args or {},
        intended_effect=f"{action_kind}_effect",
        source_tick_ref=source_tick_ref,
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:obs",),
        affordance_binding_refs=("A04:bind",),
    )
