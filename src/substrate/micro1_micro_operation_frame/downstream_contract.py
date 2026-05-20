from __future__ import annotations

from dataclasses import dataclass

from .models import MicroOperationValidationResult


@dataclass(frozen=True, slots=True)
class MICRO1DownstreamContract:
    operation_ref: str | None
    graph_ref: str | None
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_acp01_basis: bool
    compatible_with_ap01_lineage: bool
    compatible_with_ab_evidence: bool
    no_action_authority: bool
    no_publication_authority: bool
    no_execution_authority: bool


def derive_micro1_downstream_contract(result: MicroOperationValidationResult) -> MICRO1DownstreamContract:
    return MICRO1DownstreamContract(
        operation_ref=result.operation.operation_id if result.operation is not None else None,
        graph_ref=result.graph.graph_id if result.graph is not None else None,
        allowed_downstream_uses=(
            "candidate_basis_packet_for_acp01",
            "ap01_request_effect_lineage_reference_only",
            "ab_public_evidence_and_residue_basis",
            "bounded_micro_graph_input_for_future_world0_or_p17b",
        ),
        forbidden_downstream_uses=(
            "micro1_as_action_selector_or_goal_selector",
            "micro1_emits_ap01_request_or_world_submission",
            "knowledge_or_quest_or_cost_hint_as_operation_truth_permission",
            "recipe_candidate_as_operation_script_or_automation",
            "macro_task_atomic_command_without_micro_decomposition",
            "success_claim_without_public_effect_lineage",
        ),
        compatible_with_acp01_basis=True,
        compatible_with_ap01_lineage=True,
        compatible_with_ab_evidence=True,
        no_action_authority=True,
        no_publication_authority=True,
        no_execution_authority=True,
    )
