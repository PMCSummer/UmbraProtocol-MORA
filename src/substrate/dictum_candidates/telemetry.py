from __future__ import annotations

from substrate.dictum_candidates.models import (
    DictumCandidateBundle,
    DictumCandidateResult,
    DictumTelemetry,
)


def build_dictum_telemetry(
    *,
    bundle: DictumCandidateBundle,
    source_lineage: tuple[str, ...],
    attempted_construction_paths: tuple[str, ...],
    downstream_gate,
    causal_basis: str,
) -> DictumTelemetry:
    underspecified_count = sum(
        len(candidate.underspecified_slots) for candidate in bundle.dictum_candidates
    )
    negation_count = sum(
        len(candidate.negation_markers) for candidate in bundle.dictum_candidates
    )
    temporal_count = sum(
        len(candidate.temporal_markers) for candidate in bundle.dictum_candidates
    )
    magnitude_count = sum(
        len(candidate.magnitude_markers) for candidate in bundle.dictum_candidates
    )
    scope_ambiguity_count = sum(
        1
        for candidate in bundle.dictum_candidates
        for marker in candidate.scope_markers
        if marker.ambiguous
    )

    return DictumTelemetry(
        source_lineage=source_lineage,
        input_syntax_refs=bundle.linked_syntax_hypothesis_ids,
        input_lexical_grounding_ref=bundle.source_lexical_grounding_ref,
        input_surface_ref=bundle.source_surface_ref,
        processed_candidate_ids=tuple(
            candidate.dictum_candidate_id for candidate in bundle.dictum_candidates
        ),
        dictum_candidate_count=len(bundle.dictum_candidates),
        underspecified_slot_count=underspecified_count,
        negation_marker_count=negation_count,
        temporal_marker_count=temporal_count,
        magnitude_marker_count=magnitude_count,
        scope_ambiguity_count=scope_ambiguity_count,
        conflict_count=len(bundle.conflicts),
        blocked_candidate_count=len(bundle.blocked_candidate_reasons),
        ambiguity_reasons=tuple(
            dict.fromkeys(
                [
                    *(ambiguity.reason for ambiguity in bundle.ambiguities),
                    *(
                        reason
                        for candidate in bundle.dictum_candidates
                        for reason in candidate.ambiguity_reasons
                    ),
                ]
            )
        ),
        attempted_construction_paths=attempted_construction_paths,
        input_lexical_basis_classes=bundle.input_lexical_basis_classes,
        fallback_basis_present=bundle.fallback_basis_present,
        lexicon_basis_missing_or_capped=bundle.lexicon_basis_missing_or_capped,
        no_strong_lexical_basis_from_upstream=bundle.no_strong_lexical_basis_from_upstream,
        lexicon_handoff_missing_upstream=bundle.lexicon_handoff_missing_upstream,
        lexicon_handoff_present_upstream=bundle.lexicon_handoff_present_upstream,
        lexicon_query_attempted_upstream=bundle.lexicon_query_attempted_upstream,
        lexicon_usable_basis_present_upstream=bundle.lexicon_usable_basis_present_upstream,
        lexicon_backed_mentions_count_upstream=bundle.lexicon_backed_mentions_count_upstream,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def dictum_result_snapshot(result: DictumCandidateResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_resolution_performed": result.no_final_resolution_performed,
        "bundle": {
            "source_lexical_grounding_ref": bundle.source_lexical_grounding_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_syntax_hypothesis_ids": bundle.linked_syntax_hypothesis_ids,
            "linked_lexical_candidate_ids": bundle.linked_lexical_candidate_ids,
            "blocked_candidate_reasons": bundle.blocked_candidate_reasons,
            "no_final_resolution_performed": bundle.no_final_resolution_performed,
            "input_lexical_basis_classes": bundle.input_lexical_basis_classes,
            "fallback_basis_present": bundle.fallback_basis_present,
            "lexicon_basis_missing_or_capped": bundle.lexicon_basis_missing_or_capped,
            "no_strong_lexical_basis_from_upstream": bundle.no_strong_lexical_basis_from_upstream,
            "lexicon_handoff_missing_upstream": bundle.lexicon_handoff_missing_upstream,
            "lexicon_handoff_present_upstream": bundle.lexicon_handoff_present_upstream,
            "lexicon_query_attempted_upstream": bundle.lexicon_query_attempted_upstream,
            "lexicon_usable_basis_present_upstream": bundle.lexicon_usable_basis_present_upstream,
            "lexicon_backed_mentions_count_upstream": bundle.lexicon_backed_mentions_count_upstream,
            "reason": bundle.reason,
            "dictum_candidates": tuple(
                {
                    "dictum_candidate_id": candidate.dictum_candidate_id,
                    "source_syntax_hypothesis_ref": candidate.source_syntax_hypothesis_ref,
                    "source_lexical_grounding_ref": candidate.source_lexical_grounding_ref,
                    "source_surface_ref": candidate.source_surface_ref,
                    "predicate_frame": {
                        "frame_id": candidate.predicate_frame.frame_id,
                        "predicate_token_id": candidate.predicate_frame.predicate_token_id,
                        "predicate_span": (
                            candidate.predicate_frame.predicate_span.start,
                            candidate.predicate_frame.predicate_span.end,
                        ),
                        "predicate_lexeme_candidate_ids": candidate.predicate_frame.predicate_lexeme_candidate_ids,
                        "clause_id": candidate.predicate_frame.clause_id,
                        "quotation_sensitive": candidate.predicate_frame.quotation_sensitive,
                        "confidence": candidate.predicate_frame.confidence,
                        "provenance": candidate.predicate_frame.provenance,
                    },
                    "argument_slots": tuple(
                        {
                            "slot_id": slot.slot_id,
                            "role_label": slot.role_label,
                            "token_id": slot.token_id,
                            "token_span": (slot.token_span.start, slot.token_span.end),
                            "lexical_candidate_ids": slot.lexical_candidate_ids,
                            "reference_candidate_ids": slot.reference_candidate_ids,
                            "unresolved": slot.unresolved,
                            "unresolved_reason": slot.unresolved_reason,
                            "confidence": slot.confidence,
                            "provenance": slot.provenance,
                        }
                        for slot in candidate.argument_slots
                    ),
                    "scope_markers": tuple(
                        {
                            "scope_marker_id": marker.scope_marker_id,
                            "marker_kind": marker.marker_kind,
                            "affected_slot_ids": marker.affected_slot_ids,
                            "ambiguous": marker.ambiguous,
                            "reason": marker.reason,
                            "confidence": marker.confidence,
                        }
                        for marker in candidate.scope_markers
                    ),
                    "negation_markers": tuple(
                        {
                            "negation_marker_id": marker.negation_marker_id,
                            "carrier_token_ids": marker.carrier_token_ids,
                            "scope_target_slot_ids": marker.scope_target_slot_ids,
                            "scope_ambiguous": marker.scope_ambiguous,
                            "confidence": marker.confidence,
                            "reason": marker.reason,
                        }
                        for marker in candidate.negation_markers
                    ),
                    "temporal_markers": tuple(
                        {
                            "temporal_marker_id": marker.temporal_marker_id,
                            "anchor_kind": marker.anchor_kind.value,
                            "token_ids": marker.token_ids,
                            "unresolved": marker.unresolved,
                            "confidence": marker.confidence,
                            "reason": marker.reason,
                        }
                        for marker in candidate.temporal_markers
                    ),
                    "magnitude_markers": tuple(
                        {
                            "magnitude_marker_id": marker.magnitude_marker_id,
                            "marker_kind": marker.marker_kind,
                            "token_ids": marker.token_ids,
                            "value_hint": marker.value_hint,
                            "unresolved": marker.unresolved,
                            "confidence": marker.confidence,
                            "reason": marker.reason,
                        }
                        for marker in candidate.magnitude_markers
                    ),
                    "polarity": candidate.polarity.value,
                    "underspecified_slots": tuple(
                        {
                            "underspecified_id": slot.underspecified_id,
                            "slot_id_or_field": slot.slot_id_or_field,
                            "reason": slot.reason,
                            "source_ref_ids": slot.source_ref_ids,
                            "confidence": slot.confidence,
                        }
                        for slot in candidate.underspecified_slots
                    ),
                    "evidence_records": tuple(
                        {
                            "evidence_id": evidence.evidence_id,
                            "evidence_kind": evidence.evidence_kind.value,
                            "source_ref_ids": evidence.source_ref_ids,
                            "supports_dimensions": evidence.supports_dimensions,
                            "unresolved": evidence.unresolved,
                            "reason": evidence.reason,
                        }
                        for evidence in candidate.evidence_records
                    ),
                    "ambiguity_reasons": candidate.ambiguity_reasons,
                    "quotation_sensitive": candidate.quotation_sensitive,
                    "confidence": candidate.confidence,
                    "provenance": candidate.provenance,
                    "no_final_resolution_performed": candidate.no_final_resolution_performed,
                }
                for candidate in bundle.dictum_candidates
            ),
            "ambiguities": tuple(
                {
                    "ambiguity_id": ambiguity.ambiguity_id,
                    "dictum_candidate_id": ambiguity.dictum_candidate_id,
                    "reason": ambiguity.reason,
                    "related_slot_ids": ambiguity.related_slot_ids,
                    "confidence": ambiguity.confidence,
                }
                for ambiguity in bundle.ambiguities
            ),
            "conflicts": tuple(
                {
                    "conflict_id": conflict.conflict_id,
                    "dictum_candidate_ids": conflict.dictum_candidate_ids,
                    "reason": conflict.reason,
                    "confidence": conflict.confidence,
                }
                for conflict in bundle.conflicts
            ),
            "unknowns": tuple(
                {
                    "unknown_id": unknown.unknown_id,
                    "dictum_candidate_ref": unknown.dictum_candidate_ref,
                    "reason": unknown.reason,
                    "source_ref_ids": unknown.source_ref_ids,
                    "confidence": unknown.confidence,
                }
                for unknown in bundle.unknowns
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "input_syntax_refs": result.telemetry.input_syntax_refs,
            "input_lexical_grounding_ref": result.telemetry.input_lexical_grounding_ref,
            "input_surface_ref": result.telemetry.input_surface_ref,
            "processed_candidate_ids": result.telemetry.processed_candidate_ids,
            "dictum_candidate_count": result.telemetry.dictum_candidate_count,
            "underspecified_slot_count": result.telemetry.underspecified_slot_count,
            "negation_marker_count": result.telemetry.negation_marker_count,
            "temporal_marker_count": result.telemetry.temporal_marker_count,
            "magnitude_marker_count": result.telemetry.magnitude_marker_count,
            "scope_ambiguity_count": result.telemetry.scope_ambiguity_count,
            "conflict_count": result.telemetry.conflict_count,
            "blocked_candidate_count": result.telemetry.blocked_candidate_count,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "attempted_construction_paths": result.telemetry.attempted_construction_paths,
            "input_lexical_basis_classes": result.telemetry.input_lexical_basis_classes,
            "fallback_basis_present": result.telemetry.fallback_basis_present,
            "lexicon_basis_missing_or_capped": result.telemetry.lexicon_basis_missing_or_capped,
            "no_strong_lexical_basis_from_upstream": result.telemetry.no_strong_lexical_basis_from_upstream,
            "lexicon_handoff_missing_upstream": result.telemetry.lexicon_handoff_missing_upstream,
            "lexicon_handoff_present_upstream": result.telemetry.lexicon_handoff_present_upstream,
            "lexicon_query_attempted_upstream": result.telemetry.lexicon_query_attempted_upstream,
            "lexicon_usable_basis_present_upstream": result.telemetry.lexicon_usable_basis_present_upstream,
            "lexicon_backed_mentions_count_upstream": result.telemetry.lexicon_backed_mentions_count_upstream,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_candidate_ids": result.telemetry.downstream_gate.accepted_candidate_ids,
                "rejected_candidate_ids": result.telemetry.downstream_gate.rejected_candidate_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
