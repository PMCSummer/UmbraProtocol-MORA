from __future__ import annotations

from substrate.c06_surfacing_candidates import (
    C06CandidateClass,
    C06ContinuityHorizon,
    C06StrengthGrade,
    C06SurfacingResult,
    C06SurfacingStatus,
    C06SurfacedCandidate,
    C06UncertaintyState,
)
from substrate.c06_surfacing_candidates.policy import _deduplicate_candidates
from tests.substrate.c06_surfacing_candidates_testkit import build_c06_harness_case, harness_cases


def test_typed_c06_surfaces_are_materialized_not_summary_wrapper() -> None:
    result = build_c06_harness_case(harness_cases()["baseline_assertion"])
    assert isinstance(result, C06SurfacingResult)
    assert result.candidate_set.candidate_set_id.startswith("c06-candidates:")
    assert result.candidate_set.status in {
        C06SurfacingStatus.SURFACED,
        C06SurfacingStatus.NO_CONTINUITY_CANDIDATES,
    }
    assert isinstance(result.candidate_set.surfaced_candidates, tuple)
    assert isinstance(result.candidate_set.suppression_report.suppressed_items, tuple)


def test_same_text_different_discourse_state_changes_candidate_extraction() -> None:
    baseline = build_c06_harness_case(harness_cases()["baseline_assertion"])
    carry = build_c06_harness_case(harness_cases()["same_text_commitment_carry"])
    assert baseline.candidate_set.status in {
        C06SurfacingStatus.SURFACED,
        C06SurfacingStatus.NO_CONTINUITY_CANDIDATES,
    }
    assert carry.candidate_set.status == C06SurfacingStatus.SURFACED
    baseline_classes = {item.candidate_class for item in baseline.candidate_set.surfaced_candidates}
    carry_classes = {item.candidate_class for item in carry.candidate_set.surfaced_candidates}
    assert C06CandidateClass.COMMITMENT_CARRYOVER not in baseline_classes
    assert C06CandidateClass.COMMITMENT_CARRYOVER in carry_classes
    assert baseline_classes != carry_classes


def test_salience_vs_continuity_surfaces_quiet_load_bearing_and_suppresses_vivid_resolved() -> None:
    result = build_c06_harness_case(harness_cases()["salience_vs_continuity"])
    classes = {item.candidate_class for item in result.candidate_set.surfaced_candidates}
    reasons = {
        item.suppression_reason.value for item in result.candidate_set.suppression_report.suppressed_items
    }
    assert C06CandidateClass.COMMITMENT_CARRYOVER in classes
    assert "stylistically_salient_only" in reasons


def test_paraphrased_repeated_commitment_object_is_deduplicated_with_merge_trace() -> None:
    result = build_c06_harness_case(harness_cases()["dedup_commitment_repeat"])
    commitment_candidates = [
        item
        for item in result.candidate_set.surfaced_candidates
        if item.candidate_class is C06CandidateClass.COMMITMENT_CARRYOVER
    ]
    assert len(commitment_candidates) == 1
    assert result.candidate_set.metadata.duplicate_merge_count > 0
    assert "identity_merged" in commitment_candidates[0].rationale_codes


def test_superficially_similar_but_distinct_objects_do_not_false_merge() -> None:
    result = build_c06_harness_case(harness_cases()["false_merge_guard"])
    classes = {item.candidate_class for item in result.candidate_set.surfaced_candidates}
    assert C06CandidateClass.OPEN_QUESTION in classes
    assert C06CandidateClass.PENDING_CLARIFICATION in classes
    assert result.candidate_set.metadata.false_merge_detected is False


def test_identity_stabilizer_prevents_false_merge_while_paraphrase_repeat_still_merges() -> None:
    base = C06SurfacedCandidate(
        candidate_id="c06:test:1",
        candidate_class=C06CandidateClass.PROJECT_CONTINUATION_CUE,
        source_refs=("p01:active_project", "v03:aligned_source_act:a1"),
        identity_hint="project:active_continuation",
        identity_stabilizer="project_anchor:a1",
        continuity_horizon=C06ContinuityHorizon.NEXT_TURN,
        strength_grade=C06StrengthGrade.MODERATE,
        uncertainty_state=C06UncertaintyState.PROVISIONAL,
        relation_to_current_project="active_project",
        relation_to_discourse="project_continuation",
        suggested_next_layer_consumers=("P02",),
        dismissal_risk="moderate_if_dropped",
        rationale_codes=("active_project_present",),
        provenance="tests.c06.identity",
    )
    paraphrase_same_object = C06SurfacedCandidate(
        candidate_id="c06:test:2",
        candidate_class=C06CandidateClass.PROJECT_CONTINUATION_CUE,
        source_refs=("p01:active_project", "v03:aligned_source_act:a1-paraphrase"),
        identity_hint="project:active_continuation",
        identity_stabilizer="project_anchor:a1",
        continuity_horizon=C06ContinuityHorizon.NEXT_TURN,
        strength_grade=C06StrengthGrade.MODERATE,
        uncertainty_state=C06UncertaintyState.PROVISIONAL,
        relation_to_current_project="active_project",
        relation_to_discourse="project_continuation",
        suggested_next_layer_consumers=("P02",),
        dismissal_risk="moderate_if_dropped",
        rationale_codes=("paraphrased_restatement",),
        provenance="tests.c06.identity",
    )
    superficially_similar_distinct = C06SurfacedCandidate(
        candidate_id="c06:test:3",
        candidate_class=C06CandidateClass.PROJECT_CONTINUATION_CUE,
        source_refs=("p01:active_project", "v03:aligned_source_act:a2"),
        identity_hint="project:active_continuation",
        identity_stabilizer="project_anchor:a2",
        continuity_horizon=C06ContinuityHorizon.NEXT_TURN,
        strength_grade=C06StrengthGrade.MODERATE,
        uncertainty_state=C06UncertaintyState.PROVISIONAL,
        relation_to_current_project="active_project",
        relation_to_discourse="project_continuation",
        suggested_next_layer_consumers=("P02",),
        dismissal_risk="moderate_if_dropped",
        rationale_codes=("distinct_anchor",),
        provenance="tests.c06.identity",
    )
    suppressed = []
    deduped, duplicate_merge_count, false_merge_detected = _deduplicate_candidates(
        tick_id="c06-identity-test",
        candidates=[base, paraphrase_same_object, superficially_similar_distinct],
        already_false_merge=False,
        suppressed=suppressed,
    )
    assert duplicate_merge_count == 1
    assert false_merge_detected is False
    assert len(deduped) == 2
    assert len(suppressed) == 1
    assert deduped[0].identity_hint == deduped[1].identity_hint == "project:active_continuation"
    assert {item.identity_stabilizer for item in deduped} == {"project_anchor:a1", "project_anchor:a2"}


def test_suppression_report_keeps_examined_but_rejected_items_with_reasons() -> None:
    result = build_c06_harness_case(harness_cases()["c06_1_workspace_handoff"])
    assert result.candidate_set.suppression_report.examined_item_count > 0
    assert result.candidate_set.suppression_report.suppressed_item_count > 0
    reasons = {
        item.suppression_reason.value for item in result.candidate_set.suppression_report.suppressed_items
    }
    assert "frontier_not_published" in reasons


def test_c06_1_workspace_handoff_contract_is_not_decorative() -> None:
    result = build_c06_harness_case(harness_cases()["c06_1_workspace_handoff"])
    metadata = result.candidate_set.metadata
    assert metadata.published_frontier_requirement is True
    assert metadata.published_frontier_requirement_satisfied is False
    assert metadata.unresolved_ambiguity_preserved is True
    assert metadata.confidence_residue_preserved is True


def test_publication_semantics_are_non_contradictory_for_published_vs_unpublished_workspace_refs() -> None:
    published = build_c06_harness_case(harness_cases()["c06_1_workspace_published_only"])
    unpublished = build_c06_harness_case(harness_cases()["c06_1_workspace_unpublished"])
    published_reasons = {
        item.suppression_reason.value
        for item in published.candidate_set.suppression_report.suppressed_items
    }
    unpublished_reasons = {
        item.suppression_reason.value
        for item in unpublished.candidate_set.suppression_report.suppressed_items
    }

    assert "frontier_not_published" not in published_reasons
    assert "frontier_not_published" in unpublished_reasons
    assert (
        published.candidate_set.metadata.published_frontier_requirement_satisfied is True
    )
    assert (
        unpublished.candidate_set.metadata.published_frontier_requirement_satisfied is False
    )
    assert unpublished.candidate_set.metadata.unresolved_ambiguity_preserved is True
    assert unpublished.candidate_set.metadata.confidence_residue_preserved is True


def test_v03_alignment_structure_materially_changes_c06_provenance_selection() -> None:
    baseline = build_c06_harness_case(harness_cases()["alignment_anchor_baseline"])
    underconstrained = build_c06_harness_case(
        harness_cases()["alignment_anchor_underconstrained"]
    )
    baseline_project = [
        item
        for item in baseline.candidate_set.surfaced_candidates
        if item.candidate_class is C06CandidateClass.COMMITMENT_CARRYOVER
    ]
    underconstrained_project = [
        item
        for item in underconstrained.candidate_set.surfaced_candidates
        if item.candidate_class is C06CandidateClass.COMMITMENT_CARRYOVER
    ]

    assert baseline_project
    assert underconstrained_project
    assert any(
        any(source.startswith("v03:aligned_source_act:") for source in item.source_refs)
        for item in baseline_project
    )
    assert any(
        "v03:aligned_source_act:none" in item.source_refs
        for item in underconstrained_project
    )
    assert baseline_project[0].source_refs != underconstrained_project[0].source_refs


def test_disabled_or_no_basis_returns_honest_non_activating_status() -> None:
    no_basis = build_c06_harness_case(harness_cases()["no_basis"])
    disabled = build_c06_harness_case(harness_cases()["disabled"])
    assert no_basis.candidate_set.status is C06SurfacingStatus.INSUFFICIENT_SURFACING_BASIS
    assert disabled.candidate_set.status is C06SurfacingStatus.INSUFFICIENT_SURFACING_BASIS
    assert no_basis.gate.candidate_set_consumer_ready is False
    assert disabled.gate.candidate_set_consumer_ready is False
