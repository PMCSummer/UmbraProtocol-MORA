from __future__ import annotations

from substrate.w01_bounded_world_loop import (
    W01CausalLinkStatus,
    W01PacketIntegrityStatus,
    W01PresenceMode,
    W01SourceAuthority,
    W01WorldAdmissionState,
    build_w01_bounded_world_loop,
    derive_w01_contract_view,
    w01_bounded_world_loop_snapshot,
)
from tests.substrate.w01_bounded_world_loop_testkit import (
    W01HarnessCase,
    build_w01_harness_case,
    w01_packet,
    w01_packet_set,
)


def _single_packet_result(case_id: str, packet):
    return build_w01_harness_case(
        W01HarnessCase(
            case_id=case_id,
            packet_set=w01_packet_set(set_id=f"{case_id}:set", packets=(packet,), reason=case_id),
        )
    ).w01_result


def test_owner_import_surface_and_init_integrity() -> None:
    from substrate.w01_bounded_world_loop import (
        W01Result,
        W01WorldPacketSet,
        build_w01_bounded_world_loop,
        w01_bounded_world_loop_snapshot,
    )

    assert W01Result is not None
    assert W01WorldPacketSet is not None
    assert callable(build_w01_bounded_world_loop)
    assert callable(w01_bounded_world_loop_snapshot)


def test_valid_trusted_present_packet_is_admitted_scaffold_not_mature_object_claim() -> None:
    result = _single_packet_result(
        "present",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", object_label="CIRCLE", object_authority_tags=("tag",)),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.ADMITTED
    assert result.downstream_permissions[0].may_use_as_world_scaffold is True
    assert result.downstream_permissions[0].may_claim_object_presence is False
    assert result.scope_marker.no_mature_object_claim is True


def test_absent_packet_is_explicit_absence_state() -> None:
    result = _single_packet_result(
        "absent",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.ABSENT),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.ABSENT
    assert result.downstream_permissions[0].must_preserve_uncertainty is True


def test_missing_authority_does_not_produce_clean_admission() -> None:
    result = _single_packet_result(
        "missing-authority",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", source_authority=W01SourceAuthority.UNKNOWN_SOURCE),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.REJECTED
    assert result.telemetry.source_authority_missing_count == 1
    assert result.downstream_permissions[0].must_abstain is True


def test_language_only_source_does_not_produce_world_presence_claim() -> None:
    result = _single_packet_result(
        "language",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", source_authority=W01SourceAuthority.LANGUAGE_CONTEXT),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.NO_CLEAN_WORLD_CLAIM
    assert result.downstream_permissions[0].may_claim_object_presence is False


def test_unknown_presence_mode_is_not_promoted_to_present() -> None:
    result = _single_packet_result(
        "unknown-presence",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.UNKNOWN),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.CONTESTED
    assert result.telemetry.contested_count == 1


def test_partial_packet_preserves_uncertainty_and_restricts_permission() -> None:
    result = _single_packet_result(
        "partial",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.PARTIAL),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.SCAFFOLD_ONLY
    assert result.downstream_permissions[0].may_use_for_grounded_transition is False
    assert result.downstream_permissions[0].must_preserve_uncertainty is True


def test_scaffold_only_packet_cannot_become_object_claim() -> None:
    result = _single_packet_result(
        "scaffold-only",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.SCAFFOLD_ONLY, object_label="SQUARE"),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.SCAFFOLD_ONLY
    assert result.downstream_permissions[0].may_claim_object_presence is False


def test_contradictory_packets_create_ledger_and_contested_permission() -> None:
    result = build_w01_harness_case(
        W01HarnessCase(
            case_id="contradictory",
            packet_set=w01_packet_set(
                set_id="contradictory:set",
                packets=(
                    w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.PRESENT),
                    w01_packet(packet_id="p2", sequence=2, entity_ref="entity:A", presence_mode=W01PresenceMode.ABSENT),
                ),
            ),
        )
    ).w01_result
    assert result.telemetry.contradiction_count == 1
    assert result.contradiction_ledger[0].unresolved_status is True
    assert all(item.admission_state is W01WorldAdmissionState.CONTESTED for item in result.admission_records)


def test_revoked_packet_is_not_usable_evidence() -> None:
    result = _single_packet_result(
        "revoked",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", integrity_status=W01PacketIntegrityStatus.REVOKED, revoked_ref="r1"),
    )
    assert result.admission_records[0].admission_state is W01WorldAdmissionState.REVOKED
    assert result.downstream_permissions[0].must_abstain is True


def test_object_label_without_authority_tags_is_not_promoted_to_clean_object_scaffold() -> None:
    result = _single_packet_result(
        "object-no-tags",
        w01_packet(
            packet_id="p1",
            sequence=1,
            entity_ref="entity:A",
            object_label="TRIANGLE",
            object_authority_tags=(),
            source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
            presence_mode=W01PresenceMode.PRESENT,
            integrity_status=W01PacketIntegrityStatus.VALID,
        ),
    )
    record = result.admission_records[0]
    permission = result.downstream_permissions[0]
    assert record.admission_state is W01WorldAdmissionState.SCAFFOLD_ONLY
    assert "object_authority_tags_missing" in record.decision_reason_codes
    assert "object_scaffold_authority_not_admitted" in record.decision_reason_codes
    assert permission.may_use_for_grounded_transition is False
    assert permission.may_claim_object_presence is False
    assert result.scope_marker.no_mature_object_claim is True


def test_unknown_or_invalid_object_authority_tags_are_not_promoted() -> None:
    invalid = _single_packet_result(
        "object-invalid-tags",
        w01_packet(
            packet_id="p1",
            sequence=1,
            entity_ref="entity:A",
            object_label="TRIANGLE",
            object_authority_tags=("invalid",),
            source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
        ),
    )
    incompatible = _single_packet_result(
        "object-incompatible-tags",
        w01_packet(
            packet_id="p1",
            sequence=1,
            entity_ref="entity:A",
            object_label="TRIANGLE",
            object_authority_tags=("wrong_authority",),
            source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
        ),
    )
    revoked = _single_packet_result(
        "object-revoked-tags",
        w01_packet(
            packet_id="p1",
            sequence=1,
            entity_ref="entity:A",
            object_label="TRIANGLE",
            object_authority_tags=("revoked",),
            source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
        ),
    )

    assert invalid.admission_records[0].admission_state is W01WorldAdmissionState.REJECTED
    assert "object_authority_tags_invalid" in invalid.admission_records[0].decision_reason_codes
    assert invalid.downstream_permissions[0].must_abstain is True
    assert invalid.downstream_permissions[0].may_claim_object_presence is False

    assert incompatible.admission_records[0].admission_state is W01WorldAdmissionState.CONTESTED
    assert "object_authority_tags_incompatible" in incompatible.admission_records[0].decision_reason_codes
    assert incompatible.downstream_permissions[0].must_escalate is True
    assert incompatible.downstream_permissions[0].may_claim_object_presence is False

    assert revoked.admission_records[0].admission_state is W01WorldAdmissionState.REVOKED
    assert "object_authority_tags_revoked" in revoked.admission_records[0].decision_reason_codes
    assert revoked.downstream_permissions[0].must_abstain is True
    assert revoked.downstream_permissions[0].may_claim_object_presence is False


def test_object_label_with_authority_tags_remains_non_mature() -> None:
    result = _single_packet_result(
        "object-tags",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", object_label="TRIANGLE", object_authority_tags=("provider",)),
    )
    assert result.telemetry.non_mature_object_claim_count == 1
    assert result.scope_marker.no_mature_object_claim is True


def test_object_authority_tags_drive_typed_admission_difference_under_same_source_and_presence() -> None:
    tagless = _single_packet_result(
        "object-tags-missing",
        w01_packet(
            packet_id="p1",
            sequence=1,
            entity_ref="entity:A",
            source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
            presence_mode=W01PresenceMode.PRESENT,
            integrity_status=W01PacketIntegrityStatus.VALID,
            object_label="TRIANGLE",
            object_authority_tags=(),
        ),
    )
    tagged = _single_packet_result(
        "object-tags-valid",
        w01_packet(
            packet_id="p1",
            sequence=1,
            entity_ref="entity:A",
            source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
            presence_mode=W01PresenceMode.PRESENT,
            integrity_status=W01PacketIntegrityStatus.VALID,
            object_label="TRIANGLE",
            object_authority_tags=("provider",),
        ),
    )

    assert tagless.admission_records[0].admission_state is W01WorldAdmissionState.SCAFFOLD_ONLY
    assert tagged.admission_records[0].admission_state is W01WorldAdmissionState.ADMITTED
    assert "object_authority_tags_missing" in tagless.admission_records[0].decision_reason_codes
    assert "object_scaffold_authority_tagged" in tagged.admission_records[0].decision_reason_codes
    assert tagless.gate.consumer_ready is False
    assert tagged.gate.consumer_ready is True
    assert tagless.downstream_permissions[0].may_use_for_grounded_transition is False
    assert tagged.downstream_permissions[0].may_use_for_grounded_transition is True
    assert tagless.downstream_permissions[0].may_claim_object_presence is False
    assert tagged.downstream_permissions[0].may_claim_object_presence is False


def test_action_effect_valid_linkage_creates_linked_provisional() -> None:
    result = build_w01_harness_case(
        W01HarnessCase(
            case_id="link-valid",
            packet_set=w01_packet_set(
                set_id="link-valid:set",
                packets=(
                    w01_packet(packet_id="obs", sequence=1, entity_ref="entity:A", action_ref="act1", observation_payload="seen"),
                    w01_packet(packet_id="eff", sequence=2, entity_ref="entity:A", action_ref="act1", effect_payload="moved", observation_payload="state"),
                ),
            ),
        )
    ).w01_result
    assert result.action_effect_linkages[0].causal_link_status is W01CausalLinkStatus.LINKED_PROVISIONAL


def test_missing_action_ref_breaks_linkage() -> None:
    result = _single_packet_result(
        "link-missing-action",
        w01_packet(packet_id="eff", sequence=1, entity_ref="entity:A", action_ref=None, effect_payload="moved"),
    )
    assert result.action_effect_linkages[0].causal_link_status is W01CausalLinkStatus.NOT_LINKED_MISSING_ACTION_REF


def test_temporal_mismatch_breaks_linkage() -> None:
    result = build_w01_harness_case(
        W01HarnessCase(
            case_id="link-temporal",
            packet_set=w01_packet_set(
                set_id="link-temporal:set",
                packets=(
                    w01_packet(packet_id="obs", sequence=1, entity_ref="entity:A", action_ref="act1", observation_payload="seen"),
                    w01_packet(packet_id="eff", sequence=8, entity_ref="entity:A", action_ref="act1", effect_payload="moved", observation_payload="state"),
                ),
            ),
        )
    ).w01_result
    assert result.action_effect_linkages[0].causal_link_status is W01CausalLinkStatus.NOT_LINKED_TEMPORAL_MISMATCH


def test_authority_mismatch_breaks_linkage() -> None:
    result = build_w01_harness_case(
        W01HarnessCase(
            case_id="link-authority",
            packet_set=w01_packet_set(
                set_id="link-authority:set",
                packets=(
                    w01_packet(packet_id="obs", sequence=1, entity_ref="entity:A", action_ref="act1", source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER),
                    w01_packet(packet_id="eff", sequence=2, entity_ref="entity:A", action_ref="act1", effect_payload="moved", source_authority=W01SourceAuthority.WEAK_SCAFFOLD_PROVIDER),
                ),
            ),
        )
    ).w01_result
    assert result.action_effect_linkages[0].causal_link_status is W01CausalLinkStatus.NOT_LINKED_AUTHORITY_MISMATCH


def test_source_authority_ablation_changes_admission_outcome() -> None:
    admitted = _single_packet_result(
        "authority-on",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", source_authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER),
    )
    rejected = _single_packet_result(
        "authority-off",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", source_authority=W01SourceAuthority.UNKNOWN_SOURCE),
    )
    assert admitted.admission_records[0].admission_state is W01WorldAdmissionState.ADMITTED
    assert rejected.admission_records[0].admission_state is W01WorldAdmissionState.REJECTED


def test_same_payload_with_different_presence_mode_changes_permissions() -> None:
    present = _single_packet_result(
        "presence-present",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.PRESENT),
    )
    degraded = _single_packet_result(
        "presence-degraded",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A", presence_mode=W01PresenceMode.DEGRADED),
    )
    assert present.downstream_permissions[0].may_use_for_grounded_transition is True
    assert degraded.downstream_permissions[0].may_use_for_grounded_transition is False


def test_no_world_packet_does_not_synthesize_scaffold_from_text_history() -> None:
    result = build_w01_bounded_world_loop(
        tick_id="tests.w01:no-packet",
        tick_index=1,
        packet_set=w01_packet_set(set_id="no-packet:set", packets=(), reason="no packets"),
    )
    assert result.packet_refs == ()
    assert result.gate.consumer_ready is False
    assert "w01_no_world_packet" in result.gate.required_restrictions


def test_snapshot_and_contract_view_expose_scope_and_gate() -> None:
    result = _single_packet_result(
        "snapshot",
        w01_packet(packet_id="p1", sequence=1, entity_ref="entity:A"),
    )
    snapshot = w01_bounded_world_loop_snapshot(result)
    view = derive_w01_contract_view(result)
    assert snapshot["scope_marker"]["staged_world_scaffold_only"] is True
    assert view.no_world_truth_claim is True
    assert view.clean_world_claim_allowed is False
