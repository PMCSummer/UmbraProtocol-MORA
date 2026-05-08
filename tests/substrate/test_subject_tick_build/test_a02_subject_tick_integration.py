from __future__ import annotations

from dataclasses import replace

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.a02_capability_gap_detection import (
    A02ControllabilityStatus,
    A02DemandClass,
    A02DemandLegitimacyStatus,
    A02DemandPacket,
    A02DemandSet,
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


def _a02_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a02_capability_gap_detection_checkpoint"
    )


def _base_context() -> SubjectTickContext:
    return SubjectTickContext()


def _canonical_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:canonical",
        reason="canonical input",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a02.integration:{case_id}:c1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.9,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:pause_and_recover",
            ),
        ),
    )


def _communication_blocked_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:blocked",
        reason="blocked communication",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:b1",
                local_label="send_update",
                affordance_class=A01AffordanceClass.COMMUNICATION_OUTPUT,
                aliases=(),
                provenance=f"tests.a02.integration:{case_id}:b1",
                preconditions=("disabled_effector",),
                primary_outcomes=("update_sent",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.4,
                observation_signals=("sent",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.WORLD_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:send_update",
            ),
        ),
    )


def _composition_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:composition",
        reason="composition pair",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:s1",
                local_label="repair_scope_a",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a02.integration:{case_id}:s1",
                preconditions=("ok",),
                primary_outcomes=("scope_a",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("a",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:scope_a",
            ),
            a01_candidate(
                candidate_id=f"{case_id}:s2",
                local_label="repair_scope_b",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a02.integration:{case_id}:s2",
                preconditions=("ok",),
                primary_outcomes=("scope_b",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("b",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:scope_b",
            ),
        ),
    )


def _demand_set(set_id: str, demands: tuple[A02DemandPacket, ...]) -> A02DemandSet:
    return A02DemandSet(
        demand_set_id=set_id,
        demands=demands,
        source_lineage=("tests.a02.integration", set_id),
        reason="integration demand set",
    )


def test_subject_tick_emits_a02_checkpoint_between_a01_and_a_line() -> None:
    case_id = "rt-a02-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a02_demand_set=_demand_set(
                f"{case_id}:demand",
                (
                    A02DemandPacket(
                        demand_id=f"{case_id}:d1",
                        demanded_change_class=A02DemandClass.SELF_REPAIR,
                        demanded_scope=("reduce_overload",),
                        target_channels=("internal",),
                        source_kind="tests",
                        source_ref="tests.a02",
                        urgency="normal",
                        severity=1,
                        allowed_latency="bounded_tick",
                        legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                        required_controllability=A02ControllabilityStatus.CONTROLLABLE_CURRENTLY,
                        world_side_requirement="optional",
                        provenance=("tests.a02",),
                    ),
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.a01_affordance_ontology_cleanup_checkpoint" in ids
    assert "rt01.a02_capability_gap_detection_checkpoint" in ids
    assert "rt01.a_line_normalization_checkpoint" in ids
    assert ids.index("rt01.a01_affordance_ontology_cleanup_checkpoint") < ids.index(
        "rt01.a02_capability_gap_detection_checkpoint"
    )
    assert ids.index("rt01.a02_capability_gap_detection_checkpoint") < ids.index(
        "rt01.a_line_normalization_checkpoint"
    )


def test_a02_require_paths_are_deterministic() -> None:
    case_id = "rt-a02-require"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a02_demand_set=None,
            require_a02_gap_packet_consumer=True,
            require_a02_partial_coverage_consumer=True,
            require_a02_ownership_boundary_consumer=True,
            require_a02_composition_consumer=True,
        ),
    )
    checkpoint = _a02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_a02_gap_packet_consumer" in checkpoint.required_action
    assert "require_a02_partial_coverage_consumer" in checkpoint.required_action
    assert "require_a02_ownership_boundary_consumer" in checkpoint.required_action
    assert "require_a02_composition_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_basis_gated_default_missing_gap_detour_is_load_bearing() -> None:
    case_id = "rt-a02-missing"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a02_demand_set=_demand_set(
                f"{case_id}:demand",
                (
                    A02DemandPacket(
                        demand_id=f"{case_id}:d1",
                        demanded_change_class=A02DemandClass.COMMUNICATION,
                        demanded_scope=("update_sent",),
                        target_channels=("world",),
                        source_kind="tests",
                        source_ref="tests.a02",
                        urgency="normal",
                        severity=2,
                        allowed_latency="bounded_tick",
                        legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                        required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
                        world_side_requirement="optional",
                        provenance=("tests.a02",),
                    ),
                ),
            ),
        ),
    )
    checkpoint = _a02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a02_missing_affordance_exploration_detour" in checkpoint.required_action
    assert result.state.a02_missing_gap_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_basis_gated_default_blocked_gap_detour_is_load_bearing() -> None:
    case_id = "rt-a02-blocked"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_communication_blocked_candidate_set(case_id),
            a02_demand_set=_demand_set(
                f"{case_id}:demand",
                (
                    A02DemandPacket(
                        demand_id=f"{case_id}:d1",
                        demanded_change_class=A02DemandClass.COMMUNICATION,
                        demanded_scope=("update_sent",),
                        target_channels=("world",),
                        source_kind="tests",
                        source_ref="tests.a02",
                        urgency="normal",
                        severity=2,
                        allowed_latency="bounded_tick",
                        legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                        required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
                        world_side_requirement="optional",
                        provenance=("tests.a02",),
                    ),
                ),
            ),
        ),
    )
    checkpoint = _a02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a02_blocked_affordance_restoration_detour" in checkpoint.required_action
    assert result.state.a02_blocked_gap_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_ownership_boundary_path_triggers_boundary_detour() -> None:
    case_id = "rt-a02-ownership"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a02_demand_set=_demand_set(
                f"{case_id}:demand",
                (
                    A02DemandPacket(
                        demand_id=f"{case_id}:d1",
                        demanded_change_class=A02DemandClass.WORLD_FACING,
                        demanded_scope=("external_partner_compliance",),
                        target_channels=("world",),
                        source_kind="tests",
                        source_ref="tests.a02",
                        urgency="high",
                        severity=3,
                        allowed_latency="bounded_tick",
                        legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                        required_controllability=A02ControllabilityStatus.OUTSIDE_CURRENT_CONTROL,
                        world_side_requirement="required",
                        provenance=("tests.a02",),
                    ),
                ),
            ),
        ),
    )
    checkpoint = _a02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a02_ownership_boundary_detour" in checkpoint.required_action
    assert result.state.a02_ownership_boundary_gap_count > 0


def test_same_checkpoint_action_can_diverge_by_typed_a02_shape() -> None:
    clean_case = "rt-a02-envelope-clean"
    gap_case = "rt-a02-envelope-gap"
    shared_demand = _demand_set(
        "a02:shared:composition",
        (
            A02DemandPacket(
                demand_id="d1",
                demanded_change_class=A02DemandClass.SELF_REPAIR,
                demanded_scope=("scope_a", "scope_b"),
                target_channels=("internal",),
                source_kind="tests",
                source_ref="tests.a02",
                urgency="normal",
                severity=2,
                allowed_latency="bounded_tick",
                legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                required_controllability=A02ControllabilityStatus.CONTROLLABLE_CURRENTLY,
                world_side_requirement="optional",
                provenance=("tests.a02",),
            ),
        ),
    )
    clean = _result(
        clean_case,
        context=replace(
            _base_context(),
            require_a02_gap_packet_consumer=True,
            a01_raw_affordance_candidate_set=_composition_candidate_set(clean_case),
            a02_demand_set=shared_demand,
            a02_composition_enabled=True,
        ),
    )
    gap = _result(
        gap_case,
        context=replace(
            _base_context(),
            require_a02_gap_packet_consumer=True,
            a01_raw_affordance_candidate_set=_composition_candidate_set(gap_case),
            a02_demand_set=shared_demand,
            a02_composition_enabled=False,
        ),
    )
    clean_checkpoint = _a02_checkpoint(clean)
    gap_checkpoint = _a02_checkpoint(gap)
    assert clean_checkpoint.status.value == "allowed"
    assert gap_checkpoint.status.value == "allowed"
    assert clean_checkpoint.required_action == "require_a02_gap_packet_consumer"
    assert gap_checkpoint.required_action == "require_a02_gap_packet_consumer"
    assert clean.state.a02_composition_gap_count == 0
    assert gap.state.a02_composition_gap_count > 0
    assert clean.downstream_gate.accepted is True
    assert gap.downstream_gate.accepted is False


def test_disable_a02_enforcement_changes_behavior_and_no_blanket_friction_without_basis() -> None:
    case_id = "rt-a02-no-bypass"
    enabled = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a02_demand_set=_demand_set(
                f"{case_id}:demand",
                (
                    A02DemandPacket(
                        demand_id=f"{case_id}:d1",
                        demanded_change_class=A02DemandClass.COMMUNICATION,
                        demanded_scope=("update_sent",),
                        target_channels=("world",),
                        source_kind="tests",
                        source_ref="tests.a02",
                        urgency="normal",
                        severity=2,
                        allowed_latency="bounded_tick",
                        legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                        required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
                        world_side_requirement="optional",
                        provenance=("tests.a02",),
                    ),
                ),
            ),
        ),
    )
    disabled = _result(
        f"{case_id}-disabled",
        context=replace(
            _base_context(),
            disable_a02_enforcement=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(f"{case_id}-disabled"),
            a02_demand_set=_demand_set(
                f"{case_id}:demand:disabled",
                (
                    A02DemandPacket(
                        demand_id=f"{case_id}:d1",
                        demanded_change_class=A02DemandClass.COMMUNICATION,
                        demanded_scope=("update_sent",),
                        target_channels=("world",),
                        source_kind="tests",
                        source_ref="tests.a02",
                        urgency="normal",
                        severity=2,
                        allowed_latency="bounded_tick",
                        legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                        required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
                        world_side_requirement="optional",
                        provenance=("tests.a02",),
                    ),
                ),
            ),
        ),
    )
    no_basis = _result(
        f"{case_id}-no-basis",
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(f"{case_id}-no-basis"),
            a02_demand_set=None,
        ),
    )
    enabled_checkpoint = _a02_checkpoint(enabled)
    disabled_checkpoint = _a02_checkpoint(disabled)
    no_basis_checkpoint = _a02_checkpoint(no_basis)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a02_missing_affordance_exploration_detour" in enabled_checkpoint.required_action
    assert disabled_checkpoint.status.value == "allowed"
    assert disabled_checkpoint.required_action == "a02_optional"
    assert enabled.state.final_execution_outcome != disabled.state.final_execution_outcome
    assert no_basis_checkpoint.status.value == "allowed"
    assert no_basis_checkpoint.required_action == "a02_optional"
    assert no_basis.state.a02_explicit_basis_present is False
