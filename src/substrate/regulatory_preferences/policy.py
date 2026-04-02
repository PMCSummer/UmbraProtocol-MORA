from __future__ import annotations

from substrate.regulation.models import RegulationConfidence
from substrate.regulatory_preferences.models import (
    PreferenceGateDecision,
    PreferenceState,
    PreferenceUpdateResult,
    PreferenceUpdateStatus,
)


def evaluate_preference_downstream_gate(
    preference_update_result_or_state: object,
) -> PreferenceGateDecision:
    if isinstance(preference_update_result_or_state, PreferenceUpdateResult):
        state = preference_update_result_or_state.updated_preference_state
    elif isinstance(preference_update_result_or_state, PreferenceState):
        state = preference_update_result_or_state
    else:
        raise TypeError("preference downstream gate requires typed PreferenceState/PreferenceUpdateResult")

    restrictions: list[str] = []
    accepted_entry_ids: list[str] = []
    rejected_entry_ids: list[str] = []

    if not state.entries:
        restrictions.append("no_preference_entries")
    if state.unresolved_updates:
        restrictions.append("unresolved_updates_present")
    if state.frozen_updates:
        restrictions.append("frozen_updates_present")
    if state.conflict_index:
        restrictions.append("conflict_present")

    for entry in state.entries:
        if entry.update_status == PreferenceUpdateStatus.FROZEN:
            rejected_entry_ids.append(entry.entry_id)
            restrictions.append("frozen_entry_present")
            continue
        if entry.confidence == RegulationConfidence.LOW:
            restrictions.append("low_confidence_entry")
            rejected_entry_ids.append(entry.entry_id)
            continue
        if entry.update_status == PreferenceUpdateStatus.PROVISIONAL:
            restrictions.append("provisional_entry_present")
        if entry.staleness_steps > 0:
            restrictions.append("stale_entry_present")
        accepted_entry_ids.append(entry.entry_id)

    accepted = bool(accepted_entry_ids)
    if accepted:
        reason = "typed preference state exposed with restrictions for downstream use"
    else:
        reason = "preference state not strong enough for unrestricted downstream use"

    return PreferenceGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_entry_ids=tuple(accepted_entry_ids),
        rejected_entry_ids=tuple(dict.fromkeys(rejected_entry_ids)),
        state_ref=state.schema_version,
    )
