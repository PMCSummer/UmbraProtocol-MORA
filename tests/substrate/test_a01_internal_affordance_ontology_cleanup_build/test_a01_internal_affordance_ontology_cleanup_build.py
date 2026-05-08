from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
    A01RawAffordanceCandidateSet,
    A01ValidityStatus,
    derive_a01_ontology_contract_view,
)
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    A01HarnessCase,
    a01_candidate,
    a01_candidate_set,
    build_a01_harness_case,
)


def _run(case: A01HarnessCase):
    return build_a01_harness_case(case).a01_result


def _string_dedup_baseline(labels: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip().lower() for item in labels))


def _manual_whitelist_baseline(candidates: tuple) -> tuple:
    whitelist = {"safety_recheck", "pause_and_recover", "resource_hold"}
    return tuple(item for item in candidates if item.local_label in whitelist)


def test_true_alias_collapse_merges_duplicates_into_single_canonical_with_alias_linkage() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="pause_and_recover",
            affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
            aliases=("recover_pause",),
            provenance="test.alias.c1",
            preconditions=("energy_low",),
            primary_outcomes=("reduce_overload",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.8,
            observation_signals=("calmer_state",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="pause_and_recover",
            affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
            aliases=("pause_recovery",),
            provenance="test.alias.c2",
            preconditions=("energy_low",),
            primary_outcomes=("reduce_overload",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.8,
            observation_signals=("calmer_state",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="alias-collapse",
            raw_candidate_set=a01_candidate_set(
                set_id="set:alias-collapse",
                candidates=candidates,
                reason="alias collapse",
            ),
        )
    )
    assert result.telemetry.canonical_entry_count == 1
    assert result.telemetry.merged_alias_group_count == 1
    assert len(result.ontology_snapshot.ledger.alias_records) == 1


def test_same_label_different_preconditions_is_contested_not_merged() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="safety_recheck",
            affordance_class=A01AffordanceClass.SENSING_MONITORING,
            aliases=(),
            provenance="test.precondition.c1",
            preconditions=("world_signal_present",),
            primary_outcomes=("safety_verification",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
            controllability_confidence=0.7,
            observation_signals=("verified_signal",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="safety_recheck",
            affordance_class=A01AffordanceClass.SENSING_MONITORING,
            aliases=(),
            provenance="test.precondition.c2",
            preconditions=("internal_alarm",),
            primary_outcomes=("safety_verification",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.7,
            observation_signals=("alarm_settled",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="same-label-precondition",
            raw_candidate_set=a01_candidate_set(
                set_id="set:same-label-precondition",
                candidates=candidates,
                reason="precondition split",
            ),
        )
    )
    assert result.telemetry.same_label_diff_precondition_count == 1
    assert result.telemetry.split_decision_count == 1
    assert result.telemetry.contested_entry_count == 1
    assert result.telemetry.canonical_entry_count == 2


def test_same_outcome_different_controllability_stays_distinct() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="boundary_hold",
            affordance_class=A01AffordanceClass.INHIBITION_SUPPRESSION,
            aliases=(),
            provenance="test.control.c1",
            preconditions=("pressure_rising",),
            primary_outcomes=("reduce_contact",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.78,
            observation_signals=("contact_reduced",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="boundary_hold",
            affordance_class=A01AffordanceClass.INHIBITION_SUPPRESSION,
            aliases=(),
            provenance="test.control.c2",
            preconditions=("pressure_rising",),
            primary_outcomes=("reduce_contact",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
            controllability_confidence=0.45,
            observation_signals=("contact_reduced",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="same-outcome-diff-control",
            raw_candidate_set=a01_candidate_set(
                set_id="set:same-outcome-diff-control",
                candidates=candidates,
                reason="control split",
            ),
        )
    )
    assert result.telemetry.split_decision_count == 1
    assert result.telemetry.canonical_entry_count == 2


def test_coarse_vs_fine_granularity_preserves_parent_child_relation() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="repair_sequence",
            affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
            aliases=(),
            provenance="test.granularity.c1",
            preconditions=("rupture_detected",),
            primary_outcomes=("repair_progress",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.8,
            observation_signals=("repair_open",),
            observation_verification_required=True,
            granularity_level=1,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="repair_sequence",
            affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
            aliases=(),
            provenance="test.granularity.c2",
            preconditions=("rupture_detected",),
            primary_outcomes=("repair_progress",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.8,
            observation_signals=("clarify_then_repair",),
            observation_verification_required=True,
            granularity_level=3,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="coarse-fine",
            raw_candidate_set=a01_candidate_set(
                set_id="set:coarse-fine",
                candidates=candidates,
                reason="granularity relation",
            ),
        )
    )
    assert result.telemetry.parent_child_relation_count == 1
    assert len(result.ontology_snapshot.ledger.granularity_conflicts) == 1


def test_class_boundary_separation_avoids_generic_action_collapse() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c-sense",
            local_label="sense_load",
            affordance_class=A01AffordanceClass.SENSING_MONITORING,
            aliases=(),
            provenance="test.class.sense",
            preconditions=("signal_present",),
            primary_outcomes=("detect_load",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.OBSERVATIONAL,
            controllability_confidence=0.7,
            observation_signals=("load_detected",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c-reg",
            local_label="adjust_load",
            affordance_class=A01AffordanceClass.REGULATION_ADJUSTMENT,
            aliases=(),
            provenance="test.class.reg",
            preconditions=("load_detected",),
            primary_outcomes=("load_reduced",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.8,
            observation_signals=("load_reduced",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c-mode",
            local_label="shift_mode",
            affordance_class=A01AffordanceClass.INTERNAL_MODE_SHIFT,
            aliases=(),
            provenance="test.class.mode",
            preconditions=("high_pressure",),
            primary_outcomes=("mode_shifted",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.7,
            observation_signals=("mode_shifted",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c-world",
            local_label="world_action",
            affordance_class=A01AffordanceClass.WORLD_DIRECTED_ACTION,
            aliases=(),
            provenance="test.class.world",
            preconditions=("world_ready",),
            primary_outcomes=("world_changed",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
            controllability_confidence=0.5,
            observation_signals=("world_changed",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="class-boundary",
            raw_candidate_set=a01_candidate_set(
                set_id="set:class-boundary",
                candidates=candidates,
                reason="class separation",
            ),
        )
    )
    classes = {item.affordance_class for item in result.ontology_snapshot.canonical_entries}
    assert A01AffordanceClass.SENSING_MONITORING in classes
    assert A01AffordanceClass.REGULATION_ADJUSTMENT in classes
    assert A01AffordanceClass.INTERNAL_MODE_SHIFT in classes
    assert A01AffordanceClass.WORLD_DIRECTED_ACTION in classes


def test_context_invalidation_disabled_effector_deprecates_or_unavailable() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="send_update",
            affordance_class=A01AffordanceClass.COMMUNICATION_OUTPUT,
            aliases=(),
            provenance="test.invalidate.c1",
            preconditions=("disabled_effector", "invalid_assumption"),
            primary_outcomes=("update_sent",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
            controllability_confidence=0.4,
            observation_signals=("sent",),
            observation_verification_required=True,
            effector_enabled=False,
            assumption_valid=False,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="invalidated",
            raw_candidate_set=a01_candidate_set(
                set_id="set:invalidated",
                candidates=candidates,
                reason="invalidated assumption",
            ),
        )
    )
    status = result.ontology_snapshot.canonical_entries[0].validity_status
    assert status == A01ValidityStatus.UNAVAILABLE


def test_string_dedup_baseline_materially_fails_where_a01_keeps_conflict_structure() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="same_label",
            affordance_class=A01AffordanceClass.SENSING_MONITORING,
            aliases=(),
            provenance="test.dedup.c1",
            preconditions=("world_signal",),
            primary_outcomes=("observe",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.OBSERVATIONAL,
            controllability_confidence=0.7,
            observation_signals=("observed",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="same_label",
            affordance_class=A01AffordanceClass.SENSING_MONITORING,
            aliases=(),
            provenance="test.dedup.c2",
            preconditions=("internal_signal",),
            primary_outcomes=("observe",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.7,
            observation_signals=("observed",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="string-dedup-fail",
            raw_candidate_set=a01_candidate_set(
                set_id="set:string-dedup-fail",
                candidates=candidates,
                reason="string dedup baseline failure",
            ),
        )
    )
    baseline = _string_dedup_baseline(tuple(item.local_label for item in candidates))
    assert len(baseline) == 1
    assert result.telemetry.canonical_entry_count == 2
    assert result.telemetry.same_label_diff_precondition_count == 1


def test_manual_whitelist_baseline_fails_to_preserve_contested_cases() -> None:
    contested = (
        a01_candidate(
            candidate_id="c1",
            local_label="unsafe_mode_shift",
            affordance_class=A01AffordanceClass.INTERNAL_MODE_SHIFT,
            aliases=(),
            provenance="test.whitelist.c1",
            preconditions=("high_pressure",),
            primary_outcomes=("mode_shift",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.6,
            observation_signals=("mode_shift",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="unsafe_mode_shift",
            affordance_class=A01AffordanceClass.WORLD_DIRECTED_ACTION,
            aliases=(),
            provenance="test.whitelist.c2",
            preconditions=("high_pressure",),
            primary_outcomes=("mode_shift",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
            controllability_confidence=0.4,
            observation_signals=("mode_shift",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="whitelist-fail",
            raw_candidate_set=a01_candidate_set(
                set_id="set:whitelist-fail",
                candidates=contested,
                reason="manual whitelist failure",
            ),
        )
    )
    baseline = _manual_whitelist_baseline(contested)
    assert len(baseline) == 0
    assert result.telemetry.contested_entry_count == 1
    assert result.telemetry.class_conflict_count == 1


def test_mixed_source_control_overreach_is_restrained_under_contamination() -> None:
    candidates = (
        a01_candidate(
            candidate_id="c1",
            local_label="force_self_control",
            affordance_class=A01AffordanceClass.REGULATION_ADJUSTMENT,
            aliases=(),
            provenance="test.overreach.c1",
            preconditions=("pressure_high",),
            primary_outcomes=("rapid_control",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
            controllability_confidence=0.9,
            observation_signals=("control_report",),
            observation_verification_required=True,
            ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="overreach-restraint",
            raw_candidate_set=a01_candidate_set(
                set_id="set:overreach-restraint",
                candidates=candidates,
                reason="mixed-source overreach restraint",
            ),
            s05_contaminated_case=True,
            s04_no_stable_core_case=True,
        )
    )
    status = result.ontology_snapshot.canonical_entries[0].validity_status
    assert status == A01ValidityStatus.CONTESTED


def test_no_silent_deletion_of_messy_candidates() -> None:
    messy = (
        a01_candidate(
            candidate_id="c1",
            local_label="messy_aff",
            affordance_class=A01AffordanceClass.SENSING_MONITORING,
            aliases=(),
            provenance="test.messy.c1",
            preconditions=("p1",),
            primary_outcomes=("o1",),
            target_channels=("internal",),
            controllability_class=A01ControllabilityClass.OBSERVATIONAL,
            controllability_confidence=0.6,
            observation_signals=("s1",),
            observation_verification_required=True,
        ),
        a01_candidate(
            candidate_id="c2",
            local_label="messy_aff",
            affordance_class=A01AffordanceClass.WORLD_DIRECTED_ACTION,
            aliases=(),
            provenance="test.messy.c2",
            preconditions=("p1",),
            primary_outcomes=("o1",),
            target_channels=("world",),
            controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
            controllability_confidence=0.4,
            observation_signals=("s1",),
            observation_verification_required=True,
        ),
    )
    result = _run(
        A01HarnessCase(
            case_id="no-silent-deletion",
            raw_candidate_set=a01_candidate_set(
                set_id="set:no-silent-deletion",
                candidates=messy,
                reason="messy should be preserved",
            ),
        )
    )
    assert result.telemetry.contested_entry_count == 1
    assert result.telemetry.canonical_entry_count == 2


def test_source_lineage_is_threaded_and_partial_lineage_is_explicit() -> None:
    candidate = a01_candidate(
        candidate_id="lineage-c1",
        local_label="pause_and_recover",
        affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
        aliases=(),
        provenance="test.lineage.c1",
        preconditions=("energy_low",),
        primary_outcomes=("reduce_overload",),
        target_channels=("internal",),
        controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
        controllability_confidence=0.8,
        observation_signals=("calmer_state",),
        observation_verification_required=True,
        canonical_id_hint="a01:test:pause_and_recover",
    )
    partial_lineage_set = A01RawAffordanceCandidateSet(
        candidate_set_id="set:partial-lineage",
        candidates=(candidate,),
        source_lineage=(),
        reason="candidate lineage intentionally omitted",
    )
    result = _run(
        A01HarnessCase(
            case_id="partial-lineage",
            raw_candidate_set=partial_lineage_set,
        )
    )
    view = derive_a01_ontology_contract_view(result)
    assert result.ontology_snapshot.ledger.source_lineage_count >= 1
    assert result.ontology_snapshot.ledger.source_lineage_complete is False
    assert "a01_source_lineage_partial" in set(result.gate.restrictions)
    assert result.telemetry.source_lineage_complete is False
    assert view.source_lineage_complete is False


def test_canonical_id_coverage_is_explicit_for_hint_backed_vs_generated_entries() -> None:
    hinted = _run(
        A01HarnessCase(
            case_id="canonical-id-hinted",
            raw_candidate_set=a01_candidate_set(
                set_id="set:canonical-id-hinted",
                reason="hinted ids",
                candidates=(
                    a01_candidate(
                        candidate_id="hinted-c1",
                        local_label="pause_and_recover",
                        affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                        aliases=(),
                        provenance="test.canonical.hinted.c1",
                        preconditions=("energy_low",),
                        primary_outcomes=("reduce_overload",),
                        target_channels=("internal",),
                        controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                        controllability_confidence=0.8,
                        observation_signals=("calmer_state",),
                        observation_verification_required=True,
                        canonical_id_hint="a01:test:pause_and_recover",
                    ),
                ),
            ),
        )
    )
    generated = _run(
        A01HarnessCase(
            case_id="canonical-id-generated",
            raw_candidate_set=a01_candidate_set(
                set_id="set:canonical-id-generated",
                reason="generated ids",
                candidates=(
                    a01_candidate(
                        candidate_id="generated-c1",
                        local_label="pause_and_recover",
                        affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                        aliases=(),
                        provenance="test.canonical.generated.c1",
                        preconditions=("energy_low",),
                        primary_outcomes=("reduce_overload",),
                        target_channels=("internal",),
                        controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                        controllability_confidence=0.8,
                        observation_signals=("calmer_state",),
                        observation_verification_required=True,
                        canonical_id_hint=None,
                    ),
                ),
            ),
        )
    )
    assert hinted.telemetry.canonical_id_hint_used_count == 1
    assert hinted.telemetry.canonical_id_generated_count == 0
    assert hinted.telemetry.canonical_id_coverage_complete is True
    assert generated.telemetry.canonical_id_hint_used_count == 0
    assert generated.telemetry.canonical_id_generated_count == 1
    assert generated.telemetry.canonical_id_coverage_complete is False
