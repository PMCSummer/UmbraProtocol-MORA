from __future__ import annotations

from dataclasses import dataclass

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01CanonicalOntologyResult,
    A01ControllabilityClass,
    A01ControllabilityProfile,
    A01EffectScopeProfile,
    A01ObservationExpectation,
    A01OwnershipRelevance,
    A01PreconditionProfile,
    A01RawAffordanceCandidate,
    A01RawAffordanceCandidateSet,
    build_a01_internal_affordance_ontology_cleanup,
)
from tests.substrate.s04_interoceptive_self_binding_testkit import build_s04
from tests.substrate.s05_multi_cause_attribution_factorization_testkit import build_s05


@dataclass(frozen=True, slots=True)
class A01HarnessCase:
    case_id: str
    raw_candidate_set: A01RawAffordanceCandidateSet | None
    c04_execution_mode_claim: str = "continue_stream"
    c05_validity_action: str = "allow_reuse"
    cleanup_enabled: bool = True
    s04_no_stable_core_case: bool = False
    s05_contaminated_case: bool = False


@dataclass(frozen=True, slots=True)
class A01HarnessRun:
    a01_result: A01CanonicalOntologyResult


def a01_candidate(
    *,
    candidate_id: str,
    local_label: str,
    affordance_class: A01AffordanceClass,
    aliases: tuple[str, ...] = (),
    provenance: str,
    preconditions: tuple[str, ...],
    temporal_constraints: tuple[str, ...] = (),
    primary_outcomes: tuple[str, ...],
    side_effect_channels: tuple[str, ...] = (),
    target_channels: tuple[str, ...] = (),
    controllability_class: A01ControllabilityClass,
    controllability_confidence: float,
    observation_signals: tuple[str, ...],
    observation_verification_required: bool,
    interruption_semantics: str = "bounded_interruptible",
    ownership_relevance: A01OwnershipRelevance = A01OwnershipRelevance.UNKNOWN_RELEVANCE,
    self_world_relevance: str = "unknown",
    granularity_level: int = 1,
    parent_label_hint: str | None = None,
    assumption_valid: bool = True,
    effector_enabled: bool = True,
    contaminated_controllability: bool = False,
    canonical_id_hint: str | None = None,
    legacy_local_label_only: bool = False,
) -> A01RawAffordanceCandidate:
    return A01RawAffordanceCandidate(
        candidate_id=candidate_id,
        local_label=local_label,
        affordance_class=affordance_class,
        aliases=aliases,
        provenance=provenance,
        preconditions=A01PreconditionProfile(
            requirements=preconditions,
            temporal_constraints=temporal_constraints,
        ),
        effect_scope=A01EffectScopeProfile(
            primary_outcomes=primary_outcomes,
            side_effect_channels=side_effect_channels,
        ),
        target_channels=target_channels,
        controllability=A01ControllabilityProfile(
            controllability_class=controllability_class,
            confidence=controllability_confidence,
            basis_refs=("tests.a01", candidate_id),
        ),
        observation_expectation=A01ObservationExpectation(
            expected_signals=observation_signals,
            verification_required=observation_verification_required,
        ),
        interruption_semantics=interruption_semantics,
        ownership_relevance=ownership_relevance,
        self_world_relevance=self_world_relevance,
        granularity_level=granularity_level,
        parent_label_hint=parent_label_hint,
        assumption_valid=assumption_valid,
        effector_enabled=effector_enabled,
        contaminated_controllability=contaminated_controllability,
        canonical_id_hint=canonical_id_hint,
        legacy_local_label_only=legacy_local_label_only,
    )


def a01_candidate_set(
    *,
    set_id: str,
    candidates: tuple[A01RawAffordanceCandidate, ...],
    reason: str,
) -> A01RawAffordanceCandidateSet:
    return A01RawAffordanceCandidateSet(
        candidate_set_id=set_id,
        candidates=candidates,
        source_lineage=("tests.a01", set_id),
        reason=reason,
    )


def build_a01_harness_case(case: A01HarnessCase) -> A01HarnessRun:
    s04 = build_s04(
        case_id=f"a01-{case.case_id}-s04",
        tick_index=1,
        regulation_pressure_level=22.0 if case.s04_no_stable_core_case else 66.0,
        c05_revalidation_required=case.s04_no_stable_core_case,
    )
    s05 = build_s05(
        case_id=f"a01-{case.case_id}-s05",
        tick_index=1,
        c05_revalidation_required=case.s05_contaminated_case,
        world_presence_mode="present" if case.s05_contaminated_case else "absent",
        world_effect_feedback_correlated=not case.s05_contaminated_case,
        context_shift_detected=case.s05_contaminated_case,
    )
    result = build_a01_internal_affordance_ontology_cleanup(
        tick_id=f"tests.a01:{case.case_id}",
        tick_index=1,
        raw_candidate_set=case.raw_candidate_set,
        c04_execution_mode_claim=case.c04_execution_mode_claim,
        c05_validity_action=case.c05_validity_action,
        s04_result=s04,
        s05_result=s05,
        source_lineage=("tests.a01", case.case_id),
        cleanup_enabled=case.cleanup_enabled,
    )
    return A01HarnessRun(a01_result=result)
