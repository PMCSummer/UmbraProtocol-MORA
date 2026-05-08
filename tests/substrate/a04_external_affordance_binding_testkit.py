from __future__ import annotations

from dataclasses import dataclass

from substrate.a04_external_affordance_binding import (
    A04AdmissionStatus,
    A04ExternalAffordanceBindingResult,
    A04ExternalAffordanceCandidate,
    A04ExternalAffordanceCandidateSet,
    A04ObjectMaturityStatus,
    A04WorldEntityScaffold,
    build_a04_external_affordance_binding,
)


@dataclass(frozen=True, slots=True)
class A04HarnessCase:
    case_id: str
    candidate_set: A04ExternalAffordanceCandidateSet | None
    binding_enabled: bool = True


@dataclass(frozen=True, slots=True)
class A04HarnessRun:
    a04_result: A04ExternalAffordanceBindingResult


def a04_candidate(
    *,
    candidate_id: str,
    entity_ref: str,
    affordance_class: str,
    candidate_label: str,
    source_authority: str = "authority.world_scaffold",
    scaffold_scope: str = "frontier_entity_scope",
    object_ref: str | None = None,
    epistemic_basis: tuple[str, ...] = ("world_scaffold",),
    permission_basis: tuple[str, ...] = ("permitted",),
    temporal_validity: str = "valid_now",
    confidence: float = 0.8,
    provenance: tuple[str, ...] = ("tests.a04",),
    contradiction_refs: tuple[str, ...] = (),
    revocation_refs: tuple[str, ...] = (),
    required_world_scaffold_refs: tuple[str, ...] = (),
    admission_hint: A04AdmissionStatus | None = None,
) -> A04ExternalAffordanceCandidate:
    return A04ExternalAffordanceCandidate(
        candidate_id=candidate_id,
        entity_ref=entity_ref,
        object_ref=object_ref,
        affordance_class=affordance_class,
        candidate_label=candidate_label,
        source_authority=source_authority,
        scaffold_scope=scaffold_scope,
        epistemic_basis=epistemic_basis,
        permission_basis=permission_basis,
        temporal_validity=temporal_validity,
        confidence=confidence,
        provenance=provenance,
        contradiction_refs=contradiction_refs,
        revocation_refs=revocation_refs,
        required_world_scaffold_refs=required_world_scaffold_refs,
        admission_hint=admission_hint,
    )


def a04_scaffold(
    *,
    entity_ref: str,
    source_authority: str = "authority.world_scaffold",
    scaffold_scope: str = "frontier_entity_scope",
    admission_status: A04AdmissionStatus = A04AdmissionStatus.ADMITTED,
    confidence: float = 0.85,
    temporal_validity: str = "valid_now",
    provenance: tuple[str, ...] = ("tests.a04.scaffold",),
    supported_affordance_classes: tuple[str, ...] = (),
    entity_kind: str | None = None,
    object_ref: str | None = None,
    object_maturity_status: A04ObjectMaturityStatus = A04ObjectMaturityStatus.SCAFFOLD_ONLY,
    revocation_status: bool = False,
    revocation_refs: tuple[str, ...] = (),
) -> A04WorldEntityScaffold:
    return A04WorldEntityScaffold(
        entity_ref=entity_ref,
        source_authority=source_authority,
        scaffold_scope=scaffold_scope,
        admission_status=admission_status,
        confidence=confidence,
        temporal_validity=temporal_validity,
        provenance=provenance,
        supported_affordance_classes=supported_affordance_classes,
        entity_kind=entity_kind,
        object_ref=object_ref,
        object_maturity_status=object_maturity_status,
        revocation_status=revocation_status,
        revocation_refs=revocation_refs,
    )


def a04_candidate_set(
    *,
    set_id: str,
    candidates: tuple[A04ExternalAffordanceCandidate, ...],
    world_scaffolds: tuple[A04WorldEntityScaffold, ...],
    reason: str,
    source_lineage: tuple[str, ...] | None = None,
) -> A04ExternalAffordanceCandidateSet:
    return A04ExternalAffordanceCandidateSet(
        candidate_set_id=set_id,
        candidates=candidates,
        world_scaffolds=world_scaffolds,
        source_lineage=source_lineage if source_lineage is not None else ("tests.a04", set_id),
        reason=reason,
    )


def build_a04_harness_case(case: A04HarnessCase) -> A04HarnessRun:
    result = build_a04_external_affordance_binding(
        tick_id=f"tests.a04:{case.case_id}",
        tick_index=1,
        candidate_set=case.candidate_set,
        binding_enabled=case.binding_enabled,
    )
    return A04HarnessRun(a04_result=result)
