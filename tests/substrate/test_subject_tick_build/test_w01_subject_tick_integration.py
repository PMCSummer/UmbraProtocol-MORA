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
        reason="w01 integration baseline",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.w01.integration:{case_id}:c1",
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
                provenance=("tests.w01.integration", case_id),
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
                provenance=("tests.w01.integration.scaffold", case_id),
                supported_affordance_classes=("world_directed_action",),
                object_ref=f"object:{case_id}",
            ),
        ),
        source_lineage=("tests.w01.integration", case_id),
        reason="w01 integration fixture",
    )


def _w01_set(
    case_id: str,
    *,
    authority_missing: bool = False,
    contradictory: bool = False,
    include_effect_link: bool = False,
    broken_link: bool = False,
    object_authority_tags: tuple[str, ...] = ("provider",),
):
    source = (
        W01SourceAuthority.UNKNOWN_SOURCE
        if authority_missing
        else W01SourceAuthority.TRUSTED_WORLD_PROVIDER
    )
    integrity = (
        W01PacketIntegrityStatus.MISSING_AUTHORITY
        if authority_missing
        else W01PacketIntegrityStatus.VALID
    )
    packets = [
        W01WorldPacket(
            packet_id=f"{case_id}:p1",
            sequence=1,
            entity_ref=f"entity:{case_id}",
            observation_payload="obs",
            action_ref="act:probe" if include_effect_link or broken_link else None,
            effect_payload=None,
            source_authority=source,
            source_id="provider.world",
            timestamp_or_sequence="seq:1",
            presence_mode=W01PresenceMode.PRESENT,
            confidence=0.82,
            integrity_status=integrity,
            contradiction_markers=("c1",) if contradictory else (),
            provenance_ref=("tests.w01.integration", case_id),
            raw_packet_ref="raw.packet",
            object_label="CIRCLE",
            object_authority_tags=object_authority_tags,
        )
    ]
    if contradictory:
        packets.append(
            W01WorldPacket(
                packet_id=f"{case_id}:p2",
                sequence=2,
                entity_ref=f"entity:{case_id}",
                observation_payload="obs2",
                action_ref=None,
                effect_payload=None,
                source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                source_id="provider.world",
                timestamp_or_sequence="seq:2",
                presence_mode=W01PresenceMode.ABSENT,
                confidence=0.79,
                integrity_status=W01PacketIntegrityStatus.VALID,
                contradiction_markers=(),
                provenance_ref=("tests.w01.integration", case_id, "p2"),
                raw_packet_ref="raw.packet.p2",
            )
        )
    if include_effect_link:
        packets.append(
            W01WorldPacket(
                packet_id=f"{case_id}:effect",
                sequence=2,
                entity_ref=f"entity:{case_id}",
                observation_payload="obs_effect",
                action_ref="act:probe",
                effect_payload="effect",
                source_authority=source,
                source_id="provider.world",
                timestamp_or_sequence="seq:2",
                presence_mode=W01PresenceMode.PRESENT,
                confidence=0.82,
                integrity_status=integrity,
                contradiction_markers=(),
                provenance_ref=("tests.w01.integration", case_id, "effect"),
                raw_packet_ref="raw.effect",
            )
        )
    if broken_link:
        packets.append(
            W01WorldPacket(
                packet_id=f"{case_id}:effect",
                sequence=7,
                entity_ref=f"entity:{case_id}",
                observation_payload="obs_effect",
                action_ref="act:probe",
                effect_payload="effect",
                source_authority=source,
                source_id="provider.world",
                timestamp_or_sequence="seq:7",
                presence_mode=W01PresenceMode.PRESENT,
                confidence=0.82,
                integrity_status=integrity,
                contradiction_markers=(),
                provenance_ref=("tests.w01.integration", case_id, "effect"),
                raw_packet_ref="raw.effect",
            )
        )
    return W01WorldPacketSet(
        packet_set_id=f"{case_id}:w01:set",
        packets=tuple(packets),
        source_lineage=("tests.w01.integration", case_id),
        reason="w01 integration fixture",
    )


def _w01_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.w01_bounded_world_loop_checkpoint"
    )


def test_subject_tick_emits_w01_checkpoint_after_a04_before_outcome_resolution() -> None:
    case_id = "rt-w01-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert ids.index("rt01.a04_external_affordance_binding_checkpoint") < ids.index(
        "rt01.w01_bounded_world_loop_checkpoint"
    )
    assert ids.index("rt01.w01_bounded_world_loop_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_no_explicit_w01_basis_produces_no_default_friction() -> None:
    case_id = "rt-w01-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=None,
        ),
    )
    checkpoint = _w01_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "w01_optional"
    assert result.state.w01_explicit_basis_present is False


def test_explicit_missing_authority_triggers_w01_restriction_detour() -> None:
    case_id = "rt-w01-authority-missing"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id, authority_missing=True),
        ),
    )
    checkpoint = _w01_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_w01_authority_missing_detour" in checkpoint.required_action
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_explicit_contradictory_packet_triggers_contested_detour() -> None:
    case_id = "rt-w01-contradictory"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id, contradictory=True),
        ),
    )
    checkpoint = _w01_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_w01_contested_world_packet_detour" in checkpoint.required_action
    assert result.state.w01_contradiction_count > 0


def test_valid_packet_can_be_consumer_ready_but_still_non_mature_object_restricted() -> None:
    case_id = "rt-w01-valid"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(case_id),
            a04_external_candidate_set=_a04_set(case_id),
            w01_world_packet_set=_w01_set(case_id),
        ),
    )
    checkpoint = _w01_checkpoint(result)
    assert result.state.w01_downstream_consumer_ready is True
    assert result.w01_result.downstream_permissions[0].may_claim_object_presence is False
    assert "default_w01_non_mature_object_claim_restriction" in checkpoint.required_action


def test_same_checkpoint_envelope_same_required_action_but_typed_w01_shape_changes_gate_outcome() -> None:
    common = {
        "disable_w01_enforcement": True,
        "require_w01_permission_packet_consumer": True,
    }
    ready_case = "rt-w01-envelope-ready"
    blocked_case = "rt-w01-envelope-blocked"

    ready = _result(
        ready_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(ready_case),
            a04_external_candidate_set=_a04_set(ready_case),
            w01_world_packet_set=_w01_set(ready_case, authority_missing=False),
        ),
    )
    blocked = _result(
        blocked_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(blocked_case),
            a04_external_candidate_set=_a04_set(blocked_case),
            w01_world_packet_set=_w01_set(blocked_case, authority_missing=True),
        ),
    )

    ready_checkpoint = _w01_checkpoint(ready)
    blocked_checkpoint = _w01_checkpoint(blocked)
    assert ready_checkpoint.checkpoint_id == blocked_checkpoint.checkpoint_id
    assert ready_checkpoint.required_action == blocked_checkpoint.required_action
    assert ready_checkpoint.required_action == "require_w01_permission_packet_consumer"
    assert ready.state.w01_downstream_consumer_ready is True
    assert blocked.state.w01_downstream_consumer_ready is False
    assert ready.downstream_gate.accepted is True
    assert blocked.downstream_gate.usability_class.value == "degraded_bounded"
    assert (
        "w01_authority_missing_detour_required"
        in [item.value for item in blocked.downstream_gate.restrictions]
    )


def test_same_checkpoint_envelope_same_required_action_object_authority_tags_change_typed_gate_outcome() -> None:
    common = {
        "disable_w01_enforcement": False,
        "require_w01_permission_packet_consumer": True,
    }
    tagged_case = "rt-w01-object-tags-valid"
    tagless_case = "rt-w01-object-tags-missing"

    tagged = _result(
        tagged_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(tagged_case),
            a04_external_candidate_set=_a04_set(tagged_case),
            w01_world_packet_set=_w01_set(tagged_case, object_authority_tags=("provider",)),
        ),
    )
    tagless = _result(
        tagless_case,
        context=replace(
            _base_context(),
            **common,
            a01_raw_affordance_candidate_set=_a01_set(tagless_case),
            a04_external_candidate_set=_a04_set(tagless_case),
            w01_world_packet_set=_w01_set(tagless_case, object_authority_tags=()),
        ),
    )

    tagged_checkpoint = _w01_checkpoint(tagged)
    tagless_checkpoint = _w01_checkpoint(tagless)
    assert tagged_checkpoint.checkpoint_id == tagless_checkpoint.checkpoint_id
    assert tagged_checkpoint.required_action == tagless_checkpoint.required_action
    assert (
        tagged_checkpoint.required_action
        == "require_w01_permission_packet_consumer;default_w01_non_mature_object_claim_restriction"
    )
    assert tagged_checkpoint.status.value == "allowed"
    assert tagless_checkpoint.status.value == "enforced_detour"

    assert tagged.state.w01_source_authority_missing_count == 0
    assert tagless.state.w01_source_authority_missing_count == 0
    assert tagged.state.w01_permission_packet_consumer_ready is True
    assert tagless.state.w01_permission_packet_consumer_ready is False

    assert tagged.w01_result.downstream_permissions[0].may_claim_object_presence is False
    assert tagless.w01_result.downstream_permissions[0].may_claim_object_presence is False
    assert tagged.w01_result.downstream_permissions[0].may_use_for_grounded_transition is True
    assert tagless.w01_result.downstream_permissions[0].may_use_for_grounded_transition is False
    assert "object_scaffold_authority_tagged" in tagged.w01_result.downstream_permissions[0].reason_codes
    assert "object_authority_tags_missing" in tagless.w01_result.downstream_permissions[0].reason_codes

    assert tagged.state.w01_admitted_count > 0
    assert tagless.state.w01_admitted_count == 0
    assert tagless.state.w01_scaffold_only_count > 0


def test_action_effect_linkage_present_vs_broken_changes_w01_shape() -> None:
    linked_case = "rt-w01-link-ok"
    broken_case = "rt-w01-link-broken"
    linked = _result(
        linked_case,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(linked_case),
            a04_external_candidate_set=_a04_set(linked_case),
            w01_world_packet_set=_w01_set(linked_case, include_effect_link=True),
        ),
    )
    broken = _result(
        broken_case,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_a01_set(broken_case),
            a04_external_candidate_set=_a04_set(broken_case),
            w01_world_packet_set=_w01_set(broken_case, broken_link=True),
        ),
    )
    assert linked.state.w01_linked_effect_count > 0
    assert broken.state.w01_linked_effect_count == 0
    assert linked.state.w01_no_link_count < broken.state.w01_no_link_count
