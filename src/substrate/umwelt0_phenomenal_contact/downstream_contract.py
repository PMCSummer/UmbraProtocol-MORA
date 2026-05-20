from __future__ import annotations

from dataclasses import dataclass

from .models import ContactConformanceResult


@dataclass(frozen=True, slots=True)
class UMWELT0DownstreamContract:
    frame_ref: str
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_ab_int: bool
    no_action_authority: bool
    no_publication_authority: bool
    no_execution_authority: bool


def derive_umwelt0_downstream_contract(result: ContactConformanceResult) -> UMWELT0DownstreamContract:
    frame = result.phenomenal_contact_frame
    return UMWELT0DownstreamContract(
        frame_ref=frame.frame_id,
        allowed_downstream_uses=(
            "ab1_event_digest_basis_from_public_observation_effect_residue",
            "ab2_ab3_hypothesis_frontier_from_uncertainty_conflict_residue",
            "ab4_epistemic_basis_from_unresolved_contact",
            "acp01_action_surface_considered_as_possible_surface_only",
            "world0_future_loop_contact_to_tick_to_ap01_to_effect",
            "k_surf1_future_source_bound_knowledge_refs",
        ),
        forbidden_downstream_uses=(
            "treat_contact_as_worldstate",
            "treat_action_surface_as_action_request",
            "treat_effect_as_fact_or_cause_proof",
            "use_hidden_eval_as_public_basis",
            "use_provider_hint_as_mature_recipe_skill_value",
            "claim_world_understanding_from_contact_only",
        ),
        compatible_with_ab_int=True,
        no_action_authority=True,
        no_publication_authority=True,
        no_execution_authority=True,
    )

