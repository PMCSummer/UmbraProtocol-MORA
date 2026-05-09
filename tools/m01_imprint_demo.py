from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.m01_homeostatic_salience_imprint import (
    M01AttributionEvidence,
    M01AttributionStatus,
    M01InputBundle,
    M01RegulatoryAxisDelta,
    M01RegulatoryDirection,
    M01TemporalCouplingEvidence,
    M01TemporalWindowStatus,
    M01TraceInput,
    M01TraceKind,
    build_m01_homeostatic_salience_imprint,
)


def _trace(case: str) -> M01TraceInput:
    return M01TraceInput(
        trace_id=f"{case}:trace",
        trace_kind=M01TraceKind.EVENT,
        semantic_signature="demo:trace",
        timestamp_or_sequence="seq:1",
        scope="demo_scope",
        provenance=("tools.m01_demo", case),
    )


def _delta(
    case: str,
    *,
    axis_id: str,
    direction: M01RegulatoryDirection,
    intensity: float,
    deviation_before: float,
    deviation_after: float,
    recovery_marker: bool = False,
    stabilization_marker: bool = False,
) -> M01RegulatoryAxisDelta:
    return M01RegulatoryAxisDelta(
        delta_id=f"{case}:{axis_id}",
        axis_id=axis_id,
        before_value=0.5,
        after_value=0.8 if direction is M01RegulatoryDirection.WORSENING else 0.3,
        deviation_before=deviation_before,
        deviation_after=deviation_after,
        direction=direction,
        intensity=intensity,
        rate_hint=0.4,
        measurement_confidence=0.85,
        stabilization_marker=stabilization_marker,
        recovery_marker=recovery_marker,
        provenance=("tools.m01_demo.delta", case, axis_id),
    )


def _bundle_for_scenario(scenario: str) -> M01InputBundle:
    trace = _trace(scenario)
    attribution = M01AttributionEvidence(
        trace_id=trace.trace_id,
        attribution_status=M01AttributionStatus.SELF_RELEVANT,
        self_side_share=0.78,
        residual_uncertainty=0.2,
        provenance=("tools.m01_demo.attr", scenario),
    )
    deltas: tuple[M01RegulatoryAxisDelta, ...] = ()
    coupling: tuple[M01TemporalCouplingEvidence, ...] = ()
    prior_imprints = ()

    if scenario == "strain":
        delta = _delta(
            scenario,
            axis_id="axis:stress",
            direction=M01RegulatoryDirection.WORSENING,
            intensity=0.82,
            deviation_before=0.2,
            deviation_after=0.85,
        )
        deltas = (delta,)
        coupling = (
            M01TemporalCouplingEvidence(
                trace_id=trace.trace_id,
                regulatory_delta_refs=(delta.delta_id,),
                temporal_window_status=M01TemporalWindowStatus.WITHIN_WINDOW,
                confidence=0.84,
            ),
        )
    elif scenario == "relief":
        delta = _delta(
            scenario,
            axis_id="axis:stress",
            direction=M01RegulatoryDirection.IMPROVING,
            intensity=0.8,
            deviation_before=0.8,
            deviation_after=0.25,
            recovery_marker=True,
        )
        deltas = (delta,)
        coupling = (
            M01TemporalCouplingEvidence(
                trace_id=trace.trace_id,
                regulatory_delta_refs=(delta.delta_id,),
                temporal_window_status=M01TemporalWindowStatus.WITHIN_WINDOW,
                confidence=0.84,
            ),
        )
    elif scenario == "external_noise":
        delta = _delta(
            scenario,
            axis_id="axis:stress",
            direction=M01RegulatoryDirection.WORSENING,
            intensity=0.8,
            deviation_before=0.2,
            deviation_after=0.8,
        )
        deltas = (delta,)
        coupling = (
            M01TemporalCouplingEvidence(
                trace_id=trace.trace_id,
                regulatory_delta_refs=(delta.delta_id,),
                temporal_window_status=M01TemporalWindowStatus.WITHIN_WINDOW,
                confidence=0.82,
            ),
        )
        attribution = M01AttributionEvidence(
            trace_id=trace.trace_id,
            attribution_status=M01AttributionStatus.EXTERNALLY_DOMINATED,
            self_side_share=0.2,
            residual_uncertainty=0.6,
            provenance=("tools.m01_demo.attr", scenario),
        )
    elif scenario == "repeated_pattern":
        delta = _delta(
            scenario,
            axis_id="axis:stress",
            direction=M01RegulatoryDirection.WORSENING,
            intensity=0.75,
            deviation_before=0.25,
            deviation_after=0.8,
        )
        deltas = (delta,)
        coupling = (
            M01TemporalCouplingEvidence(
                trace_id=trace.trace_id,
                regulatory_delta_refs=(delta.delta_id,),
                temporal_window_status=M01TemporalWindowStatus.WITHIN_WINDOW,
                confidence=0.82,
            ),
        )
        prior = build_m01_homeostatic_salience_imprint(
            tick_id="demo:repeated:prior",
            tick_index=0,
            input_bundle=M01InputBundle(
                bundle_id="demo:repeated:prior:bundle",
                traces=(trace,),
                regulatory_deltas=(delta,),
                temporal_coupling=coupling,
                attribution=(attribution,),
                source_lineage=("tools.m01_demo", "repeated_pattern", "prior"),
                reason="prior pattern for reinforcement",
            ),
            imprint_enabled=True,
        )
        prior_imprints = prior.imprint_packets

    return M01InputBundle(
        bundle_id=f"demo:{scenario}:bundle",
        traces=(trace,),
        regulatory_deltas=deltas,
        temporal_coupling=coupling,
        attribution=(attribution,),
        prior_imprints=prior_imprints,
        source_lineage=("tools.m01_demo", scenario),
        reason=f"demo scenario: {scenario}",
    )


def run_demo(scenario: str) -> int:
    bundle = _bundle_for_scenario(scenario)
    result = build_m01_homeostatic_salience_imprint(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=bundle,
        imprint_enabled=True,
    )

    packet = result.imprint_packets[0] if result.imprint_packets else None
    print("M01 HOMEOSTATIC IMPRINT DEMO")
    print(f"scenario={scenario}")
    print(f"trace={bundle.traces[0].trace_id}")
    print(f"attribution={bundle.attribution[0].attribution_status.value}")
    print(f"axes={[item.axis_id for item in bundle.regulatory_deltas]}")
    print(f"decision={packet.decision.value if packet else 'no_packet'}")
    print(f"retention_bias={packet.retention_bias if packet else 0.0}")
    print(f"replay_priority={packet.replay_priority if packet else 0.0}")
    print(f"retrieval_bias={packet.retrieval_bias if packet else 0.0}")
    print(f"transfer_limits={packet.transfer_limits if packet else ()}")
    print(
        "no_claim_markers="
        f"(not_reward_function={result.scope_marker.not_reward_function}, "
        f"not_narrative_relevance={result.scope_marker.not_narrative_relevance}, "
        f"no_global_value_claim={result.scope_marker.no_global_value_claim})"
    )
    print(
        "gate="
        f"(consumer_ready={result.gate.consumer_ready}, "
        f"no_safe_imprint_claim={result.gate.no_safe_imprint_claim}, "
        f"restrictions={result.gate.required_restrictions})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic M01 imprint scenarios.")
    parser.add_argument(
        "--scenario",
        choices=("neutral", "strain", "relief", "external_noise", "repeated_pattern"),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
