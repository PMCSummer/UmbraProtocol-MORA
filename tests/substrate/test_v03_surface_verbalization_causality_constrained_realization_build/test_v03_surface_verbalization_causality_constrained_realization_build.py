from __future__ import annotations

import inspect

from substrate.v03_surface_verbalization_causality_constrained_realization import (
    V03ConstrainedRealizationResult,
    V03RealizationStatus,
    V03SurfaceSpanAlignment,
    build_v03_surface_verbalization_causality_constrained_realization,
)
from tests.substrate.v03_surface_verbalization_causality_constrained_realization_testkit import (
    build_v03_harness_case,
    harness_cases,
)


def test_typed_v03_surfaces_are_materialized_not_prose_wrapper() -> None:
    result = build_v03_harness_case(harness_cases()["baseline_assertion"])
    assert isinstance(result, V03ConstrainedRealizationResult)
    assert result.artifact.realization_id.startswith("v03-realization:")
    assert result.artifact.surface_text
    assert result.artifact.segment_order
    assert result.alignment_map.alignments
    assert all(isinstance(item, V03SurfaceSpanAlignment) for item in result.alignment_map.alignments)


def test_alignment_map_is_machine_usable_with_span_indices() -> None:
    result = build_v03_harness_case(harness_cases()["weak_assertion_with_qualifiers"])
    assert result.alignment_map.aligned_segment_count == len(result.alignment_map.alignments)
    for item in result.alignment_map.alignments:
        assert item.start_index >= 0
        assert item.end_index > item.start_index
        assert item.realized is True
        assert item.realized_text


def test_alignment_ordering_pass_is_computed_not_hardcoded_truthy() -> None:
    baseline = build_v03_harness_case(harness_cases()["protective_structure_baseline"])
    violated = build_v03_harness_case(harness_cases()["boundary_order_violation"])
    assert baseline.alignment_map.ordering_pass is True
    assert all(item.ordering_pass is True for item in baseline.alignment_map.alignments)
    assert violated.alignment_map.ordering_pass is False
    assert any(item.ordering_pass is False for item in violated.alignment_map.alignments)


def test_qualifier_locality_failure_is_detected() -> None:
    baseline = build_v03_harness_case(harness_cases()["weak_assertion_with_qualifiers"])
    tampered = build_v03_harness_case(harness_cases()["qualifier_locality_tamper"])
    assert baseline.constraint_report.qualifier_locality_failures == 0
    assert tampered.constraint_report.qualifier_locality_failures > 0
    assert "qualifier_locality_violation" in tampered.constraint_report.violation_codes
    assert tampered.failure_state.failed is True
    assert tampered.failure_state.replan_required is True


def test_blocked_expansion_leakage_is_detected() -> None:
    leaked = build_v03_harness_case(harness_cases()["blocked_expansion_leak"])
    assert leaked.constraint_report.blocked_expansion_leak_detected is True
    assert "blocked_expansion_leak_detected" in leaked.constraint_report.violation_codes
    assert leaked.failure_state.failed is True
    assert leaked.failure_state.partial_realization_only is True


def test_protected_omission_leakage_is_detected() -> None:
    leaked = build_v03_harness_case(harness_cases()["protected_omission_leak"])
    assert leaked.constraint_report.protected_omission_violation_detected is True
    assert "protected_omission_violation_detected" in leaked.constraint_report.violation_codes
    assert leaked.failure_state.failed is True
    assert leaked.failure_state.partial_realization_only is True


def test_boundary_before_explanation_ordering_is_enforced() -> None:
    violated = build_v03_harness_case(harness_cases()["boundary_order_violation"])
    assert violated.constraint_report.boundary_before_explanation_required is True
    assert violated.constraint_report.boundary_before_explanation_satisfied is False
    assert "boundary_before_explanation_violation" in violated.constraint_report.violation_codes
    assert violated.failure_state.failed is True


def test_hard_constraints_override_soft_fluency_preference() -> None:
    leaked = build_v03_harness_case(harness_cases()["implicit_commitment_leak"])
    assert leaked.constraint_report.implicit_commitment_leak_detected is True
    assert leaked.constraint_report.hard_constraint_violation_count > 0
    assert leaked.realization_status in {
        V03RealizationStatus.PARTIAL_REALIZATION_ONLY,
        V03RealizationStatus.CLARIFICATION_ONLY_REALIZATION,
        V03RealizationStatus.BOUNDARY_ONLY_REALIZATION,
        V03RealizationStatus.REALIZATION_FAILED,
    }
    assert leaked.failure_state.failed is True
    assert leaked.failure_state.replan_required is True


def test_paraphrase_variant_can_change_surface_while_preserving_hard_profile() -> None:
    baseline = build_v03_harness_case(harness_cases()["weak_assertion_with_qualifiers"])
    paraphrase = build_v03_harness_case(harness_cases()["paraphrase_variant"])
    assert baseline.artifact.surface_text != paraphrase.artifact.surface_text
    assert (
        baseline.constraint_report.hard_constraint_violation_count
        == paraphrase.constraint_report.hard_constraint_violation_count
    )
    assert (
        baseline.constraint_report.blocked_expansion_leak_detected
        == paraphrase.constraint_report.blocked_expansion_leak_detected
    )
    assert (
        baseline.constraint_report.qualifier_locality_failures
        == paraphrase.constraint_report.qualifier_locality_failures
    )


def test_no_basis_returns_honest_insufficient_realization_state() -> None:
    result = build_v03_harness_case(harness_cases()["no_basis"])
    assert result.realization_status is V03RealizationStatus.INSUFFICIENT_REALIZATION_BASIS
    assert result.artifact.surface_text == ""
    assert result.gate.realization_consumer_ready is False
    assert "insufficient_realization_basis" in result.gate.restrictions


def test_v03_policy_signature_has_no_direct_r05_input_seam() -> None:
    params = inspect.signature(
        build_v03_surface_verbalization_causality_constrained_realization
    ).parameters
    assert "r05_result" not in params
