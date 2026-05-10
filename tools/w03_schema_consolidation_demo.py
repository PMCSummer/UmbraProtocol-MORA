from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.w02_regularity_extraction import (
    W02InputBundle,
    W02PresenceMode,
    W02RegularityCandidateType,
    W02TraceRef,
    build_w02_regularity_extraction,
)
from substrate.w03_schema_consolidation import (
    W03InputBundle,
    build_w03_schema_consolidation,
)


def _trace(
    scenario: str,
    *,
    trace_id: str,
    sequence_index: int,
    source_authority: str = "trusted_world_provider",
    presence_mode: W02PresenceMode = W02PresenceMode.PRESENT,
    contradiction_markers: tuple[str, ...] = (),
    candidate_type: W02RegularityCandidateType = W02RegularityCandidateType.KIND,
    action_ref: str | None = "action:a",
    effect_ref: str | None = "effect:a",
) -> W02TraceRef:
    return W02TraceRef(
        trace_id=trace_id,
        sequence_index=sequence_index,
        entity_id=f"{scenario}:entity",
        source_authority=source_authority,
        presence_mode=presence_mode,
        admission_state="admitted",
        confidence_band="high",
        provenance_ref=("tools.w03_demo", scenario),
        action_ref=action_ref,
        effect_ref=effect_ref,
        structural_signature="shape:cube",
        kind_label="kind:block",
        role_label="role:anchor",
        provider_label=source_authority,
        contradiction_markers=contradiction_markers,
        is_duplicate_packet=False,
        provider_bias_marker=False,
        text_artifact_marker=False,
        revoked=False,
        candidate_type=candidate_type,
    )


def _w02_bundle_for_scenario(scenario: str) -> W02InputBundle | None:
    if scenario == "language_prior_rejected":
        return None

    if scenario == "clean_kind_prior":
        traces = (
            _trace(scenario, trace_id="k1", sequence_index=1, source_authority="trusted_world_provider"),
            _trace(scenario, trace_id="k2", sequence_index=3, source_authority="weak_scaffold_provider"),
            _trace(scenario, trace_id="k3", sequence_index=5, source_authority="trusted_world_provider"),
        )
    elif scenario == "contested_regularities_block_prior":
        traces = (
            _trace(scenario, trace_id="c1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            _trace(scenario, trace_id="c2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        )
    elif scenario == "scaffold_only_deferred":
        traces = (
            _trace(scenario, trace_id="s1", sequence_index=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            _trace(scenario, trace_id="s2", sequence_index=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            _trace(scenario, trace_id="s3", sequence_index=3, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        )
    elif scenario == "authority_scope_narrow":
        traces = (
            _trace(scenario, trace_id="a1", sequence_index=1, source_authority="trusted_world_provider"),
            _trace(scenario, trace_id="a2", sequence_index=2, source_authority="trusted_world_provider"),
        )
    elif scenario == "revoked_authority_revalidate":
        traces = (
            _trace(scenario, trace_id="r1", sequence_index=1, source_authority="revoked_source"),
            _trace(scenario, trace_id="r2", sequence_index=2, source_authority="revoked_source"),
        )
    elif scenario == "context_transfer_failure":
        traces = (
            _trace(scenario, trace_id="x1", sequence_index=1, presence_mode=W02PresenceMode.PARTIAL),
            _trace(scenario, trace_id="x2", sequence_index=2, presence_mode=W02PresenceMode.PARTIAL),
        )
    elif scenario == "contradiction_downgrades":
        traces = (
            _trace(scenario, trace_id="d1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            _trace(scenario, trace_id="d2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        )
    elif scenario == "contradictory_affordance_worlds_split":
        traces = (
            _trace(
                scenario,
                trace_id="f1",
                sequence_index=1,
                candidate_type=W02RegularityCandidateType.AFFORDANCE,
                contradiction_markers=("replacement",),
            ),
            _trace(
                scenario,
                trace_id="f2",
                sequence_index=2,
                candidate_type=W02RegularityCandidateType.AFFORDANCE,
                contradiction_markers=("replacement",),
            ),
        )
    elif scenario == "stale_schema_revalidation":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1),
            _trace(scenario, trace_id="t2", sequence_index=1),
        )
    elif scenario == "operational_default_clean_path":
        traces = (
            _trace(
                scenario,
                trace_id="o1",
                sequence_index=1,
                source_authority="trusted_world_provider",
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
            _trace(
                scenario,
                trace_id="o2",
                sequence_index=3,
                source_authority="weak_scaffold_provider",
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
            _trace(
                scenario,
                trace_id="o3",
                sequence_index=5,
                source_authority="trusted_world_provider",
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
        )
    else:
        raise ValueError(scenario)

    return W02InputBundle(
        bundle_id=f"demo:{scenario}:w02:bundle",
        traces=traces,
        source_lineage=("tools.w03_demo", scenario),
        reason=f"w03 demo scenario: {scenario}",
    )


def _w03_input_for_scenario(scenario: str) -> W03InputBundle | None:
    w02_bundle = _w02_bundle_for_scenario(scenario)
    if w02_bundle is None:
        return None
    w02_result = build_w02_regularity_extraction(
        tick_id=f"demo:{scenario}:w02",
        tick_index=1,
        input_bundle=w02_bundle,
        enforcement_enabled=True,
    )
    return W03InputBundle(
        bundle_id=f"demo:{scenario}:w03:bundle",
        source_lineage=("tools.w03_demo", scenario),
        w02_regularity_records=w02_result.regularity_records,
        w02_permission_packets=w02_result.downstream_permission_packets,
        w02_contradiction_ledger=w02_result.contradiction_ledger,
        reason=f"w03 demo scenario: {scenario}",
    )


def run_demo(scenario: str) -> int:
    input_bundle = _w03_input_for_scenario(scenario)
    result = build_w03_schema_consolidation(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=input_bundle,
        enforcement_enabled=True,
    )
    print("W03 SCHEMA CONSOLIDATION DEMO")
    print(f"scenario={scenario}")
    print(
        "counts="
        f"(schema_candidates={result.telemetry.schema_candidate_count}, priors={result.telemetry.everyday_prior_count}, "
        f"operational_defaults={result.telemetry.operational_default_count}, contested={result.telemetry.contested_count}, "
        f"stale={result.telemetry.stale_count}, must_revalidate={result.telemetry.must_revalidate_count}, "
        f"must_abstain={result.telemetry.must_abstain_count}, contradictions={result.telemetry.contradiction_count})"
    )
    for candidate in result.schema_candidates:
        print(
            "candidate="
            f"(id={candidate.schema_id}, channel={candidate.schema_channel.value}, status={candidate.status.value}, "
            f"support={len(candidate.support_regularities)}, contradictions={len(candidate.unresolved_contradictions)}, "
            f"stale_markers={candidate.stale_markers})"
        )
    for packet in result.downstream_permission_packets:
        print(
            "permission="
            f"(bounded_prior={packet.may_use_as_bounded_prior}, schema_hint={packet.may_use_as_schema_hint}, "
            f"operational_default={packet.may_use_as_operational_default}, must_revalidate={packet.must_revalidate_before_use}, "
            f"must_preserve_contradiction={packet.must_preserve_contradiction}, must_abstain={packet.must_abstain}, "
            f"prohibited_claims={packet.prohibited_claims}, reasons={packet.reason_codes})"
        )
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, no_clean_schema={result.gate.no_clean_schema}, "
        f"required_restrictions={result.gate.required_restrictions})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic W03 schema-consolidation scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "clean_kind_prior",
            "contested_regularities_block_prior",
            "scaffold_only_deferred",
            "authority_scope_narrow",
            "revoked_authority_revalidate",
            "context_transfer_failure",
            "contradiction_downgrades",
            "contradictory_affordance_worlds_split",
            "stale_schema_revalidation",
            "language_prior_rejected",
            "operational_default_clean_path",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
