from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GridWorldScenarioConfig:
    scenario_id: str
    width: int
    height: int
    subject_start: tuple[int, int]
    subject_orientation: str
    walls: tuple[tuple[int, int], ...] = ()
    water_sources: tuple[tuple[str, tuple[int, int]], ...] = ()
    stations: tuple[tuple[str, tuple[int, int], tuple[str, ...], str | None], ...] = ()
    items: tuple[tuple[str, str, tuple[int, int], int], ...] = ()
    inventory_capacity: int = 4
    initial_inventory: tuple[tuple[str, int], ...] = ()
    visibility_range: int = 2
    hidden_objects_eval_only: tuple[tuple[str, str, tuple[int, int]], ...] = ()


def list_grid_world_scenarios() -> tuple[str, ...]:
    return (
        "empty_room_presence",
        "blocked_movement_wall",
        "open_movement_forward",
        "visible_item_pickup_available",
        "pickup_without_proximity",
        "inventory_capacity_block",
        "drop_item_available",
        "station_visible_no_input",
        "station_input_available_no_recipe_execution",
        "water_source_visible",
        "hidden_map_not_visible",
        "invalid_envelope_rejected",
    )


def build_grid_world_scenario(scenario_id: str) -> GridWorldScenarioConfig:
    if scenario_id == "empty_room_presence":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
        )
    if scenario_id == "blocked_movement_wall":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
            walls=((2, 1),),
        )
    if scenario_id == "open_movement_forward":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
        )
    if scenario_id == "visible_item_pickup_available":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
            items=(("item:water_flask", "item", (2, 1), 1),),
        )
    if scenario_id == "pickup_without_proximity":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=7,
            height=7,
            subject_start=(1, 1),
            subject_orientation="east",
            items=(("item:water_flask", "item", (5, 5), 1),),
            visibility_range=10,
        )
    if scenario_id == "inventory_capacity_block":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
            items=(("item:water_flask", "item", (2, 1), 1),),
            inventory_capacity=1,
            initial_inventory=(("item:old", 1),),
        )
    if scenario_id == "drop_item_available":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
            initial_inventory=(("item:water_flask", 1),),
        )
    if scenario_id == "station_visible_no_input":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="east",
            stations=(("station:alpha", (3, 2), ("item:ore",), None),),
        )
    if scenario_id == "station_input_available_no_recipe_execution":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="east",
            stations=(("station:alpha", (3, 2), ("item:ore",), None),),
            initial_inventory=(("item:ore", 1),),
        )
    if scenario_id == "water_source_visible":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="south",
            water_sources=(("water:source:1", (2, 3)),),
        )
    if scenario_id == "hidden_map_not_visible":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=8,
            height=8,
            subject_start=(1, 1),
            subject_orientation="east",
            items=(("item:visible", "item", (2, 1), 1),),
            hidden_objects_eval_only=(("object:hidden:1", "item", (7, 7)),),
            visibility_range=2,
        )
    if scenario_id == "invalid_envelope_rejected":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="north",
        )
    raise ValueError(f"Unknown grid-world scenario: {scenario_id}")
