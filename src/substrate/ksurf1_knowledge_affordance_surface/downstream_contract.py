from __future__ import annotations

from dataclasses import dataclass

from .models import KnowledgeSurfaceValidationResult


@dataclass(frozen=True, slots=True)
class KSurf1DownstreamContract:
    frame_ref: str | None
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_umwelt0: bool
    compatible_with_umwelts: bool
    compatible_with_contact_projection_gate: bool
    may_emit_ap01_request: bool
    may_select_action: bool
    may_select_goal: bool
    may_assign_value: bool
    may_mature_recipe_or_skill: bool


def derive_ksurf1_downstream_contract(
    result: KnowledgeSurfaceValidationResult,
) -> KSurf1DownstreamContract:
    return KSurf1DownstreamContract(
        frame_ref=result.frame.frame_id if result.frame is not None else None,
        allowed_downstream_uses=(
            "source_bound_hint_surface_for_umwelts_knowledge_affordance",
            "candidate_basis_for_ab_int_without_truth_closure",
            "candidate_basis_for_exp1_inquiry_without_identity_oracle",
            "locked_or_partial_slot_basis_for_future_k1",
            "constraint_compatible_inputs_for_p15_p16_ab7",
        ),
        forbidden_downstream_uses=(
            "provider_hint_as_fact_or_mature_recipe",
            "provider_hint_as_truth_or_fact_closure",
            "provider_hint_as_action_permission",
            "provider_hint_as_goal_authority",
            "provider_hint_as_value_assignment",
            "provider_hint_as_mature_recipe_or_skill",
            "provider_hint_as_lived_evidence",
            "silent_provider_conflict_winner_selection",
            "ap01_request_emission_from_ksurf1",
        ),
        compatible_with_umwelt0=True,
        compatible_with_umwelts=True,
        compatible_with_contact_projection_gate=True,
        may_emit_ap01_request=False,
        may_select_action=False,
        may_select_goal=False,
        may_assign_value=False,
        may_mature_recipe_or_skill=False,
    )
