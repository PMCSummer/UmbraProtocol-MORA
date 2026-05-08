from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
)
from substrate.a02_capability_gap_detection import (
    A02ControllabilityStatus,
    A02CoverageStatus,
    A02DemandClass,
    A02DemandLegitimacyStatus,
    A02GapKind,
    derive_a02_capability_gap_contract_view,
)
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    A01HarnessCase,
    a01_candidate,
    a01_candidate_set,
    build_a01_harness_case,
)
from tests.substrate.a02_capability_gap_detection_testkit import (
    A02HarnessCase,
    a02_demand,
    a02_demand_set,
    build_a02_harness_case,
)


def _a01_result(case_id: str, candidates: tuple) -> object:
    return build_a01_harness_case(
        A01HarnessCase(
            case_id=f"{case_id}:a01",
            raw_candidate_set=a01_candidate_set(
                set_id=f"{case_id}:a01:set",
                reason=f"{case_id}:seed",
                candidates=candidates,
            ),
        )
    ).a01_result


def test_fully_covered_vs_missing_primitive_is_strictly_distinct() -> None:
    covered_seed = _a01_result(
        "a02-covered",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.covered",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.9,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:pause_and_recover",
            ),
        ),
    )
    missing_seed = _a01_result(
        "a02-missing",
        (
            a01_candidate(
                candidate_id="m1",
                local_label="observe_noise",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a02.missing",
                preconditions=("signal_present",),
                primary_outcomes=("observe_only",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.OBSERVATIONAL,
                controllability_confidence=0.6,
                observation_signals=("observed",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:observe_noise",
            ),
        ),
    )
    demand = a02_demand(
        demand_id="d1",
        demanded_change_class=A02DemandClass.SELF_REPAIR,
        demanded_scope=("reduce_overload",),
        target_channels=("internal",),
    )
    covered = build_a02_harness_case(
        A02HarnessCase(
            case_id="covered",
            a01_result=covered_seed,
            demand_set=a02_demand_set(set_id="covered:set", demands=(demand,), reason="covered"),
        )
    ).a02_result
    missing = build_a02_harness_case(
        A02HarnessCase(
            case_id="missing",
            a01_result=missing_seed,
            demand_set=a02_demand_set(set_id="missing:set", demands=(demand,), reason="missing"),
        )
    ).a02_result
    assert covered.gap_entries[0].coverage_status is A02CoverageStatus.FULLY_COVERED
    assert covered.gap_entries[0].gap_kind is A02GapKind.NO_GAP
    assert missing.gap_entries[0].coverage_status is A02CoverageStatus.NOT_COVERED
    assert missing.gap_entries[0].gap_kind is A02GapKind.MISSING_AFFORDANCE


def test_missing_vs_blocked_are_not_collapsed() -> None:
    blocked_seed = _a01_result(
        "a02-blocked",
        (
            a01_candidate(
                candidate_id="b1",
                local_label="send_update",
                affordance_class=A01AffordanceClass.COMMUNICATION_OUTPUT,
                aliases=(),
                provenance="tests.a02.blocked",
                preconditions=("disabled_effector",),
                primary_outcomes=("update_sent",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.4,
                observation_signals=("sent",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:send_update",
            ),
        ),
    )
    demand = a02_demand(
        demand_id="d-blocked",
        demanded_change_class=A02DemandClass.COMMUNICATION,
        demanded_scope=("update_sent",),
        target_channels=("world",),
        required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
    )
    blocked = build_a02_harness_case(
        A02HarnessCase(
            case_id="blocked",
            a01_result=blocked_seed,
            demand_set=a02_demand_set(set_id="blocked:set", demands=(demand,), reason="blocked"),
        )
    ).a02_result
    assert blocked.gap_entries[0].coverage_status is A02CoverageStatus.BLOCKED
    assert blocked.gap_entries[0].gap_kind is A02GapKind.PRECONDITION_UNSATISFIED_GAP


def test_partial_coverage_records_residual_scope_explicitly() -> None:
    seed = _a01_result(
        "a02-partial",
        (
            a01_candidate(
                candidate_id="p1",
                local_label="repair_step",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.partial",
                preconditions=("energy_low",),
                primary_outcomes=("stabilize",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("stable",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:repair_step",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="partial",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="partial:set",
                demands=(
                    a02_demand(
                        demand_id="d-partial",
                        demanded_change_class=A02DemandClass.SELF_REPAIR,
                        demanded_scope=("stabilize", "restore_homeostasis"),
                        target_channels=("internal",),
                    ),
                ),
                reason="partial coverage",
            ),
        )
    ).a02_result
    entry = result.gap_entries[0]
    assert entry.coverage_status is A02CoverageStatus.PARTIALLY_COVERED
    assert entry.partial_coverage is not None
    assert "restore_homeostasis" in set(entry.partial_coverage.residual_scope)


def test_composition_available_vs_blindness_ablation_changes_outcome() -> None:
    seed = _a01_result(
        "a02-compose",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="step1",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.compose1",
                preconditions=("ok",),
                primary_outcomes=("scope_a",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("a",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:step1",
            ),
            a01_candidate(
                candidate_id="c2",
                local_label="step2",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.compose2",
                preconditions=("ok",),
                primary_outcomes=("scope_b",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("b",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:step2",
            ),
        ),
    )
    demand = a02_demand(
        demand_id="d-compose",
        demanded_change_class=A02DemandClass.SELF_REPAIR,
        demanded_scope=("scope_a", "scope_b"),
        target_channels=("internal",),
    )
    composed = build_a02_harness_case(
        A02HarnessCase(
            case_id="compose-yes",
            a01_result=seed,
            demand_set=a02_demand_set(set_id="compose:set", demands=(demand,), reason="compose"),
            composition_enabled=True,
        )
    ).a02_result
    blind = build_a02_harness_case(
        A02HarnessCase(
            case_id="compose-no",
            a01_result=seed,
            demand_set=a02_demand_set(set_id="compose:set:no", demands=(demand,), reason="compose"),
            composition_enabled=False,
        )
    ).a02_result
    assert composed.gap_entries[0].gap_kind is A02GapKind.NO_GAP
    assert blind.gap_entries[0].gap_kind is A02GapKind.COMPOSITION_GAP


def test_ownership_boundary_gap_is_distinct_from_missing_internal_skill() -> None:
    seed = _a01_result(
        "a02-ownership",
        (
            a01_candidate(
                candidate_id="o1",
                local_label="internal_pause",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.ownership",
                preconditions=("ok",),
                primary_outcomes=("stabilize",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("stable",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:internal_pause",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="ownership",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="ownership:set",
                demands=(
                    a02_demand(
                        demand_id="d-own",
                        demanded_change_class=A02DemandClass.WORLD_FACING,
                        demanded_scope=("external_partner_compliance",),
                        target_channels=("world",),
                        required_controllability=A02ControllabilityStatus.OUTSIDE_CURRENT_CONTROL,
                        world_side_requirement="required",
                    ),
                ),
                reason="ownership boundary",
            ),
            ownership_boundary_basis=("s_minimal:world_dominant",),
        )
    ).a02_result
    entry = result.gap_entries[0]
    assert entry.gap_kind is A02GapKind.OWNERSHIP_BOUNDARY_GAP
    assert entry.coverage_status is A02CoverageStatus.BLOCKED


def test_demand_legitimacy_prevents_wish_to_missing_capability_promotion() -> None:
    seed = _a01_result(
        "a02-legitimacy",
        (
            a01_candidate(
                candidate_id="l1",
                local_label="repair_step",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.legitimacy",
                preconditions=("ok",),
                primary_outcomes=("stabilize",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("stable",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:repair_step",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="legitimacy",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="legitimacy:set",
                demands=(
                    a02_demand(
                        demand_id="d-legit",
                        demanded_change_class=A02DemandClass.SELF_REPAIR,
                        demanded_scope=(),
                        target_channels=("internal",),
                        legitimacy_status=A02DemandLegitimacyStatus.NARRATIVE_WISH_ONLY,
                    ),
                ),
                reason="wish only",
            ),
        )
    ).a02_result
    entry = result.gap_entries[0]
    assert entry.coverage_status is A02CoverageStatus.NO_CLEAN_COVERAGE_CLAIM
    assert entry.gap_kind is A02GapKind.UNKNOWN_CAPABILITY_STATUS


def test_planner_deadend_marker_does_not_force_missing_gap() -> None:
    seed = _a01_result(
        "a02-planner",
        (
            a01_candidate(
                candidate_id="pd1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.planner",
                preconditions=("ok",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.9,
                observation_signals=("stable",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:pause_and_recover",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="planner",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="planner:set",
                demands=(
                    a02_demand(
                        demand_id="d-plan",
                        demanded_change_class=A02DemandClass.SELF_REPAIR,
                        demanded_scope=("reduce_overload",),
                        target_channels=("internal",),
                        planner_deadend_signal=True,
                    ),
                ),
                reason="planner deadend marker present",
            ),
        )
    ).a02_result
    assert result.gap_entries[0].gap_kind is A02GapKind.NO_GAP


def test_low_confidence_or_planner_deadend_signal_cannot_create_missing_gap_when_ontology_covers_demand() -> None:
    seed = _a01_result(
        "a02-signal-contrast",
        (
            a01_candidate(
                candidate_id="s1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.signal",
                preconditions=("ok",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.9,
                observation_signals=("stable",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:pause_and_recover",
            ),
        ),
    )
    baseline_demand = a02_demand(
        demand_id="d-signal",
        demanded_change_class=A02DemandClass.SELF_REPAIR,
        demanded_scope=("reduce_overload",),
        target_channels=("internal",),
        planner_deadend_signal=False,
        low_confidence_signal=False,
    )
    signaled_demand = a02_demand(
        demand_id="d-signal",
        demanded_change_class=A02DemandClass.SELF_REPAIR,
        demanded_scope=("reduce_overload",),
        target_channels=("internal",),
        planner_deadend_signal=True,
        low_confidence_signal=True,
    )
    baseline = build_a02_harness_case(
        A02HarnessCase(
            case_id="signal-baseline",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="signal:baseline",
                demands=(baseline_demand,),
                reason="baseline signal-off",
            ),
        )
    ).a02_result
    signaled = build_a02_harness_case(
        A02HarnessCase(
            case_id="signal-signaled",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="signal:signaled",
                demands=(signaled_demand,),
                reason="signals on",
            ),
        )
    ).a02_result
    baseline_entry = baseline.gap_entries[0]
    signaled_entry = signaled.gap_entries[0]
    assert baseline_entry.coverage_status is A02CoverageStatus.FULLY_COVERED
    assert baseline_entry.gap_kind is A02GapKind.NO_GAP
    assert signaled_entry.coverage_status is A02CoverageStatus.FULLY_COVERED
    assert signaled_entry.gap_kind is A02GapKind.NO_GAP
    assert signaled_entry.gap_kind is not A02GapKind.MISSING_AFFORDANCE
    assert baseline.telemetry.missing_gap_count == 0
    assert signaled.telemetry.missing_gap_count == 0
    assert "planner_deadend_signal_non_authoritative" not in set(
        baseline_entry.coverage_evidence.basis_refs
    )
    assert "low_confidence_signal_non_authoritative" not in set(
        baseline_entry.coverage_evidence.basis_refs
    )
    assert "planner_deadend_signal_non_authoritative" in set(
        signaled_entry.coverage_evidence.basis_refs
    )
    assert "low_confidence_signal_non_authoritative" in set(
        signaled_entry.coverage_evidence.basis_refs
    )


def test_low_reliability_affordance_is_not_missing_primitive() -> None:
    seed = _a01_result(
        "a02-low-reliability",
        (
            a01_candidate(
                candidate_id="lr1",
                local_label="observe_signal",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a02.low_reliability",
                preconditions=("signal_present",),
                primary_outcomes=("observe_state",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.OBSERVATIONAL,
                controllability_confidence=0.35,
                observation_signals=("observed",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:observe_signal",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="low-reliability",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="low-reliability:set",
                demands=(
                    a02_demand(
                        demand_id="d-low-reliability",
                        demanded_change_class=A02DemandClass.INTERNAL_TOOL,
                        demanded_scope=("observe_state",),
                        target_channels=("internal",),
                    ),
                ),
                reason="low reliability branch",
            ),
        )
    ).a02_result
    entry = result.gap_entries[0]
    assert entry.coverage_status is A02CoverageStatus.CONTESTED
    assert entry.gap_kind is A02GapKind.LOW_RELIABILITY_AFFORDANCE
    assert entry.gap_kind is not A02GapKind.MISSING_AFFORDANCE
    assert result.telemetry.missing_gap_count == 0


def test_resource_blocked_gap_is_not_missing_primitive() -> None:
    seed = _a01_result(
        "a02-resource-blocked",
        (
            a01_candidate(
                candidate_id="rb1",
                local_label="execute_step",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance="tests.a02.resource_blocked",
                preconditions=("resource_limited",),
                primary_outcomes=("restore_homeostasis",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("restored",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:execute_step",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="resource-blocked",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="resource-blocked:set",
                demands=(
                    a02_demand(
                        demand_id="d-resource-blocked",
                        demanded_change_class=A02DemandClass.SELF_REPAIR,
                        demanded_scope=("restore_homeostasis",),
                        target_channels=("internal",),
                    ),
                ),
                reason="resource-limited branch",
            ),
        )
    ).a02_result
    entry = result.gap_entries[0]
    assert entry.coverage_status is A02CoverageStatus.BLOCKED
    assert entry.gap_kind is A02GapKind.RESOURCE_BLOCKED_GAP
    assert entry.gap_kind is not A02GapKind.MISSING_AFFORDANCE


def test_contested_coverage_status_is_real_and_no_clean_claim_is_downstream_visible() -> None:
    seed = _a01_result(
        "a02-contested",
        (
            a01_candidate(
                candidate_id="ct1",
                local_label="safety_recheck",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a02.contested.1",
                preconditions=("world_signal_present",),
                primary_outcomes=("safety_verification",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.7,
                observation_signals=("verified",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:safety_recheck.world",
            ),
            a01_candidate(
                candidate_id="ct2",
                local_label="safety_recheck",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a02.contested.2",
                preconditions=("internal_alarm",),
                primary_outcomes=("safety_verification",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.7,
                observation_signals=("verified",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:safety_recheck.internal",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="contested",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="contested:set",
                demands=(
                    a02_demand(
                        demand_id="d-contested",
                        demanded_change_class=A02DemandClass.INTERNAL_TOOL,
                        demanded_scope=("safety_verification",),
                        target_channels=("internal", "world"),
                    ),
                ),
                reason="contested coverage branch",
            ),
        )
    ).a02_result
    entry = result.gap_entries[0]
    view = derive_a02_capability_gap_contract_view(result)
    assert entry.coverage_status is A02CoverageStatus.CONTESTED
    assert entry.gap_kind is A02GapKind.UNKNOWN_CAPABILITY_STATUS
    assert entry.gap_kind is not A02GapKind.MISSING_AFFORDANCE
    assert result.telemetry.no_clean_coverage_count == 1
    assert view.no_clean_coverage_count == 1


def test_context_perturbation_shifts_from_blocked_to_covered() -> None:
    blocked_seed = _a01_result(
        "a02-perturb-blocked",
        (
            a01_candidate(
                candidate_id="pb1",
                local_label="send_update",
                affordance_class=A01AffordanceClass.COMMUNICATION_OUTPUT,
                aliases=(),
                provenance="tests.a02.perturb.blocked",
                preconditions=("disabled_effector",),
                primary_outcomes=("update_sent",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.4,
                observation_signals=("sent",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:send_update",
            ),
        ),
    )
    restored_seed = _a01_result(
        "a02-perturb-restored",
        (
            a01_candidate(
                candidate_id="pr1",
                local_label="send_update",
                affordance_class=A01AffordanceClass.COMMUNICATION_OUTPUT,
                aliases=(),
                provenance="tests.a02.perturb.restored",
                preconditions=("channel_open",),
                primary_outcomes=("update_sent",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.7,
                observation_signals=("sent",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:send_update",
            ),
        ),
    )
    demand = a02_demand(
        demand_id="d-perturb",
        demanded_change_class=A02DemandClass.COMMUNICATION,
        demanded_scope=("update_sent",),
        target_channels=("world",),
        required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
    )
    blocked = build_a02_harness_case(
        A02HarnessCase(
            case_id="perturb-blocked",
            a01_result=blocked_seed,
            demand_set=a02_demand_set(set_id="perturb:block", demands=(demand,), reason="blocked"),
        )
    ).a02_result
    restored = build_a02_harness_case(
        A02HarnessCase(
            case_id="perturb-restored",
            a01_result=restored_seed,
            demand_set=a02_demand_set(set_id="perturb:restored", demands=(demand,), reason="restored"),
        )
    ).a02_result
    assert blocked.gap_entries[0].coverage_status is A02CoverageStatus.BLOCKED
    assert restored.gap_entries[0].coverage_status is A02CoverageStatus.FULLY_COVERED


def test_no_affordance_invention_and_taxonomy_not_generic_cannot_do() -> None:
    seed = _a01_result(
        "a02-invention",
        (
            a01_candidate(
                candidate_id="i1",
                local_label="observe",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a02.invention",
                preconditions=("signal_present",),
                primary_outcomes=("observe_state",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.OBSERVATIONAL,
                controllability_confidence=0.6,
                observation_signals=("observed",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:observe",
            ),
        ),
    )
    result = build_a02_harness_case(
        A02HarnessCase(
            case_id="invention",
            a01_result=seed,
            demand_set=a02_demand_set(
                set_id="invention:set",
                demands=(
                    a02_demand(
                        demand_id="d1",
                        demanded_change_class=A02DemandClass.COMMUNICATION,
                        demanded_scope=("update_sent",),
                        target_channels=("world",),
                    ),
                    a02_demand(
                        demand_id="d2",
                        demanded_change_class=A02DemandClass.INTERNAL_TOOL,
                        demanded_scope=("observe_state", "stabilize"),
                        target_channels=("internal",),
                    ),
                ),
                reason="taxonomy check",
            ),
        )
    ).a02_result
    kinds = {entry.gap_kind for entry in result.gap_entries}
    assert A02GapKind.MISSING_AFFORDANCE in kinds
    assert A02GapKind.INSUFFICIENT_EFFECT_SCOPE in kinds
    assert result.ledger.no_affordance_invention_observed is True
    assert len(seed.ontology_snapshot.canonical_entries) == 1
    view = derive_a02_capability_gap_contract_view(result)
    assert view.gap_entry_count == 2
