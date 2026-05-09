from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.m02_predictive_relevance import (
    M02InputBundle,
    M02PredictiveFeedback,
    M02PredictiveTrace,
    M02PredictionTarget,
    M02TargetType,
    M02TraceKind,
    M02UtilityHorizon,
    build_m02_predictive_relevance,
)


def _base_trace(scenario: str) -> M02PredictiveTrace:
    return M02PredictiveTrace(
        trace_id=f"{scenario}:trace",
        trace_kind=M02TraceKind.ROUTINE,
        semantic_label="routine_low_vividness_signal",
        boredom_level=0.8,
        vividness_level=0.2,
        novelty_level=0.2,
        timestamp_or_sequence="seq:1",
        context_scope="demo_scope",
        mode_context="mode:analysis",
        tool_context="tool:diagnostic",
        homeostatic_strength_hint=0.2,
        provenance=("tools.m02_demo.trace", scenario),
    )


def _target(scenario: str) -> M02PredictionTarget:
    return M02PredictionTarget(
        target_id=f"{scenario}:target",
        target_type=M02TargetType.REGIME_DETECTION,
        utility_horizon=M02UtilityHorizon.SHORT,
        context_scope="demo_scope",
        success_metric="prediction_gain",
        provenance=("tools.m02_demo.target", scenario),
    )


def _bundle_for_scenario(scenario: str) -> M02InputBundle:
    trace = _base_trace(scenario)
    target = _target(scenario)
    feedback = M02PredictiveFeedback(
        feedback_id=f"{scenario}:feedback",
        trace_id=trace.trace_id,
        target_id=target.target_id,
        prediction_gain=0.0,
        error_delta=0.0,
        corroboration_count=3,
        failed_transfer_count=0,
        spurious_risk_score=0.1,
        context_locked=False,
        attribution_noise_risk=False,
        confidence=0.82,
        provenance=("tools.m02_demo.feedback", scenario),
    )

    if scenario == "boring_predictive":
        feedback = replace(feedback, prediction_gain=0.78, corroboration_count=4)
    elif scenario == "repetition_only":
        feedback = replace(feedback, prediction_gain=0.0, corroboration_count=7)
    elif scenario == "vivid_non_predictive":
        trace = replace(
            trace,
            semantic_label="vivid_high_novelty_trace",
            boredom_level=0.1,
            vividness_level=0.95,
            novelty_level=0.95,
        )
        feedback = replace(feedback, trace_id=trace.trace_id, prediction_gain=0.08)
    elif scenario == "context_locked":
        feedback = replace(
            feedback,
            prediction_gain=0.68,
            corroboration_count=4,
            context_locked=True,
        )
    elif scenario == "spurious":
        feedback = replace(
            feedback,
            prediction_gain=0.82,
            corroboration_count=8,
            spurious_risk_score=0.92,
        )
    elif scenario == "m01_separation":
        high_m01 = replace(
            trace,
            trace_id=f"{scenario}:trace:high_m01",
            homeostatic_strength_hint=0.95,
            semantic_label="high_homeostatic_low_predictive",
        )
        low_m01 = replace(
            trace,
            trace_id=f"{scenario}:trace:low_m01",
            homeostatic_strength_hint=0.05,
            semantic_label="low_homeostatic_high_predictive",
        )
        t1 = replace(target, target_id=f"{scenario}:target:one")
        t2 = replace(target, target_id=f"{scenario}:target:two")
        f1 = replace(
            feedback,
            feedback_id=f"{scenario}:feedback:one",
            trace_id=high_m01.trace_id,
            target_id=t1.target_id,
            prediction_gain=0.02,
            corroboration_count=5,
        )
        f2 = replace(
            feedback,
            feedback_id=f"{scenario}:feedback:two",
            trace_id=low_m01.trace_id,
            target_id=t2.target_id,
            prediction_gain=0.76,
            corroboration_count=4,
        )
        return M02InputBundle(
            bundle_id=f"demo:{scenario}:bundle",
            traces=(high_m01, low_m01),
            prediction_targets=(t1, t2),
            predictive_feedback=(f1, f2),
            source_lineage=("tools.m02_demo", scenario),
            reason=f"demo scenario: {scenario}",
        )

    return M02InputBundle(
        bundle_id=f"demo:{scenario}:bundle",
        traces=(trace,),
        prediction_targets=(target,),
        predictive_feedback=(feedback,),
        source_lineage=("tools.m02_demo", scenario),
        reason=f"demo scenario: {scenario}",
    )


def run_demo(scenario: str) -> int:
    bundle = _bundle_for_scenario(scenario)
    result = build_m02_predictive_relevance(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=bundle,
        relevance_enabled=True,
    )
    print("M02 PREDICTIVE RELEVANCE DEMO")
    print(f"scenario={scenario}")
    print(f"trace_count={len(bundle.traces)}")
    print(f"target_count={len(bundle.prediction_targets)}")
    print(f"feedback_count={len(bundle.predictive_feedback)}")
    for mark in result.predictive_marks:
        print(
            "mark="
            f"(trace={mark.source_trace_id}, decision={mark.decision.value}, strength={mark.relevance_strength}, "
            f"targets={[item.value for item in mark.predicted_target_types]}, horizon={mark.utility_horizon.value}, "
            f"context={mark.context_scope}, must_not_generalize={mark.must_not_generalize})"
        )
        print(
            "biases="
            f"(retention={mark.retention_bias}, retrieval={mark.retrieval_bias}, replay={mark.replay_priority}, "
            f"indexing={mark.indexing_bias}, planning_support={mark.planning_support_recall_bias})"
        )
        print(f"anti_spurious_limits={mark.anti_spurious_limits}")
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, must_preserve_context={result.gate.downstream_must_preserve_context}, "
        f"must_not_generalize={result.gate.downstream_must_not_generalize}, "
        f"must_not_treat_as_generic_importance={result.gate.downstream_must_not_treat_as_generic_importance})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic M02 predictive relevance scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "boring_predictive",
            "repetition_only",
            "vivid_non_predictive",
            "context_locked",
            "spurious",
            "m01_separation",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
