from __future__ import annotations

from substrate.w02_regularity_extraction import (
    W02ContradictionKind,
    W02ObjectMaturityLevel,
    W02PresenceMode,
    W02PromotionStatus,
    W02RegularityCandidateType,
)
from tests.substrate.w02_regularity_extraction_testkit import (
    W02HarnessCase,
    build_w02_harness_case,
    w02_bundle,
    w02_trace,
)


def _run(case_id: str, *, traces=()):
    bundle = w02_bundle(
        bundle_id=f"{case_id}:bundle",
        traces=traces,
        source_lineage=("tests.w02.owner", case_id),
        reason=case_id,
    )
    return build_w02_harness_case(W02HarnessCase(case_id=case_id, input_bundle=bundle)).w02_result


def _first_record(result):
    return result.regularity_records[0]


def test_single_trace_cannot_promote_to_persistent_instance() -> None:
    result = _run("single", traces=(w02_trace(trace_id="t1", sequence_index=1),))
    record = _first_record(result)
    assert record.maturity_level is W02ObjectMaturityLevel.TRACE_TOKEN


def test_recurrent_scaffold_requires_non_duplicate_repetition() -> None:
    result = _run(
        "dup-only",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, is_duplicate_packet=True),
            w02_trace(trace_id="t2", sequence_index=2, is_duplicate_packet=True),
        ),
    )
    assert _first_record(result).maturity_level is W02ObjectMaturityLevel.TRACE_TOKEN


def test_temporal_spread_affects_promotion() -> None:
    no_spread = _run(
        "no-spread",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=1),
        ),
    )
    spread = _run(
        "with-spread",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=2),
        ),
    )
    assert _first_record(no_spread).maturity_level is W02ObjectMaturityLevel.TRACE_TOKEN
    assert _first_record(spread).maturity_level is W02ObjectMaturityLevel.RECURRENT_SCAFFOLD


def test_source_authority_missing_blocks_clean_promotion() -> None:
    result = _run(
        "missing-auth",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, source_authority="unknown_source"),
            w02_trace(trace_id="t2", sequence_index=2, source_authority="unknown_source"),
        ),
    )
    assert _first_record(result).promotion_status in {
        W02PromotionStatus.CONTESTED,
        W02PromotionStatus.DOWNGRADED,
    }


def test_source_authority_diversity_changes_maturity_outcome() -> None:
    weak = _run(
        "single-authority",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, source_authority="trusted_world_provider"),
            w02_trace(trace_id="t2", sequence_index=2, source_authority="trusted_world_provider"),
            w02_trace(trace_id="t3", sequence_index=3, source_authority="trusted_world_provider"),
        ),
    )
    strong = _run(
        "multi-authority",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, source_authority="trusted_world_provider"),
            w02_trace(trace_id="t2", sequence_index=2, source_authority="weak_scaffold_provider"),
            w02_trace(trace_id="t3", sequence_index=3, source_authority="trusted_world_provider"),
        ),
    )
    assert _first_record(weak).maturity_level in {
        W02ObjectMaturityLevel.RECURRENT_SCAFFOLD,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
    }
    assert _first_record(strong).maturity_level in {
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
    }


def test_scaffold_only_input_blocks_clean_regularization() -> None:
    result = _run(
        "scaffold-only",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="t2", sequence_index=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="t3", sequence_index=3, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        ),
    )
    assert _first_record(result).maturity_level is W02ObjectMaturityLevel.RECURRENT_SCAFFOLD
    assert result.gate.consumer_ready is False
    assert result.telemetry.no_clean_regularities is True


def test_partial_or_contested_presence_shrinks_permissions() -> None:
    result = _run(
        "partial-contested",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, presence_mode=W02PresenceMode.PARTIAL),
            w02_trace(trace_id="t2", sequence_index=2, presence_mode=W02PresenceMode.CONTESTED),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert packet.must_preserve_uncertainty is True


def test_absent_trace_blocks_or_downgrades_maturity() -> None:
    result = _run(
        "absent-block",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="t2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    assert _first_record(result).promotion_status in {
        W02PromotionStatus.CONTESTED,
        W02PromotionStatus.DOWNGRADED,
    }


def test_revoked_trace_triggers_downgrade_or_revalidation() -> None:
    result = _run(
        "revoked",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=2, revoked=True, presence_mode=W02PresenceMode.REVOKED),
        ),
    )
    assert _first_record(result).promotion_status is W02PromotionStatus.DOWNGRADED


def test_same_kind_does_not_imply_same_instance() -> None:
    result = _run(
        "kind-not-instance",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, entity_id="entity:a", kind_label="kind:block", candidate_type=W02RegularityCandidateType.KIND),
            w02_trace(trace_id="t2", sequence_index=2, entity_id="entity:b", kind_label="kind:block", candidate_type=W02RegularityCandidateType.KIND),
        ),
    )
    assert len(result.regularity_records) == 2


def test_same_role_does_not_imply_kind() -> None:
    result = _run(
        "role-not-kind",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, role_label="role:support", kind_label="kind:a", candidate_type=W02RegularityCandidateType.SCENE_ROLE),
            w02_trace(trace_id="t2", sequence_index=2, role_label="role:support", kind_label="kind:b", candidate_type=W02RegularityCandidateType.SCENE_ROLE),
        ),
    )
    assert result.regularity_records[0].candidate_type is W02RegularityCandidateType.SCENE_ROLE


def test_same_structural_signature_does_not_imply_same_object() -> None:
    result = _run(
        "structure-not-object",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, entity_id="entity:a", structural_signature="shape:cube"),
            w02_trace(trace_id="t2", sequence_index=2, entity_id="entity:b", structural_signature="shape:cube"),
        ),
    )
    assert len(result.regularity_records) == 2


def test_duplicate_instances_are_not_collapsed_into_continuity() -> None:
    result = _run(
        "duplicate",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, is_duplicate_packet=True),
            w02_trace(trace_id="t2", sequence_index=2, is_duplicate_packet=True),
        ),
    )
    lineage = result.lineage_hypotheses[0]
    assert any(item.lineage_kind.value == "duplicate_instance" for item in lineage.hypotheses)


def test_replacement_ambiguity_blocks_same_instance_claim() -> None:
    result = _run(
        "replacement",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, contradiction_markers=("replacement",)),
            w02_trace(trace_id="t2", sequence_index=2, contradiction_markers=("replacement",)),
        ),
    )
    assert any(item.conflict_type is W02ContradictionKind.REPLACEMENT_AMBIGUITY for item in result.contradiction_ledger)
    assert any(h.lineage_kind.value == "replacement" for h in result.lineage_hypotheses[0].hypotheses)
    assert not any(h.lineage_kind.value == "same_instance" for h in result.lineage_hypotheses[0].hypotheses)
    assert result.downstream_permission_packets[0].may_use_as_instance_hypothesis is False
    assert result.downstream_permission_packets[0].may_claim_stable_identity is False
    assert result.downstream_permission_packets[0].must_abstain is True


def test_identity_swap_creates_contradiction_ledger() -> None:
    result = _run(
        "swap",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, contradiction_markers=("identity_swap",)),
            w02_trace(trace_id="t2", sequence_index=2, contradiction_markers=("identity_swap",)),
        ),
    )
    assert any(item.conflict_type is W02ContradictionKind.IDENTITY_SWAP for item in result.contradiction_ledger)


def test_conflicting_affordance_evidence_blocks_clean_affordance_candidate() -> None:
    result = _run(
        "affordance-conflict",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
            w02_trace(trace_id="t2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
        ),
    )
    assert _first_record(result).promotion_status in {W02PromotionStatus.BLOCKED, W02PromotionStatus.CONTESTED}


def test_affordance_candidate_requires_action_effect_lineage() -> None:
    blocked = _run(
        "affordance-blocked",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
            w02_trace(trace_id="t2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
        ),
    )
    allowed = _run(
        "affordance-allowed",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref="a1", effect_ref="e1"),
            w02_trace(trace_id="t2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref="a2", effect_ref="e2"),
        ),
    )
    assert _first_record(blocked).maturity_level in {W02ObjectMaturityLevel.BLOCKED, W02ObjectMaturityLevel.CONTESTED}
    assert _first_record(allowed).maturity_level is W02ObjectMaturityLevel.AFFORDANCE_CANDIDATE


def test_provider_bias_repetition_does_not_promote_clean_regularitiy() -> None:
    result = _run(
        "provider-bias",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, provider_bias_marker=True),
            w02_trace(trace_id="t2", sequence_index=2, provider_bias_marker=True),
        ),
    )
    assert _first_record(result).maturity_level is W02ObjectMaturityLevel.TRACE_TOKEN


def test_repeated_text_artifact_does_not_count_as_lived_recurrence() -> None:
    result = _run(
        "text-artifact",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, text_artifact_marker=True),
            w02_trace(trace_id="t2", sequence_index=2, text_artifact_marker=True),
        ),
    )
    assert _first_record(result).maturity_level is W02ObjectMaturityLevel.TRACE_TOKEN


def test_contradiction_creates_ledger_not_confidence_smoothing() -> None:
    result = _run(
        "conflict-ledger",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="t2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    assert len(result.contradiction_ledger) > 0


def test_maturity_can_downgrade_after_new_contradiction() -> None:
    clean = _run(
        "clean-promote",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=2),
            w02_trace(trace_id="t3", sequence_index=3),
        ),
    )
    downgraded = _run(
        "downgrade",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=2),
            w02_trace(trace_id="t3", sequence_index=3, contradiction_markers=("identity_swap",)),
        ),
    )
    assert _first_record(clean).maturity_level in {
        W02ObjectMaturityLevel.RECURRENT_SCAFFOLD,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
    }
    assert _first_record(downgraded).maturity_level in {
        W02ObjectMaturityLevel.CONTESTED,
        W02ObjectMaturityLevel.DOWNGRADED,
    }


def test_downstream_permission_denies_stable_identity_claim() -> None:
    result = _run(
        "permission-deny-identity",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=2),
            w02_trace(trace_id="t3", sequence_index=3),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert packet.may_claim_stable_identity is False


def test_consumer_packet_distinguishes_scaffold_instance_kind_role_affordance_permissions() -> None:
    instance = _run(
        "instance-perms",
        traces=(
            w02_trace(
                trace_id="i1",
                sequence_index=1,
                source_authority="trusted_world_provider",
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
            w02_trace(
                trace_id="i2",
                sequence_index=2,
                source_authority="weak_scaffold_provider",
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
            w02_trace(
                trace_id="i3",
                sequence_index=3,
                source_authority="trusted_world_provider",
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
        ),
    )
    kind = _run(
        "kind-perms",
        traces=(
            w02_trace(trace_id="k1", sequence_index=1, candidate_type=W02RegularityCandidateType.KIND),
            w02_trace(trace_id="k2", sequence_index=2, candidate_type=W02RegularityCandidateType.KIND),
        ),
    )
    role = _run(
        "role-perms",
        traces=(
            w02_trace(trace_id="r1", sequence_index=1, candidate_type=W02RegularityCandidateType.SCENE_ROLE),
            w02_trace(trace_id="r2", sequence_index=2, candidate_type=W02RegularityCandidateType.SCENE_ROLE),
        ),
    )
    affordance = _run(
        "affordance-perms",
        traces=(
            w02_trace(
                trace_id="a1",
                sequence_index=1,
                candidate_type=W02RegularityCandidateType.AFFORDANCE,
                action_ref="a1",
                effect_ref="e1",
            ),
            w02_trace(
                trace_id="a2",
                sequence_index=2,
                candidate_type=W02RegularityCandidateType.AFFORDANCE,
                action_ref="a2",
                effect_ref="e2",
            ),
        ),
    )
    scaffold = _run(
        "scaffold-perms",
        traces=(
            w02_trace(trace_id="s1", sequence_index=1),
            w02_trace(trace_id="s2", sequence_index=2),
        ),
    )

    instance_packet = instance.downstream_permission_packets[0]
    kind_packet = kind.downstream_permission_packets[0]
    role_packet = role.downstream_permission_packets[0]
    affordance_packet = affordance.downstream_permission_packets[0]
    scaffold_packet = scaffold.downstream_permission_packets[0]

    assert scaffold_packet.may_use_as_scaffold is True
    assert scaffold_packet.may_use_as_instance_hypothesis is False
    assert scaffold_packet.may_claim_stable_identity is False

    assert instance_packet.may_use_as_instance_hypothesis is True
    assert instance_packet.may_claim_stable_identity is False
    assert instance_packet.must_preserve_uncertainty is False

    assert kind_packet.may_use_as_kind_hint is True
    assert kind_packet.may_use_as_instance_hypothesis is False
    assert kind_packet.may_claim_stable_identity is False

    assert role_packet.may_use_as_scene_role_hint is True
    assert role_packet.may_use_as_kind_hint is False
    assert role_packet.may_claim_stable_identity is False

    assert affordance_packet.may_use_as_affordance_hint is True
    assert affordance_packet.may_claim_stable_identity is False


def test_scaffold_only_trace_stays_bounded_and_not_consumer_ready_as_clean_regularity() -> None:
    result = _run(
        "scaffold-bounded",
        traces=(
            w02_trace(trace_id="s1", sequence_index=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="s2", sequence_index=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="s3", sequence_index=3, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        ),
    )
    record = _first_record(result)
    packet = result.downstream_permission_packets[0]

    assert record.maturity_level in {
        W02ObjectMaturityLevel.TRACE_TOKEN,
        W02ObjectMaturityLevel.RECURRENT_SCAFFOLD,
        W02ObjectMaturityLevel.BLOCKED,
        W02ObjectMaturityLevel.CONTESTED,
    }
    assert record.maturity_level not in {
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
    }
    assert packet.may_claim_stable_identity is False
    assert packet.may_use_as_instance_hypothesis is False
    assert packet.must_preserve_uncertainty is True
    assert result.gate.consumer_ready is False
    assert result.telemetry.no_clean_regularities is True


def test_replacement_markers_block_clean_same_instance_continuity() -> None:
    result = _run(
        "replacement-continuity",
        traces=(
            w02_trace(trace_id="r1", sequence_index=1, structural_signature="shape:cube"),
            w02_trace(
                trace_id="r2",
                sequence_index=2,
                structural_signature="shape:cube",
                contradiction_markers=("replacement",),
            ),
            w02_trace(
                trace_id="r3",
                sequence_index=3,
                structural_signature="shape:cube",
                contradiction_markers=("replacement",),
            ),
        ),
    )
    packet = result.downstream_permission_packets[0]
    lineage = result.lineage_hypotheses[0]
    record = _first_record(result)

    assert any(item.conflict_type is W02ContradictionKind.REPLACEMENT_AMBIGUITY for item in result.contradiction_ledger)
    assert any(h.lineage_kind.value == "replacement" for h in lineage.hypotheses)
    assert not any(h.lineage_kind.value == "same_instance" for h in lineage.hypotheses)
    assert packet.may_use_as_instance_hypothesis is False
    assert packet.may_claim_stable_identity is False
    assert packet.must_abstain is True
    assert record.promotion_status in {
        W02PromotionStatus.CONTESTED,
        W02PromotionStatus.DOWNGRADED,
    }


def test_ablation_of_provenance_or_temporal_spread_changes_outcome() -> None:
    full = _run(
        "full-basis",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, provenance_ref=("a",)),
            w02_trace(trace_id="t2", sequence_index=2, provenance_ref=("b",)),
            w02_trace(trace_id="t3", sequence_index=3, provenance_ref=("c",)),
        ),
    )
    ablated = _run(
        "ablated-basis",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1, provenance_ref=()),
            w02_trace(trace_id="t2", sequence_index=1, provenance_ref=()),
            w02_trace(trace_id="t3", sequence_index=1, provenance_ref=()),
        ),
    )
    assert _first_record(full).maturity_level != _first_record(ablated).maturity_level


def test_no_typed_input_returns_no_clean_regularity_claim() -> None:
    result = build_w02_harness_case(W02HarnessCase(case_id="none", input_bundle=None)).w02_result
    assert result.gate.consumer_ready is False
    assert "w02_no_clean_regularity_claim" in result.gate.required_restrictions
