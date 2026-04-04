from __future__ import annotations

from substrate.lexical_grounding.models import (
    LexicalGroundingBundle,
    LexicalGroundingGateDecision,
    LexicalGroundingResult,
    LexicalGroundingTelemetry,
)


def build_lexical_grounding_telemetry(
    *,
    bundle: LexicalGroundingBundle,
    source_lineage: tuple[str, ...],
    discourse_context_keys_used: tuple[str, ...],
    attempted_grounding_paths: tuple[str, ...],
    blocked_grounding_reasons: tuple[str, ...],
    downstream_gate: LexicalGroundingGateDecision,
    causal_basis: str,
) -> LexicalGroundingTelemetry:
    candidate_ids = tuple(
        [
            *(candidate.candidate_id for candidate in bundle.lexeme_candidates),
            *(hypothesis.reference_id for hypothesis in bundle.reference_hypotheses),
            *(candidate.candidate_id for candidate in bundle.deixis_candidates),
        ]
    )
    return LexicalGroundingTelemetry(
        source_lineage=source_lineage,
        input_syntax_ref=bundle.source_syntax_ref,
        input_surface_ref=bundle.source_surface_ref,
        processed_mention_ids=tuple(mention.mention_id for mention in bundle.mention_anchors),
        generated_candidate_ids=candidate_ids,
        candidate_count=len(candidate_ids),
        reference_candidate_count=len(bundle.reference_hypotheses),
        entity_candidate_count=len(bundle.entity_candidates),
        sense_candidate_count=len(bundle.sense_candidates),
        unknown_count=len(bundle.unknown_states),
        conflict_count=len(bundle.conflicts),
        syntax_hypothesis_count=len(bundle.linked_hypothesis_ids),
        syntax_instability_mention_count=sum(
            1
            for mention in bundle.mention_anchors
            if len(mention.supporting_syntax_hypothesis_refs) > 1
        ),
        lexicon_primary_used=bundle.lexicon_primary_used,
        lexicon_handoff_present=bundle.lexicon_handoff_present,
        lexicon_query_attempted=bundle.lexicon_query_attempted,
        lexicon_usable_basis_present=bundle.lexicon_usable_basis_present,
        lexicon_backed_mentions_count=bundle.lexicon_backed_mentions_count,
        lexicon_backed_mention_count=bundle.lexicon_backed_mentions_count,
        lexicon_capped_unknown_mention_count=sum(
            1
            for basis in bundle.lexical_basis_records
            if basis.basis_class.value == "lexicon_capped_unknown"
        ),
        heuristic_fallback_mention_count=sum(
            1
            for basis in bundle.lexical_basis_records
            if basis.heuristic_fallback_used
        ),
        no_usable_lexical_basis_mention_count=sum(
            1
            for basis in bundle.lexical_basis_records
            if basis.basis_class.value == "no_usable_lexical_basis"
        ),
        fallback_reasons=bundle.fallback_reasons,
        no_strong_lexical_claim_from_fallback=bundle.no_strong_lexical_claim_from_fallback,
        ambiguity_reasons=bundle.ambiguity_reasons,
        discourse_context_keys_used=discourse_context_keys_used,
        attempted_grounding_paths=attempted_grounding_paths,
        blocked_grounding_reasons=blocked_grounding_reasons,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
        lexicon_handoff_missing=bundle.lexicon_handoff_missing,
        lexical_basis_degraded=bundle.lexical_basis_degraded,
        no_strong_lexical_claim_without_lexicon=bundle.no_strong_lexical_claim_without_lexicon,
    )


def lexical_grounding_result_snapshot(result: LexicalGroundingResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "lexicon_primary_used": result.lexicon_primary_used,
        "lexicon_handoff_present": result.lexicon_handoff_present,
        "lexicon_query_attempted": result.lexicon_query_attempted,
        "lexicon_usable_basis_present": result.lexicon_usable_basis_present,
        "lexicon_backed_mentions_count": result.lexicon_backed_mentions_count,
        "heuristic_fallback_used": result.heuristic_fallback_used,
        "no_usable_lexical_basis": result.no_usable_lexical_basis,
        "lexicon_handoff_missing": result.lexicon_handoff_missing,
        "lexical_basis_degraded": result.lexical_basis_degraded,
        "no_strong_lexical_claim_without_lexicon": result.no_strong_lexical_claim_without_lexicon,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_resolution_performed": result.no_final_resolution_performed,
        "bundle": {
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_hypothesis_ids": bundle.linked_hypothesis_ids,
            "syntax_instability_present": bundle.syntax_instability_present,
            "lexicon_primary_used": bundle.lexicon_primary_used,
            "lexicon_handoff_present": bundle.lexicon_handoff_present,
            "lexicon_query_attempted": bundle.lexicon_query_attempted,
            "lexicon_usable_basis_present": bundle.lexicon_usable_basis_present,
            "lexicon_backed_mentions_count": bundle.lexicon_backed_mentions_count,
            "heuristic_fallback_used": bundle.heuristic_fallback_used,
            "no_strong_lexical_claim_from_fallback": bundle.no_strong_lexical_claim_from_fallback,
            "fallback_reasons": bundle.fallback_reasons,
            "no_final_resolution_performed": bundle.no_final_resolution_performed,
            "lexicon_handoff_missing": bundle.lexicon_handoff_missing,
            "lexical_basis_degraded": bundle.lexical_basis_degraded,
            "no_strong_lexical_claim_without_lexicon": bundle.no_strong_lexical_claim_without_lexicon,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "mention_anchors": tuple(
                {
                    "mention_id": mention.mention_id,
                    "token_id": mention.token_id,
                    "span": (mention.raw_span.start, mention.raw_span.end),
                    "raw_text": mention.raw_span.raw_text,
                    "surface_text": mention.surface_text,
                    "normalized_text": mention.normalized_text,
                    "syntax_hypothesis_ref": mention.syntax_hypothesis_ref,
                    "supporting_syntax_hypothesis_refs": mention.supporting_syntax_hypothesis_refs,
                    "inside_quote": mention.inside_quote,
                    "confidence": mention.confidence,
                }
                for mention in bundle.mention_anchors
            ),
            "lexical_basis_records": tuple(
                {
                    "mention_id": basis.mention_id,
                    "token_id": basis.token_id,
                    "basis_class": basis.basis_class.value,
                    "lexicon_used": basis.lexicon_used,
                    "lexicon_usable": basis.lexicon_usable,
                    "lexicon_unknown_classes": basis.lexicon_unknown_classes,
                    "lexicon_matched_entry_ids": basis.lexicon_matched_entry_ids,
                    "lexicon_matched_sense_ids": basis.lexicon_matched_sense_ids,
                    "lexicon_context_blocked_entry_ids": basis.lexicon_context_blocked_entry_ids,
                    "heuristic_fallback_used": basis.heuristic_fallback_used,
                    "heuristic_fallback_reason": basis.heuristic_fallback_reason,
                    "no_strong_lexical_claim_from_fallback": basis.no_strong_lexical_claim_from_fallback,
                }
                for basis in bundle.lexical_basis_records
            ),
            "lexeme_candidates": tuple(
                {
                    "candidate_id": candidate.candidate_id,
                    "mention_id": candidate.mention_id,
                    "token_id": candidate.token_id,
                    "candidate_type": candidate.candidate_type.value,
                    "label": candidate.label,
                    "confidence": candidate.confidence,
                    "entropy": candidate.entropy,
                    "evidence": candidate.evidence,
                    "discourse_context_ref": candidate.discourse_context_ref,
                }
                for candidate in bundle.lexeme_candidates
            ),
            "sense_candidates": tuple(
                {
                    "candidate_id": candidate.candidate_id,
                    "mention_id": candidate.mention_id,
                    "token_id": candidate.token_id,
                    "sense_key": candidate.sense_key,
                    "confidence": candidate.confidence,
                    "entropy": candidate.entropy,
                    "evidence": candidate.evidence,
                }
                for candidate in bundle.sense_candidates
            ),
            "entity_candidates": tuple(
                {
                    "candidate_id": candidate.candidate_id,
                    "mention_id": candidate.mention_id,
                    "token_id": candidate.token_id,
                    "entity_ref": candidate.entity_ref,
                    "entity_type": candidate.entity_type,
                    "confidence": candidate.confidence,
                    "evidence": candidate.evidence,
                    "discourse_context_ref": candidate.discourse_context_ref,
                }
                for candidate in bundle.entity_candidates
            ),
            "reference_hypotheses": tuple(
                {
                    "reference_id": hypothesis.reference_id,
                    "mention_id": hypothesis.mention_id,
                    "token_id": hypothesis.token_id,
                    "reference_kind": hypothesis.reference_kind.value,
                    "candidate_ref_ids": hypothesis.candidate_ref_ids,
                    "confidence": hypothesis.confidence,
                    "unresolved": hypothesis.unresolved,
                    "evidence": hypothesis.evidence,
                    "discourse_context_ref": hypothesis.discourse_context_ref,
                }
                for hypothesis in bundle.reference_hypotheses
            ),
            "deixis_candidates": tuple(
                {
                    "candidate_id": candidate.candidate_id,
                    "mention_id": candidate.mention_id,
                    "token_id": candidate.token_id,
                    "deixis_kind": candidate.deixis_kind.value,
                    "target_ref": candidate.target_ref,
                    "confidence": candidate.confidence,
                    "unresolved": candidate.unresolved,
                    "evidence": candidate.evidence,
                    "discourse_context_ref": candidate.discourse_context_ref,
                }
                for candidate in bundle.deixis_candidates
            ),
            "unknown_states": tuple(
                {
                    "unknown_id": unknown.unknown_id,
                    "mention_id": unknown.mention_id,
                    "token_id": unknown.token_id,
                    "reason": unknown.reason,
                    "confidence": unknown.confidence,
                }
                for unknown in bundle.unknown_states
            ),
            "conflicts": tuple(
                {
                    "conflict_id": conflict.conflict_id,
                    "mention_id": conflict.mention_id,
                    "candidate_ids": conflict.candidate_ids,
                    "reason": conflict.reason,
                    "confidence": conflict.confidence,
                }
                for conflict in bundle.conflicts
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "input_syntax_ref": result.telemetry.input_syntax_ref,
            "input_surface_ref": result.telemetry.input_surface_ref,
            "processed_mention_ids": result.telemetry.processed_mention_ids,
            "generated_candidate_ids": result.telemetry.generated_candidate_ids,
            "candidate_count": result.telemetry.candidate_count,
            "reference_candidate_count": result.telemetry.reference_candidate_count,
            "entity_candidate_count": result.telemetry.entity_candidate_count,
            "sense_candidate_count": result.telemetry.sense_candidate_count,
            "unknown_count": result.telemetry.unknown_count,
            "conflict_count": result.telemetry.conflict_count,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "syntax_hypothesis_count": result.telemetry.syntax_hypothesis_count,
            "syntax_instability_mention_count": result.telemetry.syntax_instability_mention_count,
            "lexicon_primary_used": result.telemetry.lexicon_primary_used,
            "lexicon_handoff_present": result.telemetry.lexicon_handoff_present,
            "lexicon_query_attempted": result.telemetry.lexicon_query_attempted,
            "lexicon_usable_basis_present": result.telemetry.lexicon_usable_basis_present,
            "lexicon_backed_mentions_count": result.telemetry.lexicon_backed_mentions_count,
            "lexicon_backed_mention_count": result.telemetry.lexicon_backed_mention_count,
            "lexicon_capped_unknown_mention_count": result.telemetry.lexicon_capped_unknown_mention_count,
            "heuristic_fallback_mention_count": result.telemetry.heuristic_fallback_mention_count,
            "no_usable_lexical_basis_mention_count": result.telemetry.no_usable_lexical_basis_mention_count,
            "fallback_reasons": result.telemetry.fallback_reasons,
            "no_strong_lexical_claim_from_fallback": result.telemetry.no_strong_lexical_claim_from_fallback,
            "lexicon_handoff_missing": result.telemetry.lexicon_handoff_missing,
            "lexical_basis_degraded": result.telemetry.lexical_basis_degraded,
            "no_strong_lexical_claim_without_lexicon": result.telemetry.no_strong_lexical_claim_without_lexicon,
            "discourse_context_keys_used": result.telemetry.discourse_context_keys_used,
            "attempted_grounding_paths": result.telemetry.attempted_grounding_paths,
            "blocked_grounding_reasons": result.telemetry.blocked_grounding_reasons,
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
