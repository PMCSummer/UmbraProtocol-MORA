from __future__ import annotations

from dataclasses import dataclass

from .models import ProjectedSubjectTickInputs


@dataclass(frozen=True, slots=True)
class ContactProjectionDownstreamContract:
    projection_ref: str
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_ab_int: bool
    compatible_with_acp01_basis: bool
    compatible_with_ap01_lineage: bool
    no_action_authority: bool
    no_publication_authority: bool
    no_execution_authority: bool


def derive_contact_projection_downstream_contract(
    result: ProjectedSubjectTickInputs,
) -> ContactProjectionDownstreamContract:
    return ContactProjectionDownstreamContract(
        projection_ref=result.projection_id,
        allowed_downstream_uses=(
            "ab_int_public_evidence_ingestion",
            "acp01_candidate_basis_ingestion",
            "ap01_request_effect_lineage_passthrough",
            "subject_tick_future_world0_projection_packet_ingestion",
        ),
        forbidden_downstream_uses=(
            "contact_as_worldstate_dump",
            "action_surface_as_selected_action_or_command",
            "knowledge_hint_as_truth_or_mature_recipe",
            "language_claim_as_truth_or_world_fact",
            "sensory_candidate_as_mature_object_truth",
            "projection_as_ap01_request_emitter",
            "projection_as_world_submission_emitter",
            "projection_as_action_selector_or_planner",
        ),
        compatible_with_ab_int=True,
        compatible_with_acp01_basis=True,
        compatible_with_ap01_lineage=True,
        no_action_authority=True,
        no_publication_authority=True,
        no_execution_authority=True,
    )

