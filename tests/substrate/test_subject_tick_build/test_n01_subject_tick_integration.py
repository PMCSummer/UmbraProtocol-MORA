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
from substrate.n01_narrative_commitments import (
    N01CommitmentScope,
    N01GroundingBasisKind,
    N01InputBundle,
    N01NarrativeClaimCandidate,
    N01NarrativeClaimKind,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome
from substrate.w01_bounded_world_loop import (
    W01PacketIntegrityStatus,
    W01PresenceMode,
    W01SourceAuthority,
    W01WorldPacket,
    W01WorldPacketSet,
)
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


def _base_context() -> SubjectTickContext:
    return SubjectTickContext()


def _a01_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set",
        reason="n01 integration baseline",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.n01.integration:{case_id}:c1",
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


def _a04_set(case_id: str):
    return A04ExternalAffordanceCandidateSet(
        candidate_set_id=f"{case_id}:a04:set",
        candidates=(
            A04ExternalAffordanceCandidate(
                candidate_id=f"{case_id}:cand",
                entity_ref=f"entity:{case_id}",
                object_ref=f"object:{case_id}",
                affordance_class="world_directed_action",
                candidate_label="turn_handle",
                source_authority="authority.world_scaffold",
                scaffold_scope="frontier_entity_scope",
                epistemic_basis=("world_scaffold",),
                permission_basis=("permitted",),
                temporal_validity="valid_now",
                confidence=0.82,
                provenance=("tests.n01.integration", case_id),
            ),
        ),
        world_scaffolds=(
            A04WorldEntityScaffold(
                entity_ref=f"entity:{case_id}",
                source_authority="authority.world_scaffold",
                scaffold_scope="frontier_entity_scope",
                admission_status=A04AdmissionStatus.ADMITTED,
                confidence=0.86,
                temporal_validity="valid_now",
                provenance=("tests.n01.integration.scaffold", case_id),
                supported_affordance_classes=("world_directed_action",),
                object_ref=f"object:{case_id}",
            ),
        ),
        source_lineage=("tests.n01.integration", case_id),
        reason="n01 integration fixture",
    )


def _w01_set(case_id: str) -> W01WorldPacketSet:
    return W01WorldPacketSet(
        packet_set_id=f"{case_id}:w01:set",
        packets=(
            W01WorldPacket(
                packet_id=f"{case_id}:p1",
                sequence=1,
                entity_ref=f"entity:{case_id}",
                observation_payload="obs",
                action_ref="act:probe",
                effect_payload=None,
                source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                source_id="provider.world",
                timestamp_or_sequence="seq:1",
                presence_mode=W01PresenceMode.PRESENT,
                confidence=0.82,
                integrity_status=W01PacketIntegrityStatus.VALID,
                contradiction_markers=(),
                provenance_ref=("tests.n01.integration", case_id),
                raw_packet_ref="raw.packet",
                object_label="CIRCLE",
                object_authority_tags=("provider",),
            ),
        ),
        source_lineage=("tests.n01.integration", case_id),
        reason="w01 integration fixture",
    )


def _n01_bundle(case_id: str, *, variant: str) -> N01InputBundle:
    if variant == "strong":
        candidate = N01NarrativeClaimCandidate(
            candidate_id=f"{case_id}:cand:strong",
            claim_text_or_semantic_form="I am operating in analysis mode",
            claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
            requested_scope=N01CommitmentScope.CURRENT_TURN,
            expression_channel="text",
            addressee_or_audience_scope="runtime",
            grounding_basis=(
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
                N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
                N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
            ),
            temporal_validity_status="fresh",
            attribution_status="self",
            self_side_confidence=0.9,
            mixed_cause_marker=False,
        )
        return N01InputBundle(
            bundle_id=f"{case_id}:n01:strong",
            candidates=(candidate,),
            source_lineage=("tests.n01.integration", case_id),
        )
    if variant == "ungrounded_capability":
        candidate = N01NarrativeClaimCandidate(
            candidate_id=f"{case_id}:cand:cap",
            claim_text_or_semantic_form="I can execute unavailable tool directly",
            claim_kind=N01NarrativeClaimKind.CAPABILITY_CLAIM,
            requested_scope=N01CommitmentScope.DIALOGUE_LOCAL,
            expression_channel="text",
            addressee_or_audience_scope="runtime",
            grounding_basis=(N01GroundingBasisKind.EXPLICIT_SELF_REPORT,),
            temporal_validity_status="fresh",
            attribution_status="self",
            self_side_confidence=0.85,
            mixed_cause_marker=False,
        )
        return N01InputBundle(
            bundle_id=f"{case_id}:n01:cap",
            candidates=(candidate,),
            source_lineage=("tests.n01.integration", case_id),
        )
    if variant == "contested":
        existing_bundle = _n01_bundle(f"{case_id}:existing", variant="strong")
        from substrate.n01_narrative_commitments import build_n01_narrative_commitments

        existing_result = build_n01_narrative_commitments(
            tick_id=f"{case_id}:existing",
            tick_index=1,
            input_bundle=existing_bundle,
        )
        existing = existing_result.commitment_entries[0]
        candidate = N01NarrativeClaimCandidate(
            candidate_id=f"{case_id}:cand:conflict",
            claim_text_or_semantic_form="I am not operating in analysis mode",
            claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
            requested_scope=N01CommitmentScope.CURRENT_TURN,
            expression_channel="text",
            addressee_or_audience_scope="runtime",
            grounding_basis=(
                N01GroundingBasisKind.EXPLICIT_SELF_REPORT,
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
            ),
            temporal_validity_status="fresh",
            attribution_status="self",
            self_side_confidence=0.85,
            mixed_cause_marker=False,
            existing_commitment_refs=(existing.commitment_id,),
        )
        return N01InputBundle(
            bundle_id=f"{case_id}:n01:conflict",
            candidates=(candidate,),
            existing_commitments=(existing,),
            source_lineage=("tests.n01.integration", case_id),
        )
    if variant == "retired":
        existing_bundle = _n01_bundle(f"{case_id}:existing", variant="strong")
        from substrate.n01_narrative_commitments import build_n01_narrative_commitments

        existing_result = build_n01_narrative_commitments(
            tick_id=f"{case_id}:existing",
            tick_index=1,
            input_bundle=existing_bundle,
        )
        existing = existing_result.commitment_entries[0]
        candidate = N01NarrativeClaimCandidate(
            candidate_id=f"{case_id}:cand:retire",
            claim_text_or_semantic_form=existing.semantic_content,
            claim_kind=N01NarrativeClaimKind.STATE_DESCRIPTION,
            requested_scope=N01CommitmentScope.CURRENT_TURN,
            expression_channel="text",
            addressee_or_audience_scope="runtime",
            grounding_basis=(N01GroundingBasisKind.INVALIDATED_BASIS,),
            temporal_validity_status="invalid",
            attribution_status="self",
            self_side_confidence=0.62,
            mixed_cause_marker=False,
            existing_commitment_refs=(existing.commitment_id,),
        )
        return N01InputBundle(
            bundle_id=f"{case_id}:n01:retire",
            candidates=(candidate,),
            existing_commitments=(existing,),
            source_lineage=("tests.n01.integration", case_id),
        )
    raise ValueError(variant)


def _n01_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.n01_narrative_commitments_checkpoint"
    )


def test_n01_checkpoint_is_after_m02_and_before_outcome_resolution() -> None:
    case_id = "rt-n01-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=_n01_bundle(case_id, variant="strong"),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.m02_predictive_relevance_checkpoint") < ids.index(
        "rt01.n01_narrative_commitments_checkpoint"
    )
    assert ids.index("rt01.n01_narrative_commitments_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_no_explicit_n01_basis_does_not_inject_false_friction() -> None:
    case_id = "rt-n01-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=None,
        ),
    )
    checkpoint = _n01_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "n01_optional"
    assert result.state.n01_explicit_basis_present is False


def test_strong_grounded_commitment_makes_n01_consumer_ready() -> None:
    case_id = "rt-n01-strong"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=_n01_bundle(case_id, variant="strong"),
        ),
    )
    assert result.state.n01_strong_commitment_count > 0
    assert result.state.n01_downstream_consumer_ready is True


def test_contested_commitment_creates_restriction_recheck_requirement() -> None:
    case_id = "rt-n01-contested"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=_n01_bundle(case_id, variant="contested"),
        ),
    )
    checkpoint = _n01_checkpoint(result)
    assert "default_n01_contested_commitment_recheck" in checkpoint.required_action
    assert result.state.n01_contested_commitment_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_ungrounded_capability_claim_changes_gate_outcome() -> None:
    case_id = "rt-n01-ungrounded-capability"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=_n01_bundle(case_id, variant="ungrounded_capability"),
        ),
    )
    assert result.state.n01_ungrounded_capability_count > 0
    assert result.state.n01_downstream_consumer_ready is False
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE
    assert result.downstream_gate.usability_class.value in {"degraded_bounded", "blocked"}


def test_same_checkpoint_envelope_but_different_typed_n01_shape_changes_gate() -> None:
    common = {
        "disable_n01_enforcement": True,
        "require_n01_commitment_consumer": True,
    }
    strong_case = "rt-n01-envelope-strong"
    weak_case = "rt-n01-envelope-weak"
    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(strong_case),
            a04_external_candidate_set=_a04_set(strong_case),
            w01_world_packet_set=_w01_set(strong_case),
            n01_input_bundle=_n01_bundle(strong_case, variant="strong"),
        ),
    )
    weak = _result(
        weak_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(weak_case),
            a04_external_candidate_set=_a04_set(weak_case),
            w01_world_packet_set=_w01_set(weak_case),
            n01_input_bundle=_n01_bundle(weak_case, variant="ungrounded_capability"),
        ),
    )
    strong_checkpoint = _n01_checkpoint(strong)
    weak_checkpoint = _n01_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong_checkpoint.required_action == "require_n01_commitment_consumer"
    assert strong.state.n01_downstream_consumer_ready is True
    assert weak.state.n01_downstream_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    assert weak.downstream_gate.usability_class.value == "degraded_bounded"


def test_revised_or_retired_record_not_treated_as_clean_confirmed() -> None:
    case_id = "rt-n01-retired"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=_n01_bundle(case_id, variant="retired"),
        ),
    )
    assert result.state.n01_revised_or_retired_count > 0
    assert result.state.n01_strong_commitment_count == 0
    assert result.state.n01_downstream_consumer_ready is False
