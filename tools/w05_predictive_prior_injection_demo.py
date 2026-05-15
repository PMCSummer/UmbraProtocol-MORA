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

from substrate.w05_predictive_prior_injection import W05InjectionTarget
from tests.substrate.w05_predictive_prior_injection_testkit import (
    build_w05_harness,
    clone_input,
    w05_input_bundle,
)


def _scenario_input(scenario: str):
    base = w05_input_bundle(scenario)
    if scenario == "clean_prior_injection":
        return base
    if scenario == "w04_block_prevents_injection":
        return clone_input(base, permitted_signal=replace(base.permitted_signal, may_deploy_candidate=False, must_block=True))
    if scenario == "w04_revalidate_routes_revalidation":
        return clone_input(base, permitted_signal=replace(base.permitted_signal, may_deploy_candidate=False, must_revalidate=True, may_use_after_revalidation=True))
    if scenario == "permitted_false_blocks_predicted_utility":
        return clone_input(
            base,
            predicted_signal=replace(base.predicted_signal, prior_strength=1.0, prediction_confidence=1.0),
            permitted_signal=replace(base.permitted_signal, may_deploy_candidate=False, must_block=True),
        )
    if scenario == "desired_not_evidence":
        return clone_input(base, desired_signal=replace(base.desired_signal, requested_outcome="desired:other"))
    if scenario == "high_precision_observation_suppresses_prior":
        return clone_input(base, observed_signal=replace(base.observed_signal, evidence_precision=0.95, contradiction_markers=("c1",), observed_outcome="obs:other"))
    if scenario == "low_precision_noise_contested":
        return clone_input(base, observed_signal=replace(base.observed_signal, evidence_precision=0.1))
    if scenario == "weak_source_reduces_gain":
        return clone_input(base, predicted_signal=replace(base.predicted_signal, source_reliability=0.1))
    if scenario == "ambiguous_mismatch_revalidates":
        return clone_input(base, observed_signal=replace(base.observed_signal, evidence_precision=0.95, contradiction_markers=("c1",), observed_outcome="obs:other", observed_affordance="affordance:other"))
    if scenario == "constitutional_guard_blocks_update":
        return clone_input(base, permitted_signal=replace(base.permitted_signal, protected_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE,)))
    if scenario == "protected_target_escalates":
        return clone_input(base, permitted_signal=replace(base.permitted_signal, protected_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE,)))
    if scenario == "routing_not_execution":
        return base
    raise ValueError(scenario)


def run_demo(scenario: str) -> int:
    bundle = _scenario_input(scenario)
    result = build_w05_harness(scenario, input_bundle=bundle)
    mismatch = result.mismatch_classifications[0] if result.mismatch_classifications else None
    routing = result.update_routing_packets[0] if result.update_routing_packets else None
    packet = result.downstream_routing_packets[0] if result.downstream_routing_packets else None

    print("W05 PREDICTIVE PRIOR INJECTION DEMO")
    print(f"scenario={scenario}")
    print(
        "counts="
        f"(stack={result.telemetry.signal_stack_count}, prediction_use={result.telemetry.prediction_use_count}, "
        f"mismatch={result.telemetry.mismatch_count}, ambiguous={result.telemetry.ambiguous_mismatch_count}, "
        f"revalidate={result.telemetry.revalidate_route_count}, escalate={result.telemetry.escalate_route_count}, "
        f"abstain={result.telemetry.abstain_count})"
    )
    if mismatch is not None:
        print(
            "mismatch="
            f"(class={mismatch.mismatch_class.value}, direction={mismatch.mismatch_direction.value}, "
            f"candidates={[item.value for item in mismatch.competing_class_candidates]})"
        )
    if routing is not None:
        print(
            "routing="
            f"(target={routing.target_layer.value}, route={routing.recommended_route}, "
            f"execution_prohibited={routing.execution_prohibited})"
        )
    if packet is not None:
        print(
            "permission="
            f"(may_consider_update={packet.may_consider_update}, must_revalidate={packet.must_revalidate}, "
            f"must_escalate={packet.must_escalate}, must_abstain={packet.must_abstain}, "
            f"must_not_execute_update={packet.must_not_execute_update}, "
            f"execution_authorization_granted={packet.execution_authorization_granted})"
        )
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, no_clean_routing={result.gate.no_clean_routing}, "
        f"required_restrictions={result.gate.required_restrictions})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic W05 predictive prior-injection scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "clean_prior_injection",
            "w04_block_prevents_injection",
            "w04_revalidate_routes_revalidation",
            "permitted_false_blocks_predicted_utility",
            "desired_not_evidence",
            "high_precision_observation_suppresses_prior",
            "low_precision_noise_contested",
            "weak_source_reduces_gain",
            "ambiguous_mismatch_revalidates",
            "constitutional_guard_blocks_update",
            "protected_target_escalates",
            "routing_not_execution",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
