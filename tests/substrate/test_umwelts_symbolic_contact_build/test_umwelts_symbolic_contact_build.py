from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import replace

from substrate.umwelt0_phenomenal_contact import ContactAuthorityFlags
from substrate.umwelts_symbolic_contact import (
    ActionSurfaceSpec,
    ContactChannelDeclaration,
    ContactLossinessRequirement,
    ContactSourceRequirement,
    ContactSpec,
    ContactUncertaintyRequirement,
    EffectSurfaceSpec,
    ForbiddenPayloadRule,
    ProviderSurfaceSpec,
    PublicRefDeclaration,
    UMWELTSChannelKind,
    UMWELTSRefKind,
    UMWELTSValidationStatus,
    generic_grid_fixture,
    language_sensor_fixture,
    symbolic_factory_fixture,
    validate_contact_spec,
)


def _minimal_symbolic_world_spec() -> ContactSpec:
    source_req = ContactSourceRequirement(required=True, source_refs=("src:minimal:public",))
    return ContactSpec(
        spec_id="spec:minimal",
        backend_family="minimal_symbolic_world",
        spec_version="1.0",
        channel_declarations=(
            ContactChannelDeclaration(
                channel_id="ch:world",
                channel_kind=UMWELTSChannelKind.SYMBOLIC_WORLD,
                public=True,
                requires_source_refs=True,
                requires_lossiness_when_partial=False,
                allows_unknown_refs=False,
                max_refs=8,
                authority_flags=ContactAuthorityFlags(),
            ),
        ),
        public_ref_declarations=(
            PublicRefDeclaration("resource:ore", UMWELTSRefKind.RESOURCE, "ch:world", source_req),
            PublicRefDeclaration("station:furnace", UMWELTSRefKind.STATION, "ch:world", source_req),
        ),
        action_surface_declarations=(
            ActionSurfaceSpec(
                surface_id="surface:inspect",
                action_kind="inspect",
                channel_id="ch:world",
                source_requirements=source_req,
                authority_flags=ContactAuthorityFlags(),
            ),
        ),
        effect_surface_declarations=(
            EffectSurfaceSpec(
                effect_surface_id="effect:delta",
                effect_kind="delta",
                channel_id="ch:world",
                request_correlated_allowed=True,
                passive_event_allowed=False,
                required_source_refs=("src:minimal:public",),
                required_delta_refs=("delta:1",),
                authority_flags=ContactAuthorityFlags(),
            ),
        ),
        provider_declarations=(),
        source_requirements=source_req,
        lossiness_requirements=ContactLossinessRequirement(required_when_partial=False, lossiness_refs=()),
        uncertainty_requirements=ContactUncertaintyRequirement(required_when_ambiguous=False, uncertainty_refs=()),
        forbidden_payload_rules=(),
        authority_profile=ContactAuthorityFlags(),
    )


def test_umwelts_contact_spec_accepts_minimal_symbolic_world() -> None:
    run = validate_contact_spec(_minimal_symbolic_world_spec())
    assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
    assert run.normalized_ir is not None


def test_umwelts_contact_spec_rejects_selected_action_policy() -> None:
    spec = _minimal_symbolic_world_spec()
    bad_surface = replace(spec.action_surface_declarations[0], action_kind="selected_action")
    run = validate_contact_spec(replace(spec, action_surface_declarations=(bad_surface,)))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("selected_action" in reason for reason in run.blocked_reasons)


def test_umwelts_contact_spec_rejects_true_recipe_table() -> None:
    spec = replace(_minimal_symbolic_world_spec(), metadata={"true_recipe": "ore->plate"})
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("true_recipe" in reason for reason in run.blocked_reasons)


def test_umwelts_contact_spec_rejects_full_map_and_hidden_labels() -> None:
    spec = replace(_minimal_symbolic_world_spec(), metadata={"full_map": "all", "hidden_label": "x"})
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("full_map" in reason or "hidden_label" in reason for reason in run.blocked_reasons)


def test_umwelts_contact_spec_rejects_backend_worldstate_payload() -> None:
    spec = replace(_minimal_symbolic_world_spec(), metadata={"worldstate": "{...}"})
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("worldstate" in reason for reason in run.blocked_reasons)


def test_umwelts_symbolic_world_channel_requires_source_refs() -> None:
    source_req = ContactSourceRequirement(required=True, source_refs=())
    spec = _minimal_symbolic_world_spec()
    bad_ref = replace(spec.public_ref_declarations[0], source_requirements=source_req)
    run = validate_contact_spec(replace(spec, public_ref_declarations=(bad_ref, spec.public_ref_declarations[1])))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert run.counters.source_requirement_missing_count > 0


def test_umwelts_partial_channel_requires_lossiness() -> None:
    spec = _minimal_symbolic_world_spec()
    bad_channel = replace(spec.channel_declarations[0], requires_lossiness_when_partial=True)
    bad_spec = replace(
        spec,
        channel_declarations=(bad_channel,),
        lossiness_requirements=ContactLossinessRequirement(required_when_partial=True, lossiness_refs=()),
    )
    run = validate_contact_spec(bad_spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert run.counters.lossiness_requirement_missing_count > 0


def test_umwelts_action_surface_compiles_without_ap01_request() -> None:
    run = validate_contact_spec(_minimal_symbolic_world_spec())
    assert run.action_request_emitted is False
    assert run.world_action_emitted is False


def test_umwelts_effect_surface_compiles_without_fact_or_cause_claim() -> None:
    run = validate_contact_spec(_minimal_symbolic_world_spec())
    assert run.fact_claimed is False
    assert run.cause_confirmed is False


def test_umwelts_knowledge_provider_declares_hint_not_truth() -> None:
    run = validate_contact_spec(symbolic_factory_fixture())
    assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
    assert run.mature_recipe_claimed is False
    assert run.value_assigned is False


def test_umwelts_language_contact_declares_testimony_not_fact() -> None:
    run = validate_contact_spec(language_sensor_fixture())
    assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
    assert run.fact_claimed is False


def test_umwelts_sensory_candidate_declares_candidate_not_object_truth() -> None:
    run = validate_contact_spec(language_sensor_fixture())
    assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
    assert run.mature_skill_claimed is False


def test_umwelts_unknown_public_channel_is_bounded() -> None:
    spec = _minimal_symbolic_world_spec()
    unknown_channel = ContactChannelDeclaration(
        channel_id="ch:unknown",
        channel_kind=UMWELTSChannelKind.UNKNOWN_PUBLIC,
        public=True,
        requires_source_refs=True,
        requires_lossiness_when_partial=True,
        allows_unknown_refs=True,
        max_refs=4,
        authority_flags=ContactAuthorityFlags(),
    )
    unknown_ref = PublicRefDeclaration(
        ref_id="unknown:public:1",
        ref_kind=UMWELTSRefKind.UNCERTAINTY,
        channel_id="ch:unknown",
        source_requirements=ContactSourceRequirement(required=True, source_refs=("src:minimal:public",)),
        uncertainty_policy=ContactUncertaintyRequirement(required_when_ambiguous=True, uncertainty_refs=("uncertain:unknown",)),
    )
    run = validate_contact_spec(
        replace(
            spec,
            channel_declarations=(spec.channel_declarations[0], unknown_channel),
            public_ref_declarations=(*spec.public_ref_declarations, unknown_ref),
        )
    )
    assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
    assert run.counters.unknown_channel_count >= 1


def test_umwelts_unknown_channel_without_source_blocked() -> None:
    spec = _minimal_symbolic_world_spec()
    unknown_channel = ContactChannelDeclaration(
        channel_id="ch:unknown",
        channel_kind=UMWELTSChannelKind.UNKNOWN_PUBLIC,
        public=True,
        requires_source_refs=True,
        requires_lossiness_when_partial=True,
        allows_unknown_refs=True,
        max_refs=4,
        authority_flags=ContactAuthorityFlags(),
    )
    unknown_ref = PublicRefDeclaration(
        ref_id="unknown:public:1",
        ref_kind=UMWELTSRefKind.UNCERTAINTY,
        channel_id="ch:unknown",
        source_requirements=ContactSourceRequirement(required=True, source_refs=()),
    )
    run = validate_contact_spec(
        replace(
            spec,
            channel_declarations=(spec.channel_declarations[0], unknown_channel),
            public_ref_declarations=(*spec.public_ref_declarations, unknown_ref),
        )
    )
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert run.counters.source_requirement_missing_count > 0


def test_umwelts_multichannel_spec_preserves_channel_kinds() -> None:
    run = validate_contact_spec(symbolic_factory_fixture())
    assert run.normalized_ir is not None
    kinds = {channel.channel_kind.value for channel in run.normalized_ir.normalized_channels}
    assert "symbolic_world" in kinds
    assert "knowledge_affordance" in kinds
    assert "system_status" in kinds


def test_umwelts_two_symbolic_backends_share_same_contact_ir() -> None:
    grid = validate_contact_spec(generic_grid_fixture())
    factory = validate_contact_spec(symbolic_factory_fixture())
    assert grid.normalized_ir is not None
    assert factory.normalized_ir is not None
    assert grid.normalized_ir.authority_flags.has_violation() is False
    assert factory.normalized_ir.authority_flags.has_violation() is False
    assert grid.umwelt0_construction_plan is not None
    assert factory.umwelt0_construction_plan is not None


def test_umwelts_backend_specific_field_rejected_or_translated() -> None:
    spec = _minimal_symbolic_world_spec()
    bad_ref = replace(spec.public_ref_declarations[0], backend_ref="minecraft:block:iron_ore")
    run = validate_contact_spec(replace(spec, public_ref_declarations=(bad_ref, spec.public_ref_declarations[1])))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert run.counters.backend_specific_leak_count > 0


def test_umwelts_world0_does_not_need_backend_hardcoded_mapping() -> None:
    run = validate_contact_spec(symbolic_factory_fixture())
    assert run.umwelt0_construction_plan is not None
    plan = run.umwelt0_construction_plan
    assert plan.public_observation_refs
    assert plan.action_surface_refs
    assert plan.source_refs


def test_umwelts_contact_ir_to_umwelt0_frame_conformance() -> None:
    run = validate_contact_spec(generic_grid_fixture())
    assert run.umwelt0_construction_plan is not None
    plan = run.umwelt0_construction_plan
    assert plan.authority_flags.has_violation() is False
    assert plan.action_request_emitted is False
    assert plan.world_submission_emitted is False
    assert plan.fact_claimed is False
    assert plan.cause_confirmed is False


def test_umwelts_no_value_assignment_by_resource_name() -> None:
    spec = _minimal_symbolic_world_spec()
    rich_ref = replace(spec.public_ref_declarations[0], ref_id="resource:rare_iron")
    run = validate_contact_spec(replace(spec, public_ref_declarations=(rich_ref, spec.public_ref_declarations[1])))
    assert run.value_assigned is False


def test_umwelts_no_mature_recipe_skill_or_automation_claim() -> None:
    run = validate_contact_spec(symbolic_factory_fixture())
    assert run.mature_recipe_claimed is False
    assert run.mature_skill_claimed is False
    assert run.automation_claimed is False


def test_umwelts_source_lossiness_uncertainty_requirements_preserved() -> None:
    run = validate_contact_spec(symbolic_factory_fixture())
    assert run.normalized_ir is not None
    assert run.umwelt0_construction_plan is not None
    assert run.umwelt0_construction_plan.source_refs
    assert run.umwelt0_construction_plan.lossiness_refs


def test_umwelts_provider_defaults_do_not_fill_missing_evidence() -> None:
    spec = symbolic_factory_fixture()
    bad_provider = replace(
        spec.provider_declarations[0],
        source_requirements=ContactSourceRequirement(required=True, source_refs=()),
    )
    run = validate_contact_spec(replace(spec, provider_declarations=(bad_provider,)))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert run.counters.source_requirement_missing_count > 0


def test_umwelts_forbidden_payload_in_metadata_rejected() -> None:
    spec = replace(_minimal_symbolic_world_spec(), metadata={"route_plan": "A->B"})
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("planner_payload" in reason for reason in run.blocked_reasons)


def test_umwelts_contact_spec_does_not_create_ap01_request() -> None:
    run = validate_contact_spec(_minimal_symbolic_world_spec())
    assert run.action_request_emitted is False
    assert run.world_action_emitted is False


def test_umwelts_rejects_nested_planner_policy_in_metadata() -> None:
    spec = replace(_minimal_symbolic_world_spec(), metadata={"nested": {"policy": {"if_then_policy": "do_x"}}})  # type: ignore[arg-type]
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("planner_payload" in reason for reason in run.blocked_reasons)


def test_umwelts_rejects_nested_true_recipe_in_provider_metadata() -> None:
    spec = symbolic_factory_fixture()
    bad_provider = replace(spec.provider_declarations[0], metadata={"nested": {"true_recipe": "ore->plate"}})  # type: ignore[arg-type]
    run = validate_contact_spec(replace(spec, provider_declarations=(bad_provider,)))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("true_recipe" in reason for reason in run.blocked_reasons)


def test_umwelts_rejects_authority_flags_true_from_spec() -> None:
    spec = replace(_minimal_symbolic_world_spec(), authority_profile=ContactAuthorityFlags(can_publish_ap01=True))
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("authority_violation" in reason for reason in run.blocked_reasons)


def test_umwelts_unknown_public_requires_uncertainty_policy() -> None:
    spec = _minimal_symbolic_world_spec()
    unknown_channel = ContactChannelDeclaration(
        channel_id="ch:unknown",
        channel_kind=UMWELTSChannelKind.UNKNOWN_PUBLIC,
        public=True,
        requires_source_refs=True,
        requires_lossiness_when_partial=True,
        allows_unknown_refs=True,
        max_refs=4,
        authority_flags=ContactAuthorityFlags(),
    )
    unknown_ref = PublicRefDeclaration(
        ref_id="unknown:public:1",
        ref_kind=UMWELTSRefKind.UNCERTAINTY,
        channel_id="ch:unknown",
        source_requirements=ContactSourceRequirement(required=True, source_refs=("src:minimal:public",)),
        uncertainty_policy=ContactUncertaintyRequirement(required_when_ambiguous=False, uncertainty_refs=()),
    )
    run = validate_contact_spec(
        replace(
            spec,
            channel_declarations=(spec.channel_declarations[0], unknown_channel),
            public_ref_declarations=(*spec.public_ref_declarations, unknown_ref),
        )
    )
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("unknown_channel_uncertainty" in reason for reason in run.blocked_reasons)


def test_umwelts_rejects_forbidden_rule_token_in_action_surface() -> None:
    spec = _minimal_symbolic_world_spec()
    bad_surface = replace(spec.action_surface_declarations[0], metadata={"note": "please solve_task now"})
    rule = ForbiddenPayloadRule(
        rule_id="custom_no_solver",
        reason="must not carry solver hints",
        blocked_tokens=("solve_task",),
        applies_to=("action_surface",),
    )
    run = validate_contact_spec(replace(spec, action_surface_declarations=(bad_surface,), forbidden_payload_rules=(rule,)))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("forbidden_rule:custom_no_solver" in reason for reason in run.blocked_reasons)


def test_umwelts_metadata_bounded_or_sanitized() -> None:
    spec = replace(_minimal_symbolic_world_spec(), metadata={"huge": "x" * 1100})
    run = validate_contact_spec(spec)
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("oversized_value" in reason for reason in run.blocked_reasons)


def test_umwelts_body_internal_cannot_rewrite_intrinsic_need() -> None:
    spec = generic_grid_fixture()
    body_ref = next(item for item in spec.public_ref_declarations if item.channel_id == "ch:body")
    bad_body_ref = replace(
        body_ref,
        allowed_metadata_keys=("intrinsic_need", "drive_weight", "homeostatic_rule", "subject_goal", "badness_function"),
    )
    refs = tuple(bad_body_ref if item.ref_id == body_ref.ref_id else item for item in spec.public_ref_declarations)
    run = validate_contact_spec(replace(spec, public_ref_declarations=refs))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("planner_payload_forbidden" in reason for reason in run.blocked_reasons)
    assert run.action_request_emitted is False
    assert run.value_assigned is False


def test_umwelts_factory_fixture_does_not_encode_solution_sequence() -> None:
    spec = symbolic_factory_fixture()
    bad_surface = replace(spec.action_surface_declarations[0], metadata={"sequence": "craft_then_place_then_run"})
    run = validate_contact_spec(replace(spec, action_surface_declarations=(bad_surface,)))
    assert run.status is UMWELTSValidationStatus.BLOCKED
    assert any("selected_action_policy_forbidden" in reason or "forbidden_rule:planner_payload" in reason for reason in run.blocked_reasons)


def test_umwelts_contact_ir_contains_no_raw_backend_payload_after_normalization() -> None:
    forbidden_tokens = (
        "raw_payload",
        "backend_payload",
        "worldstate",
        "backend_object",
        "hidden_id",
        "full_map",
        "eval_label",
        "scenario_label",
    )
    def _string_values(value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, dict):
            tokens: list[str] = []
            for item in value.values():
                tokens.extend(_string_values(item))
            return tuple(tokens)
        if isinstance(value, (list, tuple)):
            tokens: list[str] = []
            for item in value:
                tokens.extend(_string_values(item))
            return tuple(tokens)
        return ()

    for factory in (generic_grid_fixture, symbolic_factory_fixture, language_sensor_fixture):
        run = validate_contact_spec(factory())
        assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
        assert run.normalized_ir is not None
        assert run.umwelt0_construction_plan is not None
        ir_blob = json.dumps(_string_values(asdict(run.normalized_ir)), ensure_ascii=False).lower()
        plan_blob = json.dumps(_string_values(asdict(run.umwelt0_construction_plan)), ensure_ascii=False).lower()
        for token in forbidden_tokens:
            assert token not in ir_blob
            assert token not in plan_blob


def test_umwelts_provider_conflicts_preserved_or_warned() -> None:
    spec = symbolic_factory_fixture()
    provider_a = replace(spec.provider_declarations[0], metadata={"claim_ref": "objective_hint:quest_1"})
    provider_b = replace(
        spec.provider_declarations[0],
        provider_id="provider:manual_v2",
        authority_class="hint_variant",
        hint_only=False,
        metadata={"claim_ref": "objective_hint:quest_1"},
    )
    run = validate_contact_spec(replace(spec, provider_declarations=(provider_a, provider_b)))
    assert run.status is UMWELTSValidationStatus.PARTIAL
    assert any("provider_conflict:objective_hint:quest_1" in warning for warning in run.warnings)
    assert run.action_request_emitted is False
    assert run.fact_claimed is False


def test_umwelts_quest_text_is_hint_not_truth() -> None:
    spec = symbolic_factory_fixture()
    quest_ref = PublicRefDeclaration(
        ref_id="objective_hint:quest_alpha",
        ref_kind=UMWELTSRefKind.OBJECTIVE_HINT,
        channel_id="ch:knowledge",
        source_requirements=ContactSourceRequirement(required=True, source_refs=("src:factory:public",)),
    )
    provider = replace(
        spec.provider_declarations[0],
        metadata={
            "claim_ref": "objective_hint:quest_alpha",
            "quest_text": "Collect ore and submit to station",
            "reward_text": "Unlock filter slot",
            "progress_text": "0/10 collected",
        },
    )
    run = validate_contact_spec(
        replace(
            spec,
            public_ref_declarations=(*spec.public_ref_declarations, quest_ref),
            provider_declarations=(provider,),
        )
    )
    assert run.status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}
    assert run.normalized_ir is not None
    assert any(item.ref_id == "objective_hint:quest_alpha" for item in run.normalized_ir.normalized_refs)
    assert run.fact_claimed is False
    assert run.action_request_emitted is False
    assert run.value_assigned is False
    assert run.mature_recipe_claimed is False
    assert run.mature_skill_claimed is False
    assert run.automation_claimed is False
