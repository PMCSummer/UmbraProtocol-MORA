from __future__ import annotations

from substrate.lexicon.models import (
    LexicalAcquisitionStatus,
    LexiconGateDecision,
    LexiconQueryResult,
    LexiconState,
    LexiconUpdateResult,
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
            restrictions.append("context_required_for_reference_profile")

    for entry in state.entries:
        if candidate_entry_ids is not None and entry.entry_id not in candidate_entry_ids:
            continue
        if entry.entry_id in context_blocked_entry_ids:
            rejected_entry_ids.append(entry.entry_id)
            continue
        if entry.acquisition_state.status in {
            LexicalAcquisitionStatus.CONFLICTED,
            LexicalAcquisitionStatus.FROZEN,
        }:
            rejected_entry_ids.append(entry.entry_id)
            restrictions.append("conflicted_or_frozen_entry_present")
            continue
        if entry.acquisition_state.status != LexicalAcquisitionStatus.STABLE:
            restrictions.append("provisional_or_unknown_entry_present")
        accepted_entry_ids.append(entry.entry_id)
        if len(entry.sense_records) > 1:
            restrictions.append("multi_sense_entry_present")

    for record in query_records:
        if record.ambiguity_reasons:
            restrictions.append("query_ambiguity_present")
        if "context_required_for_reference_profile" in record.ambiguity_reasons:
            restrictions.append("context_required_for_reference_profile")
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
