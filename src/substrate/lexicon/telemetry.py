from __future__ import annotations

from substrate.lexicon.models import (
    LexicalEpisodeRecordResult,
    LexicalLearningGateDecision,
    LexicalTelemetry,
    LexiconGateDecision,
    LexicalHypothesisUpdateResult,
    LexiconQueryResult,
    LexiconState,
    LexiconUpdateResult,
)


def build_lexical_telemetry(
    *,
    state: LexiconState,
    source_lineage: tuple[str, ...],
    processed_entry_ids: tuple[str, ...],
    new_entry_count: int,
    updated_entry_count: int,
    ambiguity_reasons: tuple[str, ...],
    queried_forms: tuple[str, ...],
    matched_entry_ids: tuple[str, ...],
    no_match_count: int,
    compatibility_markers: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: LexiconGateDecision | LexicalLearningGateDecision,
    causal_basis: str,
    processed_episode_ids: tuple[str, ...] = (),
    processed_hypothesis_ids: tuple[str, ...] = (),
    recorded_episode_count: int = 0,
    promoted_hypothesis_count: int = 0,
    conflicted_hypothesis_count: int = 0,
    frozen_hypothesis_count: int = 0,
    insufficient_episode_count: int = 0,
) -> LexicalTelemetry:
    provisional_count = sum(
        1 for entry in state.entries if entry.acquisition_state.status.value == "provisional"
    )
    stable_count = sum(
        1 for entry in state.entries if entry.acquisition_state.status.value == "stable"
    )
    conflict_count = sum(1 for entry in state.entries if entry.conflict_state.value != "none")
    return LexicalTelemetry(
        source_lineage=source_lineage,
        processed_entry_ids=processed_entry_ids,
        new_entry_count=new_entry_count,
        updated_entry_count=updated_entry_count,
        provisional_entry_count=provisional_count,
        stable_entry_count=stable_count,
        unknown_item_count=len(state.unknown_items),
        conflict_entry_count=conflict_count,
        blocked_update_count=len(state.unresolved_updates),
        ambiguity_reasons=ambiguity_reasons,
        queried_forms=queried_forms,
        matched_entry_ids=matched_entry_ids,
        no_match_count=no_match_count,
        compatibility_markers=compatibility_markers,
        downstream_gate=downstream_gate,
        attempted_paths=attempted_paths,
        causal_basis=causal_basis,
        processed_episode_ids=processed_episode_ids,
        processed_hypothesis_ids=processed_hypothesis_ids,
        recorded_episode_count=recorded_episode_count,
        promoted_hypothesis_count=promoted_hypothesis_count,
        conflicted_hypothesis_count=conflicted_hypothesis_count,
        frozen_hypothesis_count=frozen_hypothesis_count,
        insufficient_episode_count=insufficient_episode_count,
    )


def lexicon_result_snapshot(
    result: LexiconUpdateResult | LexiconQueryResult | LexicalEpisodeRecordResult | LexicalHypothesisUpdateResult,
) -> dict[str, object]:
    if isinstance(result, LexiconUpdateResult):
        state = result.updated_state
        query_records: tuple[object, ...] = ()
        update_events = tuple(
            {
                "event_id": event.event_id,
                "entry_id": event.entry_id,
                "update_kind": event.update_kind.value,
                "reason_tags": event.reason_tags,
                "provenance": event.provenance,
            }
            for event in result.update_events
        )
        blocked_updates = tuple(
            {
                "surface_form": blocked.surface_form,
                "reason": blocked.reason,
                "frozen": blocked.frozen,
                "provenance": blocked.provenance,
                "compatibility_marker": blocked.compatibility_marker,
            }
            for blocked in result.blocked_updates
        )
        kind = "update"
        abstain = result.abstain
        abstain_reason = result.abstain_reason
        no_final = result.no_final_meaning_resolution_performed
    elif isinstance(result, LexiconQueryResult):
        state = result.state
        query_records = tuple(
            {
                "query_form": record.query_form,
                "matched_entry_ids": record.matched_entry_ids,
                "matched_sense_ids": record.matched_sense_ids,
                "unknown_item_ids": record.unknown_item_ids,
                "context_blocked_entry_ids": record.context_blocked_entry_ids,
                "ambiguity_reasons": record.ambiguity_reasons,
                "no_final_meaning_resolution_performed": record.no_final_meaning_resolution_performed,
            }
            for record in result.query_records
        )
        update_events = ()
        blocked_updates = ()
        kind = "query"
        abstain = result.abstain
        abstain_reason = result.abstain_reason
        no_final = result.no_final_meaning_resolution_performed
    elif isinstance(result, LexicalEpisodeRecordResult):
        state = result.updated_state
        query_records = ()
        update_events = ()
        blocked_updates = ()
        kind = "episode_record"
        abstain = result.abstain
        abstain_reason = result.abstain_reason
        no_final = result.no_final_meaning_resolution_performed
    else:
        state = result.updated_state
        query_records = ()
        update_events = ()
        blocked_updates = ()
        kind = "hypothesis_update"
        abstain = result.abstain
        abstain_reason = result.abstain_reason
        no_final = result.no_final_meaning_resolution_performed

    return {
        "kind": kind,
        "abstain": abstain,
        "abstain_reason": abstain_reason,
        "no_final_meaning_resolution_performed": no_final,
        "state": {
            "schema_version": state.schema_version,
            "lexicon_version": state.lexicon_version,
            "taxonomy_version": state.taxonomy_version,
            "last_updated_step": state.last_updated_step,
            "entries": tuple(
                {
                    "entry_id": entry.entry_id,
                    "canonical_form": entry.canonical_form,
                    "lemma": entry.lemma,
                    "aliases": entry.aliases,
                    "language_code": entry.language_code,
                    "surface_variants": tuple(
                        {
                            "form": variant.form,
                            "normalized_form": variant.normalized_form,
                            "locale_hint": variant.locale_hint,
                            "variant_kind": variant.variant_kind,
                            "confidence": variant.confidence,
                            "provenance": variant.provenance,
                        }
                        for variant in entry.surface_variants
                    ),
                    "part_of_speech_candidates": entry.part_of_speech_candidates,
                    "sense_records": tuple(
                        {
                            "sense_id": sense.sense_id,
                            "sense_family": sense.sense_family,
                            "sense_label": sense.sense_label,
                            "coarse_semantic_type": sense.coarse_semantic_type.value,
                            "compatibility_cues": sense.compatibility_cues,
                            "anti_cues": sense.anti_cues,
                            "confidence": sense.confidence,
                            "provisional": sense.provisional,
                            "status": sense.status.value,
                            "evidence_count": sense.evidence_count,
                            "conflict_markers": sense.conflict_markers,
                            "example_ids": sense.example_ids,
                            "provenance": sense.provenance,
                        }
                        for sense in entry.sense_records
                    ),
                    "examples": tuple(
                        {
                            "example_id": example.example_id,
                            "example_text": example.example_text,
                            "linked_entry_id": example.linked_entry_id,
                            "linked_sense_id": example.linked_sense_id,
                            "status": example.status.value,
                            "illustrative_only": example.illustrative_only,
                            "provenance": example.provenance,
                        }
                        for example in entry.examples
                    ),
                    "entry_status": entry.entry_status.value,
                    "acquisition_mode": entry.acquisition_mode.value,
                    "composition_profile": {
                        "role_hints": tuple(role.value for role in entry.composition_profile.role_hints),
                        "argument_structure_hints": entry.composition_profile.argument_structure_hints,
                        "can_introduce_predicate_frame": entry.composition_profile.can_introduce_predicate_frame,
                        "behaves_as_modifier": entry.composition_profile.behaves_as_modifier,
                        "behaves_as_operator": entry.composition_profile.behaves_as_operator,
                        "behaves_as_participant": entry.composition_profile.behaves_as_participant,
                        "behaves_as_referential_carrier": entry.composition_profile.behaves_as_referential_carrier,
                        "scope_sensitive": entry.composition_profile.scope_sensitive,
                        "negation_sensitive": entry.composition_profile.negation_sensitive,
                        "remains_underspecified": entry.composition_profile.remains_underspecified,
                    },
                    "reference_profile": {
                        "pronoun_like": entry.reference_profile.pronoun_like,
                        "deictic": entry.reference_profile.deictic,
                        "entity_introducing": entry.reference_profile.entity_introducing,
                        "anaphora_prone": entry.reference_profile.anaphora_prone,
                        "quote_sensitive": entry.reference_profile.quote_sensitive,
                        "requires_context": entry.reference_profile.requires_context,
                        "can_remain_unresolved": entry.reference_profile.can_remain_unresolved,
                    },
                    "acquisition_state": {
                        "status": entry.acquisition_state.status.value,
                        "evidence_count": entry.acquisition_state.evidence_count,
                        "last_supporting_evidence_ref": entry.acquisition_state.last_supporting_evidence_ref,
                        "revision_count": entry.acquisition_state.revision_count,
                        "frozen_update": entry.acquisition_state.frozen_update,
                        "staleness_steps": entry.acquisition_state.staleness_steps,
                        "decay_marker": entry.acquisition_state.decay_marker,
                        "blocked_reason": entry.acquisition_state.blocked_reason,
                    },
                    "confidence": entry.confidence,
                    "conflict_state": entry.conflict_state.value,
                    "provenance": entry.provenance,
                    "schema_version": entry.schema_version,
                    "lexicon_version": entry.lexicon_version,
                    "taxonomy_version": entry.taxonomy_version,
                }
                for entry in state.entries
            ),
            "unknown_items": tuple(
                {
                    "unknown_id": item.unknown_id,
                    "surface_form": item.surface_form,
                    "occurrence_ref": item.occurrence_ref,
                    "partial_pos_hint": item.partial_pos_hint,
                    "no_strong_meaning_claim": item.no_strong_meaning_claim,
                    "candidate_similarity_hints": item.candidate_similarity_hints,
                    "confidence": item.confidence,
                    "provenance": item.provenance,
                }
                for item in state.unknown_items
            ),
            "usage_episodes": tuple(
                {
                    "episode_id": episode.episode_id,
                    "observed_surface_form": episode.observed_surface_form,
                    "observed_lemma_hint": episode.observed_lemma_hint,
                    "language_code": episode.language_code,
                    "observed_context_keys": episode.observed_context_keys,
                    "source_kind": episode.source_kind,
                    "proposed_sense_hypotheses": tuple(
                        {
                            "sense_family": sense.sense_family,
                            "sense_label": sense.sense_label,
                            "coarse_semantic_type": sense.coarse_semantic_type.value,
                            "compatibility_cues": sense.compatibility_cues,
                            "anti_cues": sense.anti_cues,
                            "confidence": sense.confidence,
                            "provisional": sense.provisional,
                            "status_hint": sense.status_hint.value if sense.status_hint else None,
                            "example_texts": sense.example_texts,
                        }
                        for sense in episode.proposed_sense_hypotheses
                    ),
                    "proposed_role_hints": tuple(role.value for role in episode.proposed_role_hints),
                    "usage_span": episode.usage_span,
                    "confidence": episode.confidence,
                    "evidence_quality": episode.evidence_quality,
                    "step_index": episode.step_index,
                    "episode_status": episode.episode_status.value,
                    "provenance": episode.provenance,
                    "schema_version": episode.schema_version,
                    "lexicon_version": episode.lexicon_version,
                    "taxonomy_version": episode.taxonomy_version,
                    "blocked_reason": episode.blocked_reason,
                }
                for episode in state.usage_episodes
            ),
            "provisional_hypotheses": tuple(
                {
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "target_surface_form": hypothesis.target_surface_form,
                    "target_lemma": hypothesis.target_lemma,
                    "language_code": hypothesis.language_code,
                    "candidate_entry_id": hypothesis.candidate_entry_id,
                    "candidate_sense_bundle": tuple(
                        {
                            "sense_family": sense.sense_family,
                            "sense_label": sense.sense_label,
                            "coarse_semantic_type": sense.coarse_semantic_type.value,
                            "compatibility_cues": sense.compatibility_cues,
                            "anti_cues": sense.anti_cues,
                            "confidence": sense.confidence,
                            "provisional": sense.provisional,
                            "status_hint": sense.status_hint.value if sense.status_hint else None,
                            "example_texts": sense.example_texts,
                        }
                        for sense in hypothesis.candidate_sense_bundle
                    ),
                    "candidate_role_hints": tuple(
                        role.value for role in hypothesis.candidate_role_hints
                    ),
                    "supporting_episode_ids": hypothesis.supporting_episode_ids,
                    "conflicting_episode_ids": hypothesis.conflicting_episode_ids,
                    "support_count": hypothesis.support_count,
                    "conflict_count": hypothesis.conflict_count,
                    "status": hypothesis.status.value,
                    "promotion_eligibility": hypothesis.promotion_eligibility,
                    "blocked_reasons": hypothesis.blocked_reasons,
                    "confidence": hypothesis.confidence,
                    "evidence_quality": hypothesis.evidence_quality,
                    "provenance": hypothesis.provenance,
                    "promoted_entry_id": hypothesis.promoted_entry_id,
                    "schema_version": hypothesis.schema_version,
                    "lexicon_version": hypothesis.lexicon_version,
                    "taxonomy_version": hypothesis.taxonomy_version,
                }
                for hypothesis in state.provisional_hypotheses
            ),
            "unresolved_updates": tuple(
                {
                    "surface_form": blocked.surface_form,
                    "reason": blocked.reason,
                    "frozen": blocked.frozen,
                    "provenance": blocked.provenance,
                    "compatibility_marker": blocked.compatibility_marker,
                }
                for blocked in state.unresolved_updates
            ),
            "frozen_updates": tuple(
                {
                    "surface_form": blocked.surface_form,
                    "reason": blocked.reason,
                    "frozen": blocked.frozen,
                    "provenance": blocked.provenance,
                    "compatibility_marker": blocked.compatibility_marker,
                }
                for blocked in state.frozen_updates
            ),
            "conflict_index": state.conflict_index,
        },
        "update_events": update_events,
        "blocked_updates": blocked_updates,
        "query_records": query_records,
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "processed_entry_ids": result.telemetry.processed_entry_ids,
            "new_entry_count": result.telemetry.new_entry_count,
            "updated_entry_count": result.telemetry.updated_entry_count,
            "provisional_entry_count": result.telemetry.provisional_entry_count,
            "stable_entry_count": result.telemetry.stable_entry_count,
            "unknown_item_count": result.telemetry.unknown_item_count,
            "conflict_entry_count": result.telemetry.conflict_entry_count,
            "blocked_update_count": result.telemetry.blocked_update_count,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "queried_forms": result.telemetry.queried_forms,
            "matched_entry_ids": result.telemetry.matched_entry_ids,
            "no_match_count": result.telemetry.no_match_count,
            "compatibility_markers": result.telemetry.compatibility_markers,
            "downstream_gate": (
                {
                    "accepted": result.telemetry.downstream_gate.accepted,
                    "restrictions": result.telemetry.downstream_gate.restrictions,
                    "reason": result.telemetry.downstream_gate.reason,
                    "accepted_hypothesis_ids": result.telemetry.downstream_gate.accepted_hypothesis_ids,
                    "rejected_hypothesis_ids": result.telemetry.downstream_gate.rejected_hypothesis_ids,
                    "state_ref": result.telemetry.downstream_gate.state_ref,
                }
                if isinstance(result.telemetry.downstream_gate, LexicalLearningGateDecision)
                else {
                    "accepted": result.telemetry.downstream_gate.accepted,
                    "restrictions": result.telemetry.downstream_gate.restrictions,
                    "reason": result.telemetry.downstream_gate.reason,
                    "accepted_entry_ids": result.telemetry.downstream_gate.accepted_entry_ids,
                    "rejected_entry_ids": result.telemetry.downstream_gate.rejected_entry_ids,
                    "state_ref": result.telemetry.downstream_gate.state_ref,
                }
            ),
            "attempted_paths": result.telemetry.attempted_paths,
            "causal_basis": result.telemetry.causal_basis,
            "processed_episode_ids": result.telemetry.processed_episode_ids,
            "processed_hypothesis_ids": result.telemetry.processed_hypothesis_ids,
            "recorded_episode_count": result.telemetry.recorded_episode_count,
            "promoted_hypothesis_count": result.telemetry.promoted_hypothesis_count,
            "conflicted_hypothesis_count": result.telemetry.conflicted_hypothesis_count,
            "frozen_hypothesis_count": result.telemetry.frozen_hypothesis_count,
            "insufficient_episode_count": result.telemetry.insufficient_episode_count,
            "emitted_at": result.telemetry.emitted_at,
        },
    }
