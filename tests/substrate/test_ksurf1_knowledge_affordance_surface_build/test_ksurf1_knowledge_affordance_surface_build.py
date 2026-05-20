from __future__ import annotations

from dataclasses import replace

from substrate.ksurf1_knowledge_affordance_surface import (
    KnowledgeAffordanceKind,
    KnowledgeProviderRef,
    KnowledgeSlotState,
    KnowledgeSurfaceInput,
    KnowledgeSurfaceValidationStatus,
    ProviderAuthorityClass,
    ProviderClaimRef,
    ProviderKind,
    ScannerCandidateHintRef,
    TransformationHintRef,
    build_knowledge_affordance_frame,
    detect_provider_conflicts,
    derive_ksurf1_downstream_contract,
    encyclopedia_locked_slot_fixture,
    encyclopedia_partial_unlock_fixture,
    hidden_provider_blocked_fixture,
    jei_index_hint_fixture,
    machine_status_hint_fixture,
    manual_claim_fixture,
    provider_conflict_fixture,
    quest_objective_hint_fixture,
    scanner_candidate_fixture,
    stale_lossy_provider_fixture,
    umwelts_provider_declaration_fixture,
)


def test_ksurf1_provider_hint_has_source_refs() -> None:
    valid = jei_index_hint_fixture()
    ok = build_knowledge_affordance_frame(valid)
    assert ok.status in {KnowledgeSurfaceValidationStatus.ACCEPTED, KnowledgeSurfaceValidationStatus.PARTIAL}
    bad_provider = replace(valid.provider_refs[0], source_refs=())
    bad = build_knowledge_affordance_frame(replace(valid, provider_refs=(bad_provider,)))
    assert bad.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("missing_source_refs" in item for item in bad.blocked_reasons)


def test_ksurf1_jei_entry_is_hint_not_recipe_truth() -> None:
    run = build_knowledge_affordance_frame(jei_index_hint_fixture())
    assert run.frame is not None
    assert run.frame.transformation_hint_refs
    assert run.frame.mature_recipe_claimed is False


def test_ksurf1_encyclopedia_locked_slot_not_usable() -> None:
    run = build_knowledge_affordance_frame(encyclopedia_locked_slot_fixture())
    assert run.frame is not None
    assert run.frame.locked_slot_refs
    assert run.frame.action_selected is False
    assert run.frame.value_assigned is False


def test_ksurf1_slot_unlock_requires_public_discovery_ref() -> None:
    locked = encyclopedia_locked_slot_fixture()
    bad_slot = replace(locked.locked_slot_refs[0], unlock_basis_refs=("private:recipe_table",))
    bad = build_knowledge_affordance_frame(replace(locked, locked_slot_refs=(bad_slot,)))
    assert bad.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("unlock_without_public_basis" in item for item in bad.blocked_reasons)

    partial = build_knowledge_affordance_frame(encyclopedia_partial_unlock_fixture())
    assert partial.status in {KnowledgeSurfaceValidationStatus.ACCEPTED, KnowledgeSurfaceValidationStatus.PARTIAL}
    assert partial.frame is not None
    assert partial.frame.partial_slot_refs
    assert partial.frame.mature_recipe_claimed is False


def test_ksurf1_quest_objective_is_hint_not_goal_authority() -> None:
    run = build_knowledge_affordance_frame(quest_objective_hint_fixture())
    assert run.frame is not None
    assert run.frame.objective_hint_refs
    assert run.frame.goal_selected is False
    assert run.frame.action_request_emitted is False


def test_ksurf1_machine_ui_status_not_fact_oracle() -> None:
    run = build_knowledge_affordance_frame(machine_status_hint_fixture())
    assert run.frame is not None
    assert run.frame.machine_status_hint_refs
    assert run.frame.fact_claimed is False
    assert run.frame.cause_confirmed is False


def test_ksurf1_scanner_candidate_not_identity_truth() -> None:
    run = build_knowledge_affordance_frame(scanner_candidate_fixture())
    assert run.frame is not None
    assert run.frame.scanner_candidate_hint_refs
    assert run.frame.fact_claimed is False


def test_ksurf1_manual_claim_not_lived_evidence() -> None:
    run = build_knowledge_affordance_frame(manual_claim_fixture())
    assert run.frame is not None
    assert run.frame.provider_claim_refs
    assert run.frame.authority_flags.can_claim_lived_evidence is False


def test_ksurf1_provider_conflict_preserved() -> None:
    run = build_knowledge_affordance_frame(provider_conflict_fixture())
    assert run.status is KnowledgeSurfaceValidationStatus.PARTIAL
    assert run.frame is not None
    assert run.frame.provider_conflict_refs


def test_ksurf1_hint_does_not_emit_ap01_request() -> None:
    run = build_knowledge_affordance_frame(jei_index_hint_fixture())
    assert run.frame is not None
    assert run.frame.action_request_emitted is False


def test_ksurf1_hint_does_not_select_action() -> None:
    run = build_knowledge_affordance_frame(machine_status_hint_fixture())
    assert run.frame is not None
    assert run.frame.action_selected is False


def test_ksurf1_hint_does_not_assign_value() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"rarity": "legendary"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("value_assignment" in item for item in run.blocked_reasons)


def test_ksurf1_recipe_like_hint_does_not_mature_recipe() -> None:
    src = jei_index_hint_fixture()
    bad_hint = replace(src.transformation_hint_refs[0], maturity=True)
    run = build_knowledge_affordance_frame(replace(src, transformation_hint_refs=(bad_hint,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("mature" in item for item in run.blocked_reasons)


def test_ksurf1_hidden_or_scenario_provider_blocked() -> None:
    run = build_knowledge_affordance_frame(hidden_provider_blocked_fixture())
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("protected_eval" in item or "scenario_label" in item for item in run.blocked_reasons)


def test_ksurf1_stale_or_lossy_provider_marked() -> None:
    run = build_knowledge_affordance_frame(stale_lossy_provider_fixture())
    assert run.status in {KnowledgeSurfaceValidationStatus.ACCEPTED, KnowledgeSurfaceValidationStatus.PARTIAL}
    assert run.counters.stale_or_lossy_count >= 1


def test_ksurf1_output_can_feed_ab_as_candidate_basis() -> None:
    run = build_knowledge_affordance_frame(manual_claim_fixture())
    assert run.frame is not None
    assert run.frame.source_refs
    assert run.frame.uncertainty_refs
    assert run.frame.fact_claimed is False


def test_ksurf1_output_can_feed_exp1_without_identity_oracle() -> None:
    run = build_knowledge_affordance_frame(scanner_candidate_fixture())
    assert run.frame is not None
    assert run.frame.scanner_candidate_hint_refs
    assert run.frame.fact_claimed is False


def test_ksurf1_output_can_feed_k1_without_oracle_unlock() -> None:
    run = build_knowledge_affordance_frame(encyclopedia_partial_unlock_fixture())
    assert run.frame is not None
    assert run.frame.locked_slot_refs
    assert run.frame.partial_slot_refs
    assert run.frame.mature_recipe_claimed is False


def test_ksurf1_no_bypass_of_p15_p16_ab7_gates() -> None:
    run = build_knowledge_affordance_frame(jei_index_hint_fixture())
    assert run.frame is not None
    assert run.frame.mature_recipe_claimed is False
    assert run.frame.value_assigned is False
    assert run.frame.automation_claimed is False


def test_ksurf1_provider_claim_does_not_confirm_cause() -> None:
    src = machine_status_hint_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"root_cause": "fuel_missing"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert run.frame is not None
    assert run.frame.cause_confirmed is False


def test_ksurf1_hidden_provider_data_public_blocked() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"backend_object_id": "hidden:obj:1"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("oracle_payload" in item for item in run.blocked_reasons)


def test_ksurf1_provider_slot_without_public_basis_blocked() -> None:
    src = encyclopedia_locked_slot_fixture()
    bad_slot = replace(src.locked_slot_refs[0], unlock_basis_refs=("provider_default:auto_unlock",))
    run = build_knowledge_affordance_frame(replace(src, locked_slot_refs=(bad_slot,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("unlock_without_public_basis" in item for item in run.blocked_reasons)


def test_ksurf1_provider_text_as_truth_rejected() -> None:
    src = manual_claim_fixture()
    bad_claim = replace(src.provider_claim_refs[0], authority_marker="truth")
    run = build_knowledge_affordance_frame(replace(src, provider_claim_refs=(bad_claim,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("oracle_payload" in item for item in run.blocked_reasons)


def test_ksurf1_provider_conflict_does_not_choose_winner() -> None:
    run = build_knowledge_affordance_frame(provider_conflict_fixture())
    assert run.frame is not None
    assert run.frame.provider_conflict_refs
    assert run.status is KnowledgeSurfaceValidationStatus.PARTIAL


def test_ksurf1_umwelts_channel_integration_source_bound() -> None:
    src = umwelts_provider_declaration_fixture()
    run = build_knowledge_affordance_frame(src)
    assert run.status in {KnowledgeSurfaceValidationStatus.ACCEPTED, KnowledgeSurfaceValidationStatus.PARTIAL}
    assert run.frame is not None
    assert run.frame.provider_refs
    assert run.frame.source_refs


def test_ksurf1_downstream_contract_forbidden_uses_present() -> None:
    run = build_knowledge_affordance_frame(jei_index_hint_fixture())
    contract = derive_ksurf1_downstream_contract(run)
    assert contract.may_emit_ap01_request is False
    assert contract.may_select_action is False
    assert any("provider_hint_as_fact_or_mature_recipe" in item for item in contract.forbidden_downstream_uses)


def test_ksurf1_selected_action_in_provider_data_blocked() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"selected_action": "mine_ore_now"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("selected_action_or_policy_forbidden" in item for item in run.blocked_reasons)


def test_ksurf1_provider_default_invents_evidence_blocked() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(
        src.provider_refs[0],
        source_refs=(),
        metadata={"provider_default_source": "auto_filled"},
    )
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("missing_source_refs" in item for item in run.blocked_reasons)


def test_ksurf1_rejects_true_recipe_hidden_in_provider_metadata() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"payload": "{'true_recipe':'ore->plate'}"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("oracle_payload" in item for item in run.blocked_reasons)


def test_ksurf1_rejects_worldstate_or_hidden_identity_payload() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"raw": "{'worldstate':{'hidden_identity':'node#17'}}"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("oracle_payload" in item or "hidden_payload" in item for item in run.blocked_reasons)


def test_ksurf1_quest_reward_does_not_assign_value_or_goal() -> None:
    src = quest_objective_hint_fixture()
    bad_hint = replace(src.objective_hint_refs[0], reward_hint_refs=("reward_value:1000",))
    run = build_knowledge_affordance_frame(replace(src, objective_hint_refs=(bad_hint,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert run.frame is not None
    assert run.frame.goal_selected is False
    assert run.frame.value_assigned is False


def test_ksurf1_machine_status_does_not_confirm_cause_even_with_confident_text() -> None:
    src = machine_status_hint_fixture()
    bad_hint = replace(src.machine_status_hint_refs[0], status_candidate_refs=("status:definitive_cause:fuel_missing",))
    run = build_knowledge_affordance_frame(replace(src, machine_status_hint_refs=(bad_hint,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert run.frame is not None
    assert run.frame.cause_confirmed is False


def test_ksurf1_scanner_identity_candidate_does_not_become_identity_truth_even_if_confident() -> None:
    src = scanner_candidate_fixture()
    bad_hint = replace(src.scanner_candidate_hint_refs[0], identity_candidate_refs=("candidate:definitive_identity:iron_ore",))
    run = build_knowledge_affordance_frame(replace(src, scanner_candidate_hint_refs=(bad_hint,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert run.frame is not None
    assert run.frame.fact_claimed is False


def test_ksurf1_provider_conflict_no_last_write_wins() -> None:
    src = provider_conflict_fixture()
    conflicts = detect_provider_conflicts(src)
    assert conflicts
    assert all(item.chosen_winner is None for item in conflicts)
    assert all(item.resolution_status == "unresolved" for item in conflicts)


def test_ksurf1_partial_slot_cannot_be_used_as_recipe_candidate_maturity() -> None:
    src = encyclopedia_partial_unlock_fixture()
    mature = TransformationHintRef(
        hint_id="hint:transform:mature_attempt",
        provider_ref=src.provider_refs[0].provider_id,
        input_candidate_refs=("resource:ore",),
        output_candidate_refs=("resource:plate",),
        station_candidate_refs=("station:smelter",),
        condition_candidate_refs=("condition:powered",),
        source_refs=("source:encyclopedia:visible",),
        maturity=True,
    )
    run = build_knowledge_affordance_frame(replace(src, transformation_hint_refs=(mature,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("mature" in item for item in run.blocked_reasons)


def test_ksurf1_provider_hint_cannot_create_ab7_readiness() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"ab7_ready": "true"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED


def test_ksurf1_provider_hint_cannot_create_p15_mature_recipe() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"p15_mature_recipe": "iron_plate"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED


def test_ksurf1_provider_hint_cannot_create_p16_value_chain() -> None:
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"p16_value_chain": "ore->plate->profit"})
    run = build_knowledge_affordance_frame(replace(src, provider_refs=(bad_provider,)))
    assert run.status is KnowledgeSurfaceValidationStatus.BLOCKED


def test_ksurf1_unknown_provider_requires_source_uncertainty_lossiness() -> None:
    src = manual_claim_fixture()
    unknown = replace(
        src.provider_refs[0],
        provider_kind=ProviderKind.UNKNOWN_PROVIDER,
        authority_class=ProviderAuthorityClass.UNKNOWN_SOURCE,
        source_refs=("source:unknown:provider",),
        uncertainty_refs=(),
        lossiness_refs=(),
    )
    blocked = build_knowledge_affordance_frame(replace(src, provider_refs=(unknown,), provider_claim_refs=()))
    assert blocked.status is KnowledgeSurfaceValidationStatus.BLOCKED
    assert any("unknown_provider_requires_uncertainty" in item for item in blocked.blocked_reasons)
    assert any("unknown_provider_requires_lossiness" in item for item in blocked.blocked_reasons)


def test_ksurf1_outputs_are_projection_compatible_without_action_authority() -> None:
    run = build_knowledge_affordance_frame(stale_lossy_provider_fixture())
    assert run.frame is not None
    assert run.frame.provider_refs
    assert run.frame.source_refs
    assert run.frame.uncertainty_refs
    assert run.frame.lossiness_refs
    assert run.frame.action_request_emitted is False
    assert run.frame.action_selected is False
    assert run.frame.goal_selected is False
