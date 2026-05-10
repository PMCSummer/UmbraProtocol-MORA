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
from substrate.n02_identity_drift_reflection import (
    N02BaselineReference,
    N02BaselineValidityStatus,
    N02CommitmentHistoryEvent,
    N02CurrentIdentityEvidence,
    N02IdentityRegionKind,
    N02IdentitySubstrateChange,
    N02InputBundle,
    N02SubstrateChangeKind,
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
        reason="n02 integration baseline",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.n02.integration:{case_id}:c1",
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
                provenance=("tests.n02.integration", case_id),
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
                provenance=("tests.n02.integration.scaffold", case_id),
                supported_affordance_classes=("world_directed_action",),
                object_ref=f"object:{case_id}",
            ),
        ),
        source_lineage=("tests.n02.integration", case_id),
        reason="n02 integration fixture",
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
                provenance_ref=("tests.n02.integration", case_id),
                raw_packet_ref="raw.packet",
                object_label="CIRCLE",
                object_authority_tags=("provider",),
            ),
        ),
        source_lineage=("tests.n02.integration", case_id),
        reason="w01 integration fixture",
    )


def _n01_bundle(case_id: str) -> N01InputBundle:
    candidate = N01NarrativeClaimCandidate(
        candidate_id=f"{case_id}:cand:n01",
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
        self_side_confidence=0.88,
        mixed_cause_marker=False,
    )
    return N01InputBundle(
        bundle_id=f"{case_id}:n01:bundle",
        candidates=(candidate,),
        source_lineage=("tests.n02.integration", case_id),
    )


def _n02_bundle(case_id: str, *, variant: str) -> N02InputBundle:
    baseline = N02BaselineReference(
        baseline_id=f"{case_id}:baseline",
        baseline_kind=N02IdentityRegionKind.SELF_DESCRIPTION,
        time_scope="context:analysis",
        source_commitment_ids=(f"{case_id}:commitment:baseline",),
        source_region_ids=(f"{case_id}:region:self",),
        validity_status=N02BaselineValidityStatus.VALID,
        confidence=0.85,
        provenance=("tests.n02.integration", case_id),
    )
    current = N02CurrentIdentityEvidence(
        current_reference_id=f"{case_id}:current",
        observed_region=N02IdentityRegionKind.SELF_DESCRIPTION,
        current_commitment_ids=(f"{case_id}:commitment:current",),
        current_self_binding_refs=(f"{case_id}:binding:current",),
        capability_or_affordance_refs=(f"{case_id}:cap:current",),
        context_scope="context:analysis",
        evidence_window="window:now",
        confidence=0.82,
        provenance=("tests.n02.integration", case_id),
    )
    history = (
        N02CommitmentHistoryEvent(
            event_id=f"{case_id}:h1",
            commitment_id=f"{case_id}:commitment:current",
            region=N02IdentityRegionKind.SELF_DESCRIPTION,
            event_kind="status_change",
            previous_status="confirmed",
            current_status="provisional",
            context_scope="context:analysis",
            confidence=0.8,
            provenance=("tests.n02.integration", case_id),
        ),
    )
    if variant == "stable":
        changes = ()
    elif variant == "unresolved":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{case_id}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION,
                magnitude_hint=0.7,
                affected_commitment_ids=(f"{case_id}:commitment:current",),
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope="context:analysis",
                temporal_pattern="accumulating",
                confidence=0.83,
                self_related=True,
                provenance=("tests.n02.integration", case_id),
            ),
        )
    elif variant == "context_split":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{case_id}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.CONTEXT_SPLIT_SIGNAL,
                magnitude_hint=0.63,
                affected_commitment_ids=(f"{case_id}:commitment:current",),
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope="context:analysis",
                temporal_pattern="split",
                confidence=0.8,
                self_related=True,
                provenance=("tests.n02.integration", case_id),
            ),
        )
    elif variant == "text_diff_only":
        changes = (
            N02IdentitySubstrateChange(
                change_id=f"{case_id}:chg1",
                region=N02IdentityRegionKind.SELF_DESCRIPTION,
                change_kind=N02SubstrateChangeKind.TEXTUAL_REPHRASE_ONLY,
                magnitude_hint=0.2,
                affected_commitment_ids=(f"{case_id}:commitment:current",),
                affected_capability_refs=(),
                affected_self_binding_refs=(),
                context_scope="context:analysis",
                temporal_pattern="single",
                confidence=0.74,
                self_related=True,
                provenance=("tests.n02.integration", case_id),
            ),
        )
    else:
        raise ValueError(variant)
    return N02InputBundle(
        bundle_id=f"{case_id}:n02:bundle",
        baseline_references=(baseline,),
        current_references=(current,),
        substrate_changes=changes,
        commitment_history=history,
        source_lineage=("tests.n02.integration", case_id),
    )


def _n02_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.n02_identity_drift_reflection_checkpoint"
    )


def test_n02_checkpoint_is_after_n01_and_before_outcome_resolution() -> None:
    case_id = "rt-n02-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
            n01_input_bundle=_n01_bundle(case_id),
            n02_input_bundle=_n02_bundle(case_id, variant="stable"),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.n01_narrative_commitments_checkpoint") < ids.index(
        "rt01.n02_identity_drift_reflection_checkpoint"
    )
    assert ids.index("rt01.n02_identity_drift_reflection_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_no_explicit_n02_basis_does_not_inject_false_friction() -> None:
    case_id = "rt-n02-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n02_input_bundle=None,
        ),
    )
    checkpoint = _n02_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "n02_optional"
    assert result.state.n02_explicit_basis_present is False


def test_required_n02_basis_with_no_clean_drift_affects_gate_readiness() -> None:
    case_id = "rt-n02-no-clean"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n02_input_bundle=_n02_bundle(case_id, variant="text_diff_only"),
        ),
    )
    assert result.state.n02_no_clean_drift_count > 0
    assert result.state.n02_consumer_ready is False
    assert result.downstream_gate.usability_class.value in {"degraded_bounded", "blocked"}


def test_unresolved_identity_tension_affects_downstream_gate() -> None:
    case_id = "rt-n02-unresolved"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n02_input_bundle=_n02_bundle(case_id, variant="unresolved"),
        ),
    )
    checkpoint = _n02_checkpoint(result)
    assert "default_n02_unresolved_tension_recheck" in checkpoint.required_action
    assert result.state.n02_unresolved_identity_tension_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_context_split_affects_downstream_caution_restriction() -> None:
    case_id = "rt-n02-context-split"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            n02_input_bundle=_n02_bundle(case_id, variant="context_split"),
        ),
    )
    checkpoint = _n02_checkpoint(result)
    assert "default_n02_context_split_restriction" in checkpoint.required_action
    assert result.state.n02_context_split_count > 0
    assert result.state.n02_downstream_caution_count > 0


def test_same_checkpoint_envelope_typed_shape_divergence_changes_gate() -> None:
    common = {
        "disable_n02_enforcement": True,
        "require_n02_reflection_consumer": True,
    }
    strong_case = "rt-n02-envelope-strong"
    weak_case = "rt-n02-envelope-weak"
    strong = _result(
        strong_case,
        context=replace(
            _base_context(),
            **common,
            n02_input_bundle=_n02_bundle(strong_case, variant="stable"),
        ),
    )
    weak = _result(
        weak_case,
        context=replace(
            _base_context(),
            **common,
            n02_input_bundle=_n02_bundle(weak_case, variant="unresolved"),
        ),
    )
    strong_checkpoint = _n02_checkpoint(strong)
    weak_checkpoint = _n02_checkpoint(weak)
    assert strong_checkpoint.checkpoint_id == weak_checkpoint.checkpoint_id
    assert strong_checkpoint.required_action == weak_checkpoint.required_action
    assert strong_checkpoint.required_action == "require_n02_reflection_consumer"
    assert strong.state.n02_consumer_ready is True
    assert weak.state.n02_consumer_ready is False
    assert strong.downstream_gate.accepted is True
    assert weak.downstream_gate.accepted is False


def test_n02_does_not_mutate_n01_commitment_state_directly() -> None:
    case_id = "rt-n02-no-n01-mutation"
    context = replace(
        _base_context(),
        n01_input_bundle=_n01_bundle(case_id),
        n02_input_bundle=_n02_bundle(case_id, variant="unresolved"),
    )
    result = _result(case_id, context=context)
    assert result.n01_result.commitment_entries
    assert result.state.n01_commitment_count == len(result.n01_result.commitment_entries)


def test_stable_continuation_not_treated_as_metaphysical_identity_claim() -> None:
    case_id = "rt-n02-stable-non-claim"
    result = _result(
        case_id,
        context=replace(_base_context(), n02_input_bundle=_n02_bundle(case_id, variant="stable")),
    )
    assert result.n02_result.scope_marker.no_metaphysical_identity_claim is True
