from __future__ import annotations

from substrate.affordances.models import (
    AffordanceGateDecision,
    AffordanceResult,
    AffordanceTelemetry,
    CapabilityState,
    RegulationAffordance,
)


def build_affordance_telemetry(
    *,
    regulation_snapshot: dict[str, object],
    capability_state: CapabilityState,
    candidates: tuple[RegulationAffordance, ...],
    gate: AffordanceGateDecision,
    confidence,
    abstain_reason: str | None,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    causal_basis: str,
) -> AffordanceTelemetry:
    capability_snapshot = {
        spec.option_class.value: {
            "enabled": spec.enabled,
            "max_intensity": spec.max_intensity,
            "cooldown_steps_remaining": spec.cooldown_steps_remaining,
            "risk_multiplier": spec.risk_multiplier,
            "source_ref": spec.source_ref,
        }
        for spec in capability_state.capabilities
    }
    return AffordanceTelemetry(
        regulation_input_snapshot=regulation_snapshot,
        capability_snapshot=capability_snapshot,
        generated_candidate_ids=tuple(candidate.affordance_id for candidate in candidates),
        candidate_statuses=tuple(
            (candidate.affordance_id, candidate.status) for candidate in candidates
        ),
        candidate_reasons=tuple(
            (candidate.affordance_id, candidate.provenance_basis) for candidate in candidates
        ),
        expected_effects=tuple(
            (candidate.affordance_id, candidate.expected_effect.effect_strength_estimate)
            for candidate in candidates
        ),
        cost_risk_surface=tuple(
            (candidate.affordance_id, candidate.cost.energy_cost, candidate.risk.level)
            for candidate in candidates
        ),
        tradeoff_surface=tuple(
            (
                candidate.affordance_id,
                candidate.tradeoff.immediate_relief_score,
                candidate.tradeoff.delayed_recovery_score,
            )
            for candidate in candidates
        ),
        downstream_gate=gate,
        confidence=confidence,
        abstain_reason=abstain_reason,
        causal_basis=causal_basis,
        source_lineage=source_lineage,
        attempted_paths=attempted_paths,
    )


def affordance_result_snapshot(result: AffordanceResult) -> dict[str, object]:
    return {
        "summary": {
            "total_candidates": result.summary.total_candidates,
            "available_count": result.summary.available_count,
            "blocked_count": result.summary.blocked_count,
            "unavailable_count": result.summary.unavailable_count,
            "unsafe_count": result.summary.unsafe_count,
            "provisional_count": result.summary.provisional_count,
        },
        "gate": {
            "accepted_candidate_ids": result.gate.accepted_candidate_ids,
            "restrictions": result.gate.restrictions,
            "bias_hints": result.gate.bias_hints,
        },
    }
