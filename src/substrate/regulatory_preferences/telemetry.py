from __future__ import annotations

from substrate.regulatory_preferences.models import (
    PreferenceGateDecision,
    PreferenceState,
    PreferenceTelemetry,
    PreferenceUpdateResult,
)


def build_preference_telemetry(
    *,
    state: PreferenceState,
    source_lineage: tuple[str, ...],
    input_regulation_snapshot_ref: str,
    input_affordance_ids: tuple[str, ...],
    processed_episode_ids: tuple[str, ...],
    updated_entry_ids: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
    short_term_signal_count: int,
    long_term_signal_count: int,
    context_keys_used: tuple[str, ...],
    decay_events: tuple[str, ...],
    downstream_gate: PreferenceGateDecision,
    causal_basis: str,
    attempted_update_paths: tuple[str, ...],
) -> PreferenceTelemetry:
    frozen_count = len(state.frozen_updates)
    return PreferenceTelemetry(
        source_lineage=source_lineage,
        input_regulation_snapshot_ref=input_regulation_snapshot_ref,
        input_affordance_ids=input_affordance_ids,
        processed_episode_ids=processed_episode_ids,
        updated_entry_ids=updated_entry_ids,
        blocked_update_count=len(state.unresolved_updates),
        conflict_count=len(state.conflict_index),
        freeze_update_count=frozen_count,
        short_term_signal_count=short_term_signal_count,
        long_term_signal_count=long_term_signal_count,
        attribution_blocked_reasons=blocked_reasons,
        context_keys_used=context_keys_used,
        decay_events=decay_events,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
        attempted_update_paths=attempted_update_paths,
    )


def preference_result_snapshot(result: PreferenceUpdateResult) -> dict[str, object]:
    state = result.updated_preference_state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_selection_performed": result.no_final_selection_performed,
        "preference_state": {
            "schema_version": state.schema_version,
            "taxonomy_version": state.taxonomy_version,
            "measurement_version": state.measurement_version,
            "last_updated_step": state.last_updated_step,
            "entries": tuple(
                {
                    "entry_id": entry.entry_id,
                    "option_class_id": entry.option_class_id.value,
                    "target_need_or_set": tuple(axis.value for axis in entry.target_need_or_set),
                    "preference_sign": entry.preference_sign.value,
                    "preference_strength": entry.preference_strength,
                    "expected_short_term_delta": entry.expected_short_term_delta,
                    "expected_long_term_delta": entry.expected_long_term_delta,
                    "confidence": entry.confidence.value,
                    "context_scope": entry.context_scope,
                    "time_horizon": entry.time_horizon.value,
                    "conflict_state": entry.conflict_state.value,
                    "episode_support": entry.episode_support,
                    "staleness_steps": entry.staleness_steps,
                    "decay_marker": entry.decay_marker,
                    "last_update_provenance": entry.last_update_provenance,
                    "update_status": entry.update_status.value,
                }
                for entry in state.entries
            ),
            "unresolved_updates": tuple(
                {
                    "episode_id": blocked.episode_id,
                    "option_class_id": (
                        blocked.option_class_id.value if blocked.option_class_id else None
                    ),
                    "uncertainty": blocked.uncertainty.value,
                    "reason": blocked.reason,
                    "frozen": blocked.frozen,
                    "provenance": blocked.provenance,
                }
                for blocked in state.unresolved_updates
            ),
            "frozen_updates": tuple(
                {
                    "episode_id": blocked.episode_id,
                    "option_class_id": (
                        blocked.option_class_id.value if blocked.option_class_id else None
                    ),
                    "uncertainty": blocked.uncertainty.value,
                    "reason": blocked.reason,
                    "frozen": blocked.frozen,
                    "provenance": blocked.provenance,
                }
                for blocked in state.frozen_updates
            ),
            "conflict_index": state.conflict_index,
        },
        "update_events": tuple(
            {
                "event_id": event.event_id,
                "entry_id": event.entry_id,
                "prior_entry_ref": event.prior_entry_ref,
                "observed_episode_ref": event.observed_episode_ref,
                "update_kind": event.update_kind.value,
                "reason_tags": event.reason_tags,
                "provenance": event.provenance,
                "delta_strength": event.delta_strength,
                "short_term_delta": event.short_term_delta,
                "long_term_delta": event.long_term_delta,
            }
            for event in result.update_events
        ),
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "input_regulation_snapshot_ref": result.telemetry.input_regulation_snapshot_ref,
            "input_affordance_ids": result.telemetry.input_affordance_ids,
            "processed_episode_ids": result.telemetry.processed_episode_ids,
            "updated_entry_ids": result.telemetry.updated_entry_ids,
            "blocked_update_count": result.telemetry.blocked_update_count,
            "conflict_count": result.telemetry.conflict_count,
            "freeze_update_count": result.telemetry.freeze_update_count,
            "short_term_signal_count": result.telemetry.short_term_signal_count,
            "long_term_signal_count": result.telemetry.long_term_signal_count,
            "attribution_blocked_reasons": result.telemetry.attribution_blocked_reasons,
            "context_keys_used": result.telemetry.context_keys_used,
            "decay_events": result.telemetry.decay_events,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_entry_ids": result.telemetry.downstream_gate.accepted_entry_ids,
                "rejected_entry_ids": result.telemetry.downstream_gate.rejected_entry_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
            "attempted_update_paths": result.telemetry.attempted_update_paths,
        },
    }
