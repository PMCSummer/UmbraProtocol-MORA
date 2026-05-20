from __future__ import annotations

from substrate.umwelts_symbolic_contact import ProviderSurfaceSpec, ContactSourceRequirement

from .models import (
    KnowledgeAffordanceKind,
    KnowledgeProviderRef,
    KnowledgeSlotState,
    KnowledgeSurfaceInput,
    LockedSlotRef,
    MachineStatusHintRef,
    ObjectiveHintRef,
    PartialSlotRef,
    ProviderAuthorityClass,
    ProviderClaimRef,
    ProviderKind,
    ScannerCandidateHintRef,
    StationCapabilityHintRef,
    TransformationHintRef,
)


def jei_index_hint_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:jei",
        provider_kind=ProviderKind.JEI_INDEX,
        authority_class=ProviderAuthorityClass.INDEX,
        channel_ref="knowledge_affordance",
        source_refs=("source:jei:index",),
    )
    claim = ProviderClaimRef(
        claim_id="claim:jei:smelter",
        provider_ref=provider.provider_id,
        claim_kind=KnowledgeAffordanceKind.PROVIDER_INDEX_HINT,
        target_ref="station:smelter",
        claim_text_ref="hint:smelter_slot_candidates",
        source_refs=("source:jei:index",),
    )
    transformation = TransformationHintRef(
        hint_id="hint:transform:ore_to_plate",
        provider_ref=provider.provider_id,
        input_candidate_refs=("resource:ore",),
        output_candidate_refs=("resource:plate",),
        station_candidate_refs=("station:smelter",),
        condition_candidate_refs=("condition:powered",),
        source_refs=("source:jei:index",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:jei_hint",
        provider_refs=(provider,),
        provider_claim_refs=(claim,),
        transformation_hint_refs=(transformation,),
    )


def encyclopedia_locked_slot_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:encyclopedia",
        provider_kind=ProviderKind.ENCYCLOPEDIA,
        authority_class=ProviderAuthorityClass.INDEX,
        channel_ref="knowledge_affordance",
        source_refs=("source:encyclopedia:visible",),
    )
    slot = LockedSlotRef(
        slot_id="slot:recipe:plate",
        slot_kind="recipe_slot",
        provider_ref=provider.provider_id,
        visible_basis_refs=("visible_cell:plate_recipe",),
        unlock_basis_refs=(),
        slot_state=KnowledgeSlotState.LOCKED,
        source_refs=("source:encyclopedia:visible",),
        uncertainty_refs=("uncertain:locked_slot",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:encyclopedia_locked",
        provider_refs=(provider,),
        locked_slot_refs=(slot,),
    )


def encyclopedia_partial_unlock_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:encyclopedia",
        provider_kind=ProviderKind.ENCYCLOPEDIA,
        authority_class=ProviderAuthorityClass.INDEX,
        channel_ref="knowledge_affordance",
        source_refs=("source:encyclopedia:visible",),
    )
    locked = LockedSlotRef(
        slot_id="slot:recipe:plate",
        slot_kind="recipe_slot",
        provider_ref=provider.provider_id,
        visible_basis_refs=("visible_cell:plate_recipe",),
        unlock_basis_refs=("public_discovery:ore",),
        slot_state=KnowledgeSlotState.LOCKED,
        source_refs=("source:encyclopedia:visible",),
        uncertainty_refs=("uncertain:unlock_partial",),
    )
    partial = PartialSlotRef(
        slot_id="slot:recipe:plate:partial",
        slot_kind="recipe_slot_partial",
        known_part_refs=("known_input:ore",),
        unknown_part_refs=("unknown_input:fuel",),
        missing_evidence_refs=("missing:effect_trace",),
        source_refs=("source:encyclopedia:visible",),
        uncertainty_refs=("uncertain:partial_slot",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:encyclopedia_partial",
        provider_refs=(provider,),
        locked_slot_refs=(locked,),
        partial_slot_refs=(partial,),
    )


def quest_objective_hint_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:questbook",
        provider_kind=ProviderKind.QUESTBOOK,
        authority_class=ProviderAuthorityClass.QUEST_OBJECTIVE,
        channel_ref="knowledge_affordance",
        source_refs=("source:questbook:ui",),
    )
    objective = ObjectiveHintRef(
        hint_id="hint:quest:collect_ore",
        provider_ref=provider.provider_id,
        objective_text_ref="quest:collect_ore_0_10",
        target_candidate_refs=("resource:ore",),
        reward_hint_refs=("reward:unlock_hint",),
        source_refs=("source:questbook:ui",),
        uncertainty_refs=("uncertain:quest_text_hint",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:quest_objective",
        provider_refs=(provider,),
        objective_hint_refs=(objective,),
    )


def machine_status_hint_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:machine_ui",
        provider_kind=ProviderKind.MACHINE_UI,
        authority_class=ProviderAuthorityClass.MACHINE_STATUS,
        channel_ref="knowledge_affordance",
        source_refs=("source:machine_ui:panel",),
    )
    hint = MachineStatusHintRef(
        hint_id="hint:machine:status",
        machine_or_station_ref="station:smelter",
        status_candidate_refs=("status:unpowered", "status:input_missing"),
        source_refs=("source:machine_ui:panel",),
        uncertainty_refs=("uncertain:status_text",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:machine_status",
        provider_refs=(provider,),
        machine_status_hint_refs=(hint,),
    )


def scanner_candidate_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:scanner",
        provider_kind=ProviderKind.SCANNER,
        authority_class=ProviderAuthorityClass.SCANNER_CANDIDATE,
        channel_ref="knowledge_affordance",
        source_refs=("source:scanner:readout",),
    )
    hint = ScannerCandidateHintRef(
        hint_id="hint:scanner:ore_node",
        scanned_ref="entity:node_17",
        identity_candidate_refs=("candidate:iron_ore",),
        property_candidate_refs=("candidate:hardness_mid",),
        source_refs=("source:scanner:readout",),
        uncertainty_refs=("uncertain:scanner_candidate",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:scanner_candidate",
        provider_refs=(provider,),
        scanner_candidate_hint_refs=(hint,),
    )


def manual_claim_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:manual",
        provider_kind=ProviderKind.MANUAL,
        authority_class=ProviderAuthorityClass.MANUAL_CLAIM,
        channel_ref="knowledge_affordance",
        source_refs=("source:manual:text",),
    )
    claim = ProviderClaimRef(
        claim_id="claim:manual:tip",
        provider_ref=provider.provider_id,
        claim_kind=KnowledgeAffordanceKind.MANUAL_CLAIM_HINT,
        target_ref="station:smelter",
        claim_text_ref="manual:smelter_requires_input_and_power",
        source_refs=("source:manual:text",),
        uncertainty_refs=("uncertain:manual_claim",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:manual_claim",
        provider_refs=(provider,),
        provider_claim_refs=(claim,),
    )


def provider_conflict_fixture() -> KnowledgeSurfaceInput:
    provider_a = KnowledgeProviderRef(
        provider_id="provider:manual_a",
        provider_kind=ProviderKind.MANUAL,
        authority_class=ProviderAuthorityClass.MANUAL_CLAIM,
        channel_ref="knowledge_affordance",
        source_refs=("source:manual:a",),
    )
    provider_b = KnowledgeProviderRef(
        provider_id="provider:manual_b",
        provider_kind=ProviderKind.MANUAL,
        authority_class=ProviderAuthorityClass.MANUAL_CLAIM,
        channel_ref="knowledge_affordance",
        source_refs=("source:manual:b",),
    )
    claim_a = ProviderClaimRef(
        claim_id="claim:a",
        provider_ref=provider_a.provider_id,
        claim_kind=KnowledgeAffordanceKind.TRANSFORMATION_HINT,
        target_ref="resource:plate",
        claim_text_ref="manual_a:ore_plus_fuel",
        source_refs=("source:manual:a",),
        slot_refs=("slot:recipe:plate",),
    )
    claim_b = ProviderClaimRef(
        claim_id="claim:b",
        provider_ref=provider_b.provider_id,
        claim_kind=KnowledgeAffordanceKind.TRANSFORMATION_HINT,
        target_ref="resource:plate",
        claim_text_ref="manual_b:ore_plus_water",
        source_refs=("source:manual:b",),
        slot_refs=("slot:recipe:plate",),
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:provider_conflict",
        provider_refs=(provider_a, provider_b),
        provider_claim_refs=(claim_a, claim_b),
    )


def hidden_provider_blocked_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:hidden",
        provider_kind=ProviderKind.UNKNOWN_PROVIDER,
        authority_class=ProviderAuthorityClass.UNKNOWN_SOURCE,
        channel_ref="knowledge_affordance",
        source_refs=("source:hidden",),
        protected_eval=True,
        scenario_label=True,
        metadata={"eval_label": "gold_truth", "scenario_label": "case_01"},
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:hidden_provider",
        provider_refs=(provider,),
    )


def stale_lossy_provider_fixture() -> KnowledgeSurfaceInput:
    provider = KnowledgeProviderRef(
        provider_id="provider:status_panel",
        provider_kind=ProviderKind.STATUS_PANEL,
        authority_class=ProviderAuthorityClass.UI_STATUS,
        channel_ref="knowledge_affordance",
        source_refs=("source:status_panel",),
        uncertainty_refs=("uncertain:stale_panel",),
        lossiness_refs=("lossiness:cached_status",),
        metadata={"cache_state": "stale"},
    )
    claim = ProviderClaimRef(
        claim_id="claim:status:stale",
        provider_ref=provider.provider_id,
        claim_kind=KnowledgeAffordanceKind.MACHINE_STATUS_HINT,
        target_ref="station:smelter",
        claim_text_ref="status:stalled_maybe",
        source_refs=("source:status_panel",),
        uncertainty_refs=("uncertain:stale_panel",),
        lossiness_refs=("lossiness:cached_status",),
        stale_marker="stale",
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:stale_lossy",
        provider_refs=(provider,),
        provider_claim_refs=(claim,),
    )


def umwelts_provider_declaration_fixture() -> KnowledgeSurfaceInput:
    declaration = ProviderSurfaceSpec(
        provider_id="umwelts:provider:manual",
        provider_kind="manual_tooltip",
        channel_id="ch:knowledge",
        authority_class="hint_only",
        source_requirements=ContactSourceRequirement(required=True, source_refs=("source:umwelts:manual",)),
        hint_only=True,
        truth_authority=False,
        can_mature_recipe=False,
        can_assign_value=False,
        can_select_action=False,
    )
    provider = KnowledgeProviderRef(
        provider_id=declaration.provider_id,
        provider_kind=ProviderKind.MANUAL,
        authority_class=ProviderAuthorityClass.MANUAL_CLAIM,
        channel_ref=declaration.channel_id,
        source_refs=declaration.source_requirements.source_refs,
    )
    return KnowledgeSurfaceInput(
        frame_id="ksurf1:umwelts_integration",
        provider_refs=(provider,),
        from_umwelts_provider_declarations=(declaration,),
    )

