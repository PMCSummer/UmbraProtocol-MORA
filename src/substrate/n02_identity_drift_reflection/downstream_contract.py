from __future__ import annotations

from dataclasses import dataclass

from substrate.n02_identity_drift_reflection.models import N02Result


@dataclass(frozen=True, slots=True)
class N02ContractView:
    drift_entry_count: int
    stable_continuation_count: int
    bounded_revision_count: int
    reflection_needed_count: int
    unresolved_identity_tension_count: int
    context_split_count: int
    no_clean_drift_count: int
    baseline_uncertain_count: int
    text_diff_only_blocked_count: int
    downstream_caution_count: int
    n02_consumer_ready: bool
    reflection_consumer_ready: bool
    consistency_consumer_ready: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    identity_drift_reflection_registry_only: bool
    no_metaphysical_identity_claim: bool
    no_autobiographical_relevance_claim: bool
    no_memory_lifecycle_claim: bool
    no_user_model_claim: bool
    no_commitment_rewrite_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class N02ConsumerView:
    drift_id: str
    affected_identity_region: str
    drift_kind: str
    drift_magnitude: float
    continuity_preserved_flag: bool
    context_split_scope: str | None
    reflection_need_level: str
    revision_pressure: str
    downstream_caution: tuple[str, ...]
    baseline_reference_id: str | None
    current_reference_id: str
    affected_commitment_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    confidence: float
    non_claim_constraints: tuple[str, ...]


def derive_n02_contract_view(result: N02Result) -> N02ContractView:
    if not isinstance(result, N02Result):
        raise TypeError("derive_n02_contract_view requires N02Result")
    return N02ContractView(
        drift_entry_count=result.telemetry.drift_entry_count,
        stable_continuation_count=result.telemetry.stable_continuation_count,
        bounded_revision_count=result.telemetry.bounded_revision_count,
        reflection_needed_count=result.telemetry.reflection_needed_count,
        unresolved_identity_tension_count=result.telemetry.unresolved_identity_tension_count,
        context_split_count=result.telemetry.context_split_count,
        no_clean_drift_count=result.telemetry.no_clean_drift_count,
        baseline_uncertain_count=result.telemetry.baseline_uncertain_count,
        text_diff_only_blocked_count=result.telemetry.text_diff_only_blocked_count,
        downstream_caution_count=result.telemetry.downstream_caution_count,
        n02_consumer_ready=result.gate.n02_consumer_ready,
        reflection_consumer_ready=result.gate.reflection_consumer_ready,
        consistency_consumer_ready=result.gate.consistency_consumer_ready,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        identity_drift_reflection_registry_only=result.scope_marker.identity_drift_reflection_registry_only,
        no_metaphysical_identity_claim=result.scope_marker.no_metaphysical_identity_claim,
        no_autobiographical_relevance_claim=result.scope_marker.no_autobiographical_relevance_claim,
        no_memory_lifecycle_claim=result.scope_marker.no_memory_lifecycle_claim,
        no_user_model_claim=result.scope_marker.no_user_model_claim,
        no_commitment_rewrite_claim=result.scope_marker.no_commitment_rewrite_claim,
        reason=result.reason,
    )


def derive_n02_consumer_packets(result: N02Result) -> tuple[N02ConsumerView, ...]:
    if not isinstance(result, N02Result):
        raise TypeError("derive_n02_consumer_packets requires N02Result")
    return tuple(
        N02ConsumerView(
            drift_id=item.drift_id,
            affected_identity_region=item.affected_identity_region.value,
            drift_kind=item.drift_kind.value,
            drift_magnitude=item.drift_magnitude,
            continuity_preserved_flag=item.continuity_preserved_flag,
            context_split_scope=item.context_split_scope,
            reflection_need_level=item.reflection_need_level.value,
            revision_pressure=item.revision_pressure,
            downstream_caution=item.downstream_caution,
            baseline_reference_id=item.baseline_reference_id,
            current_reference_id=item.current_reference_id,
            affected_commitment_ids=item.affected_commitment_ids,
            reason_codes=item.reason_codes,
            confidence=item.confidence,
            non_claim_constraints=(
                "not_full_identity_model",
                "not_truth_evaluation",
                "does_not_rewrite_commitments",
                "context_split_not_global_rupture",
                "stable_not_metaphysical_identity_claim",
            ),
        )
        for item in result.drift_entries
    )


def require_n02_reflection_consumer_ready(result_or_view: N02Result | N02ContractView) -> N02ContractView:
    view = derive_n02_contract_view(result_or_view) if isinstance(result_or_view, N02Result) else result_or_view
    if not isinstance(view, N02ContractView):
        raise TypeError("require_n02_reflection_consumer_ready requires N02Result/N02ContractView")
    if not view.reflection_consumer_ready:
        raise PermissionError("n02 reflection consumer requires typed drift reflection packets")
    return view


def require_n02_consistency_consumer_ready(result_or_view: N02Result | N02ContractView) -> N02ContractView:
    view = derive_n02_contract_view(result_or_view) if isinstance(result_or_view, N02Result) else result_or_view
    if not isinstance(view, N02ContractView):
        raise TypeError("require_n02_consistency_consumer_ready requires N02Result/N02ContractView")
    if not view.consistency_consumer_ready:
        raise PermissionError("n02 consistency consumer requires unresolved tension handling before reuse")
    return view
