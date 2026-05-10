from __future__ import annotations

from substrate.w02_regularity_extraction import W02PresenceMode, W02RegularityCandidateType
from tests.substrate.w02_regularity_extraction_testkit import w02_bundle, w02_trace
from tests.substrate.w03_schema_consolidation_testkit import (
    W03HarnessCase,
    build_w03_harness_case,
    w03_input_from_w02,
)
from substrate.w03_schema_consolidation import (
    W03ContradictionConsequenceRoute,
    W03SchemaChannel,
    W03SchemaStatus,
)


def _run_from_w02(case_id: str, traces=()):
    w02_input = w02_bundle(bundle_id=f"{case_id}:w02", traces=traces, source_lineage=("tests.w03.owner", case_id), reason=case_id)
    w03_input = w03_input_from_w02(case_id=case_id, w02_input=w02_input, source_lineage=("tests.w03.owner", case_id))
    return build_w03_harness_case(W03HarnessCase(case_id=case_id, w03_input=w03_input)).w03_result


def _first_candidate(result):
    return result.schema_candidates[0]


def test_no_w02_support_blocks_schema_claim() -> None:
    result = build_w03_harness_case(W03HarnessCase(case_id="none", w03_input=None)).w03_result
    assert result.gate.no_clean_schema is True
    assert result.gate.consumer_ready is False


def test_clean_w02_kind_regularities_form_bounded_kind_schema_candidate() -> None:
    result = _run_from_w02(
        "kind-clean",
        traces=(
            w02_trace(trace_id="k1", sequence_index=1, source_authority="trusted_world_provider", candidate_type=W02RegularityCandidateType.KIND),
            w02_trace(trace_id="k2", sequence_index=2, source_authority="trusted_world_provider", candidate_type=W02RegularityCandidateType.KIND),
        ),
    )
    candidate = _first_candidate(result)
    assert candidate.schema_channel is W03SchemaChannel.KIND_PRIOR
    assert candidate.status in {W03SchemaStatus.NARROW_PRIOR, W03SchemaStatus.BOUNDED_PRIOR}


def test_contested_w02_regularities_do_not_become_clean_everyday_prior() -> None:
    result = _run_from_w02(
        "contested",
        traces=(
            w02_trace(trace_id="c1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="c2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    assert len(result.everyday_priors) == 0
    assert result.gate.consumer_ready is False


def test_scaffold_only_or_low_maturity_regularities_are_blocked_or_narrow() -> None:
    result = _run_from_w02(
        "scaffold-only",
        traces=(
            w02_trace(trace_id="s1", sequence_index=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="s2", sequence_index=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="s3", sequence_index=3, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        ),
    )
    candidate = _first_candidate(result)
    assert candidate.status in {W03SchemaStatus.DEFERRED, W03SchemaStatus.BLOCKED, W03SchemaStatus.CONTESTED}
    packet = result.downstream_permission_packets[0]
    assert packet.may_use_as_bounded_prior is False
    assert packet.may_use_as_operational_default is False
    assert "clean_everyday_prior_without_clean_w02_support" in packet.prohibited_claims


def test_support_set_integrity_requires_regularities_negative_refs_authority_context() -> None:
    result = _run_from_w02(
        "support-integrity",
        traces=(
            w02_trace(trace_id="i1", sequence_index=1),
            w02_trace(trace_id="i2", sequence_index=2),
        ),
    )
    candidate = _first_candidate(result)
    assert candidate.support_regularities
    assert isinstance(candidate.negative_evidence_refs, tuple)
    assert candidate.source_authority_scope
    assert candidate.context_scope


def test_instance_kind_role_channels_do_not_collapse() -> None:
    instance = _run_from_w02(
        "channel-instance",
        traces=(
            w02_trace(trace_id="i1", sequence_index=1, candidate_type=W02RegularityCandidateType.INSTANCE),
            w02_trace(trace_id="i2", sequence_index=2, candidate_type=W02RegularityCandidateType.INSTANCE),
        ),
    )
    kind = _run_from_w02(
        "channel-kind",
        traces=(
            w02_trace(trace_id="k1", sequence_index=1, candidate_type=W02RegularityCandidateType.KIND),
            w02_trace(trace_id="k2", sequence_index=2, candidate_type=W02RegularityCandidateType.KIND),
        ),
    )
    role = _run_from_w02(
        "channel-role",
        traces=(
            w02_trace(trace_id="r1", sequence_index=1, candidate_type=W02RegularityCandidateType.SCENE_ROLE),
            w02_trace(trace_id="r2", sequence_index=2, candidate_type=W02RegularityCandidateType.SCENE_ROLE),
        ),
    )
    assert _first_candidate(instance).schema_channel is W03SchemaChannel.INSTANCE_PRIOR
    assert _first_candidate(kind).schema_channel is W03SchemaChannel.KIND_PRIOR
    assert _first_candidate(role).schema_channel is W03SchemaChannel.SCENE_ROLE_PRIOR


def test_affordance_prior_requires_affordance_channel_support() -> None:
    blocked = _run_from_w02(
        "aff-block",
        traces=(
            w02_trace(trace_id="a1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
            w02_trace(trace_id="a2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref=None, effect_ref=None),
        ),
    )
    allowed = _run_from_w02(
        "aff-ok",
        traces=(
            w02_trace(trace_id="a1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref="a1", effect_ref="e1"),
            w02_trace(trace_id="a2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, action_ref="a2", effect_ref="e2"),
        ),
    )
    assert _first_candidate(blocked).status in {
        W03SchemaStatus.BLOCKED,
        W03SchemaStatus.CONTESTED,
        W03SchemaStatus.QUARANTINED,
    }
    assert _first_candidate(allowed).schema_channel is W03SchemaChannel.AFFORDANCE_PRIOR


def test_scene_role_prior_does_not_become_kind_prior() -> None:
    result = _run_from_w02(
        "role-kind",
        traces=(
            w02_trace(trace_id="r1", sequence_index=1, candidate_type=W02RegularityCandidateType.SCENE_ROLE),
            w02_trace(trace_id="r2", sequence_index=2, candidate_type=W02RegularityCandidateType.SCENE_ROLE),
        ),
    )
    assert _first_candidate(result).schema_channel is W03SchemaChannel.SCENE_ROLE_PRIOR


def test_narrow_authority_scope_blocks_global_generalization() -> None:
    result = _run_from_w02(
        "authority-narrow",
        traces=(
            w02_trace(trace_id="n1", sequence_index=1, source_authority="trusted_world_provider"),
            w02_trace(trace_id="n2", sequence_index=2, source_authority="trusted_world_provider"),
        ),
    )
    prior = result.everyday_priors[0]
    assert "global_truth_claim" in prior.blocked_use_cases


def test_revoked_authority_triggers_must_revalidate_or_block() -> None:
    result = _run_from_w02(
        "authority-revoked",
        traces=(
            w02_trace(trace_id="v1", sequence_index=1, source_authority="revoked_source"),
            w02_trace(trace_id="v2", sequence_index=2, source_authority="revoked_source"),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert packet.must_revalidate_before_use or packet.must_abstain


def test_context_transfer_requires_explicit_gate() -> None:
    result = _run_from_w02(
        "ctx-gate",
        traces=(
            w02_trace(trace_id="c1", sequence_index=1),
            w02_trace(trace_id="c2", sequence_index=2),
        ),
    )
    prior = result.everyday_priors[0]
    assert "override_by_live_w01_w02" in _first_candidate(result).applicability_conditions
    assert "live_w01_w02_evidence_overrides_w03_prior" in prior.override_conditions


def test_failed_context_transfer_narrows_or_blocks_prior() -> None:
    result = _run_from_w02(
        "ctx-fail",
        traces=(
            w02_trace(trace_id="f1", sequence_index=1, presence_mode=W02PresenceMode.PARTIAL),
            w02_trace(trace_id="f2", sequence_index=2, presence_mode=W02PresenceMode.PARTIAL),
        ),
    )
    assert _first_candidate(result).status in {W03SchemaStatus.DEFERRED, W03SchemaStatus.BLOCKED, W03SchemaStatus.CONTESTED}


def test_contradiction_invalidates_or_downgrades_permissions() -> None:
    result = _run_from_w02(
        "contra-perm",
        traces=(
            w02_trace(trace_id="p1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="p2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert packet.must_abstain is True
    assert packet.may_use_as_bounded_prior is False
    assert packet.may_use_as_operational_default is False


def test_unresolved_contradiction_is_not_decorative() -> None:
    result = _run_from_w02(
        "contra-not-decorative",
        traces=(
            w02_trace(trace_id="d1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="d2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    assert result.contradiction_consequences
    assert result.gate.contradiction_count > 0
    assert result.downstream_permission_packets[0].must_preserve_contradiction is True


def test_contradictory_affordance_worlds_split_or_quarantine() -> None:
    result = _run_from_w02(
        "aff-split",
        traces=(
            w02_trace(trace_id="a1", sequence_index=1, candidate_type=W02RegularityCandidateType.AFFORDANCE, contradiction_markers=("replacement",)),
            w02_trace(trace_id="a2", sequence_index=2, candidate_type=W02RegularityCandidateType.AFFORDANCE, contradiction_markers=("replacement",)),
        ),
    )
    assert _first_candidate(result).status in {W03SchemaStatus.CONTESTED, W03SchemaStatus.QUARANTINED}
    assert any(
        item.consequence_route is W03ContradictionConsequenceRoute.SPLIT
        for item in result.contradiction_consequences
    )
    assert result.split_or_merge_proposals
    packet = result.downstream_permission_packets[0]
    assert packet.may_use_as_operational_default is False
    assert packet.must_preserve_contradiction is True


def test_stale_schema_detection_from_context_drift() -> None:
    result = _run_from_w02(
        "stale-drift",
        traces=(
            w02_trace(trace_id="s1", sequence_index=1),
            w02_trace(trace_id="s2", sequence_index=1),
        ),
    )
    assert result.stale_assessments[0].revalidation_required is True


def test_missing_expected_trace_triggers_revalidation() -> None:
    result = _run_from_w02(
        "missing-expected",
        traces=(
            w02_trace(trace_id="m1", sequence_index=1),
            w02_trace(trace_id="m2", sequence_index=1),
        ),
    )
    assert "temporal_spread_revalidation" in result.stale_assessments[0].missing_expected_evidence


def test_schema_version_record_emitted_on_update() -> None:
    result = _run_from_w02(
        "version-update",
        traces=(
            w02_trace(trace_id="u1", sequence_index=1),
            w02_trace(trace_id="u2", sequence_index=2),
        ),
    )
    assert result.version_records
    assert result.version_records[0].new_version >= 1


def test_schema_version_record_emitted_on_downgrade() -> None:
    result = _run_from_w02(
        "version-downgrade",
        traces=(
            w02_trace(trace_id="d1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="d2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    assert any(item.update_trigger.value == "contradiction_downgrade" for item in result.version_records)


def test_identity_swap_or_duplicate_lineage_blocks_clean_schema_continuity() -> None:
    result = _run_from_w02(
        "identity-swap",
        traces=(
            w02_trace(trace_id="i1", sequence_index=1, contradiction_markers=("identity_swap",)),
            w02_trace(trace_id="i2", sequence_index=2, contradiction_markers=("identity_swap",)),
        ),
    )
    assert _first_candidate(result).status in {W03SchemaStatus.CONTESTED, W03SchemaStatus.QUARANTINED}


def test_language_prior_without_w02_support_is_rejected() -> None:
    result = build_w03_harness_case(W03HarnessCase(case_id="lang-prior", w03_input=None)).w03_result
    assert result.gate.no_clean_schema is True


def test_downstream_permission_packet_has_exact_permission_boundaries() -> None:
    result = _run_from_w02(
        "perm-boundary",
        traces=(
            w02_trace(trace_id="p1", sequence_index=1),
            w02_trace(trace_id="p2", sequence_index=2),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert packet.prohibited_claims
    assert packet.may_use_as_operational_default is False
    assert packet.may_use_as_bounded_prior is False
    assert packet.may_use_as_schema_hint is True


def test_operational_default_requires_clean_nonstale_authority_scoped_prior() -> None:
    result = _run_from_w02(
        "operational-default",
        traces=(
            w02_trace(trace_id="o1", sequence_index=1, source_authority="trusted_world_provider", confidence_band="high"),
            w02_trace(trace_id="o2", sequence_index=3, source_authority="weak_scaffold_provider", confidence_band="high"),
            w02_trace(trace_id="o3", sequence_index=5, source_authority="trusted_world_provider", confidence_band="high"),
        ),
    )
    assert any(item.operational_default_status is True for item in result.everyday_priors)


def test_live_w01_w02_override_condition_is_preserved() -> None:
    result = _run_from_w02(
        "override-condition",
        traces=(
            w02_trace(trace_id="x1", sequence_index=1),
            w02_trace(trace_id="x2", sequence_index=2),
        ),
    )
    prior = result.everyday_priors[0]
    assert "live_w01_w02_evidence_overrides_w03_prior" in prior.override_conditions


def test_ablation_removing_support_provenance_changes_outcome() -> None:
    full = _run_from_w02(
        "ablation-full",
        traces=(
            w02_trace(trace_id="f1", sequence_index=1, source_authority="trusted_world_provider", confidence_band="high", provenance_ref=("a",)),
            w02_trace(trace_id="f2", sequence_index=3, source_authority="weak_scaffold_provider", confidence_band="high", provenance_ref=("b",)),
            w02_trace(trace_id="f3", sequence_index=5, source_authority="trusted_world_provider", confidence_band="high", provenance_ref=("c",)),
        ),
    )
    ablated = _run_from_w02(
        "ablation-empty",
        traces=(
            w02_trace(trace_id="a1", sequence_index=1, source_authority="", confidence_band="high", provenance_ref=()),
            w02_trace(trace_id="a2", sequence_index=3, source_authority="", confidence_band="high", provenance_ref=()),
            w02_trace(trace_id="a3", sequence_index=5, source_authority="", confidence_band="high", provenance_ref=()),
        ),
    )
    full_candidate = _first_candidate(full)
    ablated_candidate = _first_candidate(ablated)
    full_packet = full.downstream_permission_packets[0]
    ablated_packet = ablated.downstream_permission_packets[0]
    assert full_candidate.provenance != ablated_candidate.provenance
    assert full_candidate.status != ablated_candidate.status
    assert full_packet.may_use_as_bounded_prior is True
    assert ablated_packet.may_use_as_bounded_prior is False
    assert full_packet.must_revalidate_before_use is False
    assert ablated_packet.must_revalidate_before_use is True


def test_ablation_removing_contradiction_policy_changes_outcome() -> None:
    clean = _run_from_w02(
        "ablation-clean",
        traces=(
            w02_trace(trace_id="c1", sequence_index=1),
            w02_trace(trace_id="c2", sequence_index=2),
        ),
    )
    conflict = _run_from_w02(
        "ablation-conflict",
        traces=(
            w02_trace(trace_id="c1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="c2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    assert clean.gate.contradiction_count != conflict.gate.contradiction_count


def test_deferred_or_scaffold_regularities_do_not_emit_bounded_prior_permission() -> None:
    result = _run_from_w02(
        "deferred-scaffold-permission",
        traces=(
            w02_trace(trace_id="s1", sequence_index=1, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="s2", sequence_index=2, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
            w02_trace(trace_id="s3", sequence_index=3, presence_mode=W02PresenceMode.SCAFFOLD_ONLY),
        ),
    )
    candidate = _first_candidate(result)
    packet = result.downstream_permission_packets[0]
    assert candidate.status in {
        W03SchemaStatus.DEFERRED,
        W03SchemaStatus.BLOCKED,
        W03SchemaStatus.CONTESTED,
        W03SchemaStatus.QUARANTINED,
        W03SchemaStatus.MUST_REVALIDATE,
    }
    assert packet.may_use_as_bounded_prior is False
    assert packet.may_use_as_operational_default is False
    assert packet.must_revalidate_before_use or packet.must_abstain
    assert "clean_everyday_prior_without_clean_w02_support" in packet.prohibited_claims


def test_stale_schema_requires_revalidation_and_blocks_bounded_prior_use() -> None:
    result = _run_from_w02(
        "stale-bounded-block",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=1),
        ),
    )
    stale = result.stale_assessments[0]
    packet = result.downstream_permission_packets[0]
    assert stale.revalidation_required is True
    assert packet.must_revalidate_before_use is True
    assert packet.may_use_as_operational_default is False
    assert packet.may_use_as_bounded_prior is False


def test_contested_w02_regularities_block_clean_bounded_prior_permission() -> None:
    result = _run_from_w02(
        "contested-bounded-block",
        traces=(
            w02_trace(trace_id="c1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="c2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert result.contradiction_consequences
    assert packet.may_use_as_bounded_prior is False
    assert packet.may_use_as_operational_default is False
    assert packet.must_preserve_contradiction is True
    assert packet.must_abstain or packet.must_revalidate_before_use


def test_authority_or_provenance_ablation_changes_schema_permission_not_only_metadata() -> None:
    clean = _run_from_w02(
        "authority-clean",
        traces=(
            w02_trace(trace_id="a1", sequence_index=1, source_authority="trusted_world_provider", confidence_band="high", provenance_ref=("p1",)),
            w02_trace(trace_id="a2", sequence_index=3, source_authority="weak_scaffold_provider", confidence_band="high", provenance_ref=("p2",)),
            w02_trace(trace_id="a3", sequence_index=5, source_authority="trusted_world_provider", confidence_band="high", provenance_ref=("p3",)),
        ),
    )
    ablated = _run_from_w02(
        "authority-ablated",
        traces=(
            w02_trace(trace_id="a1", sequence_index=1, source_authority="", confidence_band="high", provenance_ref=()),
            w02_trace(trace_id="a2", sequence_index=3, source_authority="", confidence_band="high", provenance_ref=()),
            w02_trace(trace_id="a3", sequence_index=5, source_authority="", confidence_band="high", provenance_ref=()),
        ),
    )
    clean_packet = clean.downstream_permission_packets[0]
    ablated_packet = ablated.downstream_permission_packets[0]
    assert clean_packet.may_use_as_bounded_prior is True
    assert ablated_packet.may_use_as_bounded_prior is False
    assert clean_packet.must_revalidate_before_use is False
    assert ablated_packet.must_revalidate_before_use is True
    assert _first_candidate(clean).status != _first_candidate(ablated).status


def test_contradiction_route_downgrades_or_invalidates_permission_distinctly() -> None:
    result = _run_from_w02(
        "route-block",
        traces=(
            w02_trace(trace_id="r1", sequence_index=1, presence_mode=W02PresenceMode.PRESENT),
            w02_trace(trace_id="r2", sequence_index=2, presence_mode=W02PresenceMode.ABSENT),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert any(
        item.consequence_route is W03ContradictionConsequenceRoute.BLOCK_DOWNSTREAM_USE
        for item in result.contradiction_consequences
    )
    assert packet.may_use_as_bounded_prior is False
    assert packet.may_use_as_operational_default is False
    assert packet.must_preserve_contradiction is True


def test_contradictory_affordance_or_identity_worlds_split_or_quarantine_schema() -> None:
    result = _run_from_w02(
        "route-split",
        traces=(
            w02_trace(trace_id="x1", sequence_index=1, contradiction_markers=("replacement",)),
            w02_trace(trace_id="x2", sequence_index=2, contradiction_markers=("replacement",)),
        ),
    )
    packet = result.downstream_permission_packets[0]
    assert any(
        item.consequence_route is W03ContradictionConsequenceRoute.SPLIT
        for item in result.contradiction_consequences
    )
    assert result.split_or_merge_proposals
    assert packet.may_use_as_operational_default is False
    assert packet.must_abstain is True


def test_telemetry_reconstructs_consolidation_path() -> None:
    result = _run_from_w02(
        "telemetry-path",
        traces=(
            w02_trace(trace_id="t1", sequence_index=1),
            w02_trace(trace_id="t2", sequence_index=2),
        ),
    )
    telemetry = result.telemetry
    assert telemetry.regularity_intake_count >= 1
    assert telemetry.schema_candidate_count >= 1
    assert telemetry.version_update_count >= 1
