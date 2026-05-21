from __future__ import annotations

from dataclasses import dataclass

from .models import P17BLiveMiniFactoryRun


@dataclass(frozen=True, slots=True)
class P17BDownstreamContract:
    run_ref: str
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    world0_required: bool
    ap01_required: bool
    verified_intermediate_required: bool
    no_factory_automation_claim: bool
    no_autonomy_claim: bool


def derive_p17b_downstream_contract(run: P17BLiveMiniFactoryRun) -> P17BDownstreamContract:
    return P17BDownstreamContract(
        run_ref=run.run_id,
        allowed_downstream_uses=(
            "bounded_live_symbolic_minifactory_trace_validation",
            "residue_and_uncertainty_preserving_chain_progress_checks",
            "world0_ap01_effect_lineage_audit",
        ),
        forbidden_downstream_uses=(
            "treat_as_general_factory_automation",
            "treat_as_planner_or_action_selector",
            "execute_without_world0_or_ap01",
            "treat_provider_or_cost_hints_as_permission",
            "claim_general_autonomy_or_mature_skill_recipe",
        ),
        world0_required=True,
        ap01_required=True,
        verified_intermediate_required=True,
        no_factory_automation_claim=True,
        no_autonomy_claim=True,
    )

