from __future__ import annotations

from dataclasses import dataclass

from .models import WorldRunnerLoopResult


@dataclass(frozen=True, slots=True)
class WORLD0DownstreamContract:
    run_ref: str
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_umwelt0: bool
    compatible_with_projection_gate: bool
    compatible_with_subject_tick: bool
    compatible_with_ap01_execution_boundary: bool
    no_action_authority: bool
    no_publication_authority: bool
    no_execution_without_ap01: bool


def derive_world0_downstream_contract(result: WorldRunnerLoopResult) -> WORLD0DownstreamContract:
    return WORLD0DownstreamContract(
        run_ref=result.run_id,
        allowed_downstream_uses=(
            "generic_world_orchestration_through_umwelts_umwelt0_projection_tick_ap01_effect_feedback",
            "blocked_noop_cycle_visibility_for_ab_residue_revision",
            "replay_trace_for_world_cycle_audit_without_planner_authority",
            "adapter_family_agnostic_execution_boundary_via_ap01_only",
        ),
        forbidden_downstream_uses=(
            "runner_action_or_goal_or_candidate_selection",
            "runner_ap01_request_creation",
            "backend_execution_without_ap01_envelope",
            "contactspec_as_planner_or_factory_script",
            "provider_or_adapter_truth_oracle_for_subject_path",
            "p17b_or_exp1_or_path1_or_actlearn1_behavior_claim",
        ),
        compatible_with_umwelt0=True,
        compatible_with_projection_gate=True,
        compatible_with_subject_tick=True,
        compatible_with_ap01_execution_boundary=True,
        no_action_authority=True,
        no_publication_authority=True,
        no_execution_without_ap01=True,
    )
