from __future__ import annotations

from substrate.v02_communicative_intent_utterance_plan_bridge import (
    V02PlanSegment,
    V02PlanStatus,
    V02SegmentRole,
)
from tests.substrate.v02_communicative_intent_utterance_plan_bridge_testkit import (
    build_v02_harness_case,
    harness_cases,
)


def test_typed_v02_surfaces_are_materialized_as_plan_graph_state() -> None:
    result = build_v02_harness_case(harness_cases()["assertion_base"])
    assert result.state.plan_id.startswith("v02-plan:")
    assert result.state.plan_status is V02PlanStatus.FULL_PLAN_READY
    assert result.state.segment_count == 1
    assert result.state.ordering_edge_count == 0
    assert all(isinstance(segment, V02PlanSegment) for segment in result.state.segment_graph)
    assert result.gate.plan_consumer_ready is True


def test_same_acts_with_different_history_change_plan_topology() -> None:
    base = build_v02_harness_case(harness_cases()["assertion_base"])
    with_history = build_v02_harness_case(harness_cases()["assertion_with_unresolved_history"])
    assert base.state.plan_status is V02PlanStatus.FULL_PLAN_READY
    assert with_history.state.plan_status is V02PlanStatus.CLARIFICATION_FIRST_PLAN
    assert base.state.clarification_first_required is False
    assert with_history.state.clarification_first_required is True
    assert with_history.state.segment_count > base.state.segment_count
    assert with_history.state.ordering_edge_count > base.state.ordering_edge_count


def test_qualifier_binding_and_ordering_are_real_structural_edges() -> None:
    weak = build_v02_harness_case(harness_cases()["weak_assertion_qualifier_binding"])
    assert weak.state.mandatory_qualifier_attachment_count > 0
    assert any(
        segment.segment_role is V02SegmentRole.QUALIFICATION
        for segment in weak.state.segment_graph
    )
    assert any(
        edge.reason_code == "mandatory_qualifier_binding"
        for edge in weak.state.ordering_edges
    )


def test_branch_ambiguity_is_explicit_in_plan_state() -> None:
    ambiguous = build_v02_harness_case(harness_cases()["branch_ambiguity"])
    assert ambiguous.state.unresolved_branching is True
    assert ambiguous.state.plan_status is V02PlanStatus.MULTIPLE_BRANCHES_UNRESOLVED
    assert ambiguous.state.branch_count >= 3
    assert len(ambiguous.state.alternative_branch_ids) >= 2


def test_protective_state_changes_plan_structure_not_just_reason_text() -> None:
    baseline = build_v02_harness_case(harness_cases()["assertion_base"])
    protective = build_v02_harness_case(harness_cases()["protective_structure"])
    assert baseline.state.protective_boundary_first is False
    assert protective.state.protective_boundary_first is True
    assert any(
        segment.segment_role is V02SegmentRole.BOUNDARY
        for segment in protective.state.segment_graph
    )
    assert protective.state.segment_count >= baseline.state.segment_count


def test_p01_blocked_handoff_basis_modulates_v02_plan_shape() -> None:
    baseline = build_v02_harness_case(harness_cases()["assertion_base"])
    blocked = build_v02_harness_case(harness_cases()["p01_blocked_handoff"])
    assert baseline.state.clarification_first_required is False
    assert blocked.state.clarification_first_required is True
    assert baseline.state.discourse_history_sensitive is False
    assert blocked.state.discourse_history_sensitive is True
    assert blocked.state.plan_status is V02PlanStatus.CLARIFICATION_FIRST_PLAN
    assert "p01_handoff_blocked:True" in blocked.state.justification_links


def test_blocked_expansions_and_protected_omissions_are_explicit() -> None:
    split = build_v02_harness_case(harness_cases()["commitment_split"])
    assert split.state.blocked_expansion_count > 0
    assert split.state.protected_omission_count > 0
    assert split.state.blocked_expansion_ids
    assert split.state.protected_omission_ids
    assert any(
        segment.blocked_expansion_ids or segment.protected_omission_ids
        for segment in split.state.segment_graph
    )


def test_plan_is_not_a_draft_masquerading_as_typed_structure() -> None:
    weak = build_v02_harness_case(harness_cases()["weak_assertion_qualifier_binding"])
    assert weak.state.segment_ids
    assert weak.state.source_act_ids
    assert weak.state.segment_count >= 2
    assert weak.state.ordering_edge_count >= 1
    assert all(segment.target_update for segment in weak.state.segment_graph)


def test_no_explicit_basis_returns_honest_insufficient_plan_state() -> None:
    no_basis = build_v02_harness_case(harness_cases()["no_basis"])
    assert no_basis.state.plan_status is V02PlanStatus.INSUFFICIENT_PLAN_BASIS
    assert no_basis.state.segment_count == 0
    assert no_basis.gate.plan_consumer_ready is False
    assert "insufficient_plan_basis" in no_basis.gate.restrictions
