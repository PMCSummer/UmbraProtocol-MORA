from __future__ import annotations

from pathlib import Path

from substrate.contact_projection_gate import (
    ContactChannelKind,
    ContactProjectionConfig,
    ContactProjectionInput,
    derive_contact_projection_downstream_contract,
    project_contact_frame_to_subject_inputs,
    validate_projection_authority,
)
from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    ContactBuildInput,
    LossinessMarker,
    SourceRef,
    WorldEffectFrame,
    build_phenomenal_contact_frame,
)


def _public_source(source_id: str = "src:public:1") -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_kind="provider",
        public=True,
        protected_eval=False,
        scenario_label=False,
        provider_ref="provider:test",
    )


def _scenario_source(source_id: str = "src:scenario:1") -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_kind="scenario",
        public=False,
        protected_eval=False,
        scenario_label=True,
        provider_ref="provider:scenario",
    )


def _protected_source(source_id: str = "src:protected:1") -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_kind="eval",
        public=False,
        protected_eval=True,
        scenario_label=False,
        provider_ref="provider:eval",
    )


def _umwelt0_result(
    *,
    observations: tuple[str, ...] = ("resource:ore",),
    effects: tuple[str, ...] = ("effect:mine:ore",),
    passive: tuple[str, ...] = (),
    residue: tuple[str, ...] = ("residue:block:0",),
    uncertainty: tuple[str, ...] = (),
    conflict: tuple[str, ...] = (),
    action_surfaces: tuple[ActionSurfaceDeclaration, ...] = (),
    effect_frames: tuple[WorldEffectFrame, ...] = (),
    source_refs: tuple[SourceRef, ...] = (_public_source(),),
    lossiness_markers: tuple[LossinessMarker, ...] = (),
    requires_lossiness_marker: bool = False,
    protected_eval_present: bool = False,
    scenario_label_present: bool = False,
    backend_truth_present: bool = False,
    worldstate_payload_present: bool = False,
    true_recipe_present: bool = False,
    full_map_present: bool = False,
) -> object:
    candidate = ContactBuildInput(
        frame_id="contact:frame:1",
        tick_id="tick:1",
        provider_refs=("provider:test",),
        public_observation_refs=observations,
        public_effect_refs=effects,
        passive_event_refs=passive,
        action_surfaces=action_surfaces,
        effect_frames=effect_frames,
        residue_refs=residue,
        uncertainty_refs=uncertainty,
        conflict_refs=conflict,
        source_refs=source_refs,
        lossiness_markers=lossiness_markers,
        requires_lossiness_marker=requires_lossiness_marker,
        protected_eval_present=protected_eval_present,
        scenario_label_present=scenario_label_present,
        backend_truth_present=backend_truth_present,
        worldstate_payload_present=worldstate_payload_present,
        true_recipe_present=true_recipe_present,
        full_map_present=full_map_present,
    )
    return build_phenomenal_contact_frame(candidate)


def _projection_input(
    *,
    result: object,
    channel_overrides: dict[str, ContactChannelKind] | None = None,
    effects: tuple[WorldEffectFrame, ...] = (),
    surfaces: tuple[ActionSurfaceDeclaration, ...] = (),
) -> ContactProjectionInput:
    return ContactProjectionInput(
        projection_id="projection:test:1",
        contact_result=result,  # type: ignore[arg-type]
        channel_overrides=channel_overrides or {},
        world_effect_frames=effects,
        action_surface_declarations=surfaces,
        recipe_candidate_refs=("recipe:candidate:1",),
        precursor_candidate_refs=("precursor:candidate:1",),
        value_chain_refs=("value:chain:1",),
        factory_chain_refs=("factory:chain:1",),
        p13_credit_refs=("p13:credit:1",),
        p14_station_affordance_refs=("p14:station:1",),
    )


def test_projection_accepts_valid_umwelt0_contact() -> None:
    result = _umwelt0_result()
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.projection_status in {"accepted", "partial"}
    assert projected.action_request_emitted is False
    assert projected.world_submission_emitted is False
    assert validate_projection_authority(projected) is True


def test_projection_blocked_frame_noops() -> None:
    result = _umwelt0_result(worldstate_payload_present=True)
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.projection_status == "blocked"
    assert projected.public_basis_refs == ()


def test_projection_public_observations_to_ab_input() -> None:
    result = _umwelt0_result(observations=("resource:ore", "station:forge"))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert "resource:ore" in projected.projected_ab_input.public_observation_refs
    assert "station:forge" in projected.projected_ab_input.public_observation_refs


def test_projection_public_effects_to_ab_input_and_ap01_lineage() -> None:
    effect = WorldEffectFrame(
        effect_ref="effect:plate:created",
        effect_kind="resource_transform",
        request_ref="ap01:req:1",
        source_refs=("src:public:1",),
        public_delta_refs=("resource:plate",),
    )
    result = _umwelt0_result(effects=("effect:plate:created",), effect_frames=(effect,))
    projected = project_contact_frame_to_subject_inputs(
        _projection_input(result=result, effects=(effect,))
    )
    assert "effect:plate:created" in projected.projected_ab_input.public_effect_refs
    assert "ap01:req:1" in projected.projected_ap01_lineage.request_refs


def test_projection_passive_event_effect_not_cause_proof() -> None:
    effect = WorldEffectFrame(
        effect_ref="effect:ambient:noise",
        effect_kind="passive_event",
        passive_event_ref="event:ambient:1",
        source_refs=("src:public:1",),
    )
    result = _umwelt0_result(effects=("effect:ambient:noise",), effect_frames=(effect,))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result, effects=(effect,)))
    assert "passive:event:ambient:1->effect:ambient:noise" in projected.projected_ap01_lineage.correlation_refs
    assert projected.cause_confirmed is False


def test_projection_action_surface_to_acp01_basis_not_command() -> None:
    surface = ActionSurfaceDeclaration(
        surface_ref="surface:inspect:ore",
        action_kind="inspect",
        source_refs=("src:public:1",),
        target_ref="resource:ore",
    )
    result = _umwelt0_result(action_surfaces=(surface,))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result, surfaces=(surface,)))
    assert "surface:inspect:ore" in projected.projected_acp01_basis.action_surface_basis_refs
    assert projected.action_request_emitted is False


def test_projection_rejects_action_policy_surface() -> None:
    surface = ActionSurfaceDeclaration(
        surface_ref="surface:route",
        action_kind="selected_action",
        source_refs=("src:public:1",),
        selected_action_ref="ap01:selected:1",
    )
    result = _umwelt0_result()
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result, surfaces=(surface,)))
    assert "action_policy_surface_rejected" in projected.projected_acp01_basis.blocked_reasons


def test_projection_knowledge_hint_not_truth() -> None:
    result = _umwelt0_result(observations=("knowledge:jei:hint:filter",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert "knowledge:jei:hint:filter" in projected.projected_acp01_basis.knowledge_hint_refs
    assert projected.fact_claimed is False


def test_projection_language_claim_not_truth() -> None:
    result = _umwelt0_result(observations=("language:claim:water_safe",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert "language:claim:water_safe" in projected.projected_acp01_basis.language_hint_refs
    assert projected.fact_claimed is False


def test_projection_sensory_candidate_not_object_truth() -> None:
    result = _umwelt0_result(observations=("sensory:visual:candidate:ore_patch",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert "sensory:visual:candidate:ore_patch" in projected.projected_acp01_basis.sensory_candidate_refs
    assert projected.value_assigned is False


def test_projection_preserves_uncertainty_lossiness_residue() -> None:
    result = _umwelt0_result(
        residue=("residue:blocked:station",),
        uncertainty=("uncertain:partial",),
        lossiness_markers=(
            LossinessMarker(
                marker_id="loss:provider:1",
                kind="provider_declared",
                description="compressed snapshot",
            ),
        ),
        requires_lossiness_marker=True,
    )
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert "residue:blocked:station" in projected.projected_ab_input.residue_refs
    assert "uncertain:partial" in projected.projected_ab_input.uncertainty_refs


def test_projection_blocks_hidden_eval_or_scenario_source() -> None:
    hidden = _umwelt0_result(source_refs=(_protected_source(),), protected_eval_present=True)
    hidden_projected = project_contact_frame_to_subject_inputs(_projection_input(result=hidden))
    assert hidden_projected.projection_status == "blocked"

    scenario = _umwelt0_result(source_refs=(_scenario_source(),), scenario_label_present=True)
    scenario_projected = project_contact_frame_to_subject_inputs(_projection_input(result=scenario))
    assert scenario_projected.projection_status == "blocked"


def test_projection_unknown_public_channel_is_preserved_bounded() -> None:
    result = _umwelt0_result(observations=("mystery_channel:ref:1",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert "mystery_channel:ref:1" in projected.projected_ab_input.public_basis_refs
    assert "mystery_channel:ref:1" in projected.projected_ab_input.channel_refs.get("unknown_public", ())


def test_projection_unknown_channel_without_source_blocked() -> None:
    result = _umwelt0_result(observations=("mystery_channel:ref:1",), source_refs=())
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.projection_status == "blocked"


def test_projection_no_ap01_request_emitted() -> None:
    result = _umwelt0_result()
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.action_request_emitted is False


def test_projection_no_world_submission_emitted() -> None:
    result = _umwelt0_result()
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.world_submission_emitted is False


def test_projection_no_fact_cause_value_recipe_skill_automation_claims() -> None:
    result = _umwelt0_result()
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.fact_claimed is False
    assert projected.cause_confirmed is False
    assert projected.value_assigned is False
    assert projected.mature_recipe_claimed is False
    assert projected.mature_skill_claimed is False
    assert projected.automation_claimed is False


def test_projection_bounded_ref_limit() -> None:
    observations = tuple(f"resource:item:{idx}" for idx in range(20))
    result = _umwelt0_result(observations=observations)
    projected = project_contact_frame_to_subject_inputs(
        _projection_input(result=result),
        config=ContactProjectionConfig(max_projected_refs_per_channel=5),
    )
    assert len(projected.projected_ab_input.public_observation_refs) == 5
    assert projected.counters.bounded_ref_limit_triggered_count >= 1


def test_projection_does_not_modify_subject_tick() -> None:
    update_path = Path("src/substrate/subject_tick/update.py")
    assert "contact_projection_gate" not in update_path.read_text(encoding="utf-8")


def test_projection_downstream_contract_for_ab_int_and_acp01() -> None:
    result = _umwelt0_result()
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    contract = derive_contact_projection_downstream_contract(projected)
    assert contract.compatible_with_ab_int is True
    assert contract.compatible_with_acp01_basis is True
    assert contract.no_action_authority is True


def test_projection_multichannel_mixed_contact() -> None:
    observations = (
        "resource:ore",
        "knowledge:manual:filter_recipe_hint",
        "language:claim:clean_water",
        "sensory:audio:candidate:pump",
        "pressure:hunger",
    )
    result = _umwelt0_result(observations=observations)
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    channels = projected.projected_ab_input.channel_refs
    assert "resource:ore" in channels.get("symbolic_world", ())
    assert "knowledge:manual:filter_recipe_hint" in channels.get("knowledge_affordance", ())
    assert "language:claim:clean_water" in channels.get("language_contact", ())
    assert "sensory:audio:candidate:pump" in channels.get("sensory_candidate", ())
    assert "pressure:hunger" in channels.get("body_internal", ())


def test_projection_no_worldstate_unwrap() -> None:
    result = _umwelt0_result(observations=("resource:ore",), worldstate_payload_present=True)
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.projection_status == "blocked"
    assert all("worldstate" not in item.lower() for item in projected.public_basis_refs)


def test_projection_does_not_derive_goal_from_quest_hint() -> None:
    result = _umwelt0_result(observations=("knowledge:quest:need_collect_ore",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.projected_acp01_basis.pressure_basis_refs == ()
    assert "knowledge:quest:need_collect_ore" in projected.projected_acp01_basis.knowledge_hint_refs


def test_projection_does_not_assign_value_from_resource_name() -> None:
    result = _umwelt0_result(observations=("resource:iron", "resource:rare_filter", "resource:clean_water"))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.value_assigned is False
    assert projected.mature_recipe_claimed is False
    assert projected.mature_skill_claimed is False


def test_projection_does_not_mature_recipe_from_knowledge_hint() -> None:
    result = _umwelt0_result(observations=("knowledge:manual:recipe:ore_to_plate",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.mature_recipe_claimed is False
    assert projected.automation_claimed is False


def test_projection_does_not_mature_object_from_sensory_candidate() -> None:
    result = _umwelt0_result(observations=("sensory:visual:candidate:unknown_object",))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.mature_skill_claimed is False
    assert projected.fact_claimed is False


def test_projection_request_lineage_does_not_create_ap01() -> None:
    effect = WorldEffectFrame(
        effect_ref="effect:station:started",
        effect_kind="state_change",
        request_ref="ap01:req:10",
        source_refs=("src:public:1",),
    )
    result = _umwelt0_result(effects=("effect:station:started",), effect_frames=(effect,))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result, effects=(effect,)))
    assert "ap01:req:10" in projected.projected_ap01_lineage.request_refs
    assert projected.action_request_emitted is False


def test_projection_effect_lineage_does_not_confirm_cause() -> None:
    effect = WorldEffectFrame(
        effect_ref="effect:passive:rain",
        effect_kind="passive_event",
        passive_event_ref="event:rain:1",
        source_refs=("src:public:1",),
    )
    result = _umwelt0_result(effects=("effect:passive:rain",), effect_frames=(effect,))
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result, effects=(effect,)))
    assert projected.cause_confirmed is False
    assert "passive:event:rain:1->effect:passive:rain" in projected.projected_ap01_lineage.correlation_refs


def test_projection_oversized_mixed_channels_bounded() -> None:
    observations = tuple([f"resource:item:{idx}" for idx in range(20)] + [f"knowledge:hint:{idx}" for idx in range(20)])
    result = _umwelt0_result(observations=observations)
    projected = project_contact_frame_to_subject_inputs(
        _projection_input(result=result),
        config=ContactProjectionConfig(max_projected_refs_per_channel=4),
    )
    assert len(projected.projected_ab_input.public_observation_refs) == 4
    assert projected.counters.bounded_ref_limit_triggered_count >= 1


def test_projection_blocked_contact_cannot_project_partial_basis_by_accident() -> None:
    result = _umwelt0_result(source_refs=(_protected_source(),), protected_eval_present=True)
    projected = project_contact_frame_to_subject_inputs(_projection_input(result=result))
    assert projected.projection_status == "blocked"
    assert projected.projected_ab_input.public_basis_refs == ()
    assert projected.projected_acp01_basis.public_basis_refs == ()
