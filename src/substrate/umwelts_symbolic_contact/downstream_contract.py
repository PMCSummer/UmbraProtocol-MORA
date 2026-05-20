from __future__ import annotations

from dataclasses import dataclass

from .models import ContactSpecValidationResult


@dataclass(frozen=True, slots=True)
class UMWELTSDownstreamContract:
    spec_ref: str
    ir_ref: str | None
    umwelt0_plan_ref: str | None
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_umwelt0: bool
    compatible_with_contact_projection_gate: bool
    no_action_authority: bool
    no_publication_authority: bool
    no_execution_authority: bool


def derive_umwelts_downstream_contract(result: ContactSpecValidationResult) -> UMWELTSDownstreamContract:
    return UMWELTSDownstreamContract(
        spec_ref=result.spec_id,
        ir_ref=result.normalized_ir.ir_id if result.normalized_ir is not None else None,
        umwelt0_plan_ref=result.umwelt0_construction_plan.plan_id if result.umwelt0_construction_plan is not None else None,
        allowed_downstream_uses=(
            "umwelt0_contact_construction_plan_generation",
            "contact_projection_gate_consumes_validated_public_contact",
            "future_world0_runner_consumes_contact_ir_without_world_truth_shortcut",
            "future_k_surf1_provider_affordance_binding_under_hint_only_discipline",
        ),
        forbidden_downstream_uses=(
            "spec_as_planner_or_action_selector",
            "spec_as_worldstate_oracle",
            "provider_hint_as_fact_or_mature_recipe",
            "language_or_sensory_contact_as_truth_or_object_identity",
            "spec_creates_ap01_request_or_world_action",
            "spec_assigns_value_or_matures_skill",
        ),
        compatible_with_umwelt0=True,
        compatible_with_contact_projection_gate=True,
        no_action_authority=True,
        no_publication_authority=True,
        no_execution_authority=True,
    )

