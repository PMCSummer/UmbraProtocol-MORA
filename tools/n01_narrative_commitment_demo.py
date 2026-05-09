from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.n01_narrative_commitments import (
    N01CommitmentScope,
    N01GroundingBasisKind,
    N01InputBundle,
    N01NarrativeClaimCandidate,
    N01NarrativeClaimKind,
    build_n01_narrative_commitments,
)


def _candidate_for_scenario(scenario: str) -> tuple[N01NarrativeClaimCandidate, ...]:
    if scenario == "statement_only":
        return (
            N01NarrativeClaimCandidate(
                candidate_id="demo:statement-only",
                claim_text_or_semantic_form="I can run hidden module path",
                claim_kind=N01NarrativeClaimKind.CAPABILITY_CLAIM,
                requested_scope=N01CommitmentScope.DIALOGUE_LOCAL,
                expression_channel="text",
                addressee_or_audience_scope="demo",
                grounding_basis=(N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
                temporal_validity_status="fresh",
                attribution_status="self",
                self_side_confidence=0.78,
                mixed_cause_marker=False,
            ),
        )
    if scenario == "grounded_state_commitment":
        return (
            N01NarrativeClaimCandidate(
                candidate_id="demo:grounded-state",
                claim_text_or_semantic_form="I am operating in analysis mode",
                claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
                requested_scope=N01CommitmentScope.CURRENT_TURN,
                expression_channel="text",
                addressee_or_audience_scope="demo",
                grounding_basis=(
                    N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                    N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
                    N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
                    N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
                ),
                temporal_validity_status="fresh",
                attribution_status="self",
                self_side_confidence=0.9,
                mixed_cause_marker=False,
            ),
        )
    if scenario == "ungrounded_capability":
        return (
            N01NarrativeClaimCandidate(
                candidate_id="demo:ungrounded-capability",
                claim_text_or_semantic_form="I can invoke unavailable external runtime directly",
                claim_kind=N01NarrativeClaimKind.CAPABILITY_CLAIM,
                requested_scope=N01CommitmentScope.DIALOGUE_LOCAL,
                expression_channel="text",
                addressee_or_audience_scope="demo",
                grounding_basis=(N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
                temporal_validity_status="fresh",
                attribution_status="self",
                self_side_confidence=0.82,
                mixed_cause_marker=False,
            ),
        )
    if scenario == "grounded_limitation":
        return (
            N01NarrativeClaimCandidate(
                candidate_id="demo:grounded-limitation",
                claim_text_or_semantic_form="I cannot complete this path until support is available",
                claim_kind=N01NarrativeClaimKind.LIMITATION_CLAIM,
                requested_scope=N01CommitmentScope.SHORT_HORIZON,
                expression_channel="text",
                addressee_or_audience_scope="demo",
                grounding_basis=(
                    N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                    N01GroundingBasisKind.CAPABILITY_GAP_SUPPORT,
                ),
                temporal_validity_status="fresh",
                attribution_status="self",
                self_side_confidence=0.86,
                mixed_cause_marker=False,
                limitation_support=True,
                gap_support=True,
            ),
        )
    if scenario == "contradiction":
        return (
            N01NarrativeClaimCandidate(
                candidate_id="demo:contradiction",
                claim_text_or_semantic_form="I am not operating in analysis mode",
                claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
                requested_scope=N01CommitmentScope.CURRENT_TURN,
                expression_channel="text",
                addressee_or_audience_scope="demo",
                grounding_basis=(
                    N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                    N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
                ),
                temporal_validity_status="fresh",
                attribution_status="self",
                self_side_confidence=0.83,
                mixed_cause_marker=False,
                existing_commitment_refs=("demo:existing",),
            ),
        )
    if scenario == "invalidated_basis":
        return (
            N01NarrativeClaimCandidate(
                candidate_id="demo:invalidated",
                claim_text_or_semantic_form="I am operating in analysis mode",
                claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
                requested_scope=N01CommitmentScope.CURRENT_TURN,
                expression_channel="text",
                addressee_or_audience_scope="demo",
                grounding_basis=(N01GroundingBasisKind.INVALIDATED_BASIS,),
                temporal_validity_status="invalid",
                attribution_status="self",
                self_side_confidence=0.62,
                mixed_cause_marker=False,
                existing_commitment_refs=("demo:existing",),
            ),
        )
    raise ValueError(f"Unsupported scenario: {scenario}")


def _existing_for_scenario(scenario: str):
    if scenario in {"contradiction", "invalidated_basis"}:
        existing_result = build_n01_narrative_commitments(
            tick_id="demo-existing",
            tick_index=1,
            input_bundle=N01InputBundle(
                bundle_id="demo:existing:bundle",
                candidates=(
                    N01NarrativeClaimCandidate(
                        candidate_id="demo:existing:candidate",
                        claim_text_or_semantic_form="I am operating in analysis mode",
                        claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
                        requested_scope=N01CommitmentScope.CURRENT_TURN,
                        expression_channel="text",
                        addressee_or_audience_scope="demo",
                        grounding_basis=(
                            N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                            N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
                            N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
                        ),
                        temporal_validity_status="fresh",
                        attribution_status="self",
                        self_side_confidence=0.88,
                        mixed_cause_marker=False,
                    ),
                ),
            ),
        )
        existing = existing_result.commitment_entries[0]
        return (existing,)
    return ()


def run_demo(scenario: str) -> int:
    candidates = _candidate_for_scenario(scenario)
    existing = _existing_for_scenario(scenario)
    if existing:
        candidates = tuple(
            replace(candidate, existing_commitment_refs=(existing[0].commitment_id,))
            for candidate in candidates
        )
    result = build_n01_narrative_commitments(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        input_bundle=N01InputBundle(
            bundle_id=f"demo:{scenario}:bundle",
            candidates=candidates,
            existing_commitments=existing,
            source_lineage=("tools.n01_demo", scenario),
            reason=f"demo scenario: {scenario}",
        ),
    )
    print("N01 NARRATIVE COMMITMENT DEMO")
    print(f"scenario={scenario}")
    print(f"candidate_count={result.telemetry.candidate_count}")
    for entry in result.commitment_entries:
        print(
            "record="
            f"(id={entry.commitment_id}, decision={entry.decision.value}, strength={entry.strength.value}, "
            f"scope={entry.scope.value}, kind={entry.claim_kind.value}, conflict={entry.conflict_status.value})"
        )
        print(f"support_basis={[item.value for item in entry.grounding_basis]}")
        print(f"obligations={[item.value for item in entry.downstream_obligations]}")
        print(f"revision_action={entry.revision_action.value}")
        print(f"reason_codes={entry.reason_codes}")
    print(
        "gate="
        f"(consumer_ready={result.gate.consumer_ready}, consistency_consumer_ready={result.gate.consistency_consumer_ready}, "
        f"strong_count={result.gate.strong_commitment_count}, provisional_count={result.gate.provisional_commitment_count}, "
        f"contested_count={result.gate.contested_commitment_count})"
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic N01 commitment scenarios.")
    parser.add_argument(
        "--scenario",
        choices=(
            "statement_only",
            "grounded_state_commitment",
            "ungrounded_capability",
            "grounded_limitation",
            "contradiction",
            "invalidated_basis",
        ),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
