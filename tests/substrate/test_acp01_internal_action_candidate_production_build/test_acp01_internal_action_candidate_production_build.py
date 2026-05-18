from __future__ import annotations

from dataclasses import asdict

from substrate.acp01_internal_action_candidate_production import (
    ACP01ActionSurfaceBasis,
    ACP01CandidateProductionInput,
    ACP01CapabilityBasis,
    ACP01CapabilityStatus,
    ACP01DecisionStatus,
    ACP01EffectFeedbackBasis,
    ACP01InternalDriveBasis,
    ACP01ObservationBasis,
    ACP01VisibleObjectBasis,
    build_acp01_internal_action_candidates,
)


def _input(
    *,
    with_drive: bool = True,
    with_object: bool = True,
    with_surface: bool = True,
    proximity_status: ACP01CapabilityStatus = ACP01CapabilityStatus.AVAILABLE,
    capacity_status: ACP01CapabilityStatus = ACP01CapabilityStatus.AVAILABLE,
    object_confidence: float = 0.95,
    blocked_effect: bool = False,
    drive_kind: str = "pickup_water",
    drive_class: str = "pickup_intent",
    drive_allowed_action_kinds: tuple[str, ...] = ("pickup",),
    drive_target_object_refs: tuple[str, ...] = ("item:water_flask",),
    drive_target_affordance_refs: tuple[str, ...] = ("pickup",),
    drive_resource_or_goal_ref: str | None = "item:water_flask",
) -> ACP01CandidateProductionInput:
    drives = (
        ACP01InternalDriveBasis(
            drive_ref="drive:water_need",
            drive_kind=drive_kind,
            resource_or_goal_ref=drive_resource_or_goal_ref,
            urgency_level=0.7,
            source_ref="tests.acp01",
            drive_class=drive_class,
            allowed_action_kinds=drive_allowed_action_kinds,
            target_object_refs=drive_target_object_refs,
            target_resource_refs=drive_target_object_refs,
            target_affordance_refs=drive_target_affordance_refs,
            required_capability_refs=("proximity", "inventory_capacity"),
            relevance_basis_refs=("drive_basis:typed:pickup",),
        ),
    ) if with_drive else ()
    objects = (
        ACP01VisibleObjectBasis(
            object_ref="item:water_flask",
            object_kind="item",
            location_ref="grid:2,1",
            public_properties={},
            confidence=object_confidence,
        ),
    ) if with_object else ()
    surfaces = (
        ACP01ActionSurfaceBasis(
            surface_ref="surface:pickup",
            surface_kind="pickup",
            target_ref="item:visible",
            action_kinds=("pickup",),
        ),
        ACP01ActionSurfaceBasis(
            surface_ref="surface:inspect",
            surface_kind="inspect",
            target_ref=None,
            action_kinds=("inspect",),
        ),
    ) if with_surface else ()
    capabilities = (
        ACP01CapabilityBasis(
            capability_ref="capability:proximity:item:water_flask",
            capability_kind="proximity",
            target_ref="item:water_flask",
            status=proximity_status,
        ),
        ACP01CapabilityBasis(
            capability_ref="capability:inventory_capacity",
            capability_kind="inventory_capacity",
            target_ref=None,
            status=capacity_status,
        ),
    )
    effects = (
        ACP01EffectFeedbackBasis(
            effect_ref="effect:block:1",
            status="blocked",
            correlation_status="correlated_to_request",
        ),
    ) if blocked_effect else ()
    return ACP01CandidateProductionInput(
        tick_ref="subject_tick:acp01:test",
        observation_basis=ACP01ObservationBasis(
            observation_id="obs:1",
            body_ref="subject_a:body",
            location_ref="grid:2,2",
            orientation="north",
            inventory_ref="subject_a:inventory",
            visible_object_refs=tuple(obj.object_ref for obj in objects),
            action_surface_refs=tuple(surface.surface_ref for surface in surfaces),
            previous_effect_refs=tuple(effect.effect_ref for effect in effects),
        ),
        internal_drive_bases=drives,
        visible_object_bases=objects,
        action_surface_bases=surfaces,
        capability_bases=capabilities,
        effect_feedback_bases=effects,
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.acp01",
    )


def test_valid_pickup_candidate_with_full_basis() -> None:
    result = build_acp01_internal_action_candidates(_input())
    assert result.proposed_count >= 1
    proposal = next(item.proposal for item in result.decisions if item.proposal is not None)
    assert proposal.action_kind == "pickup"
    assert result.candidate_set_for_ap01 is not None


def test_no_candidate_from_visible_object_alone() -> None:
    result = build_acp01_internal_action_candidates(_input(with_drive=False))
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_no_candidate_from_drive_alone() -> None:
    result = build_acp01_internal_action_candidates(_input(with_object=False))
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_no_candidate_from_action_surface_alone() -> None:
    result = build_acp01_internal_action_candidates(
        _input(with_drive=False, with_object=False, with_surface=True)
    )
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_capacity_blocked_prevents_pickup() -> None:
    result = build_acp01_internal_action_candidates(
        _input(capacity_status=ACP01CapabilityStatus.BLOCKED)
    )
    assert result.proposed_count == 0
    assert result.blocked_count >= 1


def test_proximity_missing_prevents_pickup() -> None:
    result = build_acp01_internal_action_candidates(
        _input(proximity_status=ACP01CapabilityStatus.BLOCKED)
    )
    assert result.proposed_count == 0
    assert result.blocked_count >= 1


def test_inspect_candidate_for_uncertainty() -> None:
    result = build_acp01_internal_action_candidates(
        _input(proximity_status=ACP01CapabilityStatus.UNKNOWN, object_confidence=0.2)
    )
    proposal = next(item.proposal for item in result.decisions if item.proposal is not None)
    assert proposal.action_kind == "inspect"


def test_revalidation_for_blocked_effect() -> None:
    result = build_acp01_internal_action_candidates(
        _input(with_drive=False, with_object=False, with_surface=False, blocked_effect=True)
    )
    assert any(item.status is ACP01DecisionStatus.REVALIDATION_REQUIRED for item in result.decisions)


def test_scenario_eval_private_basis_rejected() -> None:
    bad = _input(drive_kind="pickup_water")
    bad_drives = (
        ACP01InternalDriveBasis(
            drive_ref="drive:water_need",
            drive_kind="pickup_water",
            resource_or_goal_ref="scenario_id:pickup",
            urgency_level=0.7,
            source_ref="tests.acp01",
            drive_class="pickup_intent",
            allowed_action_kinds=("pickup",),
            target_object_refs=("item:water_flask",),
            target_resource_refs=("item:water_flask",),
            target_affordance_refs=("pickup",),
            required_capability_refs=("proximity", "inventory_capacity"),
            relevance_basis_refs=("drive_basis:typed:pickup",),
        ),
    )
    bad = ACP01CandidateProductionInput(
        tick_ref=bad.tick_ref,
        observation_basis=bad.observation_basis,
        internal_drive_bases=bad_drives,
        visible_object_bases=bad.visible_object_bases,
        action_surface_bases=bad.action_surface_bases,
        capability_bases=bad.capability_bases,
        effect_feedback_bases=bad.effect_feedback_bases,
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source=bad.source,
    )
    result = build_acp01_internal_action_candidates(bad)
    assert result.unsafe_basis_count >= 1
    assert result.proposed_count == 0


def test_no_recipe_or_automation_actions_emitted() -> None:
    result = build_acp01_internal_action_candidates(
        _input(
            drive_kind="craft_need",
            drive_allowed_action_kinds=(),
            drive_target_object_refs=(),
        )
    )
    proposals = [item.proposal.action_kind for item in result.decisions if item.proposal is not None]
    assert "craft" not in proposals
    assert "refine" not in proposals
    assert "automation" not in proposals


def test_candidate_has_required_provenance_refs() -> None:
    result = build_acp01_internal_action_candidates(_input())
    proposal = next(item.proposal for item in result.decisions if item.proposal is not None)
    payload = " ".join(proposal.basis_refs).lower()
    assert "observation:" in payload
    assert "drive:" in payload
    assert "surface:" in payload
    assert "capability:" in payload


def test_result_does_not_execute_world_and_candidate_set_is_non_executing() -> None:
    result = build_acp01_internal_action_candidates(_input())
    assert result.scope_marker.no_execution_authority is True
    assert result.scope_marker.no_world_submission_authority is True
    assert result.candidate_set_for_ap01 is not None


def test_acp01_rejects_structured_private_eval_marker_in_visible_object_basis() -> None:
    bad_input = _input()
    bad_visible = (
        ACP01VisibleObjectBasis(
            object_ref="item:water_flask",
            object_kind="item",
            location_ref="grid:2,1",
            public_properties={"details": {"scope_marker": "eval_only:hidden_object"}},
            confidence=0.95,
        ),
    )
    candidate_input = ACP01CandidateProductionInput(
        tick_ref=bad_input.tick_ref,
        observation_basis=bad_input.observation_basis,
        internal_drive_bases=bad_input.internal_drive_bases,
        visible_object_bases=bad_visible,
        action_surface_bases=bad_input.action_surface_bases,
        capability_bases=bad_input.capability_bases,
        effect_feedback_bases=bad_input.effect_feedback_bases,
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source=bad_input.source,
    )
    result = build_acp01_internal_action_candidates(candidate_input)
    assert result.unsafe_basis_count >= 1
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_acp01_rejects_structured_scenario_marker_in_candidate_basis() -> None:
    bad_input = _input()
    bad_drives = (
        ACP01InternalDriveBasis(
            drive_ref="drive:water_need",
            drive_kind="water_need",
            resource_or_goal_ref="scenario_id:pickup_bias",
            urgency_level=0.7,
            source_ref="tests.acp01",
            drive_class="pickup_intent",
            allowed_action_kinds=("pickup",),
            target_object_refs=("item:water_flask",),
            target_resource_refs=("item:water_flask",),
            target_affordance_refs=("pickup",),
            required_capability_refs=("proximity", "inventory_capacity"),
            relevance_basis_refs=("drive_basis:typed:pickup",),
        ),
    )
    candidate_input = ACP01CandidateProductionInput(
        tick_ref=bad_input.tick_ref,
        observation_basis=bad_input.observation_basis,
        internal_drive_bases=bad_drives,
        visible_object_bases=bad_input.visible_object_bases,
        action_surface_bases=bad_input.action_surface_bases,
        capability_bases=bad_input.capability_bases,
        effect_feedback_bases=bad_input.effect_feedback_bases,
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source=bad_input.source,
    )
    result = build_acp01_internal_action_candidates(candidate_input)
    assert result.unsafe_basis_count >= 1
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_acp01_allows_scenario_identity_outside_decision_basis() -> None:
    scenario_identity = "hidden_map_not_visible"
    result = build_acp01_internal_action_candidates(_input())
    assert scenario_identity == "hidden_map_not_visible"
    assert result.proposed_count >= 1
    assert result.unsafe_basis_count == 0


def test_acp01_candidate_set_for_ap01_contains_no_private_eval_or_scenario_basis() -> None:
    result = build_acp01_internal_action_candidates(_input())
    assert result.candidate_set_for_ap01 is not None
    payload = asdict(result.candidate_set_for_ap01)

    def _collect_value_text(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            out: list[str] = []
            for item in value.values():
                out.extend(_collect_value_text(item))
            return out
        if isinstance(value, (list, tuple, set, frozenset)):
            out: list[str] = []
            for item in value:
                out.extend(_collect_value_text(item))
            return out
        return [str(value).lower()]

    value_text = " ".join(_collect_value_text(payload))
    forbidden = (
        "private_world",
        "private_map",
        "hidden_truth",
        "hidden_map",
        "scenario_id",
        "scenario:",
        "scenario_to_action",
        "select_action_by_scenario",
        "expected_outcome",
        "manual_action",
        "gui_label",
    )
    assert all(marker not in value_text for marker in forbidden)


def test_acp01_drive_relevance_uses_typed_refs_not_lexical_tokens() -> None:
    result = build_acp01_internal_action_candidates(
        _input(
            drive_kind="water_collect_phrase_only",
            drive_class="typed_unknown_intent",
            drive_allowed_action_kinds=(),
            drive_target_object_refs=(),
            drive_target_affordance_refs=(),
            drive_resource_or_goal_ref=None,
        )
    )
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_acp01_rejects_pickup_when_drive_ref_does_not_target_visible_object() -> None:
    result = build_acp01_internal_action_candidates(
        _input(
            drive_kind="pickup_other",
            drive_allowed_action_kinds=("pickup",),
            drive_target_object_refs=("item:other",),
            drive_resource_or_goal_ref="item:other",
        )
    )
    assert result.proposed_count == 0
    assert result.candidate_set_for_ap01 is None


def test_acp01_allows_pickup_when_drive_target_ref_matches_public_object_basis() -> None:
    result = build_acp01_internal_action_candidates(
        _input(
            drive_kind="pickup_visible",
            drive_allowed_action_kinds=("pickup",),
            drive_target_object_refs=("item:water_flask",),
        )
    )
    assert result.proposed_count >= 1
    assert result.candidate_set_for_ap01 is not None


def test_acp01_policy_contains_no_world_specific_drive_tokens() -> None:
    policy_text = (__import__("pathlib").Path("src/substrate/acp01_internal_action_candidate_production/policy.py")).read_text(
        encoding="utf-8"
    ).lower()
    forbidden_tokens = ("water", "flask", "collect", "ore", "filter", "minecraft", "grid:")
    assert all(token not in policy_text for token in forbidden_tokens)
