from __future__ import annotations

from substrate.lexicon.models import (
    LexicalAcquisitionStatus,
    LexicalEntry,
    LexicalEpisodeRecordResult,
    LexicalHypothesisStatus,
    LexicalHypothesisUpdateResult,
    LexicalLearningGateDecision,
    LexicalSenseStatus,
    LexicalUnknownClass,
    LexiconQueryRecord,
    LexiconGateDecision,
    LexiconQueryResult,
    LexiconState,
    LexiconUpdateResult,
)


def _entry_version_incompatible(*, entry: LexicalEntry, state: LexiconState) -> bool:
    return (
        entry.schema_version != state.schema_version
        or entry.lexicon_version != state.lexicon_version
        or entry.taxonomy_version != state.taxonomy_version
    )


def build_lexicon_gate_decision(
    *,
    state: LexiconState,
    query_records: tuple[LexiconQueryRecord, ...] = (),
    abstain: bool = False,
) -> LexiconGateDecision:
    restrictions: list[str] = []
    accepted_entry_ids: list[str] = []
    rejected_entry_ids: list[str] = []
    candidate_entry_ids: set[str] | None = None
    context_blocked_entry_ids: set[str] = set()

    if abstain:
        restrictions.append("abstain")
    if state.unresolved_updates:
        restrictions.append("blocked_updates_present")
    if state.frozen_updates:
        restrictions.append("frozen_updates_present")
    if any(update.compatibility_marker for update in state.unresolved_updates):
        restrictions.append("compatibility_mismatch")
    if state.conflict_index:
        restrictions.append("conflict_entries_present")
    if state.unknown_items:
        restrictions.append("unknown_items_present")
    if state.provisional_hypotheses:
        restrictions.append("learning_hypotheses_present")
        if any(
            hypothesis.status == LexicalHypothesisStatus.PROVISIONAL
            for hypothesis in state.provisional_hypotheses
        ):
            restrictions.append("learning_hypothesis_provisional")
        if any(
            hypothesis.status == LexicalHypothesisStatus.CONFLICTED
            for hypothesis in state.provisional_hypotheses
        ):
            restrictions.append("learning_hypothesis_conflicted")
        if any(
            hypothesis.status == LexicalHypothesisStatus.FROZEN
            for hypothesis in state.provisional_hypotheses
        ):
            restrictions.append("learning_hypothesis_frozen")

    if query_records:
        candidate_entry_ids = {
            entry_id
            for record in query_records
            for entry_id in record.matched_entry_ids
        }
        context_blocked_entry_ids = {
            entry_id
            for record in query_records
            for entry_id in record.context_blocked_entry_ids
        }
        if not candidate_entry_ids:
            restrictions.append("query_no_match")
        if context_blocked_entry_ids:
            restrictions.append("context_blocked_query_match_present")

    for entry in state.entries:
        if candidate_entry_ids is not None and entry.entry_id not in candidate_entry_ids:
            continue
        if _entry_version_incompatible(entry=entry, state=state):
            rejected_entry_ids.append(entry.entry_id)
            restrictions.append("entry_version_mismatch")
            continue
        if entry.acquisition_state.status in {
            LexicalAcquisitionStatus.CONFLICTED,
            LexicalAcquisitionStatus.FROZEN,
        }:
            rejected_entry_ids.append(entry.entry_id)
            restrictions.append("conflicted_or_frozen_entry_present")
            continue
        if entry.entry_id in context_blocked_entry_ids:
            rejected_entry_ids.append(entry.entry_id)
            continue
        stable_senses = tuple(
            sense for sense in entry.sense_records if sense.status == LexicalSenseStatus.STABLE
        )
        if query_records and not stable_senses:
            rejected_entry_ids.append(entry.entry_id)
            restrictions.append("only_unstable_senses")
            continue
        if (
            query_records
            and entry.acquisition_state.status != LexicalAcquisitionStatus.STABLE
            and not entry.examples
        ):
            rejected_entry_ids.append(entry.entry_id)
            restrictions.append("non_stable_entry_without_example_support")
            continue
        if entry.acquisition_state.status != LexicalAcquisitionStatus.STABLE:
            restrictions.append("provisional_or_unknown_entry_present")
        accepted_entry_ids.append(entry.entry_id)
        if len(entry.sense_records) > 1:
            restrictions.append("multi_sense_entry_present")
        if any(sense.status != LexicalSenseStatus.STABLE for sense in entry.sense_records):
            restrictions.append("non_stable_sense_present")

    for record in query_records:
        if record.ambiguity_reasons:
            restrictions.append("query_ambiguity_present")
        if record.hard_unknown_or_capped:
            restrictions.append("query_record_hard_unknown_or_capped")
        if not record.strong_lexical_claim_permitted:
            restrictions.append("query_record_strong_claim_capped")
            restrictions.append("no_strong_meaning_claim")
        if record.dominant_unknown_class is not None:
            restrictions.append(f"dominant_{record.dominant_unknown_class.value}")
        if record.unknown_states:
            restrictions.append("query_unknown_state_present")
            restrictions.append("no_strong_meaning_claim")
        for unknown_state in record.unknown_states:
            if unknown_state.unknown_class == LexicalUnknownClass.UNKNOWN_WORD:
                restrictions.append("unknown_word")
            elif unknown_state.unknown_class == LexicalUnknownClass.PARTIAL_LEXICAL_HYPOTHESIS:
                restrictions.append("partial_lexical_hypothesis")
            elif unknown_state.unknown_class == LexicalUnknownClass.KNOWN_SYNTAX_UNKNOWN_LEXEME:
                restrictions.append("known_syntax_unknown_lexeme")
            elif (
                unknown_state.unknown_class
                == LexicalUnknownClass.KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT
            ):
                restrictions.append("known_lexeme_unknown_sense_in_context")
                for entry_id in unknown_state.entry_ids:
                    if entry_id in accepted_entry_ids:
                        accepted_entry_ids.remove(entry_id)
                        rejected_entry_ids.append(entry_id)
        if "context_required_for_reference_profile" in record.ambiguity_reasons:
            restrictions.append("context_required_for_reference_profile")
        if "operator_scope_context_required" in record.ambiguity_reasons:
            restrictions.append("operator_scope_context_required")
        if not record.matched_entry_ids and not record.unknown_item_ids:
            restrictions.append("query_no_match")
        if not record.matched_entry_ids and record.unknown_item_ids:
            restrictions.append("query_unknown_item_present")

    accepted = bool(accepted_entry_ids) and not abstain
    reason = (
        "typed lexical substrate exposed with bounded lexical uncertainty"
        if accepted
        else "lexical substrate currently too uncertain for unrestricted downstream use"
    )

    return LexiconGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_entry_ids=tuple(dict.fromkeys(accepted_entry_ids)),
        rejected_entry_ids=tuple(dict.fromkeys(rejected_entry_ids)),
        state_ref=f"{state.schema_version}|{state.lexicon_version}|{state.taxonomy_version}",
    )


def evaluate_lexicon_downstream_gate(lexicon_result_or_state: object) -> LexiconGateDecision:
    if isinstance(lexicon_result_or_state, LexiconUpdateResult):
        state = lexicon_result_or_state.updated_state
        query_records = ()
        abstain = lexicon_result_or_state.abstain
    elif isinstance(lexicon_result_or_state, LexiconQueryResult):
        state = lexicon_result_or_state.state
        query_records = lexicon_result_or_state.query_records
        abstain = lexicon_result_or_state.abstain
    elif isinstance(lexicon_result_or_state, LexiconState):
        state = lexicon_result_or_state
        query_records = ()
        abstain = False
    else:
        raise TypeError(
            "lexicon downstream gate requires typed LexiconState/LexiconUpdateResult/LexiconQueryResult"
        )
    return build_lexicon_gate_decision(
        state=state,
        query_records=query_records,
        abstain=abstain,
    )


def evaluate_lexical_learning_downstream_gate(
    lexical_learning_artifact: object,
) -> LexicalLearningGateDecision:
    if isinstance(lexical_learning_artifact, LexicalEpisodeRecordResult):
        state = lexical_learning_artifact.updated_state
        abstain = lexical_learning_artifact.abstain
    elif isinstance(lexical_learning_artifact, LexicalHypothesisUpdateResult):
        state = lexical_learning_artifact.updated_state
        abstain = lexical_learning_artifact.abstain
    elif isinstance(lexical_learning_artifact, LexiconState):
        state = lexical_learning_artifact
        abstain = False
    else:
        raise TypeError(
            "lexical learning downstream gate requires typed LexiconState/LexicalEpisodeRecordResult/LexicalHypothesisUpdateResult"
        )

    restrictions: list[str] = []
    accepted_hypothesis_ids: list[str] = []
    rejected_hypothesis_ids: list[str] = []
    if abstain:
        restrictions.append("abstain")

    if not state.provisional_hypotheses:
        restrictions.append("no_learning_hypotheses")

    for hypothesis in state.provisional_hypotheses:
        status = hypothesis.status
        if status == LexicalHypothesisStatus.PROMOTION_ELIGIBLE:
            accepted_hypothesis_ids.append(hypothesis.hypothesis_id)
            continue
        if status == LexicalHypothesisStatus.STABLE_PROMOTED:
            restrictions.append("already_promoted_hypothesis_present")
            continue
        rejected_hypothesis_ids.append(hypothesis.hypothesis_id)
        if status == LexicalHypothesisStatus.CONFLICTED:
            restrictions.append("learning_conflict_present")
        elif status == LexicalHypothesisStatus.FROZEN:
            restrictions.append("learning_frozen_present")
        elif status == LexicalHypothesisStatus.PROVISIONAL:
            if hypothesis.support_count <= 1:
                restrictions.append("single_episode_only")
            restrictions.append("learning_provisional_only")
        else:
            restrictions.append("learning_unknown_state")

    accepted = bool(accepted_hypothesis_ids) and not abstain
    reason = (
        "episode-backed lexical hypotheses have promotion-eligible support"
        if accepted
        else "lexical learning state remains provisional/conflicted/insufficient"
    )
    return LexicalLearningGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_hypothesis_ids=tuple(dict.fromkeys(accepted_hypothesis_ids)),
        rejected_hypothesis_ids=tuple(dict.fromkeys(rejected_hypothesis_ids)),
        state_ref=f"{state.schema_version}|{state.lexicon_version}|{state.taxonomy_version}",
    )
