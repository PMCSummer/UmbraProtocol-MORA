from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StationScenarioSpec:
    scenario_id: str
    description: str
    world_scenario_id: str
    station_ref: str | None
    attempt_station_use: bool
    use_passive_effect_fixture: bool = False
    evaluator_only_rule_present: bool = False


_SCENARIOS: tuple[StationScenarioSpec, ...] = (
    StationScenarioSpec(
        scenario_id="station_visible_not_usable",
        description="Station is visible but not proximate; visibility alone is insufficient for use.",
        world_scenario_id="p14_station_visible_far_no_input",
        station_ref="station:alpha",
        attempt_station_use=False,
    ),
    StationScenarioSpec(
        scenario_id="station_proximate_no_input",
        description="Station is proximate but required public input is missing.",
        world_scenario_id="station_visible_no_input",
        station_ref="station:alpha",
        attempt_station_use=True,
    ),
    StationScenarioSpec(
        scenario_id="station_proximate_with_input",
        description="Station is proximate and required public input is available.",
        world_scenario_id="station_input_available_no_recipe_execution",
        station_ref="station:alpha",
        attempt_station_use=True,
    ),
    StationScenarioSpec(
        scenario_id="station_blocked",
        description="Station has required basis and input but remains blocked.",
        world_scenario_id="p14_station_blocked_with_input",
        station_ref="station:alpha",
        attempt_station_use=True,
    ),
    StationScenarioSpec(
        scenario_id="station_protected_eval_only_rule",
        description="Evaluator-only transformation rule exists but subject path lacks public basis.",
        world_scenario_id="empty_room_presence",
        station_ref=None,
        attempt_station_use=False,
        evaluator_only_rule_present=True,
    ),
    StationScenarioSpec(
        scenario_id="station_action_surface_only",
        description="Action surface exists, but no station/proximity/input basis exists.",
        world_scenario_id="water_source_visible",
        station_ref=None,
        attempt_station_use=True,
    ),
    StationScenarioSpec(
        scenario_id="station_far_with_input",
        description="Required input exists but station is not reachable.",
        world_scenario_id="p14_station_far_with_input",
        station_ref="station:alpha",
        attempt_station_use=True,
    ),
    StationScenarioSpec(
        scenario_id="station_missing_station_ref",
        description="Input/action surfaces exist but station ref is absent in public observation.",
        world_scenario_id="p14_action_surface_and_input_no_station",
        station_ref=None,
        attempt_station_use=True,
    ),
    StationScenarioSpec(
        scenario_id="station_effect_without_ap01_attempt",
        description="Passive world-side station-like effect appears without AP01 request.",
        world_scenario_id="station_input_available_no_recipe_execution",
        station_ref="station:alpha",
        attempt_station_use=False,
        use_passive_effect_fixture=True,
    ),
    StationScenarioSpec(
        scenario_id="station_use_effect_feedback",
        description="Station use effect appears through correlated ActionEffectFrame path.",
        world_scenario_id="station_input_available_no_recipe_execution",
        station_ref="station:alpha",
        attempt_station_use=True,
    ),
)


def list_station_scenarios() -> tuple[StationScenarioSpec, ...]:
    return _SCENARIOS


def station_scenario_for_id(scenario_id: str) -> StationScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown station scenario id: {scenario_id}")
