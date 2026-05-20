from __future__ import annotations

from dataclasses import replace

from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    BlockedContactReason,
    ContactAuthorityFlags,
    ContactBuildInput,
    ContactRef,
    LossinessMarker,
    SourceRef,
    WorldEffectFrame,
    build_phenomenal_contact_frame,
    derive_umwelt0_downstream_contract,
)


def _public_source(source_id: str = "src:public:1") -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_kind="world_provider",
        public=True,
        protected_eval=False,
        scenario_label=False,
        provider_ref="provider:test",
    )


def _protected_source(source_id: str = "src:protected:1") -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_kind="eval_fixture",
        public=False,
        protected_eval=True,
        scenario_label=False,
        provider_ref="provider:eval",
    )


def _scenario_source(source_id: str = "src:scenario:1") -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_kind="scenario_label",
        public=False,
        protected_eval=False,
        scenario_label=True,
        provider_ref="provider:scenario",
    )


def _base_input(**overrides: object) -> ContactBuildInput:
    payload = ContactBuildInput(
        frame_id="umwelt0:test:frame",
        tick_id="tick:1",
        provider_refs=("provider:test",),
        public_observation_refs=("obs:public:1",),
        public_effect_refs=("effect:public:1",),
        passive_event_refs=(),
        action_surfaces=(),
        effect_frames=(),
        residue_refs=("residue:1",),
        uncertainty_refs=(),
        conflict_refs=(),
        source_refs=(_public_source(),),
        lossiness_markers=(),
        uncertainty_markers=(),
    )
    return replace(payload, **overrides)


def test_umwelt0_contact_frame_excludes_worldstate() -> None:
    run = build_phenomenal_contact_frame(_base_input(worldstate_payload_present=True))
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.WORLDSTATE_DETECTED in run.blocked_reasons
    assert run.accepted_refs == ()


def test_umwelt0_public_refs_require_source_refs() -> None:
    run = build_phenomenal_contact_frame(_base_input(source_refs=()))
    assert BlockedContactReason.MISSING_SOURCE_REFS in run.blocked_reasons
    assert run.counters.missing_source_ref_count >= 1


def test_umwelt0_hidden_eval_excluded_from_public_contact() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            source_refs=(_protected_source(),),
            protected_eval_present=True,
        )
    )
    assert BlockedContactReason.PROTECTED_EVAL_ONLY in run.blocked_reasons
    assert run.phenomenal_contact_frame.hidden_eval_used is False
    assert run.counters.hidden_eval_block_count >= 1


def test_umwelt0_scenario_label_not_public_basis() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            source_refs=(_scenario_source(),),
            scenario_label_present=True,
        )
    )
    assert BlockedContactReason.SCENARIO_LABEL_ONLY in run.blocked_reasons


def test_umwelt0_lossiness_marked_for_partial_contact() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            requires_lossiness_marker=True,
            lossiness_markers=(),
            public_effect_refs=("effect:compressed",),
        )
    )
    assert BlockedContactReason.LOSSINESS_REQUIRED_BUT_MISSING in run.blocked_reasons


def test_umwelt0_action_surface_does_not_emit_action() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            action_surfaces=(
                ActionSurfaceDeclaration(
                    surface_ref="surface:inspect",
                    action_kind="inspect",
                    source_refs=("src:public:1",),
                ),
            )
        )
    )
    frame = run.phenomenal_contact_frame
    assert frame.action_request_emitted is False
    assert frame.world_submission_emitted is False
    assert frame.authority_flags.can_publish_ap01 is False
    assert frame.authority_flags.can_execute_world_action is False


def test_umwelt0_action_policy_rejected() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            action_surfaces=(
                ActionSurfaceDeclaration(
                    surface_ref="surface:route",
                    action_kind="inspect",
                    source_refs=("src:public:1",),
                    selected_action_ref="ap01:selected:1",
                ),
            )
        )
    )
    assert BlockedContactReason.ACTION_POLICY_DETECTED in run.blocked_reasons


def test_umwelt0_effect_frame_requires_request_ref_or_passive_marker() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            effect_frames=(
                WorldEffectFrame(
                    effect_ref="effect:1",
                    effect_kind="output_appeared",
                    source_refs=("src:public:1",),
                ),
            ),
        )
    )
    assert BlockedContactReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER in run.blocked_reasons


def test_umwelt0_effect_frame_not_truth_oracle() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            effect_frames=(
                WorldEffectFrame(
                    effect_ref="effect:1",
                    effect_kind="output_appeared",
                    request_ref="ap01:req:1",
                    source_refs=("src:public:1",),
                    fact_claimed=True,
                    cause_confirmed=True,
                ),
            ),
        )
    )
    assert run.counters.authority_violation_count >= 1
    assert run.phenomenal_contact_frame.fact_claimed is False
    assert run.phenomenal_contact_frame.cause_confirmed is False


def test_umwelt0_true_recipe_not_public_contact() -> None:
    run = build_phenomenal_contact_frame(_base_input(true_recipe_present=True))
    assert BlockedContactReason.TRUE_RECIPE_DETECTED in run.blocked_reasons


def test_umwelt0_full_map_not_public_contact() -> None:
    run = build_phenomenal_contact_frame(_base_input(full_map_present=True))
    assert BlockedContactReason.FULL_MAP_DETECTED in run.blocked_reasons


def test_umwelt0_hidden_identity_not_public_contact() -> None:
    run = build_phenomenal_contact_frame(_base_input(hidden_identity_present=True))
    assert BlockedContactReason.HIDDEN_IDENTITY_DETECTED in run.blocked_reasons


def test_umwelt0_backend_specific_fields_rejected_or_translated() -> None:
    run = build_phenomenal_contact_frame(_base_input(backend_specific_fields=("backend.internal.inventory",)))
    assert BlockedContactReason.UNSUPPORTED_BACKEND_SPECIFIC_FIELD in run.blocked_reasons


def test_umwelt0_contact_authority_flags_no_action_fact_execution() -> None:
    run = build_phenomenal_contact_frame(_base_input())
    flags = run.phenomenal_contact_frame.authority_flags
    assert flags.can_select_action is False
    assert flags.can_publish_ap01 is False
    assert flags.can_execute_world_action is False
    assert flags.can_claim_fact is False
    assert flags.can_confirm_cause is False
    assert flags.can_assign_value is False
    assert flags.can_mature_recipe is False
    assert flags.can_mature_skill is False
    assert flags.can_claim_automation is False


def test_umwelt0_empty_or_disabled_contact_noop() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            public_observation_refs=(),
            public_effect_refs=(),
            passive_event_refs=(),
            residue_refs=(),
            uncertainty_refs=(),
            conflict_refs=(),
            action_surfaces=(),
            effect_frames=(),
            contact_refs=(),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "noop"


def test_umwelt0_subject_tick_compatibility_payload_is_contact_not_worldstate() -> None:
    run = build_phenomenal_contact_frame(_base_input())
    frame = run.phenomenal_contact_frame
    assert frame.public_observation_refs
    assert frame.public_effect_refs
    assert frame.backend_truth_excluded is True
    assert BlockedContactReason.WORLDSTATE_DETECTED not in run.blocked_reasons


def test_umwelt0_contact_preserves_residue_and_uncertainty() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            residue_refs=("residue:blocked_station",),
            uncertainty_refs=("uncertain:ambiguous",),
        )
    )
    assert "residue:blocked_station" in run.phenomenal_contact_frame.residue_refs
    assert "uncertain:ambiguous" in run.phenomenal_contact_frame.uncertainty_refs


def test_umwelt0_no_value_assignment_by_resource_name() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            public_observation_refs=("resource:iron", "resource:filter", "resource:rare"),
        )
    )
    assert run.phenomenal_contact_frame.value_assigned is False


def test_umwelt0_ab_int_consumes_public_contact_without_action_authority() -> None:
    run = build_phenomenal_contact_frame(_base_input())
    contract = derive_umwelt0_downstream_contract(run)
    assert contract.compatible_with_ab_int is True
    assert contract.no_action_authority is True
    assert contract.no_publication_authority is True
    assert contract.no_execution_authority is True


def test_umwelt0_source_refs_not_scenario_labels() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            source_refs=(_scenario_source("src:scenario:a"), _scenario_source("src:scenario:b")),
            scenario_label_present=True,
        )
    )
    assert BlockedContactReason.SCENARIO_LABEL_ONLY in run.blocked_reasons


def test_umwelt0_lossy_provider_hint_remains_partial() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            public_observation_refs=("obs:provider:lossy",),
            lossiness_markers=(
                LossinessMarker(
                    marker_id="loss:provider:1",
                    kind="provider_declared",
                    description="provider reports compressed snapshot",
                ),
            ),
            uncertainty_refs=("uncertain:partial",),
            requires_lossiness_marker=True,
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "partial"
    assert run.phenomenal_contact_frame.lossiness_refs == ("loss:provider:1",)


def test_umwelt0_no_mature_recipe_skill_or_automation_claim() -> None:
    run = build_phenomenal_contact_frame(_base_input())
    frame = run.phenomenal_contact_frame
    assert frame.mature_recipe_claimed is False
    assert frame.automation_claimed is False


def test_umwelt0_rejects_worldstate_dump_hidden_in_metadata() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            contact_refs=(
                ContactRef(
                    ref_id="ref:meta:worldstate",
                    ref_kind="public_observation",
                    source_refs=("src:public:1",),
                    metadata={"worldstate_dump": "{\"x\":1,\"y\":2}"},
                ),
            ),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.WORLDSTATE_DETECTED in run.blocked_reasons


def test_umwelt0_rejects_true_recipe_hidden_in_metadata() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            contact_refs=(
                ContactRef(
                    ref_id="ref:meta:recipe",
                    ref_kind="public_observation",
                    source_refs=("src:public:1",),
                    metadata={"true_recipe": "iron -> plate"},
                ),
            ),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.TRUE_RECIPE_DETECTED in run.blocked_reasons


def test_umwelt0_rejects_selected_action_hidden_in_action_surface_metadata() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            action_surfaces=(
                ActionSurfaceDeclaration(
                    surface_ref="surface:inspect",
                    action_kind="selected_action",
                    source_refs=("src:public:1",),
                ),
            )
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.ACTION_POLICY_DETECTED in run.blocked_reasons


def test_umwelt0_rejects_custom_authority_flags_true() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            action_surfaces=(
                ActionSurfaceDeclaration(
                    surface_ref="surface:inspect",
                    action_kind="inspect",
                    source_refs=("src:public:1",),
                    authority_flags=ContactAuthorityFlags(can_select_action=True),
                ),
            )
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert run.counters.authority_violation_count >= 1


def test_umwelt0_rejects_scenario_label_source_ref() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            source_refs=(_public_source(), _scenario_source("src:scenario:aux")),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.SCENARIO_LABEL_ONLY in run.blocked_reasons


def test_umwelt0_rejects_protected_eval_source_ref() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            source_refs=(_public_source(), _protected_source("src:protected:aux")),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.PROTECTED_EVAL_ONLY in run.blocked_reasons


def test_umwelt0_rejects_effect_truth_claim_hidden_in_metadata() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            effect_frames=(
                WorldEffectFrame(
                    effect_ref="effect:true_recipe:hidden",
                    effect_kind="output_appeared",
                    request_ref="ap01:req:1",
                    source_refs=("src:public:1",),
                ),
            ),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.TRUE_RECIPE_DETECTED in run.blocked_reasons


def test_umwelt0_backend_specific_payload_not_accepted_as_subject_concept() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            contact_refs=(
                ContactRef(
                    ref_id="ref:backend:surface",
                    ref_kind="public_observation",
                    source_refs=("src:public:1",),
                    metadata={"backend_object_id": "minecraft:ore#hidden"},
                ),
            )
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.HIDDEN_IDENTITY_DETECTED in run.blocked_reasons


def test_umwelt0_contact_ref_metadata_is_bounded_or_sanitized() -> None:
    run = build_phenomenal_contact_frame(
        _base_input(
            contact_refs=(
                ContactRef(
                    ref_id="ref:meta:block",
                    ref_kind="public_observation",
                    source_refs=("src:public:1",),
                    metadata={"nested": 1},  # type: ignore[dict-item]
                ),
            ),
        )
    )
    assert run.phenomenal_contact_frame.validation_status.value == "blocked"
    assert BlockedContactReason.UNSUPPORTED_BACKEND_SPECIFIC_FIELD in run.blocked_reasons
