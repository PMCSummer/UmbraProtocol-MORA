from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig
from experiments.embodied_playground.falsifiers import (
    action_space_alone_creates_candidate,
    ap01_publication_without_acp01_basis,
    blocked_effect_auto_alternative_action,
    bridge_calls_acp01_policy_directly,
    candidate_bypasses_ap01,
    candidate_executes_world,
    candidate_from_eval_or_private_data,
    candidate_from_scenario_id,
    candidate_without_provenance_refs,
    drive_alone_creates_pickup,
    inspect_as_pickup_shortcut,
    manual_provider_used_in_internal_mode,
    pickup_when_capacity_blocked,
    pickup_without_capacity_basis,
    pickup_without_proximity_basis,
    previous_effect_as_success_oracle,
    public_payload_eval_scope_violation,
    recipe_or_automation_candidate_in_p4,
    station_visibility_as_use_candidate,
    visible_object_alone_creates_pickup,
)
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


def test_acp01_falsifier_presence() -> None:
    required = [
        candidate_from_scenario_id,
        candidate_from_eval_or_private_data,
        visible_object_alone_creates_pickup,
        drive_alone_creates_pickup,
        action_space_alone_creates_candidate,
        pickup_without_proximity_basis,
        pickup_without_capacity_basis,
        pickup_when_capacity_blocked,
        candidate_executes_world,
        candidate_bypasses_ap01,
        ap01_publication_without_acp01_basis,
        previous_effect_as_success_oracle,
        blocked_effect_auto_alternative_action,
        inspect_as_pickup_shortcut,
        station_visibility_as_use_candidate,
        recipe_or_automation_candidate_in_p4,
        bridge_calls_acp01_policy_directly,
        manual_provider_used_in_internal_mode,
        public_payload_eval_scope_violation,
        candidate_without_provenance_refs,
    ]
    assert len(required) == 20


def test_negative_controls_for_structural_acp01_falsifiers() -> None:
    assert candidate_from_scenario_id({"action_kind": "pickup", "args": {"basis": "scenario_id:foo"}}) is True
    assert candidate_from_scenario_id({"action_kind": "pickup", "args": {"basis": "typed"}}) is False
    assert candidate_from_eval_or_private_data({"basis_refs": ("eval_only:truth",)}) is True
    assert candidate_from_eval_or_private_data({"basis_refs": ("observation:obs:1",)}) is False
    assert visible_object_alone_creates_pickup(
        has_visible_object_basis=True,
        has_internal_drive_basis=False,
        proposed_action_kind="pickup",
    ) is True
    assert drive_alone_creates_pickup(
        has_internal_drive_basis=True,
        has_visible_object_basis=False,
        has_action_surface_basis=False,
        proposed_action_kind="pickup",
    ) is True
    assert action_space_alone_creates_candidate(
        has_action_surface_basis=True,
        has_internal_drive_basis=False,
        has_visible_object_basis=False,
        proposed_action_kind="pickup",
    ) is True
    assert pickup_without_proximity_basis(
        proposed_action_kind="pickup",
        proximity_basis_status="blocked",
    ) is True
    assert pickup_without_capacity_basis(
        proposed_action_kind="pickup",
        capacity_basis_status="unknown",
    ) is True
    assert pickup_when_capacity_blocked(
        proposed_action_kind="pickup",
        capacity_basis_status="blocked",
    ) is True


def test_negative_controls_for_execution_and_boundary_falsifiers() -> None:
    assert candidate_executes_world({"world_effect": "x"}) is True
    assert candidate_executes_world({"candidate_id": "c1"}) is False
    assert candidate_bypasses_ap01(
        candidate_proposed=True,
        ap01_published_request_count=0,
        world_submission_attempted=True,
    ) is True
    assert ap01_publication_without_acp01_basis(
        ap01_candidate_source="acp01_internal",
        ap01_published_request_count=1,
        acp01_proposed_count=0,
    ) is True
    assert previous_effect_as_success_oracle(
        only_previous_effect_basis=True,
        proposed_action_kind="pickup",
    ) is True
    assert blocked_effect_auto_alternative_action(
        previous_effect_status="blocked",
        revalidation_required=False,
        proposed_action_kind="turn_left",
    ) is True
    assert inspect_as_pickup_shortcut(
        previous_action_kind="inspect",
        current_action_kind="pickup",
        new_evidence_present=False,
    ) is True
    assert station_visibility_as_use_candidate(
        station_visible=True,
        has_drive_basis=False,
        has_capability_basis=False,
        proposed_action_kind="use_station",
    ) is True
    assert recipe_or_automation_candidate_in_p4("craft") is True
    assert recipe_or_automation_candidate_in_p4("pickup") is False


def test_negative_controls_for_runtime_path_falsifiers() -> None:
    source = Path("experiments/embodied_playground/subject_bridge.py").read_text(encoding="utf-8")
    assert bridge_calls_acp01_policy_directly(source) is False
    assert bridge_calls_acp01_policy_directly("build_acp01_internal_action_candidates()") is True
    assert manual_provider_used_in_internal_mode(
        use_internal_candidate_producer=True,
        manual_candidate_input=True,
    ) is True
    assert manual_provider_used_in_internal_mode(
        use_internal_candidate_producer=True,
        manual_candidate_input=False,
    ) is False


def test_public_payload_eval_scope_violation_and_provenance_refs() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=False,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    payload = run.steps[0].subject_tick_surface_payload
    assert public_payload_eval_scope_violation(payload) is False
    leaked = dict(payload)
    leaked["expected_outcome"] = "leak"
    assert public_payload_eval_scope_violation(leaked) is True

    valid_candidate = {"basis_refs": ("observation:obs:1", "drive:d1", "surface:s1", "capability:c1")}
    invalid_candidate = {"basis_refs": ("observation:obs:1",)}
    assert candidate_without_provenance_refs(valid_candidate) is False
    assert candidate_without_provenance_refs(invalid_candidate) is True


def test_internal_mode_bridge_path_has_ap01_candidate_source_from_acp01() -> None:
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.candidate_source == "acp01_internal"
    assert step.internal_candidate_producer_used is True
    assert manual_provider_used_in_internal_mode(
        use_internal_candidate_producer=step.internal_candidate_producer_used,
        manual_candidate_input=step.manual_candidate_input,
    ) is False
    assert candidate_bypasses_ap01(
        candidate_proposed=step.acp01_proposed_count > 0,
        ap01_published_request_count=step.ap01_published_request_count,
        world_submission_attempted=step.world_submission_attempted,
    ) is False
    assert ap01_publication_without_acp01_basis(
        ap01_candidate_source=step.candidate_source,
        ap01_published_request_count=step.ap01_published_request_count,
        acp01_proposed_count=step.acp01_proposed_count,
    ) is False
    assert public_payload_eval_scope_violation(asdict(step)["subject_tick_surface_payload"]) is False


def test_p4_falsifier_detects_structured_private_eval_basis() -> None:
    payload = {
        "candidate_id": "acp01:test:1",
        "action_kind": "pickup",
        "target_ref": "item:water_flask",
        "args": {"basis": {"scope": "private_world:hidden_map"}},
        "intended_effect": "pickup:item:water_flask",
        "basis_refs": ("observation:obs:1", "drive:d1", "surface:s1", "capability:c1"),
    }
    assert candidate_from_eval_or_private_data(payload) is True
    safe = {
        "candidate_id": "acp01:test:2",
        "action_kind": "pickup",
        "target_ref": "item:water_flask",
        "args": {"basis": {"scope": "public_visible"}},
        "intended_effect": "pickup:item:water_flask",
        "basis_refs": ("observation:obs:1", "drive:d1", "surface:s1", "capability:c1"),
    }
    assert candidate_from_eval_or_private_data(safe) is False


def test_p4_falsifier_detects_structured_scenario_action_basis() -> None:
    with_basis_marker = {
        "candidate_id": "acp01:test:scenario",
        "action_kind": "pickup",
        "target_ref": "item:water_flask",
        "args": {"basis": {"source_marker": "scenario_id:pickup_bias"}},
        "intended_effect": "pickup:item:water_flask",
        "basis_refs": ("observation:obs:1", "drive:d1", "surface:s1", "capability:c1"),
    }
    assert candidate_from_scenario_id(with_basis_marker) is True

    scenario_identity_only = {
        "scenario_id": "hidden_map_not_visible",
        "run_id": "bridge-run:1",
        "status": "ok",
    }
    assert candidate_from_scenario_id(scenario_identity_only) is False
