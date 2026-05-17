from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.action_space import default_interaction_surfaces
from experiments.embodied_playground.falsifiers import (
    action_space_as_permission,
    action_without_ap01_envelope,
    ap01_boundary_missing,
    backend_selects_action,
    body_delta_without_effect,
    effect_without_correlation,
    eval_label_leakage,
    grid_specific_lockin,
    hidden_recipe_visible,
    hidden_truth_leakage,
    inventory_delta_without_effect,
    minecraft_specific_leak,
    request_as_success_or_completion,
    request_as_execution,
    scenario_id_action_selection,
)
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
from experiments.embodied_playground.observation import to_public_snapshot
from experiments.embodied_playground.world_backend import ContractOnlyWorldBackend


def _observation() -> ObservationFrame:
    subject_id = "subject_a"
    action_space = ActionSpaceFrame(
        frame_id="as:1",
        subject_id=subject_id,
        tick_index=1,
        available_surfaces=default_interaction_surfaces(subject_id),
        allowed_action_kinds_from_body=("inspect", "move_forward"),
        body_constraints=(),
    )
    body = BodyState(
        subject_id=subject_id,
        body_ref="body:a",
        location_ref="loc:origin",
        orientation=Orientation.NORTH,
        posture_status=BodyPostureStatus.READY,
        hand_slot=None,
        held_item_ref=None,
        actuator_status="available",
    )
    inventory = InventoryState(
        inventory_ref="inv:a",
        owner_subject_id=subject_id,
        capacity_slots=4,
        used_slots=0,
        item_refs=(),
        item_counts={},
        knowledge_status=InventoryKnowledgeStatus.EMPTY,
    )
    return ObservationFrame(
        observation_id="obs:1",
        subject_id=subject_id,
        tick_index=1,
        body_state=body,
        inventory_state=inventory,
        visible_objects=(
            WorldObjectObservation(
                object_ref="object:1",
                object_kind=WorldObjectKind.ITEM,
                display_label="item",
                location_ref="loc:near",
                relation_to_subject="near",
                observable_properties={"quantity": 1},
                source_authority="world_backend_public_observation",
                claim_not_fact_marker=False,
            ),
        ),
        action_space=action_space,
        previous_effect_refs=(),
        world_time_ref="t:1",
        source_authority="world_backend_public_observation",
    )


def _envelope() -> PublishedActionEnvelope:
    return PublishedActionEnvelope(
        envelope_id="env:1",
        subject_id="subject_a",
        ap01_request_ref="ap01_request:1",
        action_kind="inspect",
        target_ref="object:1",
        args={"distance": 1},
        intended_effect="inspection",
        source_tick_ref="tick:1",
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:obs",),
        affordance_binding_refs=("A04:bind",),
    )


def _effect() -> ActionEffectFrame:
    return ActionEffectFrame(
        effect_id="effect:1",
        subject_id="subject_a",
        tick_index=1,
        request_ref="ap01_request:1",
        envelope_ref="env:1",
        action_kind="inspect",
        target_ref="object:1",
        effect_status=EffectStatus.SUCCEEDED,
        body_delta={},
        inventory_delta={},
        world_delta_public={},
        observed_result_refs=("result:1",),
        correlation_status=CorrelationStatus.CORRELATED_TO_REQUEST,
    )


def test_hidden_truth_and_eval_label_falsifiers() -> None:
    observation = _observation()
    snapshot = to_public_snapshot(observation)
    effect = _effect()
    assert hidden_truth_leakage(observation, snapshot) is False
    assert eval_label_leakage(observation, observation.action_space, effect) is False

    class _LeakedObservation:
        hidden_truth_excluded = False
        eval_only_excluded = True

    leaked_observation = _LeakedObservation()
    assert hidden_truth_leakage(leaked_observation, snapshot) is True

    leaked_effect = replace(effect, observed_result_refs=("eval_label:success",))
    assert eval_label_leakage(observation, observation.action_space, leaked_effect) is True


def test_action_space_permission_and_request_execution_falsifiers() -> None:
    observation = _observation()
    envelope = _envelope()
    assert action_space_as_permission(observation.action_space) is False
    assert request_as_execution(envelope) is False

    class _Surface:
        is_permission = True

    class _Frame:
        action_space_is_permission = False
        action_space_is_selection = False
        action_space_is_execution = False
        available_surfaces = (_Surface(),)

    bad_action_space = _Frame()
    assert action_space_as_permission(bad_action_space) is True

    class _ExecutedEnvelope:
        submitted_to_world = True
        executed_by_world = False

    executed_envelope = _ExecutedEnvelope()
    assert request_as_execution(executed_envelope) is True


def test_falsifier_request_as_success_or_completion_uses_typed_boundary_fields() -> None:
    envelope = _envelope()
    assert request_as_success_or_completion(envelope) is False

    class _BadEnvelope:
        submitted_to_world = False
        executed_by_world = False
        request_boundary_preserved = False
        no_hidden_truth_used = True
        no_eval_only_used = True
        no_scenario_label_used = True
        __dataclass_fields__ = {"completion_claim": object()}
        ap01_request_ref = "ap01_request:bad"

    assert request_as_success_or_completion(_BadEnvelope()) is True


def test_effect_correlation_falsifiers() -> None:
    effect = _effect()
    assert action_without_ap01_envelope(effect) is False
    assert effect_without_correlation(effect) is False

    missing_refs = replace(effect, request_ref=None, envelope_ref=None)
    assert action_without_ap01_envelope(missing_refs) is True
    assert effect_without_correlation(missing_refs) is True


def test_inventory_body_delta_requires_effect() -> None:
    assert inventory_delta_without_effect({"water": 1}, {"water": 1}, None) is False
    assert inventory_delta_without_effect({"water": 1}, {"water": 2}, None) is True
    assert body_delta_without_effect("loc:a", "loc:a", None) is False
    assert body_delta_without_effect("loc:a", "loc:b", None) is True


def test_hidden_recipe_visible_and_backend_action_selection_falsifiers() -> None:
    observation = _observation()
    assert hidden_recipe_visible(observation) is False
    leaked = replace(
        observation,
        visible_objects=(
            replace(
                observation.visible_objects[0],
                observable_properties={"true_recipe_table": {"x": "y"}},
            ),
        ),
    )
    assert hidden_recipe_visible(leaked) is True

    backend = ContractOnlyWorldBackend()
    assert backend_selects_action(backend) is False

    class BadBackend:
        def choose_action(self) -> str:
            return "bad"

    assert backend_selects_action(BadBackend()) is True


def test_falsifier_backend_selects_action_rejects_backend_returning_action_request() -> None:
    class BadBackend:
        def reset(self, seed: int | None, scenario_config: object | None = None) -> object:
            return {}

        def observe(self, subject_id: str) -> "PublishedActionEnvelope":
            return _envelope()

        def action_space(self, subject_id: str) -> ActionSpaceFrame:
            return _observation().action_space

        def submit_action(self, action_kind: str) -> ActionEffectFrame:
            return _effect()

        def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot:
            from experiments.embodied_playground.observation import to_public_snapshot
            return to_public_snapshot(_observation())

        def eval_snapshot(self) -> EvalOnlyWorldTruth:
            return EvalOnlyWorldTruth(snapshot_id="eval:bad", tick_index=0)

    assert backend_selects_action(BadBackend()) is True


def test_minecraft_grid_ap01_and_scenario_falsifiers() -> None:
    from experiments.embodied_playground.models import BodyState

    assert minecraft_specific_leak(BodyState) is False
    assert grid_specific_lockin(BodyState) is False

    envelope = _envelope()
    assert ap01_boundary_missing(envelope) is False
    assert scenario_id_action_selection({"state": "normal"}) is False
    assert scenario_id_action_selection({"planner": "select_action_by_scenario"}) is True

    class _BrokenEnvelope:
        ap01_request_ref = ""
        request_boundary_preserved = True

    broken = _BrokenEnvelope()
    assert ap01_boundary_missing(broken) is True


def test_falsifier_scenario_id_action_selection_detects_envelope_basis_marker() -> None:
    class _ScenarioEnvelope:
        action_kind = "inspect"
        target_ref = "object:1"
        args = {"scenario_id_action_basis": "scenario_id:mirrored_resource_asymmetry"}
        intended_effect = "inspection"
        source_tick_ref = "tick:1"
        source_phase_refs = ("W04:permit",)
        permission_refs = ("W04:permit",)
        evidence_refs = ("W01:obs",)
        affordance_binding_refs = ("A04:bind",)
        ap01_request_id = "ap01_request:scenario_id:mirrored"

    payload = {
        "action_kind": _ScenarioEnvelope.action_kind,
        "target_ref": _ScenarioEnvelope.target_ref,
        "args": _ScenarioEnvelope.args,
        "intended_effect": _ScenarioEnvelope.intended_effect,
        "source_tick_ref": _ScenarioEnvelope.source_tick_ref,
    }
    assert scenario_id_action_selection(payload) is True


def test_falsifier_scenario_id_action_selection_ignores_docs_only_strings() -> None:
    docs_payload = {"docs": "This documentation mentions scenario_id for explanation only."}
    assert scenario_id_action_selection(docs_payload) is False


def test_eval_truth_model_stays_isolated() -> None:
    eval_truth = EvalOnlyWorldTruth(
        snapshot_id="eval:1",
        tick_index=1,
        hidden_objects=({"object_ref": "hidden:1"},),
        expected_outcome="eval_only",
        scenario_labels=("scenario:label",),
    )
    assert eval_truth.must_never_enter_subject_visible is True
