from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.n03_autobiographical_relevance import (
    N03AutobiographicalTraceKind,
    N03CurrentTarget,
    N03CurrentTargetKind,
    N03InputBundle,
    N03TraceCandidate,
    build_n03_autobiographical_relevance,
)


def _trace(scenario: str, **overrides) -> N03TraceCandidate:
    base = N03TraceCandidate(
        source_trace_id=f"{scenario}:trace",
        trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE,
        semantic_topic_tags=("topic:regulation",),
        commitment_refs=("commitment:alpha",),
        capability_gap_refs=(),
        affordance_refs=(),
        internal_tool_refs=(),
        self_binding_refs=(),
        attribution_profile="self",
        failure_or_recovery_signature="sig:failure",
        identity_region_refs=("region:self",),
        temporal_validity_status="valid",
        recurrence_count=3,
        vividness_hint=0.3,
        recency_hint=0.4,
        confidence=0.82,
        provenance=("tools.n03_demo.trace", scenario),
    )
    return replace(base, **overrides)


def _target(scenario: str, **overrides) -> N03CurrentTarget:
    base = N03CurrentTarget(
        current_target_id=f"{scenario}:target",
        target_kind=N03CurrentTargetKind.REGULATION_DEMAND,
        active_commitment_refs=("commitment:alpha",),
        active_capability_gap_refs=(),
        active_affordance_refs=(),
        active_internal_tool_refs=(),
        active_self_binding_refs=(),
        active_identity_region_refs=("region:self",),
        active_drift_markers=(),
        semantic_topic_tags=("topic:regulation",),
        attribution_profile="self",
        regulation_or_planning_pressure=0.74,
        current_evidence_signature="sig:current",
        provenance=("tools.n03_demo.target", scenario),
    )
    return replace(base, **overrides)


def _bundle_for_scenario(scenario: str) -> N03InputBundle:
    if scenario == "semantic_similarity_only":
        traces = (
            _trace(
                scenario,
                commitment_refs=(),
                capability_gap_refs=(),
                affordance_refs=(),
                internal_tool_refs=(),
                self_binding_refs=(),
                identity_region_refs=(),
                semantic_topic_tags=("topic:regulation",),
                recency_hint=0.92,
                vividness_hint=0.94,
            ),
        )
        targets = (
            _target(
                scenario,
                active_commitment_refs=(),
                active_capability_gap_refs=(),
                active_affordance_refs=(),
                active_internal_tool_refs=(),
                active_self_binding_refs=(),
                active_identity_region_refs=(),
                semantic_topic_tags=("topic:regulation",),
            ),
        )
    elif scenario == "recovery_pattern":
        traces = (
            _trace(
                scenario,
                trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY,
                failure_or_recovery_signature="sig:recovery",
                recurrence_count=4,
            ),
        )
        targets = (
            _target(
                scenario,
                target_kind=N03CurrentTargetKind.RECOVERY_NEED,
            ),
        )
    elif scenario == "single_episode_overgeneralization":
        traces = (_trace(scenario, recurrence_count=1),)
        targets = (_target(scenario),)
    elif scenario == "identity_drift_blocks_transfer":
        traces = (_trace(scenario, recurrence_count=3),)
        targets = (_target(scenario, active_drift_markers=("drift_contested",)),)
    elif scenario == "affordance_change_blocks_transfer":
        traces = (
            _trace(
                scenario,
                trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY,
                affordance_refs=("aff:tool-a",),
            ),
        )
        targets = (
            _target(
                scenario,
                target_kind=N03CurrentTargetKind.PLAN_CONSTRAINT_NEED,
                active_affordance_refs=("aff:tool-a",),
                active_drift_markers=("affordance_changed",),
            ),
        )
    elif scenario == "conflicting_traces":
        traces = (
            _trace(
                scenario,
                source_trace_id=f"{scenario}:failure",
                trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE,
                recurrence_count=3,
            ),
            _trace(
                scenario,
                source_trace_id=f"{scenario}:recovery",
                trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY,
                failure_or_recovery_signature="sig:recovery",
                recurrence_count=3,
            ),
        )
        targets = (_target(scenario, target_kind=N03CurrentTargetKind.RECOVERY_NEED),)
    elif scenario == "commitment_anchor":
        traces = (
            _trace(
                scenario,
                trace_kind=N03AutobiographicalTraceKind.PRIOR_COMMITMENT_KEPT,
                commitment_refs=("commitment:anchor",),
                recurrence_count=4,
            ),
        )
        targets = (
            _target(
                scenario,
                target_kind=N03CurrentTargetKind.COMMITMENT_UNDER_LOAD,
                active_commitment_refs=("commitment:anchor",),
            ),
        )
    else:
        raise ValueError(scenario)

    return N03InputBundle(
        bundle_id=f"demo:{scenario}:bundle",
        trace_candidates=traces,
        current_targets=targets,
        source_lineage=("tools.n03_demo", scenario),
        reason=f"demo scenario: {scenario}",
    )


def run_demo(scenario: str) -> int:
    bundle = _bundle_for_scenario(scenario)
    result = build_n03_autobiographical_relevance(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=bundle,
        relevance_enabled=True,
    )
    print("N03 AUTOBIOGRAPHICAL RELEVANCE DEMO")
    print(f"scenario={scenario}")
    print(f"trace_count={len(bundle.trace_candidates)}")
    print(f"target_count={len(bundle.current_targets)}")
    for entry in result.relevance_entries:
        print(
            "entry="
            f"(trace={entry.source_trace_id}, target={entry.current_target_id}, "
            f"kind={entry.relevance_kind.value}, decision={entry.transfer_decision.value}, "
            f"scope={entry.transfer_scope.value}, strength={entry.relevance_strength}, "
            f"confidence={entry.confidence})"
        )
        print(
            "supports="
            f"{[item.value for item in entry.supported_by_dimensions]} limits={entry.anti_generalization_limits} "
            f"reasons={[item.value for item in entry.limiting_reasons]}"
        )
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, transfer_packet_consumer_ready={result.gate.transfer_packet_consumer_ready}, "
        f"consistency_consumer_ready={result.gate.consistency_consumer_ready}, "
        f"relevant={result.telemetry.relevant_trace_count}, blocked={result.telemetry.blocked_transfer_count}, "
        f"conflict={result.telemetry.conflict_count}, provisional={result.telemetry.provisional_transfer_count})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic N03 autobiographical relevance scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "semantic_similarity_only",
            "recovery_pattern",
            "single_episode_overgeneralization",
            "identity_drift_blocks_transfer",
            "affordance_change_blocks_transfer",
            "conflicting_traces",
            "commitment_anchor",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
