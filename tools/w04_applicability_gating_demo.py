from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.w04_applicability_gating import (
    W04ConstraintHardness,
    W04ConstraintType,
)
from tests.substrate.w04_applicability_gating_testkit import (
    build_w04_harness,
    clone_input,
    w04_constraint,
    w04_desired_state,
    w04_input_bundle,
    w04_intake,
    w04_context,
    w04_perspective,
    w04_profile,
)


def _base(case_id: str):
    intake = w04_intake(case_id=case_id)
    desired = w04_desired_state(case_id=case_id)
    ctx = w04_context(case_id=case_id)
    frame = w04_perspective()
    profile = w04_profile(
        case_id=case_id,
        world_constraints=(
            w04_constraint(
                constraint_id=f"{case_id}:world-hard",
                constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
                hard_or_soft=W04ConstraintHardness.HARD,
                current_status="passed",
            ),
        ),
    )
    return w04_input_bundle(
        case_id=case_id,
        intake_views=(intake,),
        desired_state=desired,
        context=ctx,
        perspective=frame,
        profile=profile,
    )


def _scenario_input(scenario: str):
    base = _base(scenario)

    if scenario == "clean_allowed_bounded_prior":
        return base
    if scenario == "w03_must_revalidate_blocks_clean_deploy":
        intake = replace(base.w03_intake_views[0], must_revalidate_before_use=True)
        return clone_input(base, w03_intake_views=(intake,))
    if scenario == "stale_prior_revalidation":
        intake = replace(base.w03_intake_views[0], stale_or_revalidation_status=("stale",))
        return clone_input(base, w03_intake_views=(intake,))
    if scenario == "hard_world_constraint_blocks":
        hard = w04_constraint(
            constraint_id=f"{scenario}:hard",
            constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
            hard_or_soft=W04ConstraintHardness.HARD,
            current_status="failed",
        )
        profile = w04_profile(case_id=scenario, world_constraints=(hard,))
        return clone_input(base, constraint_profile=profile)
    if scenario == "soft_constraint_relaxes_with_ledger":
        soft = w04_constraint(
            constraint_id="soft_conflict",
            constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
            hard_or_soft=W04ConstraintHardness.SOFT,
            current_status="failed",
        )
        profile = w04_profile(
            case_id=scenario,
            world_constraints=base.constraint_profile.world_constraints,
            epistemic_constraints=(soft,),
        )
        desired = w04_desired_state(case_id=scenario, acceptable_relaxation_dimensions=("soft_conflict",))
        return clone_input(base, desired_state_request=desired, constraint_profile=profile)
    if scenario == "hard_constraint_cannot_relax":
        hard = w04_constraint(
            constraint_id=f"{scenario}:hard",
            constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
            hard_or_soft=W04ConstraintHardness.HARD,
            current_status="failed",
        )
        profile = w04_profile(case_id=scenario, world_constraints=(hard,))
        desired = w04_desired_state(case_id=scenario, acceptable_relaxation_dimensions=(f"{scenario}:hard",))
        return clone_input(base, desired_state_request=desired, constraint_profile=profile)
    if scenario == "empty_intersection_blocks":
        hard = w04_constraint(
            constraint_id=f"{scenario}:hard",
            constraint_type=W04ConstraintType.SAFETY_CONSTRAINT,
            hard_or_soft=W04ConstraintHardness.HARD,
            current_status="failed",
        )
        return clone_input(base, constraint_profile=w04_profile(case_id=scenario, safety_constraints=(hard,)))
    if scenario == "authority_scope_mismatch":
        desired = w04_desired_state(case_id=scenario, source_authority="other_authority")
        return clone_input(base, desired_state_request=desired)
    if scenario == "perspective_transfer_blocked":
        desired = w04_desired_state(case_id=scenario, perspective_id="other")
        frame = w04_perspective(
            requested_perspective="other",
            source_perspective="self",
            allowed_perspective_transfer=(),
            blocked_perspective_transfer=("self->other",),
        )
        return clone_input(base, desired_state_request=desired, perspective_frame=frame)
    if scenario == "malformed_desired_state_rejected":
        desired = w04_desired_state(case_id=scenario, target_subject="")
        return clone_input(base, desired_state_request=desired)
    if scenario == "unknown_hard_feasibility_revalidates":
        unknown = w04_constraint(
            constraint_id=f"{scenario}:hard",
            constraint_type=W04ConstraintType.LEGALITY_CONSTRAINT,
            hard_or_soft=W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED,
            current_status="unknown",
        )
        return clone_input(base, constraint_profile=w04_profile(case_id=scenario, legality_constraints=(unknown,)))
    if scenario == "applicability_not_action_authorization":
        desired = w04_desired_state(case_id=scenario, intended_use="action_authorization")
        return clone_input(base, desired_state_request=desired)
    raise ValueError(scenario)


def run_demo(scenario: str) -> int:
    bundle = _scenario_input(scenario)
    result = build_w04_harness(scenario, input_bundle=bundle)
    decision = result.applicability_decisions[0] if result.applicability_decisions else None
    packet = result.downstream_permission_packets[0] if result.downstream_permission_packets else None

    print("W04 APPLICABILITY GATING DEMO")
    print(f"scenario={scenario}")
    print(
        "counts="
        f"(decisions={result.telemetry.applicability_decision_count}, allowed={result.telemetry.allowed_count}, "
        f"blocked={result.telemetry.blocked_count}, narrowed={result.telemetry.narrowed_count}, "
        f"hint_only={result.telemetry.hint_only_count}, revalidate={result.telemetry.revalidate_required_count}, "
        f"abstain={result.telemetry.abstain_count}, relaxation={result.telemetry.relaxation_count})"
    )
    if decision is not None:
        print(
            "decision="
            f"(status={decision.decision_status.value}, blocked_reason={decision.blocked_reason}, "
            f"reasons={decision.decision_reason_codes})"
        )
    if packet is not None:
        print(
            "permission="
            f"(deploy={packet.may_deploy_candidate}, hint_only={packet.may_use_as_hint_only}, "
            f"after_revalidate={packet.may_use_after_revalidation}, with_relaxation={packet.may_use_with_relaxation}, "
            f"must_block={packet.must_block}, must_abstain={packet.must_abstain}, must_revalidate={packet.must_revalidate}, "
            f"action_authorization_granted={packet.action_authorization_granted}, prohibited_uses={packet.prohibited_uses})"
        )
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, no_clean_applicability={result.gate.no_clean_applicability}, "
        f"required_restrictions={result.gate.required_restrictions})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic W04 applicability-gating scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "clean_allowed_bounded_prior",
            "w03_must_revalidate_blocks_clean_deploy",
            "stale_prior_revalidation",
            "hard_world_constraint_blocks",
            "soft_constraint_relaxes_with_ledger",
            "hard_constraint_cannot_relax",
            "empty_intersection_blocks",
            "authority_scope_mismatch",
            "perspective_transfer_blocked",
            "malformed_desired_state_rejected",
            "unknown_hard_feasibility_revalidates",
            "applicability_not_action_authorization",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
