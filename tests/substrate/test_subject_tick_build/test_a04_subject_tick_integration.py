from __future__ import annotations

from dataclasses import replace

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.a04_external_affordance_binding import (
    A04AdmissionStatus,
    A04ExternalAffordanceCandidate,
    A04ExternalAffordanceCandidateSet,
    A04WorldEntityScaffold,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    a01_candidate,
    a01_candidate_set,
)
from tests.substrate.subject_tick_testkit import build_subject_tick


def _result(case_id: str, *, context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context=context,
    )


def _a04_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a04_external_affordance_binding_checkpoint"
    )


def _base_context() -> SubjectTickContext:
    return SubjectTickContext()


def _canonical_a01_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set",
        reason="a04 integration baseline",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.a04.integration:{case_id}:c1",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:internal_diagnostic_scan",
            ),
        ),
    )


def _a04_candidate_set(
    case_id: str,
    *,
    authority_missing: bool = False,
    revoked: bool = False,
) -> A04ExternalAffordanceCandidateSet:
    candidate = A04ExternalAffordanceCandidate(
        candidate_id=f"{case_id}:cand",
        entity_ref=f"entity:{case_id}",
        object_ref=f"object:{case_id}",
        affordance_class="world_directed_action",
        candidate_label="turn_handle",
        source_authority="" if authority_missing else "authority.world_scaffold",
        scaffold_scope="frontier_entity_scope",
        epistemic_basis=("world_scaffold",),
        permission_basis=("permitted",),
        temporal_validity="valid_now",
        confidence=0.82,
        provenance=("tests.a04.integration", case_id),
    )
    scaffold = A04WorldEntityScaffold(
        entity_ref=f"entity:{case_id}",
        source_authority="authority.world_scaffold",
        scaffold_scope="frontier_entity_scope",
        admission_status=A04AdmissionStatus.REVOKED if revoked else A04AdmissionStatus.ADMITTED,
        confidence=0.86,
        temporal_validity="valid_now",
        provenance=("tests.a04.integration.scaffold", case_id),
        supported_affordance_classes=("world_directed_action",),
        object_ref=f"object:{case_id}",
        revocation_status=revoked,
        revocation_refs=(f"{case_id}:revoked",) if revoked else (),
    )
    return A04ExternalAffordanceCandidateSet(
        candidate_set_id=f"{case_id}:a04:set",
        candidates=(candidate,),
        world_scaffolds=(scaffold,),
        source_lineage=("tests.a04.integration", case_id),
        reason="a04 integration fixture",
    )


def test_subject_tick_emits_a04_checkpoint_after_p04_before_outcome_resolution() -> None:
    case_id = "rt-a04-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_a01_set(case_id),
            a04_external_candidate_set=_a04_candidate_set(case_id),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.p04_counterfactual_policy_simulation_checkpoint" in ids
    assert "rt01.a04_external_affordance_binding_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.p04_counterfactual_policy_simulation_checkpoint") < ids.index(
        "rt01.a04_external_affordance_binding_checkpoint"
    )
    assert ids.index("rt01.a04_external_affordance_binding_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_a04_explicit_blocked_or_revoked_basis_triggers_restriction() -> None:
    case_id = "rt-a04-revoked"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_a01_set(case_id),
            a04_external_candidate_set=_a04_candidate_set(case_id, revoked=True),
        ),
    )
    checkpoint = _a04_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a04_revoked_binding_detour" in checkpoint.required_action
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_no_explicit_a04_basis_means_no_default_detour_pressure() -> None:
    case_id = "rt-a04-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_a01_set(case_id),
            a04_external_candidate_set=None,
        ),
    )
    checkpoint = _a04_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "a04_optional"
    assert result.state.a04_explicit_basis_present is False


def test_a04_gate_disabled_in_test_fixture_changes_behavior_materially() -> None:
    case_id = "rt-a04-gate-disabled"
    enabled = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_a01_set(case_id),
            a04_external_candidate_set=_a04_candidate_set(case_id, authority_missing=True),
        ),
    )
    disabled = _result(
        f"{case_id}-disabled",
        context=replace(
            _base_context(),
            disable_a04_enforcement=True,
            a01_raw_affordance_candidate_set=_canonical_a01_set(f"{case_id}-disabled"),
            a04_external_candidate_set=_a04_candidate_set(
                f"{case_id}-disabled",
                authority_missing=True,
            ),
        ),
    )
    enabled_checkpoint = _a04_checkpoint(enabled)
    disabled_checkpoint = _a04_checkpoint(disabled)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a04_no_authority_path_detour" in enabled_checkpoint.required_action
    assert disabled_checkpoint.status.value == "allowed"
    assert disabled_checkpoint.reason == "A04 gate disabled in test fixture"
    assert enabled.state.final_execution_outcome != disabled.state.final_execution_outcome


def test_same_checkpoint_envelope_with_authority_path_flip_changes_gate_outcome() -> None:
    ready_case = "rt-a04-envelope-ready"
    blocked_case = "rt-a04-envelope-blocked"
    common_flags = {
        "disable_a04_enforcement": True,
        "require_a04_binding_packet_consumer": True,
    }

    ready = _result(
        ready_case,
        context=replace(
            _base_context(),
            **common_flags,
            a01_raw_affordance_candidate_set=_canonical_a01_set(ready_case),
            a04_external_candidate_set=_a04_candidate_set(ready_case, authority_missing=False),
        ),
    )
    blocked = _result(
        blocked_case,
        context=replace(
            _base_context(),
            **common_flags,
            a01_raw_affordance_candidate_set=_canonical_a01_set(blocked_case),
            a04_external_candidate_set=_a04_candidate_set(blocked_case, authority_missing=True),
        ),
    )

    ready_checkpoint = _a04_checkpoint(ready)
    blocked_checkpoint = _a04_checkpoint(blocked)
    assert ready_checkpoint.checkpoint_id == blocked_checkpoint.checkpoint_id
    assert ready_checkpoint.required_action == blocked_checkpoint.required_action
    assert ready_checkpoint.required_action == "require_a04_binding_packet_consumer"
    assert ready.state.a04_downstream_consumer_ready is True
    assert blocked.state.a04_downstream_consumer_ready is False
    assert ready.downstream_gate.accepted is True
    assert blocked.downstream_gate.accepted is False
