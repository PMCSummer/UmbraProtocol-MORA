from __future__ import annotations

from substrate.temporal_validity.models import (
    TemporalValidityGateDecision,
    TemporalValidityLedgerEvent,
    TemporalValidityResult,
    TemporalValidityState,
    TemporalValidityTelemetry,
)


def build_temporal_validity_telemetry(
    *,
    state: TemporalValidityState,
    ledger_events: tuple[TemporalValidityLedgerEvent, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: TemporalValidityGateDecision,
    causal_basis: str,
) -> TemporalValidityTelemetry:
    return TemporalValidityTelemetry(
        source_lineage=state.source_lineage,
        validity_id=state.validity_id,
        stream_id=state.stream_id,
        source_stream_sequence_index=state.source_stream_sequence_index,
        item_count=len(state.items),
        reusable_count=len(state.reusable_item_ids),
        provisional_count=len(state.provisional_item_ids),
        revalidation_count=len(state.revalidation_item_ids),
        invalidated_count=len(state.invalidated_item_ids),
        expired_count=len(state.expired_item_ids),
        dependency_contaminated_count=len(state.dependency_contaminated_item_ids),
        no_safe_reuse_count=len(state.no_safe_reuse_item_ids),
        selective_scope_target_count=len(state.selective_scope_targets),
        insufficient_basis_for_revalidation=state.insufficient_basis_for_revalidation,
        provisional_carry_only=state.provisional_carry_only,
        dependency_graph_incomplete=state.dependency_graph_incomplete,
        invalidation_possible_but_unproven=state.invalidation_possible_but_unproven,
        selective_scope_uncertain=state.selective_scope_uncertain,
        ledger_events=ledger_events,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def temporal_validity_result_snapshot(result: TemporalValidityResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_ttl_only_shortcut_dependency": result.no_ttl_only_shortcut_dependency,
        "no_blanket_reset_dependency": result.no_blanket_reset_dependency,
        "no_blanket_reuse_dependency": result.no_blanket_reuse_dependency,
        "no_global_recompute_dependency": result.no_global_recompute_dependency,
        "state": {
            "validity_id": state.validity_id,
            "stream_id": state.stream_id,
            "source_stream_sequence_index": state.source_stream_sequence_index,
            "items": tuple(
                {
                    "item_id": item.item_id,
                    "item_kind": item.item_kind.value,
                    "source_provenance": item.source_provenance,
                    "dependency_set": item.dependency_set,
                    "dependent_item_ids": item.dependent_item_ids,
                    "current_validity_status": item.current_validity_status.value,
                    "reusable_now": item.reusable_now,
                    "revalidation_priority": item.revalidation_priority,
                    "revalidation_scope": item.revalidation_scope.value,
                    "invalidation_triggers": item.invalidation_triggers,
                    "last_validated_sequence_index": item.last_validated_sequence_index,
                    "grace_window_remaining": item.grace_window_remaining,
                    "provisional_horizon": item.provisional_horizon,
                    "confidence": item.confidence,
                    "reason": item.reason,
                    "provenance": item.provenance,
                }
                for item in state.items
            ),
            "reusable_item_ids": state.reusable_item_ids,
            "provisional_item_ids": state.provisional_item_ids,
            "revalidation_item_ids": state.revalidation_item_ids,
            "invalidated_item_ids": state.invalidated_item_ids,
            "expired_item_ids": state.expired_item_ids,
            "dependency_contaminated_item_ids": state.dependency_contaminated_item_ids,
            "no_safe_reuse_item_ids": state.no_safe_reuse_item_ids,
            "selective_scope_targets": state.selective_scope_targets,
            "insufficient_basis_for_revalidation": state.insufficient_basis_for_revalidation,
            "provisional_carry_only": state.provisional_carry_only,
            "dependency_graph_incomplete": state.dependency_graph_incomplete,
            "invalidation_possible_but_unproven": state.invalidation_possible_but_unproven,
            "selective_scope_uncertain": state.selective_scope_uncertain,
            "source_c01_state_ref": state.source_c01_state_ref,
            "source_c02_state_ref": state.source_c02_state_ref,
            "source_c03_state_ref": state.source_c03_state_ref,
            "source_c04_state_ref": state.source_c04_state_ref,
            "source_regulation_ref": state.source_regulation_ref,
            "source_affordance_ref": state.source_affordance_ref,
            "source_preference_ref": state.source_preference_ref,
            "source_viability_ref": state.source_viability_ref,
            "source_lineage": state.source_lineage,
            "last_update_provenance": state.last_update_provenance,
        },
        "downstream_gate": {
            "accepted": result.downstream_gate.accepted,
            "usability_class": result.downstream_gate.usability_class.value,
            "restrictions": tuple(code.value for code in result.downstream_gate.restrictions),
            "reason": result.downstream_gate.reason,
            "state_ref": result.downstream_gate.state_ref,
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "validity_id": result.telemetry.validity_id,
            "stream_id": result.telemetry.stream_id,
            "source_stream_sequence_index": result.telemetry.source_stream_sequence_index,
            "item_count": result.telemetry.item_count,
            "reusable_count": result.telemetry.reusable_count,
            "provisional_count": result.telemetry.provisional_count,
            "revalidation_count": result.telemetry.revalidation_count,
            "invalidated_count": result.telemetry.invalidated_count,
            "expired_count": result.telemetry.expired_count,
            "dependency_contaminated_count": result.telemetry.dependency_contaminated_count,
            "no_safe_reuse_count": result.telemetry.no_safe_reuse_count,
            "selective_scope_target_count": result.telemetry.selective_scope_target_count,
            "insufficient_basis_for_revalidation": result.telemetry.insufficient_basis_for_revalidation,
            "provisional_carry_only": result.telemetry.provisional_carry_only,
            "dependency_graph_incomplete": result.telemetry.dependency_graph_incomplete,
            "invalidation_possible_but_unproven": result.telemetry.invalidation_possible_but_unproven,
            "selective_scope_uncertain": result.telemetry.selective_scope_uncertain,
            "ledger_events": tuple(
                {
                    "event_id": event.event_id,
                    "event_kind": event.event_kind.value,
                    "item_id": event.item_id,
                    "stream_id": event.stream_id,
                    "reason": event.reason,
                    "reason_code": event.reason_code,
                    "provenance": event.provenance,
                }
                for event in result.telemetry.ledger_events
            ),
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": tuple(
                    code.value for code in result.telemetry.downstream_gate.restrictions
                ),
                "reason": result.telemetry.downstream_gate.reason,
                "state_ref": result.telemetry.downstream_gate.state_ref,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
