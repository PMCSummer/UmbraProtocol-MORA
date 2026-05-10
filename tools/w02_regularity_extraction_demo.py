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


def _trace(
    scenario: str,
    *,
    trace_id: str,
    sequence_index: int,
    entity_id: str = "entity:a",
    source_authority: str = "trusted_world_provider",
    presence_mode: W02PresenceMode = W02PresenceMode.PRESENT,
    action_ref: str | None = "action:a",
    effect_ref: str | None = "effect:a",
    structural_signature: str | None = "shape:cube",
    kind_label: str | None = "kind:block",
    role_label: str | None = "role:anchor",
    contradiction_markers: tuple[str, ...] = (),
    is_duplicate_packet: bool = False,
    provider_bias_marker: bool = False,
    text_artifact_marker: bool = False,
    revoked: bool = False,
    candidate_type: W02RegularityCandidateType = W02RegularityCandidateType.INSTANCE,
) -> W02TraceRef:
    return W02TraceRef(
        trace_id=trace_id,
        sequence_index=sequence_index,
        entity_id=entity_id,
        source_authority=source_authority,
        presence_mode=presence_mode,
        admission_state="admitted",
        confidence_band="high",
        provenance_ref=("tools.w02_demo", scenario),
        action_ref=action_ref,
        effect_ref=effect_ref,
        structural_signature=structural_signature,
        kind_label=kind_label,
        role_label=role_label,
        provider_label=source_authority,
        contradiction_markers=contradiction_markers,
        is_duplicate_packet=is_duplicate_packet,
        provider_bias_marker=provider_bias_marker,
        text_artifact_marker=text_artifact_marker,
        revoked=revoked,
        candidate_type=candidate_type,
    )


def _bundle_for_scenario(scenario: str) -> W02InputBundle:
    if scenario == "single_trace_blocked":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1),
        )
    elif scenario == "recurrent_scaffold":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1),
            _trace(scenario, trace_id="t2", sequence_index=2),
        )
    elif scenario == "persistent_instance_candidate":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1, source_authority="trusted_world_provider"),
            _trace(scenario, trace_id="t2", sequence_index=2, source_authority="weak_scaffold_provider"),
            _trace(scenario, trace_id="t3", sequence_index=3, source_authority="trusted_world_provider"),
        )
    elif scenario == "same_kind_not_same_instance":
        traces = (
            _trace(scenario, trace_id="a1", sequence_index=1, entity_id="entity:a", candidate_type=W02RegularityCandidateType.KIND, kind_label="kind:block"),
            _trace(scenario, trace_id="b1", sequence_index=2, entity_id="entity:b", candidate_type=W02RegularityCandidateType.KIND, kind_label="kind:block"),
        )
    elif scenario == "duplicate_vs_continuity":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1, is_duplicate_packet=True),
            _trace(scenario, trace_id="t2", sequence_index=2, is_duplicate_packet=True),
        )
    elif scenario == "replacement_vs_continuity":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1, contradiction_markers=("replacement",)),
            _trace(scenario, trace_id="t2", sequence_index=2, contradiction_markers=("replacement",)),
        )
    elif scenario == "scaffold_only_blocks_promotion":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            _trace(scenario, trace_id="t2", sequence_index=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            _trace(scenario, trace_id="t3", sequence_index=3, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        )
    elif scenario == "contradiction_downgrades":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1),
            _trace(scenario, trace_id="t2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        )
    elif scenario == "affordance_requires_action_effect_linkage":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
            _trace(scenario, trace_id="t2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
        )
    elif scenario == "provider_bias_blocked":
        traces = (
            _trace(scenario, trace_id="t1", sequence_index=1, provider_bias_marker=True),
            _trace(scenario, trace_id="t2", sequence_index=2, provider_bias_marker=True),
        )
    else:
        raise ValueError(scenario)

    return W02InputBundle(
        bundle_id=f"demo:{scenario}:bundle",
        traces=traces,
        source_lineage=("tools.w02_demo", scenario),
        reason=f"demo scenario: {scenario}",
    )


def run_demo(scenario: str) -> int:
    bundle = _bundle_for_scenario(scenario)
    result = build_w02_regularity_extraction(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=bundle,
        enforcement_enabled=True,
    )
    print("W02 REGULARITY EXTRACTION DEMO")
    print(f"scenario={scenario}")
    print(f"trace_count={len(bundle.traces)}")
    for record in result.regularity_records:
        print(
            "record="
            f"(id={record.regularity_id}, candidate_type={record.candidate_type.value}, "
            f"maturity_level={record.maturity_level.value}, promotion_status={record.promotion_status.value}, "
            f"evidence_count={record.evidence_count}, temporal_span={record.temporal_span})"
        )
    print(
        "telemetry="
        f"(promoted={result.telemetry.promoted_count}, blocked={result.telemetry.blocked_count}, "
        f"contested={result.telemetry.contested_count}, downgraded={result.telemetry.downgraded_count}, "
        f"contradiction_count={result.telemetry.contradiction_count}, lineage_ambiguity={result.telemetry.lineage_ambiguity_count})"
    )
    for packet in result.downstream_permission_packets:
        print(
            "permission="
            f"(scaffold={packet.may_use_as_scaffold}, instance={packet.may_use_as_instance_hypothesis}, "
            f"kind={packet.may_use_as_kind_hint}, affordance={packet.may_use_as_affordance_hint}, "
            f"scene_role={packet.may_use_as_scene_role_hint}, stable_identity={packet.may_claim_stable_identity}, "
            f"must_abstain={packet.must_abstain}, reasons={packet.reason_codes})"
        )
    print(
        "consumer_flags="
        f"(consumer_ready={result.gate.consumer_ready}, no_clean_regularities={result.telemetry.no_clean_regularities}, "
        f"must_abstain_count={result.telemetry.must_abstain_count})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic W02 regularity extraction scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "single_trace_blocked",
            "recurrent_scaffold",
            "persistent_instance_candidate",
            "same_kind_not_same_instance",
            "duplicate_vs_continuity",
            "replacement_vs_continuity",
            "scaffold_only_blocks_promotion",
            "contradiction_downgrades",
            "affordance_requires_action_effect_linkage",
            "provider_bias_blocked",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
