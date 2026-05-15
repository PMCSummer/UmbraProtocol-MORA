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

from substrate.w06_error_driven_revision import W06MismatchClass
from tests.substrate.w06_error_driven_revision_testkit import (
    build_w06_harness,
    clone_bundle,
    w06_bundle,
    w06_context,
    w06_mismatch,
)


def _scenario_input(scenario: str):
    base = w06_bundle(scenario)
    if scenario == "clean_local_downgrade_from_world_model_mismatch":
        return clone_bundle(
            base,
            contradiction_intake=(),
            mismatch_intake=w06_mismatch(
                scenario,
                mismatch_class=W06MismatchClass.WORLD_MODEL,
                evidence_precision=0.9,
                source_reliability=0.9,
            ),
        )
    if scenario == "contradiction_blocks_claim":
        return clone_bundle(base, mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.AUTHORITY_SCOPE))
    if scenario == "repeated_revalidation_triggers_anti_paralysis":
        return clone_bundle(
            base,
            contradiction_intake=(),
            mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.VALIDITY),
            revision_context=w06_context(scenario, repeated_revalidation_count=5, progress_detected=False, loop_threshold=3),
        )
    if scenario == "identity_split_candidate":
        return clone_bundle(
            base,
            contradiction_intake=(),
            mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.OWNERSHIP),
        )
    if scenario == "correction_candidate_not_executed":
        return base
    if scenario == "local_error_not_global_invalidation":
        return clone_bundle(base, contradiction_intake=(), mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.AFFORDANCE))
    if scenario == "confidence_drop_precision_sensitive":
        return clone_bundle(base, contradiction_intake=(), mismatch_intake=w06_mismatch(scenario, evidence_precision=0.95, source_reliability=0.95, severity="critical"))
    if scenario == "protected_target_escalates":
        return clone_bundle(base, mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.CONSTITUTIONAL_BOUNDARY, severity="high", constitutional_guard_flags=("protected",)))
    if scenario == "residual_uncertainty_preserved_after_downgrade":
        return clone_bundle(base, contradiction_intake=(), mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.WORLD_MODEL, evidence_precision=0.9))
    if scenario == "ambiguous_mismatch_retains_competing_routes":
        return clone_bundle(base, contradiction_intake=(), mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.AMBIGUOUS_MULTI_CLASS, ambiguity_markers=("ambiguous",)))
    if scenario == "claim_block_propagates_to_downstream":
        return clone_bundle(base, mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.AUTHORITY_SCOPE))
    if scenario == "decorative_contradiction_forbidden":
        return clone_bundle(base, mismatch_intake=w06_mismatch(scenario, mismatch_class=W06MismatchClass.AUTHORITY_SCOPE))
    raise ValueError(scenario)


def run_demo(scenario: str) -> int:
    bundle = _scenario_input(scenario)
    result = build_w06_harness(scenario, input_bundle=bundle)

    print("W06 ERROR-DRIVEN REVISION DEMO")
    print(f"scenario={scenario}")
    print(
        "decision="
        f"(consequence={result.decision.consequence_type.value}, scope={result.decision.revision_scope.value}, "
        f"route={result.decision.route_status.value})"
    )
    print(
        "counts="
        f"(revalidate={result.telemetry.revalidate_count}, downgrade={result.telemetry.downgrade_count}, "
        f"invalidate={result.telemetry.invalidate_count}, split_identity={result.telemetry.split_identity_count}, "
        f"block_claim={result.telemetry.block_claim_count}, quarantine={result.telemetry.quarantine_count}, "
        f"residue={result.telemetry.residue_retention_count}, anti_paralysis={result.telemetry.anti_paralysis_count})"
    )
    print(
        "seam="
        f"(execution_prohibited={result.correction_candidate.execution_prohibited}, "
        f"must_not_execute_correction={result.downstream_packet.must_not_execute_correction}, "
        f"must_block_claim={result.downstream_packet.must_block_claim}, "
        f"must_revalidate={result.downstream_packet.must_revalidate}, "
        f"must_escalate={result.downstream_packet.must_escalate})"
    )
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, no_clean_revision={result.gate.no_clean_revision}, "
        f"required_restrictions={result.gate.required_restrictions})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic W06 error-driven revision scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "clean_local_downgrade_from_world_model_mismatch",
            "contradiction_blocks_claim",
            "repeated_revalidation_triggers_anti_paralysis",
            "identity_split_candidate",
            "correction_candidate_not_executed",
            "local_error_not_global_invalidation",
            "confidence_drop_precision_sensitive",
            "protected_target_escalates",
            "residual_uncertainty_preserved_after_downgrade",
            "ambiguous_mismatch_retains_competing_routes",
            "claim_block_propagates_to_downstream",
            "decorative_contradiction_forbidden",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
