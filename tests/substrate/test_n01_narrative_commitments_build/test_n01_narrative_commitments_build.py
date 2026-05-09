from __future__ import annotations

from substrate.n01_narrative_commitments import (
    N01CommitmentDecision,
    N01CommitmentScope,
    N01CommitmentStrength,
    N01ConflictStatus,
    N01DownstreamObligationKind,
    N01GroundingBasisKind,
    N01NarrativeClaimKind,
    derive_n01_consumer_packets,
    n01_narrative_commitment_snapshot,
)
from tests.substrate.n01_narrative_commitments_testkit import (
    N01HarnessCase,
    build_n01_harness_case,
    n01_bundle,
    n01_candidate,
)


def _run_single(case_id: str, *, candidate_kwargs: dict | None = None, existing=()):
    candidate = n01_candidate(candidate_id=f"{case_id}:candidate", **(candidate_kwargs or {}))
    bundle = n01_bundle(
        bundle_id=f"{case_id}:bundle",
        candidates=(candidate,),
        existing_commitments=existing,
        source_lineage=("tests.n01.owner", case_id),
        reason=case_id,
    )
    return build_n01_harness_case(N01HarnessCase(case_id=case_id, input_bundle=bundle)).n01_result


def test_owner_import_surface_and_init_integrity() -> None:
    from substrate.n01_narrative_commitments import (
        N01InputBundle,
        N01Result,
        build_n01_narrative_commitments,
    )

    assert N01InputBundle is not None
    assert N01Result is not None
    assert callable(build_n01_narrative_commitments)
    assert callable(n01_narrative_commitment_snapshot)


def test_no_typed_candidate_produces_no_safe_commitment_result() -> None:
    result = build_n01_harness_case(
        N01HarnessCase(case_id="no-typed", input_bundle=None)
    ).n01_result
    assert result.commitment_entries == ()
    assert result.gate.consumer_ready is False
    assert "n01_no_clean_commitment_claim" in result.gate.required_restrictions


def test_self_report_alone_remains_statement_only_or_provisional_not_strong() -> None:
    result = _run_single(
        "self-report-alone",
        candidate_kwargs={
            "grounding_basis": (N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
            "self_side_confidence": 0.5,
        },
    )
    entry = result.commitment_entries[0]
    assert entry.decision in {
        N01CommitmentDecision.STATEMENT_ONLY_RECORD,
        N01CommitmentDecision.PROVISIONAL_COMMITMENT,
    }
    assert entry.strength is not N01CommitmentStrength.STRONG


def test_grounded_state_claim_becomes_bounded_commitment() -> None:
    result = _run_single(
        "grounded-state",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.STATE_DESCRIPTION,
            "requested_scope": N01CommitmentScope.CURRENT_TURN,
        },
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.CONFIRMED_COMMITMENT
    assert entry.scope is N01CommitmentScope.CURRENT_TURN


def test_capability_claim_without_affordance_support_is_not_strong() -> None:
    result = _run_single(
        "capability-unsupported",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.CAPABILITY_CLAIM,
            "capability_support": False,
            "affordance_support": False,
            "internal_tool_support": False,
            "grounding_basis": (N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
        },
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.STATEMENT_ONLY_RECORD
    assert "ungrounded_capability_claim" in entry.reason_codes


def test_capability_claim_with_tool_or_affordance_support_can_be_bounded() -> None:
    result = _run_single(
        "capability-supported",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.CAPABILITY_CLAIM,
            "capability_support": True,
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.CAPABILITY_AFFORDANCE_SUPPORT,
                N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
            ),
        },
    )
    assert result.commitment_entries[0].decision is N01CommitmentDecision.CONFIRMED_COMMITMENT


def test_limitation_claim_with_gap_support_becomes_bounded_limitation_commitment() -> None:
    result = _run_single(
        "limitation-supported",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.LIMITATION_CLAIM,
            "limitation_support": True,
            "gap_support": True,
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.CAPABILITY_GAP_SUPPORT,
            ),
        },
    )
    assert result.commitment_entries[0].decision is N01CommitmentDecision.CONFIRMED_COMMITMENT


def test_limitation_claim_without_gap_support_is_not_strong() -> None:
    result = _run_single(
        "limitation-unsupported",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.LIMITATION_CLAIM,
            "limitation_support": False,
            "gap_support": False,
            "grounding_basis": (N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
        },
    )
    assert result.commitment_entries[0].decision is N01CommitmentDecision.STATEMENT_ONLY_RECORD


def test_short_scope_basis_does_not_become_long_horizon_commitment() -> None:
    result = _run_single(
        "scope-not-long",
        candidate_kwargs={
            "requested_scope": N01CommitmentScope.LONG_HORIZON,
            "continuity_support": False,
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
            ),
        },
    )
    assert result.commitment_entries[0].scope is N01CommitmentScope.SHORT_HORIZON


def test_scope_narrowing_is_recorded_in_ledger() -> None:
    result = _run_single(
        "scope-narrowed",
        candidate_kwargs={
            "requested_scope": N01CommitmentScope.GLOBAL_FORBIDDEN_UNLESS_EXPLICITLY_GROUNDED,
            "continuity_support": False,
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
            ),
        },
    )
    assert "scope_narrowed_to_basis" in result.commitment_entries[0].reason_codes
    assert result.telemetry.scope_narrowed_count == 1


def test_contradiction_with_existing_strong_commitment_is_contested_not_overwritten() -> None:
    old = _run_single("existing-strong")
    existing = old.commitment_entries[0]
    result = _run_single(
        "conflict",
        candidate_kwargs={
            "claim_text_or_semantic_form": "I am not in analysis mode",
            "existing_commitment_refs": (existing.commitment_id,),
        },
        existing=(existing,),
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.CONTESTED_COMMITMENT
    assert entry.conflict_status in {
        N01ConflictStatus.CONTRADICTS_EXISTING_STRONG,
        N01ConflictStatus.CONTRADICTS_EXISTING_PROVISIONAL,
    }


def test_invalidated_basis_downgrades_or_retracts_commitment_explicitly() -> None:
    old = _run_single("existing-for-invalidation")
    existing = old.commitment_entries[0]
    result = _run_single(
        "invalidated-basis",
        candidate_kwargs={
            "claim_text_or_semantic_form": existing.semantic_content,
            "grounding_basis": (N01GroundingBasisKind.INVALIDATED_BASIS,),
            "existing_commitment_refs": (existing.commitment_id,),
        },
        existing=(existing,),
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.RETIRED_COMMITMENT
    assert "basis_invalidated" in entry.reason_codes


def test_revision_records_provenance_and_preserves_old_commit_reference() -> None:
    old = _run_single("revision-old")
    existing = old.commitment_entries[0]
    result = _run_single(
        "revision-ref",
        candidate_kwargs={
            "grounding_basis": (N01GroundingBasisKind.INVALIDATED_BASIS,),
            "existing_commitment_refs": (existing.commitment_id,),
        },
        existing=(existing,),
    )
    entry = result.commitment_entries[0]
    assert existing.commitment_id in entry.referenced_commitment_refs
    assert any("revision-ref:candidate" in item for item in entry.provenance)


def test_mixed_attribution_caps_commitment_strength() -> None:
    result = _run_single(
        "mixed-support",
        candidate_kwargs={
            "mixed_cause_marker": True,
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.MIXED_OR_CONTESTED_BASIS,
            ),
        },
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.PROVISIONAL_COMMITMENT
    assert entry.strength is N01CommitmentStrength.PROVISIONAL


def test_stale_temporal_basis_requires_recheck_or_provisional_status() -> None:
    result = _run_single(
        "stale-basis",
        candidate_kwargs={"temporal_validity_status": "stale"},
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.PROVISIONAL_COMMITMENT
    assert N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE in entry.downstream_obligations


def test_downstream_obligations_are_emitted_for_accepted_commitments() -> None:
    result = _run_single("obligations")
    entry = result.commitment_entries[0]
    assert N01DownstreamObligationKind.MUST_NOT_CLAIM_BEYOND_SCOPE in entry.downstream_obligations


def test_statement_only_has_no_binding_obligation() -> None:
    result = _run_single(
        "statement-only-obligation",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.CAPABILITY_CLAIM,
            "grounding_basis": (N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
        },
    )
    assert result.commitment_entries[0].downstream_obligations == (
        N01DownstreamObligationKind.NO_DOWNSTREAM_OBLIGATION,
    )


def test_claim_kinds_are_preserved_not_collapsed_to_generic_text() -> None:
    state = _run_single(
        "kind-state",
        candidate_kwargs={"claim_kind": N01NarrativeClaimKind.STATE_DESCRIPTION},
    )
    limitation = _run_single(
        "kind-limitation",
        candidate_kwargs={
            "claim_kind": N01NarrativeClaimKind.LIMITATION_CLAIM,
            "limitation_support": True,
            "gap_support": True,
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.CAPABILITY_GAP_SUPPORT,
            ),
        },
    )
    assert state.commitment_entries[0].claim_kind is N01NarrativeClaimKind.STATE_DESCRIPTION
    assert limitation.commitment_entries[0].claim_kind is N01NarrativeClaimKind.LIMITATION_CLAIM


def test_prompt_history_like_repetition_does_not_create_strong_commitment_without_grounding() -> None:
    c1 = n01_candidate(
        candidate_id="repeat:c1",
        claim_text_or_semantic_form="I can execute unknown operation",
        claim_kind=N01NarrativeClaimKind.CAPABILITY_CLAIM,
        grounding_basis=(N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
    )
    c2 = n01_candidate(
        candidate_id="repeat:c2",
        claim_text_or_semantic_form="I can execute unknown operation",
        claim_kind=N01NarrativeClaimKind.CAPABILITY_CLAIM,
        grounding_basis=(N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
    )
    bundle = n01_bundle(
        bundle_id="repeat:bundle",
        candidates=(c1, c2),
        source_lineage=("tests.n01.owner", "repeat"),
    )
    result = build_n01_harness_case(N01HarnessCase(case_id="repeat", input_bundle=bundle)).n01_result
    assert all(item.decision is N01CommitmentDecision.STATEMENT_ONLY_RECORD for item in result.commitment_entries)


def test_downstream_consumer_packet_is_machine_readable() -> None:
    result = _run_single("consumer-view")
    packet = derive_n01_consumer_packets(result)[0]
    assert packet.commitment_id
    assert packet.claim_kind == N01NarrativeClaimKind.STATE_DESCRIPTION.value
    assert packet.commitment_scope == N01CommitmentScope.CURRENT_TURN.value
    assert packet.semantic_content != ""


def test_revision_path_emits_revised_commitment_with_provenance() -> None:
    old = _run_single("revision-prior")
    existing = old.commitment_entries[0]
    result = _run_single(
        "revision-emitted",
        candidate_kwargs={
            "claim_text_or_semantic_form": "I am operating in bounded analysis mode",
            "grounding_basis": (
                N01GroundingBasisKind.INVALIDATED_BASIS,
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
                N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
                N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
            ),
            "existing_commitment_refs": (existing.commitment_id,),
            "temporal_validity_status": "fresh",
            "self_side_confidence": 0.84,
        },
        existing=(existing,),
    )
    entry = result.commitment_entries[0]
    assert entry.decision is N01CommitmentDecision.REVISED_COMMITMENT
    assert entry.revision_action.value == "replace_with_explicit_revision"
    assert entry.prior_decision is not None
    assert entry.prior_validation_status
    assert entry.revision_reason == "explicit_revision_after_invalidated_basis"
    assert existing.commitment_id in entry.referenced_commitment_refs
    assert result.ledger.revised_commitments and result.ledger.revised_commitments[0].commitment_id == entry.commitment_id
    packet = derive_n01_consumer_packets(result)[0]
    assert packet.revision_action == "replace_with_explicit_revision"
    assert packet.prior_decision is not None
    assert packet.revision_reason == "explicit_revision_after_invalidated_basis"
    assert entry.decision is not N01CommitmentDecision.CONTESTED_COMMITMENT
    assert entry.decision is not N01CommitmentDecision.RETIRED_COMMITMENT


def test_unreferenced_contradiction_does_not_silently_confirm_or_overwrite() -> None:
    old = _run_single("unreferenced-prior")
    existing = old.commitment_entries[0]
    result = _run_single(
        "unreferenced-contradiction",
        candidate_kwargs={
            "claim_text_or_semantic_form": "I am not in analysis mode",
            "conflict_marker": True,
            "conflict_basis": "typed_conflict_marker_without_reference",
            "existing_commitment_refs": (),
            "grounding_basis": (
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
            ),
        },
        existing=(existing,),
    )
    entry = result.commitment_entries[0]
    assert entry.decision not in {
        N01CommitmentDecision.CONFIRMED_COMMITMENT,
        N01CommitmentDecision.REVISED_COMMITMENT,
    }
    assert entry.decision is N01CommitmentDecision.CONTESTED_COMMITMENT
    assert entry.conflict_status is not N01ConflictStatus.NO_CONFLICT
    assert "unreferenced_conflict_marker" in entry.reason_codes
    assert result.ledger.accepted_commitments == ()
    assert result.telemetry.contested_commitment_count == 1
