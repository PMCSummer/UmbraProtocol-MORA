from __future__ import annotations

from dataclasses import dataclass

from substrate.n01_narrative_commitments import (
    N01CommitmentEntry,
    N01CommitmentScope,
    N01GroundingBasisKind,
    N01InputBundle,
    N01NarrativeClaimCandidate,
    N01NarrativeClaimKind,
    N01Result,
    build_n01_narrative_commitments,
)


@dataclass(frozen=True, slots=True)
class N01HarnessCase:
    case_id: str
    input_bundle: N01InputBundle | None
    commitments_enabled: bool = True


@dataclass(frozen=True, slots=True)
class N01HarnessRun:
    n01_result: N01Result


def n01_candidate(
    *,
    candidate_id: str,
    claim_text_or_semantic_form: str = "I am in analysis mode",
    claim_kind: N01NarrativeClaimKind = N01NarrativeClaimKind.STATE_DESCRIPTION,
    requested_scope: N01CommitmentScope = N01CommitmentScope.CURRENT_TURN,
    expression_channel: str = "text",
    addressee_or_audience_scope: str = "runtime_local",
    grounding_basis: tuple[N01GroundingBasisKind, ...] = (
        N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
        N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
        N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
        N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
    ),
    temporal_validity_status: str = "fresh",
    attribution_status: str = "self",
    self_side_confidence: float = 0.82,
    mixed_cause_marker: bool = False,
    capability_support: bool = False,
    limitation_support: bool = False,
    affordance_support: bool = False,
    gap_support: bool = False,
    internal_tool_support: bool = False,
    active_mode_support: bool = False,
    continuity_support: bool = False,
    conflict_marker: bool = False,
    conflict_basis: str = "",
    existing_commitment_refs: tuple[str, ...] = (),
    provenance: tuple[str, ...] = ("tests.n01.candidate",),
    timestamp_or_sequence: str = "seq:1",
) -> N01NarrativeClaimCandidate:
    return N01NarrativeClaimCandidate(
        candidate_id=candidate_id,
        claim_text_or_semantic_form=claim_text_or_semantic_form,
        claim_kind=claim_kind,
        requested_scope=requested_scope,
        expression_channel=expression_channel,
        addressee_or_audience_scope=addressee_or_audience_scope,
        grounding_basis=grounding_basis,
        temporal_validity_status=temporal_validity_status,
        attribution_status=attribution_status,
        self_side_confidence=self_side_confidence,
        mixed_cause_marker=mixed_cause_marker,
        capability_support=capability_support,
        limitation_support=limitation_support,
        affordance_support=affordance_support,
        gap_support=gap_support,
        internal_tool_support=internal_tool_support,
        active_mode_support=active_mode_support,
        continuity_support=continuity_support,
        conflict_marker=conflict_marker,
        conflict_basis=conflict_basis,
        existing_commitment_refs=existing_commitment_refs,
        provenance=provenance,
        timestamp_or_sequence=timestamp_or_sequence,
    )


def n01_bundle(
    *,
    bundle_id: str,
    candidates: tuple[N01NarrativeClaimCandidate, ...],
    existing_commitments: tuple[N01CommitmentEntry, ...] = (),
    source_lineage: tuple[str, ...] = (),
    reason: str = "tests.n01 bundle",
) -> N01InputBundle:
    return N01InputBundle(
        bundle_id=bundle_id,
        candidates=candidates,
        existing_commitments=existing_commitments,
        source_lineage=source_lineage,
        reason=reason,
    )


def build_n01_harness_case(case: N01HarnessCase) -> N01HarnessRun:
    result = build_n01_narrative_commitments(
        tick_id=f"tests.n01:{case.case_id}",
        tick_index=1,
        input_bundle=case.input_bundle,
        commitments_enabled=case.commitments_enabled,
    )
    return N01HarnessRun(n01_result=result)
