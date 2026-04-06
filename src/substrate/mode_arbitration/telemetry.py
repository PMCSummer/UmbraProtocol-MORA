from __future__ import annotations

from substrate.mode_arbitration.models import (
    ModeArbitrationGateDecision,
    ModeArbitrationLedgerEvent,
    ModeArbitrationResult,
    ModeArbitrationState,
    ModeArbitrationTelemetry,
)


def build_mode_arbitration_telemetry(
    *,
    state: ModeArbitrationState,
    ledger_events: tuple[ModeArbitrationLedgerEvent, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: ModeArbitrationGateDecision,
    causal_basis: str,
) -> ModeArbitrationTelemetry:
    return ModeArbitrationTelemetry(
        source_lineage=state.source_lineage,
        arbitration_id=state.arbitration_id,
        tick_id=state.tick_id,
        stream_id=state.stream_id,
        source_stream_sequence_index=state.source_stream_sequence_index,
        active_mode=state.active_mode,
        candidate_count=len(state.candidate_modes),
        basis_count=len(state.arbitration_basis),
        hold_or_switch_decision=state.hold_or_switch_decision,
        endogenous_tick_kind=state.endogenous_tick_kind,
        endogenous_tick_allowed=state.endogenous_tick_allowed,
        external_turn_present=state.external_turn_present,
        dwell_budget_remaining=state.dwell_budget_remaining,
        forced_rearbitration=state.forced_rearbitration,
        arbitration_confidence=state.arbitration_confidence,
        interruptibility=state.interruptibility,
        mode_priority_vector=state.mode_priority_vector,
        ledger_events=ledger_events,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def mode_arbitration_result_snapshot(result: ModeArbitrationResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_planner_mode_selection_dependency": result.no_planner_mode_selection_dependency,
        "no_background_loop_dependency": result.no_background_loop_dependency,
        "no_external_turn_substitution_dependency": result.no_external_turn_substitution_dependency,
        "state": {
            "arbitration_id": state.arbitration_id,
            "tick_id": state.tick_id,
            "stream_id": state.stream_id,
            "source_stream_sequence_index": state.source_stream_sequence_index,
            "active_mode": state.active_mode.value,
            "candidate_modes": tuple(mode.value for mode in state.candidate_modes),
            "arbitration_basis": state.arbitration_basis,
            "mode_priority_vector": tuple(
                {
                    "mode": entry.mode.value,
                    "score": entry.score,
                    "enabled": entry.enabled,
                    "reason": entry.reason,
                }
                for entry in state.mode_priority_vector
            ),
            "hold_or_switch_decision": state.hold_or_switch_decision.value,
            "interruptibility": state.interruptibility.value,
            "dwell_budget_remaining": state.dwell_budget_remaining,
            "forced_rearbitration": state.forced_rearbitration,
            "endogenous_tick_kind": state.endogenous_tick_kind.value,
            "endogenous_tick_allowed": state.endogenous_tick_allowed,
            "external_turn_present": state.external_turn_present,
            "handoff_reason": state.handoff_reason,
            "arbitration_confidence": state.arbitration_confidence,
            "source_c01_state_ref": state.source_c01_state_ref,
            "source_c02_state_ref": state.source_c02_state_ref,
            "source_c03_state_ref": state.source_c03_state_ref,
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
            "arbitration_id": result.telemetry.arbitration_id,
            "tick_id": result.telemetry.tick_id,
            "stream_id": result.telemetry.stream_id,
            "source_stream_sequence_index": result.telemetry.source_stream_sequence_index,
            "active_mode": result.telemetry.active_mode.value,
            "candidate_count": result.telemetry.candidate_count,
            "basis_count": result.telemetry.basis_count,
            "hold_or_switch_decision": result.telemetry.hold_or_switch_decision.value,
            "endogenous_tick_kind": result.telemetry.endogenous_tick_kind.value,
            "endogenous_tick_allowed": result.telemetry.endogenous_tick_allowed,
            "external_turn_present": result.telemetry.external_turn_present,
            "dwell_budget_remaining": result.telemetry.dwell_budget_remaining,
            "forced_rearbitration": result.telemetry.forced_rearbitration,
            "arbitration_confidence": result.telemetry.arbitration_confidence,
            "interruptibility": result.telemetry.interruptibility.value,
            "mode_priority_vector": tuple(
                {
                    "mode": entry.mode.value,
                    "score": entry.score,
                    "enabled": entry.enabled,
                    "reason": entry.reason,
                }
                for entry in result.telemetry.mode_priority_vector
            ),
            "ledger_events": tuple(
                {
                    "event_id": event.event_id,
                    "event_kind": event.event_kind.value,
                    "tick_id": event.tick_id,
                    "stream_id": event.stream_id,
                    "mode": event.mode.value if event.mode is not None else None,
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
