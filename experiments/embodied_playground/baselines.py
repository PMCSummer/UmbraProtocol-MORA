from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Protocol

from experiments.embodied_playground.models import ActionEffectFrame, ActionSpaceFrame, ObservationFrame


class BaselineFairnessClass(str, Enum):
    FAIR_PUBLIC = "fair_public"
    DIAGNOSTIC_UNFAIR = "diagnostic_unfair"
    BOUNDARY_VIOLATION_BASELINE = "boundary_violation_baseline"


@dataclass(frozen=True, slots=True)
class BaselineDecision:
    decision_id: str
    controller_id: str
    action_kind: str | None
    target_ref: str | None
    args: dict[str, object]
    abstained: bool
    reason_codes: tuple[str, ...]
    used_public_observation: bool
    used_action_space: bool
    used_drive_basis: bool
    used_previous_effect: bool
    used_hidden_or_eval: bool
    used_scenario_label: bool
    boundary_notes: tuple[str, ...] = ()
    expected_boundary_violation: bool = False


class BaselineController(Protocol):
    controller_id: str
    controller_kind: str
    fairness_class: BaselineFairnessClass

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision: ...


def _pick_target_item(observation: ObservationFrame) -> str | None:
    for obj in observation.visible_objects:
        kind = str(getattr(obj.object_kind, "value", obj.object_kind))
        if kind == "item":
            return obj.object_ref
    return None


def _pick_first_action(action_space: ActionSpaceFrame) -> tuple[str | None, str | None]:
    for surface in action_space.available_surfaces:
        if surface.action_kinds:
            return surface.action_kinds[0], surface.target_ref
    return None, None


def _has_action_kind(action_space: ActionSpaceFrame, action_kind: str) -> tuple[bool, str | None]:
    for surface in action_space.available_surfaces:
        if action_kind in surface.action_kinds:
            return True, surface.target_ref
    return False, None


@dataclass(slots=True)
class RandomActionBaseline:
    seed: int = 7
    controller_id: str = "baseline:random_action"
    controller_kind: str = "random_action_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.FAIR_PUBLIC
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = scenario_id
        _ = eval_only
        candidates: list[tuple[str, str | None]] = []
        for surface in action_space.available_surfaces:
            for action_kind in surface.action_kinds:
                candidates.append((action_kind, surface.target_ref))
        if not candidates:
            return BaselineDecision(
                decision_id=f"{self.controller_id}:{tick_index}",
                controller_id=self.controller_id,
                action_kind=None,
                target_ref=None,
                args={},
                abstained=True,
                reason_codes=("no_action_surface",),
                used_public_observation=True,
                used_action_space=True,
                used_drive_basis=bool(drive_basis),
                used_previous_effect=bool(previous_effects),
                used_hidden_or_eval=False,
                used_scenario_label=False,
            )
        action_kind, target_ref = self._rng.choice(candidates)
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind=action_kind,
            target_ref=target_ref,
            args={},
            abstained=False,
            reason_codes=("random_surface_pick",),
            used_public_observation=True,
            used_action_space=True,
            used_drive_basis=bool(drive_basis),
            used_previous_effect=bool(previous_effects),
            used_hidden_or_eval=False,
            used_scenario_label=False,
        )


@dataclass(slots=True)
class ActionSpaceGreedyBaseline:
    controller_id: str = "baseline:action_space_greedy"
    controller_kind: str = "action_space_greedy_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.FAIR_PUBLIC

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = observation
        _ = drive_basis
        _ = previous_effects
        _ = scenario_id
        _ = eval_only
        priorities = ("pickup", "use_station", "interact", "move_forward", "inspect", "wait")
        selected: tuple[str | None, str | None] = (None, None)
        for preferred in priorities:
            for surface in action_space.available_surfaces:
                if preferred in surface.action_kinds:
                    selected = (preferred, surface.target_ref)
                    break
            if selected[0] is not None:
                break
        if selected[0] is None:
            selected = _pick_first_action(action_space)
        action_kind, target_ref = selected
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind=action_kind,
            target_ref=target_ref,
            args={},
            abstained=action_kind is None,
            reason_codes=("action_space_as_permission_bias",),
            used_public_observation=False,
            used_action_space=True,
            used_drive_basis=False,
            used_previous_effect=False,
            used_hidden_or_eval=False,
            used_scenario_label=False,
        )


@dataclass(slots=True)
class VisibleObjectHeuristicBaseline:
    controller_id: str = "baseline:visible_object_heuristic"
    controller_kind: str = "visible_object_heuristic_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.FAIR_PUBLIC

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = action_space
        _ = drive_basis
        _ = previous_effects
        _ = scenario_id
        _ = eval_only
        target = _pick_target_item(observation)
        action_kind = "pickup" if target else "inspect"
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind=action_kind,
            target_ref=target,
            args={},
            abstained=False,
            reason_codes=("visible_object_shortcut",),
            used_public_observation=True,
            used_action_space=False,
            used_drive_basis=False,
            used_previous_effect=False,
            used_hidden_or_eval=False,
            used_scenario_label=False,
        )


@dataclass(slots=True)
class DriveOnlyBaseline:
    controller_id: str = "baseline:drive_only"
    controller_kind: str = "drive_only_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.FAIR_PUBLIC

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = observation
        _ = action_space
        _ = previous_effects
        _ = scenario_id
        _ = eval_only
        if not drive_basis:
            return BaselineDecision(
                decision_id=f"{self.controller_id}:{tick_index}",
                controller_id=self.controller_id,
                action_kind=None,
                target_ref=None,
                args={},
                abstained=True,
                reason_codes=("no_drive_basis",),
                used_public_observation=False,
                used_action_space=False,
                used_drive_basis=False,
                used_previous_effect=False,
                used_hidden_or_eval=False,
                used_scenario_label=False,
            )
        target = "item:water_flask" if any("water" in d for d in drive_basis) else None
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind="pickup",
            target_ref=target,
            args={},
            abstained=False,
            reason_codes=("drive_as_permission",),
            used_public_observation=False,
            used_action_space=False,
            used_drive_basis=True,
            used_previous_effect=False,
            used_hidden_or_eval=False,
            used_scenario_label=False,
        )


@dataclass(slots=True)
class DirectBridgeBypassBaseline:
    controller_id: str = "baseline:direct_bridge_bypass"
    controller_kind: str = "direct_bridge_bypass_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.BOUNDARY_VIOLATION_BASELINE

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = observation
        _ = action_space
        _ = drive_basis
        _ = previous_effects
        _ = scenario_id
        _ = eval_only
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind="move_forward",
            target_ref=None,
            args={},
            abstained=False,
            reason_codes=("direct_world_bypass",),
            used_public_observation=False,
            used_action_space=False,
            used_drive_basis=False,
            used_previous_effect=False,
            used_hidden_or_eval=False,
            used_scenario_label=False,
            boundary_notes=("ap01_bypassed", "direct_world_submission"),
            expected_boundary_violation=True,
        )


@dataclass(slots=True)
class HiddenOracleBaseline:
    controller_id: str = "baseline:hidden_oracle"
    controller_kind: str = "hidden_oracle_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.DIAGNOSTIC_UNFAIR

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = observation
        _ = action_space
        _ = drive_basis
        _ = previous_effects
        _ = scenario_id
        hidden_target = None
        if eval_only:
            hidden_objects = eval_only.get("hidden_objects", ())
            if isinstance(hidden_objects, tuple) and hidden_objects:
                first = hidden_objects[0]
                if isinstance(first, dict):
                    hidden_target = first.get("object_ref")
            elif isinstance(hidden_objects, list) and hidden_objects:
                first = hidden_objects[0]
                if isinstance(first, dict):
                    hidden_target = first.get("object_ref")
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind="pickup",
            target_ref=str(hidden_target) if hidden_target is not None else "object:hidden:1",
            args={"oracle": True},
            abstained=False,
            reason_codes=("hidden_eval_oracle",),
            used_public_observation=False,
            used_action_space=False,
            used_drive_basis=False,
            used_previous_effect=False,
            used_hidden_or_eval=True,
            used_scenario_label=False,
            boundary_notes=("uses_eval_truth",),
            expected_boundary_violation=True,
        )


class FSMState(str, Enum):
    IDLE = "idle"
    SEEK_VISIBLE_NEED_OBJECT = "seek_visible_need_object"
    INSPECT_UNCERTAIN_OBJECT = "inspect_uncertain_object"
    ATTEMPT_PICKUP_VISIBLE_TARGET = "attempt_pickup_visible_target"
    BLOCKED_REVALIDATE = "blocked_revalidate"
    ABSTAIN_INSUFFICIENT_BASIS = "abstain_insufficient_basis"


@dataclass(slots=True)
class SimpleFSMBaseline:
    controller_id: str = "baseline:simple_fsm"
    controller_kind: str = "simple_fsm_baseline"
    fairness_class: BaselineFairnessClass = BaselineFairnessClass.FAIR_PUBLIC
    _state: FSMState = field(default=FSMState.IDLE, init=False, repr=False)

    def choose_action(
        self,
        *,
        tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
        drive_basis: tuple[str, ...],
        previous_effects: tuple[ActionEffectFrame, ...],
        scenario_id: str,
        eval_only: dict[str, object] | None = None,
    ) -> BaselineDecision:
        _ = scenario_id
        _ = eval_only
        last_effect = previous_effects[-1] if previous_effects else None
        last_status = None if last_effect is None else str(getattr(last_effect.effect_status, "value", last_effect.effect_status))

        if last_status in {"blocked", "failed"}:
            self._state = FSMState.BLOCKED_REVALIDATE
            can_inspect, inspect_target = _has_action_kind(action_space, "inspect")
            if can_inspect:
                return BaselineDecision(
                    decision_id=f"{self.controller_id}:{tick_index}",
                    controller_id=self.controller_id,
                    action_kind="inspect",
                    target_ref=inspect_target,
                    args={},
                    abstained=False,
                    reason_codes=("fsm_blocked_revalidate",),
                    used_public_observation=True,
                    used_action_space=True,
                    used_drive_basis=bool(drive_basis),
                    used_previous_effect=True,
                    used_hidden_or_eval=False,
                    used_scenario_label=False,
                )
            return BaselineDecision(
                decision_id=f"{self.controller_id}:{tick_index}",
                controller_id=self.controller_id,
                action_kind=None,
                target_ref=None,
                args={},
                abstained=True,
                reason_codes=("fsm_blocked_revalidate_wait",),
                used_public_observation=True,
                used_action_space=True,
                used_drive_basis=bool(drive_basis),
                used_previous_effect=True,
                used_hidden_or_eval=False,
                used_scenario_label=False,
            )

        target_item = _pick_target_item(observation)
        drive_relevant = any("water" in d or "collect" in d for d in drive_basis)

        if target_item and drive_relevant:
            self._state = FSMState.ATTEMPT_PICKUP_VISIBLE_TARGET
            can_pickup, pickup_target = _has_action_kind(action_space, "pickup")
            if can_pickup:
                return BaselineDecision(
                    decision_id=f"{self.controller_id}:{tick_index}",
                    controller_id=self.controller_id,
                    action_kind="pickup",
                    target_ref=pickup_target or target_item,
                    args={},
                    abstained=False,
                    reason_codes=("fsm_pickup_visible_need_object",),
                    used_public_observation=True,
                    used_action_space=True,
                    used_drive_basis=True,
                    used_previous_effect=False,
                    used_hidden_or_eval=False,
                    used_scenario_label=False,
                )

        if target_item and not drive_relevant:
            self._state = FSMState.INSPECT_UNCERTAIN_OBJECT
            can_inspect, inspect_target = _has_action_kind(action_space, "inspect")
            if can_inspect:
                return BaselineDecision(
                    decision_id=f"{self.controller_id}:{tick_index}",
                    controller_id=self.controller_id,
                    action_kind="inspect",
                    target_ref=inspect_target or target_item,
                    args={},
                    abstained=False,
                    reason_codes=("fsm_visible_object_without_drive",),
                    used_public_observation=True,
                    used_action_space=True,
                    used_drive_basis=False,
                    used_previous_effect=False,
                    used_hidden_or_eval=False,
                    used_scenario_label=False,
                )

        if drive_relevant and not target_item:
            self._state = FSMState.SEEK_VISIBLE_NEED_OBJECT
            can_move, move_target = _has_action_kind(action_space, "move_forward")
            if can_move:
                return BaselineDecision(
                    decision_id=f"{self.controller_id}:{tick_index}",
                    controller_id=self.controller_id,
                    action_kind="move_forward",
                    target_ref=move_target,
                    args={},
                    abstained=False,
                    reason_codes=("fsm_drive_seek_without_visible_object",),
                    used_public_observation=True,
                    used_action_space=True,
                    used_drive_basis=True,
                    used_previous_effect=False,
                    used_hidden_or_eval=False,
                    used_scenario_label=False,
                )

        self._state = FSMState.ABSTAIN_INSUFFICIENT_BASIS
        return BaselineDecision(
            decision_id=f"{self.controller_id}:{tick_index}",
            controller_id=self.controller_id,
            action_kind=None,
            target_ref=None,
            args={},
            abstained=True,
            reason_codes=("fsm_abstain_insufficient_basis",),
            used_public_observation=True,
            used_action_space=True,
            used_drive_basis=bool(drive_basis),
            used_previous_effect=bool(previous_effects),
            used_hidden_or_eval=False,
            used_scenario_label=False,
        )


def build_default_baselines(
    *,
    seed: int = 7,
    include_hidden_oracle: bool = False,
    include_direct_bridge: bool = False,
    include_simple_fsm: bool = False,
) -> list[BaselineController]:
    baselines: list[BaselineController] = [
        RandomActionBaseline(seed=seed),
        ActionSpaceGreedyBaseline(),
        VisibleObjectHeuristicBaseline(),
        DriveOnlyBaseline(),
    ]
    if include_simple_fsm:
        baselines.append(SimpleFSMBaseline())
    if include_direct_bridge:
        baselines.append(DirectBridgeBypassBaseline())
    if include_hidden_oracle:
        baselines.append(HiddenOracleBaseline())
    return baselines
