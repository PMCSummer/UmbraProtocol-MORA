from __future__ import annotations

from dataclasses import dataclass

from substrate.n01_narrative_commitments.models import N01Result


@dataclass(frozen=True, slots=True)
class N01ContractView:
    candidate_count: int
    commitment_count: int
    strong_commitment_count: int
    provisional_commitment_count: int
    statement_only_count: int
    contested_commitment_count: int
    revised_count: int
    retired_count: int
    scope_narrowed_count: int
    ungrounded_capability_claim_count: int
    consumer_ready: bool
    consistency_consumer_ready: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    narrative_commitment_registry_only: bool
    no_identity_metaphysics_claim: bool
    no_full_autobiography_claim: bool
    no_memory_lifecycle_claim: bool
    no_policy_selection_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class N01ConsumerView:
    commitment_id: str
    claim_kind: str
    semantic_content: str
    commitment_strength: str
    commitment_scope: str
    grounding_basis: tuple[str, ...]
    referenced_commitment_refs: tuple[str, ...]
    conflict_status: str
    revision_action: str
    prior_decision: str | None
    prior_validation_status: str | None
    revision_reason: str | None
    downstream_obligations: tuple[str, ...]
    validation_status: str
    confidence: float
    reason_codes: tuple[str, ...]
    provenance: tuple[str, ...]


def derive_n01_contract_view(result: N01Result) -> N01ContractView:
    if not isinstance(result, N01Result):
        raise TypeError("derive_n01_contract_view requires N01Result")
    return N01ContractView(
        candidate_count=result.telemetry.candidate_count,
        commitment_count=result.telemetry.commitment_count,
        strong_commitment_count=result.telemetry.strong_commitment_count,
        provisional_commitment_count=result.telemetry.provisional_commitment_count,
        statement_only_count=result.telemetry.statement_only_count,
        contested_commitment_count=result.telemetry.contested_commitment_count,
        revised_count=result.telemetry.revised_count,
        retired_count=result.telemetry.retired_count,
        scope_narrowed_count=result.telemetry.scope_narrowed_count,
        ungrounded_capability_claim_count=result.telemetry.ungrounded_capability_claim_count,
        consumer_ready=result.gate.consumer_ready,
        consistency_consumer_ready=result.gate.consistency_consumer_ready,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        narrative_commitment_registry_only=result.scope_marker.narrative_commitment_registry_only,
        no_identity_metaphysics_claim=result.scope_marker.no_identity_metaphysics_claim,
        no_full_autobiography_claim=result.scope_marker.no_full_autobiography_claim,
        no_memory_lifecycle_claim=result.scope_marker.no_memory_lifecycle_claim,
        no_policy_selection_claim=result.scope_marker.no_policy_selection_claim,
        reason=result.reason,
    )


def derive_n01_consumer_packets(result: N01Result) -> tuple[N01ConsumerView, ...]:
    if not isinstance(result, N01Result):
        raise TypeError("derive_n01_consumer_packets requires N01Result")
    return tuple(
        N01ConsumerView(
            commitment_id=item.commitment_id,
            claim_kind=item.claim_kind.value,
            semantic_content=item.semantic_content,
            commitment_strength=item.strength.value,
            commitment_scope=item.scope.value,
            grounding_basis=tuple(value.value for value in item.grounding_basis),
            referenced_commitment_refs=item.referenced_commitment_refs,
            conflict_status=item.conflict_status.value,
            revision_action=item.revision_action.value,
            prior_decision=item.prior_decision.value if item.prior_decision else None,
            prior_validation_status=item.prior_validation_status,
            revision_reason=item.revision_reason,
            downstream_obligations=tuple(value.value for value in item.downstream_obligations),
            validation_status=item.validation_status,
            confidence=item.confidence,
            reason_codes=item.reason_codes,
            provenance=item.provenance,
        )
        for item in result.commitment_entries
    )


def require_n01_commitment_consumer_ready(
    result_or_view: N01Result | N01ContractView,
) -> N01ContractView:
    view = derive_n01_contract_view(result_or_view) if isinstance(result_or_view, N01Result) else result_or_view
    if not isinstance(view, N01ContractView):
        raise TypeError("require_n01_commitment_consumer_ready requires N01Result/N01ContractView")
    if not view.consumer_ready:
        raise PermissionError("n01 commitment consumer requires typed confirmed commitment readiness")
    return view


def require_n01_consistency_consumer_ready(
    result_or_view: N01Result | N01ContractView,
) -> N01ContractView:
    view = derive_n01_contract_view(result_or_view) if isinstance(result_or_view, N01Result) else result_or_view
    if not isinstance(view, N01ContractView):
        raise TypeError("require_n01_consistency_consumer_ready requires N01Result/N01ContractView")
    if not view.consistency_consumer_ready:
        raise PermissionError("n01 consistency consumer requires scope/obligation-ready commitment records")
    return view
