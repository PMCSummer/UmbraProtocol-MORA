from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.n02_identity_drift_reflection import (
    N02BaselineReference,
    N02BaselineValidityStatus,
    N02CurrentIdentityEvidence,
    N02IdentityRegionKind,
    N02IdentitySubstrateChange,
    N02InputBundle,
    N02SubstrateChangeKind,
    build_n02_identity_drift_reflection,
)


def _base_bundle(scenario: str) -> N02InputBundle:
    baseline = N02BaselineReference(
        baseline_id=f"{scenario}:baseline",
        baseline_kind=N02IdentityRegionKind.SELF_DESCRIPTION,
        time_scope="context:analysis",
        source_commitment_ids=(f"{scenario}:commitment:baseline",),
        source_region_ids=(f"{scenario}:region:self",),
        validity_status=N02BaselineValidityStatus.VALID,
        confidence=0.85,
        provenance=("tools.n02.demo", scenario),
    )
    current = N02CurrentIdentityEvidence(
        current_reference_id=f"{scenario}:current",
        observed_region=N02IdentityRegionKind.SELF_DESCRIPTION,
        current_commitment_ids=(f"{scenario}:commitment:current",),
        current_self_binding_refs=(f"{scenario}:binding:current",),
        capability_or_affordance_refs=(f"{scenario}:cap:current",),
        context_scope="context:analysis",
        evidence_window="window:now",
        confidence=0.82,
        provenance=("tools.n02.demo", scenario),
    )
    changes: tuple[N02IdentitySubstrateChange, ...] = ()
    if scenario == "bounded_revision":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.LOCAL_REVISION,
                magnitude_hint=0.35,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="single",
                confidence=0.8,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
        )
    elif scenario == "gradual_shift":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.REPETITIVE_REVISION,
                magnitude_hint=0.45,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="accumulating",
                confidence=0.79,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg2",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.REPETITIVE_REVISION,
                magnitude_hint=0.52,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="accumulating",
                confidence=0.82,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
        )
    elif scenario == "abrupt_reorientation":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.ABRUPT_INCOMPATIBLE_REPLACEMENT,
                magnitude_hint=0.86,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="abrupt",
                confidence=0.84,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg2",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.ABRUPT_INCOMPATIBLE_REPLACEMENT,
                magnitude_hint=0.8,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="abrupt",
                confidence=0.83,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
        )
    elif scenario == "context_split":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.CONTEXT_SPLIT_SIGNAL,
                magnitude_hint=0.64,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="split",
                confidence=0.82,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
        )
    elif scenario == "text_diff_only":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.TEXTUAL_REPHRASE_ONLY,
                magnitude_hint=0.2,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="single",
                confidence=0.75,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
        )
    elif scenario == "silent_rewrite":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION,
                magnitude_hint=0.9,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="accumulating",
                confidence=0.86,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
            N02IdentitySubstrateChange(
                change_id=f"{scenario}:chg2",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION,
                magnitude_hint=0.88,
                affected_commitment_ids=current.current_commitment_ids,
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope=current.context_scope,
                temporal_pattern="accumulating",
                confidence=0.82,
                self_related=True,
                provenance=("tools.n02.demo", scenario),
            ),
        )
    return N02InputBundle(
        bundle_id=f"demo:{scenario}:bundle",
        baseline_references=(baseline,),
        current_references=(current,),
        substrate_changes=changes,
        source_lineage=("tools.n02.demo", scenario),
        reason=f"demo scenario: {scenario}",
    )


def run_demo(scenario: str) -> int:
    bundle = _base_bundle(scenario)
    result = build_n02_identity_drift_reflection(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=bundle,
        reflection_enabled=True,
    )
    print("N02 IDENTITY DRIFT REFLECTION DEMO")
    print(f"scenario={scenario}")
    print(f"baseline_count={len(bundle.baseline_references)}")
    print(f"current_count={len(bundle.current_references)}")
    print(f"change_count={len(bundle.substrate_changes)}")
    for entry in result.drift_entries:
        print(
            "entry="
            f"(drift_id={entry.drift_id}, region={entry.affected_identity_region.value}, kind={entry.drift_kind.value}, "
            f"magnitude={entry.drift_magnitude}, continuity={entry.continuity_preserved_flag}, "
            f"reflection_need={entry.reflection_need_level.value}, caution={entry.downstream_caution})"
        )
    print(
        "gate="
        f"(consumer_ready={result.gate.n02_consumer_ready}, reflection_ready={result.gate.reflection_consumer_ready}, "
        f"consistency_ready={result.gate.consistency_consumer_ready}, restrictions={result.gate.required_restrictions})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic N02 identity drift scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "stable_continuation",
            "bounded_revision",
            "gradual_shift",
            "abrupt_reorientation",
            "context_split",
            "text_diff_only",
            "silent_rewrite",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
