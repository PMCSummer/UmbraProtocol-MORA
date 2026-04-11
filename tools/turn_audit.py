from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    derive_runtime_dispatch_contract_view,
    dispatch_rt01_production_tick,
    dispatch_runtime_tick,
)
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    derive_subject_tick_runtime_domain_contract_view,
)


ARTIFACT_VERSION = "turn_audit_artifact_v1"
SEAM_PHASE = "RT01"
DEFAULT_SEAM_CONTRACT_PATH = "docs/seams/RT01.seam.md"
UNRESOLVED_TOKEN = "UNRESOLVED_FOR_V1"

CONTEXT_BOOL_FLAGS: tuple[str, ...] = (
    "disable_gate_application",
    "disable_c04_mode_execution_binding",
    "disable_c05_validity_enforcement",
    "disable_downstream_obedience_enforcement",
    "disable_s_minimal_enforcement",
    "disable_a_line_enforcement",
    "disable_m_minimal_enforcement",
    "disable_n_minimal_enforcement",
    "disable_t01_unresolved_slot_maintenance",
    "disable_t01_field_enforcement",
    "disable_t02_enforcement",
    "disable_t03_enforcement",
    "disable_t04_enforcement",
    "require_world_grounded_transition",
    "require_world_effect_feedback_for_success_claim",
    "require_t01_preverbal_scene_consumer",
    "require_t01_scene_comparison_consumer",
    "require_t02_constrained_scene_consumer",
    "require_t02_raw_vs_propagated_distinction",
    "require_t03_convergence_consumer",
    "require_t03_frontier_consumer",
    "require_t03_nonconvergence_preservation",
    "require_t04_focus_ownership_consumer",
    "require_t04_reportable_focus_consumer",
    "require_t04_peripheral_preservation",
    "require_s01_comparison_consumer",
    "require_s01_unexpected_change_consumer",
    "require_s01_prediction_validity_consumer",
    "require_s02_boundary_consumer",
    "require_s02_controllability_consumer",
    "require_s02_mixed_source_consumer",
    "require_s03_learning_packet_consumer",
    "require_s03_mixed_update_consumer",
    "require_s03_freeze_obedience_consumer",
    "emit_world_action_candidate",
)

CONTEXT_VALUE_FLAGS: tuple[str, ...] = (
    "t02_assembly_mode",
    "t03_competition_mode",
)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return _enum_value(value)


def _unresolved_entry(
    *,
    code: str,
    message: str,
    blocking_surface: str,
    severity: str,
    impacted_sections: list[str],
    requires_non_v1_extension: bool,
) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "blocking_surface": blocking_surface,
        "severity": severity,
        "impacted_sections": impacted_sections,
        "requires_non_v1_extension": requires_non_v1_extension,
    }


def _collect_scope_markers(view: Any) -> dict[str, object]:
    return {
        "world_entry": {
            "scope": view.world_entry_scope,
            "admission_layer_only": view.world_entry_scope_admission_layer_only,
            "w01_implemented": view.world_entry_scope_w01_implemented,
            "w_line_implemented": view.world_entry_scope_w_line_implemented,
            "repo_wide_adoption": view.world_entry_scope_repo_wide_adoption,
        },
        "s_minimal": {
            "scope": view.s_scope,
            "rt01_contour_only": view.s_scope_rt01_contour_only,
            "s_minimal_only": view.s_scope_s_minimal_only,
            "s01_implemented": view.s_scope_s01_implemented,
            "s_line_implemented": view.s_scope_s_line_implemented,
            "minimal_contour_only": view.s_scope_minimal_contour_only,
            "s01_s05_implemented": view.s_scope_s01_s05_implemented,
            "full_self_model_implemented": view.s_scope_full_self_model_implemented,
            "repo_wide_adoption": view.s_scope_repo_wide_adoption,
        },
        "a_line_normalization": {
            "scope": view.a_scope,
            "rt01_contour_only": view.a_scope_rt01_contour_only,
            "a_line_normalization_only": view.a_scope_a_line_normalization_only,
            "readiness_gate_only": view.a_scope_readiness_gate_only,
            "a04_implemented": view.a_scope_a04_implemented,
            "a05_touched": view.a_scope_a05_touched,
            "full_agency_stack_implemented": view.a_scope_full_agency_stack_implemented,
            "repo_wide_adoption": view.a_scope_repo_wide_adoption,
        },
        "m_minimal": {
            "scope": view.m_scope,
            "rt01_contour_only": view.m_scope_rt01_contour_only,
            "m_minimal_only": view.m_scope_m_minimal_only,
            "readiness_gate_only": view.m_scope_readiness_gate_only,
            "m01_implemented": view.m_scope_m01_implemented,
            "m02_implemented": view.m_scope_m02_implemented,
            "m03_implemented": view.m_scope_m03_implemented,
            "full_memory_stack_implemented": view.m_scope_full_memory_stack_implemented,
            "repo_wide_adoption": view.m_scope_repo_wide_adoption,
        },
        "n_minimal": {
            "scope": view.n_scope,
            "rt01_contour_only": view.n_scope_rt01_contour_only,
            "n_minimal_only": view.n_scope_n_minimal_only,
            "readiness_gate_only": view.n_scope_readiness_gate_only,
            "n01_implemented": view.n_scope_n01_implemented,
            "n02_implemented": view.n_scope_n02_implemented,
            "n03_implemented": view.n_scope_n03_implemented,
            "n04_implemented": view.n_scope_n04_implemented,
            "full_narrative_line_implemented": view.n_scope_full_narrative_line_implemented,
            "repo_wide_adoption": view.n_scope_repo_wide_adoption,
        },
        "t01": {
            "scope": view.t01_scope,
            "rt01_contour_only": view.t01_scope_rt01_contour_only,
            "t01_first_slice_only": view.t01_scope_t01_first_slice_only,
            "t02_implemented": view.t01_scope_t02_implemented,
            "t03_implemented": view.t01_scope_t03_implemented,
            "t04_implemented": view.t01_scope_t04_implemented,
            "o01_implemented": view.t01_scope_o01_implemented,
            "full_silent_thought_line_implemented": view.t01_scope_full_silent_thought_line_implemented,
            "repo_wide_adoption": view.t01_scope_repo_wide_adoption,
        },
        "s02": {
            "scope": view.s02_scope,
            "rt01_contour_only": view.s02_scope_rt01_contour_only,
            "s02_first_slice_only": view.s02_scope_s02_first_slice_only,
            "s03_implemented": view.s02_scope_s03_implemented,
            "s04_implemented": view.s02_scope_s04_implemented,
            "s05_implemented": view.s02_scope_s05_implemented,
            "full_self_model_implemented": view.s02_scope_full_self_model_implemented,
            "repo_wide_adoption": view.s02_scope_repo_wide_adoption,
        },
        "s03": {
            "scope": view.s03_scope,
            "rt01_contour_only": view.s03_scope_rt01_contour_only,
            "s03_first_slice_only": view.s03_scope_s03_first_slice_only,
            "s04_implemented": view.s03_scope_s04_implemented,
            "s05_implemented": view.s03_scope_s05_implemented,
            "repo_wide_adoption": view.s03_scope_repo_wide_adoption,
        },
        "t02": {
            "scope": view.t02_scope,
            "rt01_contour_only": view.t02_scope_rt01_contour_only,
            "t02_first_slice_only": view.t02_scope_t02_first_slice_only,
            "t03_implemented": view.t02_scope_t03_implemented,
            "t04_implemented": view.t02_scope_t04_implemented,
            "o01_implemented": view.t02_scope_o01_implemented,
            "full_silent_thought_line_implemented": view.t02_scope_full_silent_thought_line_implemented,
            "repo_wide_adoption": view.t02_scope_repo_wide_adoption,
        },
        "t03": {
            "scope": view.t03_scope,
            "rt01_contour_only": view.t03_scope_rt01_contour_only,
            "t03_first_slice_only": view.t03_scope_t03_first_slice_only,
            "t04_implemented": view.t03_scope_t04_implemented,
            "o01_implemented": view.t03_scope_o01_implemented,
            "o02_implemented": view.t03_scope_o02_implemented,
            "o03_implemented": view.t03_scope_o03_implemented,
            "full_silent_thought_line_implemented": view.t03_scope_full_silent_thought_line_implemented,
            "repo_wide_adoption": view.t03_scope_repo_wide_adoption,
        },
        "t04": {
            "scope": view.t04_scope,
            "rt01_contour_only": view.t04_scope_rt01_contour_only,
            "t04_first_slice_only": view.t04_scope_t04_first_slice_only,
            "o01_implemented": view.t04_scope_o01_implemented,
            "o02_implemented": view.t04_scope_o02_implemented,
            "o03_implemented": view.t04_scope_o03_implemented,
            "full_attention_line_implemented": view.t04_scope_full_attention_line_implemented,
            "repo_wide_adoption": view.t04_scope_repo_wide_adoption,
        },
    }


def _phase_surfaces_unresolved() -> dict[str, object]:
    payload = {
        "status": UNRESOLVED_TOKEN,
        "reason": "dispatch rejected before subject_tick execution surfaces were materialized",
    }
    keys = (
        "downstream_obedience",
        "epistemics",
        "regulation",
        "world_entry",
        "s_minimal",
        "a_line_normalization",
        "m_minimal",
        "n_minimal",
        "s01_efference_copy",
        "s02_prediction_boundary",
        "s03_ownership_weighted_learning",
        "t01_semantic_field",
        "t02_relation_binding",
        "t03_hypothesis_competition",
        "t04_attention_schema",
    )
    return {key: dict(payload) for key in keys}


def _collect_phase_surfaces(view: Any, subject_tick_result: Any | None) -> dict[str, object]:
    if subject_tick_result is None:
        return _phase_surfaces_unresolved()
    state = subject_tick_result.state

    def _state_or_view(field: str) -> Any:
        if hasattr(state, field):
            return getattr(state, field)
        if hasattr(view, field):
            return getattr(view, field)
        return UNRESOLVED_TOKEN

    epistemic_allowance_restrictions = _state_or_view("epistemic_allowance_restrictions")
    if isinstance(epistemic_allowance_restrictions, tuple):
        epistemic_allowance_restrictions = list(epistemic_allowance_restrictions)

    return {
        "downstream_obedience": {
            "status": state.downstream_obedience_status,
            "fallback": state.downstream_obedience_fallback,
            "lawful_continue": state.downstream_obedience_status in {"allow_continue", "allow_continue_with_restriction"},
            "source_of_truth_surface": state.downstream_obedience_source_of_truth_surface,
            "requires_restrictions_read": state.downstream_obedience_requires_restrictions_read,
            "authority_basis_ok": state.downstream_obedience_status != "insufficient_authority_basis",
            "invalidated_upstream_surface": state.downstream_obedience_status == "invalidated_upstream_surface",
            "blocked_by_survival_override": state.downstream_obedience_status == "blocked_by_survival_override",
            "reason": state.downstream_obedience_reason,
        },
        "epistemics": {
            "epistemic_unit_id": _state_or_view("epistemic_unit_id"),
            "epistemic_status": _state_or_view("epistemic_status"),
            "epistemic_confidence": _state_or_view("epistemic_confidence"),
            "epistemic_source_class": _state_or_view("epistemic_source_class"),
            "epistemic_modality": _state_or_view("epistemic_modality"),
            "epistemic_classification_basis": _state_or_view("epistemic_classification_basis"),
            "epistemic_can_treat_as_observation": _state_or_view("epistemic_can_treat_as_observation"),
            "epistemic_should_abstain": _state_or_view("epistemic_should_abstain"),
            "epistemic_claim_strength": _state_or_view("epistemic_claim_strength"),
            "epistemic_allowance_restrictions": epistemic_allowance_restrictions,
            "epistemic_allowance_reason": _state_or_view("epistemic_allowance_reason"),
            "epistemic_unknown_reason": _state_or_view("epistemic_unknown_reason"),
            "epistemic_conflict_reason": _state_or_view("epistemic_conflict_reason"),
            "epistemic_abstain_reason": _state_or_view("epistemic_abstain_reason"),
        },
        "regulation": {
            "regulation_pressure_level": _state_or_view("regulation_pressure_level"),
            "regulation_escalation_stage": _state_or_view("regulation_escalation_stage"),
            "regulation_override_scope": _state_or_view("regulation_override_scope"),
            "regulation_no_strong_override_claim": _state_or_view("regulation_no_strong_override_claim"),
            "regulation_gate_accepted": _state_or_view("regulation_gate_accepted"),
            "regulation_source_state_ref": _state_or_view("regulation_source_state_ref"),
        },
        "world_entry": {
            "world_entry_episode_id": view.world_entry_episode_id,
            "world_entry_w01_admission_ready": view.world_entry_w01_admission_ready,
            "world_entry_w01_admission_restrictions": state.world_entry_w01_admission_restrictions,
            "world_entry_forbidden_claim_classes": view.world_entry_forbidden_claim_classes,
            "world_entry_world_grounded_transition_admissible": view.world_grounded_transition_allowed,
            "world_entry_world_effect_success_admissible": view.world_effect_feedback_correlated,
            "world_entry_degraded": state.world_entry_degraded,
            "world_entry_incomplete": state.world_entry_incomplete,
            "scope": _collect_scope_markers(view)["world_entry"],
        },
        "s_minimal": {
            "s_boundary_state_id": view.s_boundary_state_id,
            "s_attribution_class": view.s_attribution_class,
            "s_underconstrained": view.s_underconstrained,
            "s_no_safe_self_claim": view.s_no_safe_self_claim,
            "s_no_safe_world_claim": view.s_no_safe_world_claim,
            "s_forbidden_shortcuts": view.s_forbidden_shortcuts,
            "s_restrictions": state.s_restrictions,
            "s_s01_admission_ready": view.s_s01_admission_ready,
            "s_readiness_blockers": view.s_readiness_blockers,
            "scope": _collect_scope_markers(view)["s_minimal"],
        },
        "a_line_normalization": {
            "a_capability_id": view.a_capability_id,
            "a_capability_status": view.a_capability_status,
            "a_underconstrained": view.a_underconstrained,
            "a_no_safe_capability_claim": view.a_no_safe_capability_claim,
            "a_forbidden_shortcuts": view.a_forbidden_shortcuts,
            "a_restrictions": state.a_restrictions,
            "a_a04_admission_ready": view.a_a04_admission_ready,
            "a_a04_blockers": view.a_a04_blockers,
            "a_a04_structurally_present_but_not_ready": view.a_a04_structurally_present_but_not_ready,
            "a_a04_capability_basis_missing": view.a_a04_capability_basis_missing,
            "a_a04_world_dependency_unmet": view.a_a04_world_dependency_unmet,
            "a_a04_self_dependency_unmet": view.a_a04_self_dependency_unmet,
            "a_a04_policy_legitimacy_unmet": view.a_a04_policy_legitimacy_unmet,
            "a_a04_underconstrained_capability_surface": view.a_a04_underconstrained_capability_surface,
            "a_a04_external_means_not_justified": view.a_a04_external_means_not_justified,
            "scope": _collect_scope_markers(view)["a_line_normalization"],
        },
        "m_minimal": {
            "m_memory_item_id": view.m_memory_item_id,
            "m_lifecycle_status": view.m_lifecycle_status,
            "m_retention_class": view.m_retention_class,
            "m_underconstrained": state.m_underconstrained,
            "m_no_safe_memory_claim": state.m_no_safe_memory_claim,
            "m_forbidden_shortcuts": view.m_forbidden_shortcuts,
            "m_restrictions": state.m_restrictions,
            "m_m01_admission_ready": view.m_m01_admission_ready,
            "m_m01_blockers": view.m_m01_blockers,
            "m_m01_structurally_present_but_not_ready": view.m_m01_structurally_present_but_not_ready,
            "m_m01_stale_risk_unacceptable": view.m_m01_stale_risk_unacceptable,
            "m_m01_conflict_risk_unacceptable": view.m_m01_conflict_risk_unacceptable,
            "m_m01_reactivation_requires_review": view.m_m01_reactivation_requires_review,
            "m_m01_temporary_carry_not_stable_enough": view.m_m01_temporary_carry_not_stable_enough,
            "m_m01_no_safe_memory_basis": view.m_m01_no_safe_memory_basis,
            "m_m01_provenance_insufficient": view.m_m01_provenance_insufficient,
            "m_m01_lifecycle_underconstrained": view.m_m01_lifecycle_underconstrained,
            "scope": _collect_scope_markers(view)["m_minimal"],
        },
        "n_minimal": {
            "n_narrative_commitment_id": view.n_narrative_commitment_id,
            "n_commitment_status": view.n_commitment_status,
            "n_ambiguity_residue": view.n_ambiguity_residue,
            "n_contradiction_risk": view.n_contradiction_risk,
            "n_underconstrained": state.n_underconstrained,
            "n_safe_narrative_commitment_allowed": state.n_safe_narrative_commitment_allowed,
            "n_bounded_commitment_allowed": state.n_bounded_commitment_allowed,
            "n_no_safe_narrative_claim": state.n_no_safe_narrative_claim,
            "n_forbidden_shortcuts": view.n_forbidden_shortcuts,
            "n_restrictions": state.n_restrictions,
            "n_n01_admission_ready": view.n_n01_admission_ready,
            "n_n01_blockers": view.n_n01_blockers,
            "scope": _collect_scope_markers(view)["n_minimal"],
        },
        "s01_efference_copy": {
            "s01_latest_comparison_status": view.s01_latest_comparison_status,
            "s01_comparison_ready": view.s01_comparison_ready,
            "s01_unexpected_change_detected": view.s01_unexpected_change_detected,
            "s01_prediction_validity_ready": view.s01_prediction_validity_ready,
            "s01_comparison_blocked_by_contamination": view.s01_comparison_blocked_by_contamination,
            "s01_stale_prediction_detected": view.s01_stale_prediction_detected,
            "s01_pending_predictions_count": view.s01_pending_predictions_count,
            "s01_comparisons_count": view.s01_comparisons_count,
            "s01_require_comparison_consumer": view.s01_require_comparison_consumer,
            "s01_require_unexpected_change_consumer": view.s01_require_unexpected_change_consumer,
            "s01_require_prediction_validity_consumer": view.s01_require_prediction_validity_consumer,
        },
        "s02_prediction_boundary": {
            "s02_boundary_id": view.s02_boundary_id,
            "s02_active_boundary_status": view.s02_active_boundary_status,
            "s02_boundary_uncertain": view.s02_boundary_uncertain,
            "s02_insufficient_coverage": view.s02_insufficient_coverage,
            "s02_no_clean_seam_claim": view.s02_no_clean_seam_claim,
            "s02_controllability_estimate": view.s02_controllability_estimate,
            "s02_prediction_reliability_estimate": view.s02_prediction_reliability_estimate,
            "s02_external_dominance_estimate": view.s02_external_dominance_estimate,
            "s02_mixed_source_score": view.s02_mixed_source_score,
            "s02_boundary_confidence": view.s02_boundary_confidence,
            "s02_boundary_consumer_ready": view.s02_boundary_consumer_ready,
            "s02_controllability_consumer_ready": view.s02_controllability_consumer_ready,
            "s02_mixed_source_consumer_ready": view.s02_mixed_source_consumer_ready,
            "s02_forbidden_shortcuts": view.s02_forbidden_shortcuts,
            "s02_restrictions": view.s02_restrictions,
            "s02_require_boundary_consumer": view.s02_require_boundary_consumer,
            "s02_require_controllability_consumer": view.s02_require_controllability_consumer,
            "s02_require_mixed_source_consumer": view.s02_require_mixed_source_consumer,
            "scope": _collect_scope_markers(view)["s02"],
        },
        "s03_ownership_weighted_learning": {
            "s03_learning_id": view.s03_learning_id,
            "s03_latest_packet_id": view.s03_latest_packet_id,
            "s03_latest_update_class": view.s03_latest_update_class,
            "s03_latest_commit_class": view.s03_latest_commit_class,
            "s03_latest_ambiguity_class": view.s03_latest_ambiguity_class,
            "s03_freeze_or_defer_state": view.s03_freeze_or_defer_state,
            "s03_requested_revalidation": view.s03_requested_revalidation,
            "s03_self_update_weight": view.s03_self_update_weight,
            "s03_world_update_weight": view.s03_world_update_weight,
            "s03_observation_update_weight": view.s03_observation_update_weight,
            "s03_anomaly_update_weight": view.s03_anomaly_update_weight,
            "s03_learning_packet_consumer_ready": view.s03_learning_packet_consumer_ready,
            "s03_mixed_update_consumer_ready": view.s03_mixed_update_consumer_ready,
            "s03_freeze_obedience_consumer_ready": view.s03_freeze_obedience_consumer_ready,
            "s03_require_learning_packet_consumer": view.s03_require_learning_packet_consumer,
            "s03_require_mixed_update_consumer": view.s03_require_mixed_update_consumer,
            "s03_require_freeze_obedience_consumer": view.s03_require_freeze_obedience_consumer,
            "scope": _collect_scope_markers(view)["s03"],
        },
        "t01_semantic_field": {
            "t01_scene_id": view.t01_scene_id,
            "t01_scene_status": view.t01_scene_status,
            "t01_stability_state": view.t01_stability_state,
            "t01_preverbal_consumer_ready": view.t01_preverbal_consumer_ready,
            "t01_scene_comparison_ready": view.t01_scene_comparison_ready,
            "t01_no_clean_scene_commit": view.t01_no_clean_scene_commit,
            "t01_unresolved_slots_count": view.t01_unresolved_slots_count,
            "t01_forbidden_shortcuts": view.t01_forbidden_shortcuts,
            "t01_restrictions": state.t01_restrictions,
            "t01_require_preverbal_scene_consumer": state.t01_require_preverbal_scene_consumer,
            "t01_require_scene_comparison_consumer": view.t01_require_scene_comparison_consumer,
            "scope": _collect_scope_markers(view)["t01"],
        },
        "t02_relation_binding": {
            "t02_constrained_scene_id": view.t02_constrained_scene_id,
            "t02_scene_status": view.t02_scene_status,
            "t02_preverbal_constraint_consumer_ready": view.t02_preverbal_constraint_consumer_ready,
            "t02_no_clean_binding_commit": view.t02_no_clean_binding_commit,
            "t02_confirmed_bindings_count": view.t02_confirmed_bindings_count,
            "t02_provisional_bindings_count": view.t02_provisional_bindings_count,
            "t02_blocked_bindings_count": view.t02_blocked_bindings_count,
            "t02_conflicted_bindings_count": view.t02_conflicted_bindings_count,
            "t02_propagated_consequences_count": view.t02_propagated_consequences_count,
            "t02_blocked_or_conflicted_consequences_count": view.t02_blocked_or_conflicted_consequences_count,
            "t02_forbidden_shortcuts": view.t02_forbidden_shortcuts,
            "t02_require_constrained_scene_consumer": view.t02_require_constrained_scene_consumer,
            "t02_require_raw_vs_propagated_distinction": view.t02_require_raw_vs_propagated_distinction,
            "t02_raw_vs_propagated_distinct": view.t02_raw_vs_propagated_distinct,
            "scope": _collect_scope_markers(view)["t02"],
        },
        "t03_hypothesis_competition": {
            "t03_competition_id": view.t03_competition_id,
            "t03_convergence_status": view.t03_convergence_status,
            "t03_current_leader_hypothesis_id": view.t03_current_leader_hypothesis_id,
            "t03_provisional_frontrunner_hypothesis_id": view.t03_provisional_frontrunner_hypothesis_id,
            "t03_tied_competitor_count": view.t03_tied_competitor_count,
            "t03_blocked_hypothesis_count": view.t03_blocked_hypothesis_count,
            "t03_eliminated_hypothesis_count": view.t03_eliminated_hypothesis_count,
            "t03_reactivated_hypothesis_count": view.t03_reactivated_hypothesis_count,
            "t03_honest_nonconvergence": view.t03_honest_nonconvergence,
            "t03_bounded_plurality": view.t03_bounded_plurality,
            "t03_convergence_consumer_ready": view.t03_convergence_consumer_ready,
            "t03_frontier_consumer_ready": view.t03_frontier_consumer_ready,
            "t03_nonconvergence_preserved": view.t03_nonconvergence_preserved,
            "t03_forbidden_shortcuts": view.t03_forbidden_shortcuts,
            "t03_restrictions": view.t03_restrictions,
            "t03_publication_current_leader": view.t03_publication_current_leader,
            "t03_publication_competitive_neighborhood": view.t03_publication_competitive_neighborhood,
            "t03_publication_unresolved_conflicts": view.t03_publication_unresolved_conflicts,
            "t03_publication_open_slots": view.t03_publication_open_slots,
            "t03_publication_stability_status": view.t03_publication_stability_status,
            "t03_require_convergence_consumer": view.t03_require_convergence_consumer,
            "t03_require_frontier_consumer": view.t03_require_frontier_consumer,
            "t03_require_nonconvergence_preservation": view.t03_require_nonconvergence_preservation,
            "scope": _collect_scope_markers(view)["t03"],
        },
        "t04_attention_schema": {
            "t04_schema_id": view.t04_schema_id,
            "t04_focus_targets_count": view.t04_focus_targets_count,
            "t04_peripheral_targets_count": view.t04_peripheral_targets_count,
            "t04_attention_owner": view.t04_attention_owner,
            "t04_focus_mode": view.t04_focus_mode,
            "t04_control_estimate": view.t04_control_estimate,
            "t04_stability_estimate": view.t04_stability_estimate,
            "t04_redirect_cost": view.t04_redirect_cost,
            "t04_reportability_status": view.t04_reportability_status,
            "t04_focus_ownership_consumer_ready": view.t04_focus_ownership_consumer_ready,
            "t04_reportable_focus_consumer_ready": view.t04_reportable_focus_consumer_ready,
            "t04_peripheral_preservation_ready": view.t04_peripheral_preservation_ready,
            "t04_forbidden_shortcuts": view.t04_forbidden_shortcuts,
            "t04_restrictions": view.t04_restrictions,
            "t04_require_focus_ownership_consumer": view.t04_require_focus_ownership_consumer,
            "t04_require_reportable_focus_consumer": view.t04_require_reportable_focus_consumer,
            "t04_require_peripheral_preservation": view.t04_require_peripheral_preservation,
            "scope": _collect_scope_markers(view)["t04"],
        },
    }


def _collect_checkpoints(result: Any) -> dict[str, object]:
    mandatory = list(result.tick_graph.mandatory_checkpoint_ids)
    if result.subject_tick_result is None:
        return {
            "mandatory_checkpoint_ids": mandatory,
            "observed_checkpoint_results": [],
            "missing_mandatory_checkpoint_ids": mandatory,
            "checkpoint_coverage_complete": False,
            "blocked_checkpoint_ids": [],
            "enforced_detour_checkpoint_ids": [],
            "epistemic_admission_checkpoint": UNRESOLVED_TOKEN,
            "shared_runtime_domain_checkpoint": UNRESOLVED_TOKEN,
            "downstream_obedience_checkpoint": UNRESOLVED_TOKEN,
            "outcome_resolution_checkpoint": UNRESOLVED_TOKEN,
        }
    observed = []
    observed_ids = set()
    blocked = []
    detour = []
    epistemic_checkpoint = None
    shared_runtime_domain_checkpoint = None
    downstream_checkpoint = None
    outcome_checkpoint = None
    for checkpoint in result.subject_tick_result.state.execution_checkpoints:
        item = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "source_contract": checkpoint.source_contract,
            "status": checkpoint.status.value,
            "required_action": checkpoint.required_action,
            "applied_action": checkpoint.applied_action,
            "reason": checkpoint.reason,
        }
        observed.append(item)
        observed_ids.add(checkpoint.checkpoint_id)
        if checkpoint.status.value == "blocked":
            blocked.append(checkpoint.checkpoint_id)
        if checkpoint.status.value == "enforced_detour":
            detour.append(checkpoint.checkpoint_id)
        if checkpoint.checkpoint_id == "rt01.epistemic_admission_checkpoint":
            epistemic_checkpoint = item
        if checkpoint.checkpoint_id == "rt01.shared_runtime_domain_checkpoint":
            shared_runtime_domain_checkpoint = item
        if checkpoint.checkpoint_id == "rt01.downstream_obedience_checkpoint":
            downstream_checkpoint = item
        if checkpoint.checkpoint_id == "rt01.outcome_resolution_checkpoint":
            outcome_checkpoint = item
    missing = [checkpoint_id for checkpoint_id in mandatory if checkpoint_id not in observed_ids]
    return {
        "mandatory_checkpoint_ids": mandatory,
        "observed_checkpoint_results": observed,
        "missing_mandatory_checkpoint_ids": missing,
        "checkpoint_coverage_complete": len(missing) == 0,
        "blocked_checkpoint_ids": blocked,
        "enforced_detour_checkpoint_ids": detour,
        "epistemic_admission_checkpoint": epistemic_checkpoint or UNRESOLVED_TOKEN,
        "shared_runtime_domain_checkpoint": shared_runtime_domain_checkpoint or UNRESOLVED_TOKEN,
        "downstream_obedience_checkpoint": downstream_checkpoint or UNRESOLVED_TOKEN,
        "outcome_resolution_checkpoint": outcome_checkpoint or UNRESOLVED_TOKEN,
    }


def _collect_restrictions_and_shortcuts(view: Any, result: Any) -> dict[str, object]:
    state = None if result.subject_tick_result is None else result.subject_tick_result.state

    def _to_text_list(value: object) -> list[str] | object:
        if value is None:
            return UNRESOLVED_TOKEN
        if value == UNRESOLVED_TOKEN:
            return UNRESOLVED_TOKEN
        if isinstance(value, tuple):
            value = list(value)
        if isinstance(value, list):
            out: list[str] = []
            for item in value:
                if hasattr(item, "value"):
                    out.append(str(item.value))
                else:
                    out.append(str(item))
            return out
        return [str(value)]

    if state is None:
        gate_restrictions: list[str] = []
        epistemic_allowance_restrictions: object = UNRESOLVED_TOKEN
        regulation_gate_restrictions: object = UNRESOLVED_TOKEN
        t02_restrictions: object = UNRESOLVED_TOKEN
    else:
        gate_restrictions = [code.value for code in result.subject_tick_result.downstream_gate.restrictions]
        epistemic_allowance_restrictions = list(
            getattr(state, "epistemic_allowance_restrictions", ())
        )
        regulation_gate_restrictions = _to_text_list(
            getattr(view, "regulation_gate_restrictions", None)
        )
        if regulation_gate_restrictions == UNRESOLVED_TOKEN:
            regulation_gate_restrictions = _to_text_list(
                getattr(
                    getattr(
                        getattr(result.subject_tick_result, "viability_result", None),
                        "downstream_gate",
                        None,
                    ),
                    "restrictions",
                    None,
                )
            )
        t02_restrictions = _to_text_list(getattr(view, "t02_restrictions", None))
        if t02_restrictions == UNRESOLVED_TOKEN:
            t02_result = getattr(result.subject_tick_result, "t02_result", None)
            t02_restrictions = _to_text_list(
                None if t02_result is None else getattr(t02_result.gate, "restrictions", None)
            )
    return {
        "dispatch_restrictions": list(view.restrictions),
        "downstream_gate_restrictions": gate_restrictions,
        "epistemic_allowance_restrictions": epistemic_allowance_restrictions,
        "regulation_gate_restrictions": regulation_gate_restrictions,
        "t02_restrictions": t02_restrictions,
        "phase_restrictions": {
            "world_entry_w01": list(() if state is None else state.world_entry_w01_admission_restrictions),
            "s": list(() if state is None else state.s_restrictions),
            "a": list(() if state is None else state.a_restrictions),
            "m": list(() if state is None else state.m_restrictions),
            "n": list(() if state is None else state.n_restrictions),
            "t01": list(() if state is None else state.t01_restrictions),
            "s02": list(() if state is None else state.s02_restrictions),
            "t02": t02_restrictions,
            "t03": list(() if state is None else state.t03_restrictions),
            "t04": list(view.t04_restrictions or ()),
        },
        "phase_forbidden_shortcuts": {
            "s": list(() if state is None else state.s_forbidden_shortcuts),
            "a": list(() if state is None else state.a_forbidden_shortcuts),
            "m": list(() if state is None else state.m_forbidden_shortcuts),
            "n": list(() if state is None else state.n_forbidden_shortcuts),
            "t01": list(() if state is None else state.t01_forbidden_shortcuts),
            "s02": list(view.s02_forbidden_shortcuts or ()),
            "t02": list(view.t02_forbidden_shortcuts or ()),
            "t03": list(() if state is None else state.t03_forbidden_shortcuts),
            "t04": list(view.t04_forbidden_shortcuts or ()),
        },
        "requires_restrictions_read_flags": {
            "dispatch_contract_must_be_read": True,
            "downstream_obedience_requires_restrictions_read": (
                UNRESOLVED_TOKEN if state is None else bool(state.downstream_obedience_requires_restrictions_read)
            ),
            "subject_tick_gate_requires_restrictions_read": result.subject_tick_result is not None,
        },
    }


def _collect_uncertainty(view: Any, result: Any, runtime_domain_view: Any | None) -> dict[str, object]:
    if result.subject_tick_result is None:
        return {
            "abstain": UNRESOLVED_TOKEN,
            "abstain_reason": UNRESOLVED_TOKEN,
            "epistemic_should_abstain": UNRESOLVED_TOKEN,
            "epistemic_claim_strength": UNRESOLVED_TOKEN,
            "epistemic_allowance_reason": UNRESOLVED_TOKEN,
            "epistemic_unknown_reason": UNRESOLVED_TOKEN,
            "epistemic_conflict_reason": UNRESOLVED_TOKEN,
            "epistemic_abstain_reason": UNRESOLVED_TOKEN,
            "regulation_no_strong_override_claim": UNRESOLVED_TOKEN,
            "regulation_gate_accepted": UNRESOLVED_TOKEN,
            "regulation_pressure_level": UNRESOLVED_TOKEN,
            "regulation_escalation_stage": UNRESOLVED_TOKEN,
            "regulation_override_scope": UNRESOLVED_TOKEN,
            "downstream_obedience_status": UNRESOLVED_TOKEN,
            "downstream_obedience_fallback": UNRESOLVED_TOKEN,
            "gate_accepted": UNRESOLVED_TOKEN,
            "usability_class": UNRESOLVED_TOKEN,
            "uncertainty_markers": {},
            "no_safe_markers": {},
            "degraded_markers": {},
            "packet_snapshot_precedence_blocked": (
                UNRESOLVED_TOKEN if runtime_domain_view is None else runtime_domain_view.packet_snapshot_precedence_blocked
            ),
        }
    state = result.subject_tick_result.state
    return {
        "abstain": result.subject_tick_result.abstain,
        "abstain_reason": result.subject_tick_result.abstain_reason,
        "epistemic_should_abstain": state.epistemic_should_abstain,
        "epistemic_claim_strength": state.epistemic_claim_strength,
        "epistemic_allowance_reason": state.epistemic_allowance_reason,
        "epistemic_unknown_reason": state.epistemic_unknown_reason,
        "epistemic_conflict_reason": state.epistemic_conflict_reason,
        "epistemic_abstain_reason": state.epistemic_abstain_reason,
        "regulation_no_strong_override_claim": state.regulation_no_strong_override_claim,
        "regulation_gate_accepted": state.regulation_gate_accepted,
        "regulation_pressure_level": state.regulation_pressure_level,
        "regulation_escalation_stage": state.regulation_escalation_stage,
        "regulation_override_scope": state.regulation_override_scope,
        "downstream_obedience_status": state.downstream_obedience_status,
        "downstream_obedience_fallback": state.downstream_obedience_fallback,
        "gate_accepted": result.subject_tick_result.downstream_gate.accepted,
        "usability_class": result.subject_tick_result.downstream_gate.usability_class.value,
        "uncertainty_markers": {
            "s_underconstrained": state.s_underconstrained,
            "a_underconstrained": state.a_underconstrained,
            "m_underconstrained": state.m_underconstrained,
            "n_underconstrained": state.n_underconstrained,
            "n_ambiguity_residue": state.n_ambiguity_residue,
            "n_contradiction_risk": state.n_contradiction_risk,
            "t01_no_clean_scene_commit": state.t01_no_clean_scene_commit,
            "t01_unresolved_slots_count": state.t01_unresolved_slots_count,
            "s02_boundary_uncertain": state.s02_boundary_uncertain,
            "s02_insufficient_coverage": state.s02_insufficient_coverage,
            "s02_no_clean_seam_claim": state.s02_no_clean_seam_claim,
            "t03_honest_nonconvergence": state.t03_honest_nonconvergence,
            "t03_nonconvergence_preserved": state.t03_nonconvergence_preserved,
            "t03_publication_unresolved_conflicts": list(state.t03_publication_unresolved_conflicts),
            "t03_publication_open_slots": list(state.t03_publication_open_slots),
            "epistemic_should_abstain": state.epistemic_should_abstain,
            "epistemic_unknown": state.epistemic_unknown_reason is not None,
            "epistemic_conflict": state.epistemic_conflict_reason is not None,
            "epistemic_abstain": state.epistemic_abstain_reason is not None,
        },
        "no_safe_markers": {
            "s_no_safe_self_claim": state.s_no_safe_self_claim,
            "s_no_safe_world_claim": state.s_no_safe_world_claim,
            "a_no_safe_capability_claim": state.a_no_safe_capability_claim,
            "m_no_safe_memory_claim": state.m_no_safe_memory_claim,
            "n_no_safe_narrative_claim": state.n_no_safe_narrative_claim,
        },
        "degraded_markers": {
            "world_adapter_degraded": state.world_adapter_degraded,
            "world_entry_degraded": state.world_entry_degraded,
            "s_degraded": state.s_degraded,
            "a_degraded": state.a_degraded,
            "m_degraded": state.m_degraded,
            "n_degraded": state.n_degraded,
            "downstream_authority_degraded_restriction": (
                "downstream_authority_degraded"
                in [code.value for code in result.subject_tick_result.downstream_gate.restrictions]
            ),
        },
        "packet_snapshot_precedence_blocked": (
            UNRESOLVED_TOKEN if runtime_domain_view is None else runtime_domain_view.packet_snapshot_precedence_blocked
        ),
    }


def _collect_regulation_observability(
    *,
    regulation_surface: dict[str, object],
    checkpoints: dict[str, object],
    restrictions: dict[str, object],
    final_outcome: dict[str, object],
) -> dict[str, object]:
    shared_checkpoint = checkpoints.get("shared_runtime_domain_checkpoint", UNRESOLVED_TOKEN)
    shared_status: object = UNRESOLVED_TOKEN
    shared_action: object = UNRESOLVED_TOKEN
    shared_source_surface: object = UNRESOLVED_TOKEN
    shared_reason: object = UNRESOLVED_TOKEN
    shared_checkpoint_observed = isinstance(shared_checkpoint, dict)
    if shared_checkpoint_observed:
        shared_status = shared_checkpoint.get("status", UNRESOLVED_TOKEN)
        shared_action = shared_checkpoint.get("applied_action", UNRESOLVED_TOKEN)
        shared_source_surface = shared_checkpoint.get("source_contract", UNRESOLVED_TOKEN)
        shared_reason = shared_checkpoint.get("reason", UNRESOLVED_TOKEN)

    local_fields = (
        "regulation_pressure_level",
        "regulation_escalation_stage",
        "regulation_override_scope",
        "regulation_no_strong_override_claim",
        "regulation_gate_accepted",
        "regulation_source_state_ref",
    )
    local_surface_observed = any(
        regulation_surface.get(field_name, UNRESOLVED_TOKEN) not in {UNRESOLVED_TOKEN, None}
        for field_name in local_fields
    )
    if local_surface_observed and shared_checkpoint_observed:
        influence_source: object = "both"
    elif shared_checkpoint_observed:
        influence_source = "shared_runtime_domain_precedence"
    elif local_surface_observed:
        influence_source = "local_regulation_surface"
    else:
        influence_source = UNRESOLVED_TOKEN

    if shared_checkpoint_observed:
        path_consequence: object = {
            "shared_runtime_domain_checkpoint_status": shared_status,
            "shared_runtime_domain_checkpoint_applied_action": shared_action,
            "active_execution_mode": final_outcome.get("active_execution_mode", UNRESOLVED_TOKEN),
            "final_execution_outcome": final_outcome.get("final_execution_outcome", UNRESOLVED_TOKEN),
        }
    else:
        path_consequence = UNRESOLVED_TOKEN

    if shared_reason not in {None, "", UNRESOLVED_TOKEN}:
        causal_reason: object = shared_reason
    else:
        causal_reason = final_outcome.get("halt_reason", UNRESOLVED_TOKEN)
        if causal_reason in {None, ""}:
            causal_reason = UNRESOLVED_TOKEN

    regulation_gate_restrictions = restrictions.get("regulation_gate_restrictions", UNRESOLVED_TOKEN)
    if regulation_gate_restrictions == UNRESOLVED_TOKEN:
        restriction_source: object = UNRESOLVED_TOKEN
    elif isinstance(regulation_gate_restrictions, list) and regulation_gate_restrictions:
        restriction_source = "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions"
    elif shared_checkpoint_observed:
        restriction_source = "checkpoints.shared_runtime_domain_checkpoint.reason"
    else:
        restriction_source = "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions"

    return {
        "effective_regulation_shared_domain_source_surface": shared_source_surface,
        "effective_shared_runtime_domain_checkpoint_status": shared_status,
        "effective_shared_runtime_domain_checkpoint_applied_action": shared_action,
        "effective_regulation_path_consequence": path_consequence,
        "effective_regulation_causal_reason": causal_reason,
        "effective_regulation_influence_source": influence_source,
        "effective_regulation_restriction_source": restriction_source,
    }


def _contains_risk_markers(uncertainty: dict[str, object]) -> bool:
    uncertainty_markers = uncertainty.get("uncertainty_markers", {})
    no_safe_markers = uncertainty.get("no_safe_markers", {})
    degraded_markers = uncertainty.get("degraded_markers", {})
    for value in uncertainty_markers.values():
        if isinstance(value, bool) and value:
            return True
        if isinstance(value, list) and value:
            return True
    for value in no_safe_markers.values():
        if isinstance(value, bool) and value:
            return True
    for value in degraded_markers.values():
        if isinstance(value, bool) and value:
            return True
    return False


def _compute_verdicts(
    *,
    route_and_scope: dict[str, object],
    checkpoints: dict[str, object],
    uncertainty: dict[str, object],
    final_outcome: dict[str, object],
    input_summary: dict[str, object],
) -> dict[str, object]:
    verdicts: dict[str, object] = {}

    mechanistic_status = "PASS"
    mechanistic_reasons: list[str] = []
    if route_and_scope["accepted"] is False:
        mechanistic_status = "PARTIAL"
        mechanistic_reasons.append(
            "dispatch rejected pre-execution; legality evaluated but execution checkpoints absent"
        )
    elif checkpoints["checkpoint_coverage_complete"] is False:
        mechanistic_status = "FAIL"
        mechanistic_reasons.append("mandatory checkpoint coverage is incomplete")
    elif final_outcome["final_execution_outcome"] == "continue" and len(checkpoints["blocked_checkpoint_ids"]) > 0:
        mechanistic_status = "FAIL"
        mechanistic_reasons.append("blocked checkpoints conflict with continue outcome")
    elif checkpoints.get("epistemic_admission_checkpoint") == UNRESOLVED_TOKEN:
        mechanistic_status = "PARTIAL"
        mechanistic_reasons.append("epistemic admission checkpoint is not materialized as a typed execution row")
    elif route_and_scope["lawful_production_route"] is False:
        mechanistic_status = "PARTIAL"
        mechanistic_reasons.append("non-production route is coherent but not lawful production contour")
    verdicts["mechanistic_integrity"] = {
        "status": mechanistic_status,
        "reasons": mechanistic_reasons or ["route legality and checkpoint coherence are bounded"],
        "evidence_field_paths": [
            "route_and_scope.accepted",
            "route_and_scope.lawful_production_route",
            "checkpoints.missing_mandatory_checkpoint_ids",
            "checkpoints.epistemic_admission_checkpoint",
            "final_outcome.final_execution_outcome",
        ],
    }

    claim_status = "PASS"
    claim_reasons: list[str] = []
    if route_and_scope["accepted"] is False:
        claim_status = "UNRESOLVED"
        claim_reasons.append("subject_tick state is absent due to pre-execution dispatch rejection")
    else:
        risky = _contains_risk_markers(uncertainty)
        outcome = str(final_outcome["final_execution_outcome"])
        epistemic_should_abstain = uncertainty.get("epistemic_should_abstain") is True
        epistemic_unknown = uncertainty.get("epistemic_unknown_reason") not in {None, "", UNRESOLVED_TOKEN}
        epistemic_conflict = uncertainty.get("epistemic_conflict_reason") not in {None, "", UNRESOLVED_TOKEN}
        if outcome == "continue" and (epistemic_should_abstain or epistemic_unknown or epistemic_conflict):
            claim_status = "FAIL"
            claim_reasons.append("continue outcome conflicts with epistemic abstain/unknown/conflict admission surface")
        elif risky and outcome == "continue":
            claim_status = "FAIL"
            claim_reasons.append("continue outcome is emitted while uncertainty/no-safe/degraded markers remain active")
        elif risky:
            claim_reasons.append("uncertainty/no-safe markers are preserved with bounded detour/halt outcome")
        else:
            claim_reasons.append("no unresolved/no-safe marker was laundered into stronger claim")
    verdicts["claim_honesty"] = {
        "status": claim_status,
        "reasons": claim_reasons,
        "evidence_field_paths": [
            "uncertainty_and_fallbacks.abstain",
            "uncertainty_and_fallbacks.epistemic_should_abstain",
            "uncertainty_and_fallbacks.epistemic_unknown_reason",
            "uncertainty_and_fallbacks.epistemic_conflict_reason",
            "uncertainty_and_fallbacks.uncertainty_markers",
            "uncertainty_and_fallbacks.no_safe_markers",
            "final_outcome.final_execution_outcome",
        ],
    }

    path_status = "PASS"
    path_reasons: list[str] = []
    if route_and_scope["accepted"] is False:
        path_status = "UNRESOLVED"
        path_reasons.append("dispatch rejected pre-execution; no path-affecting execution evidence")
    else:
        context = input_summary.get("context_flags", {})
        trigger_keys = [
            key
            for key, value in context.items()
            if (
                (key.startswith("require_") and value is True)
                or (key.startswith("disable_") and value is True)
                or (key in {"t02_assembly_mode", "t03_competition_mode"} and bool(value))
            )
        ]
        has_path_evidence = bool(checkpoints["enforced_detour_checkpoint_ids"]) or bool(
            checkpoints["blocked_checkpoint_ids"]
        )
        if trigger_keys:
            if has_path_evidence:
                path_reasons.append("triggered requirement/ablation flags produced explicit detour/block checkpoints")
            else:
                path_status = "FAIL"
                path_reasons.append("triggered requirement/ablation flags did not produce path-affecting evidence")
        else:
            path_status = "PARTIAL"
            path_reasons.append("single-turn artifact has no explicit trigger; sensitivity cannot be fully proven")
    verdicts["path_affecting_sensitivity"] = {
        "status": path_status,
        "reasons": path_reasons,
        "evidence_field_paths": [
            "input_summary.context_flags",
            "checkpoints.enforced_detour_checkpoint_ids",
            "checkpoints.blocked_checkpoint_ids",
        ],
    }

    statuses = [
        verdicts["mechanistic_integrity"]["status"],
        verdicts["claim_honesty"]["status"],
        verdicts["path_affecting_sensitivity"]["status"],
    ]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "UNRESOLVED" in statuses:
        overall = "UNRESOLVED"
    elif "PARTIAL" in statuses:
        overall = "PARTIAL"
    else:
        overall = "PASS"
    verdicts["overall"] = {
        "status": overall,
        "reasons": ["aggregated from load-bearing verdict statuses without laundering"],
        "evidence_field_paths": [
            "verdicts.mechanistic_integrity.status",
            "verdicts.claim_honesty.status",
            "verdicts.path_affecting_sensitivity.status",
        ],
    }
    return verdicts


def build_turn_audit_artifact(
    *,
    result: Any,
    seam_contract_path: str = DEFAULT_SEAM_CONTRACT_PATH,
) -> dict[str, object]:
    request = result.request
    view = derive_runtime_dispatch_contract_view(result)
    unresolved: list[dict[str, object]] = []

    if result.subject_tick_result is None:
        unresolved.append(
            _unresolved_entry(
                code="PRE_EXECUTION_DISPATCH_REJECTION",
                message="dispatch rejected before subject_tick execution; phase-level artifact is structurally incomplete",
                blocking_surface="runtime_topology.evaluate_runtime_dispatch_decision",
                severity="high",
                impacted_sections=[
                    "phase_surfaces",
                    "checkpoints",
                    "uncertainty_and_fallbacks",
                    "final_outcome",
                    "verdicts",
                ],
                requires_non_v1_extension=False,
            )
        )

    runtime_domain_view = None
    if result.persist_transition is not None and result.persist_transition.accepted:
        runtime_domain_view = derive_subject_tick_runtime_domain_contract_view(
            result.persist_transition.state
        )
    else:
        unresolved.append(
            _unresolved_entry(
                code="RUNTIME_DOMAIN_VIEW_NOT_MATERIALIZED_IN_ARTIFACT_RUN",
                message="runtime domain contract view is unavailable without accepted persistence transition in the same run",
                blocking_surface="subject_tick.persist_subject_tick_result_via_f01",
                severity="low",
                impacted_sections=["final_outcome", "uncertainty_and_fallbacks"],
                requires_non_v1_extension=False,
            )
        )

    artifact_metadata = {
        "artifact_version": ARTIFACT_VERSION,
        "seam_phase": SEAM_PHASE,
        "seam_contract_path": seam_contract_path,
        "bundle_id": result.bundle.bundle_id,
        "contour_id": result.bundle.contour_id,
        "graph_id": result.tick_graph.graph_id,
        "runtime_entry": result.bundle.runtime_entry,
        "execution_spine_phase": result.bundle.execution_spine_phase,
        "dispatch_lineage": list(result.dispatch_lineage),
        "source_of_truth_surfaces": list(result.tick_graph.source_of_truth_surfaces),
        "mandatory_checkpoint_ids": list(result.tick_graph.mandatory_checkpoint_ids),
        "subject_tick_present": result.subject_tick_result is not None,
        "persist_transition_present": result.persist_transition is not None,
        "transition_id_requested": request.transition_id,
        "requested_at": request.requested_at,
    }

    context_flags = {}
    for flag in CONTEXT_BOOL_FLAGS:
        context_flags[flag] = None if request.context is None else bool(getattr(request.context, flag))
    for flag in CONTEXT_VALUE_FLAGS:
        context_flags[flag] = None if request.context is None else getattr(request.context, flag)

    input_summary = {
        "tick_input": {
            "case_id": request.tick_input.case_id,
            "energy": request.tick_input.energy,
            "cognitive": request.tick_input.cognitive,
            "safety": request.tick_input.safety,
            "unresolved_preference": request.tick_input.unresolved_preference,
        },
        "route_class_requested": request.route_class.value,
        "allow_helper_route": request.allow_helper_route,
        "allow_test_only_route": request.allow_test_only_route,
        "allow_non_production_consumer_opt_in": request.allow_non_production_consumer_opt_in,
        "persist_via_f01_requested": request.persist_via_f01,
        "context_flags": context_flags,
    }

    route_and_scope = {
        "accepted": view.accepted,
        "lawful_production_route": view.lawful_production_route,
        "route_class": view.route_class,
        "route_binding_consequence": view.route_binding_consequence,
        "decision_restrictions": list(view.restrictions),
        "decision_reason": view.reason,
        "production_consumer_ready": view.production_consumer_ready,
        "runtime_order": list(result.tick_graph.runtime_order),
        "scope_markers": _collect_scope_markers(view),
    }

    phase_surfaces = _collect_phase_surfaces(view, result.subject_tick_result)
    checkpoints = _collect_checkpoints(result)
    restrictions_and_forbidden_shortcuts = _collect_restrictions_and_shortcuts(view, result)
    uncertainty_and_fallbacks = _collect_uncertainty(view, result, runtime_domain_view)

    if restrictions_and_forbidden_shortcuts.get("t02_restrictions", UNRESOLVED_TOKEN) == UNRESOLVED_TOKEN:
        unresolved.append(
            _unresolved_entry(
                code="T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD",
                message="t02 restrictions are not exposed as a stable dedicated field in current contract projection",
                blocking_surface="runtime_topology.downstream_contract.RuntimeDispatchContractView",
                severity="medium",
                impacted_sections=["restrictions_and_forbidden_shortcuts", "phase_surfaces"],
                requires_non_v1_extension=False,
            )
        )
    if (
        restrictions_and_forbidden_shortcuts.get("regulation_gate_restrictions", UNRESOLVED_TOKEN)
        == UNRESOLVED_TOKEN
    ):
        unresolved.append(
            _unresolved_entry(
                code="REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD",
                message="regulation gate restrictions are not exposed as a dedicated typed field in current RT01 contract projection",
                blocking_surface="runtime_topology.downstream_contract.RuntimeDispatchContractView",
                severity="medium",
                impacted_sections=["restrictions_and_forbidden_shortcuts", "phase_surfaces", "uncertainty_and_fallbacks"],
                requires_non_v1_extension=False,
            )
        )

    if route_and_scope["accepted"] and checkpoints["missing_mandatory_checkpoint_ids"]:
        unresolved.append(
            _unresolved_entry(
                code="MANDATORY_CHECKPOINT_COVERAGE_INCOMPLETE",
                message="one or more mandatory runtime checkpoints are missing from observed execution",
                blocking_surface="subject_tick.state.execution_checkpoints",
                severity="high",
                impacted_sections=["checkpoints", "verdicts", "final_outcome"],
                requires_non_v1_extension=False,
            )
        )

    epistemics_surface = phase_surfaces.get("epistemics")
    if route_and_scope["accepted"] and isinstance(epistemics_surface, dict):
        required_epistemic_fields = (
            "epistemic_unit_id",
            "epistemic_status",
            "epistemic_confidence",
            "epistemic_source_class",
            "epistemic_modality",
            "epistemic_claim_strength",
            "epistemic_should_abstain",
        )
        missing_epistemic_fields = [
            field_name
            for field_name in required_epistemic_fields
            if epistemics_surface.get(field_name, UNRESOLVED_TOKEN) == UNRESOLVED_TOKEN
        ]
        if missing_epistemic_fields:
            unresolved.append(
                _unresolved_entry(
                    code="EPISTEMIC_RT01_SURFACES_NOT_FULLY_MATERIALIZED",
                    message=(
                        "one or more required epistemic RT01 fields are unresolved: "
                        + ", ".join(missing_epistemic_fields)
                    ),
                    blocking_surface="subject_tick.state.epistemic_*",
                    severity="medium",
                    impacted_sections=["phase_surfaces", "uncertainty_and_fallbacks", "verdicts"],
                    requires_non_v1_extension=False,
                )
            )

    if result.subject_tick_result is None:
        final_outcome = {
            "final_execution_outcome": UNRESOLVED_TOKEN,
            "execution_stance": UNRESOLVED_TOKEN,
            "active_execution_mode": UNRESOLVED_TOKEN,
            "repair_needed": UNRESOLVED_TOKEN,
            "revalidation_needed": UNRESOLVED_TOKEN,
            "halt_reason": UNRESOLVED_TOKEN,
            "abstain": UNRESOLVED_TOKEN,
            "abstain_reason": UNRESOLVED_TOKEN,
            "downstream_gate": UNRESOLVED_TOKEN,
            "dispatch_contract_final_execution_outcome": (
                UNRESOLVED_TOKEN if view.final_execution_outcome is None else view.final_execution_outcome
            ),
            "runtime_domain_recommended_outcome": (
                UNRESOLVED_TOKEN if runtime_domain_view is None else runtime_domain_view.recommended_outcome
            ),
            "runtime_domain_reason": (
                UNRESOLVED_TOKEN if runtime_domain_view is None else runtime_domain_view.reason
            ),
            "persist_transition_accepted": (
                None if result.persist_transition is None else result.persist_transition.accepted
            ),
        }
    else:
        gate = result.subject_tick_result.downstream_gate
        state = result.subject_tick_result.state
        final_outcome = {
            "final_execution_outcome": state.final_execution_outcome,
            "execution_stance": state.execution_stance,
            "active_execution_mode": state.active_execution_mode,
            "repair_needed": state.repair_needed,
            "revalidation_needed": state.revalidation_needed,
            "halt_reason": state.halt_reason,
            "abstain": result.subject_tick_result.abstain,
            "abstain_reason": result.subject_tick_result.abstain_reason,
            "downstream_gate": {
                "accepted": gate.accepted,
                "usability_class": gate.usability_class,
                "restrictions": list(gate.restrictions),
                "reason": gate.reason,
                "state_ref": gate.state_ref,
            },
            "dispatch_contract_final_execution_outcome": view.final_execution_outcome,
            "runtime_domain_recommended_outcome": (
                UNRESOLVED_TOKEN if runtime_domain_view is None else runtime_domain_view.recommended_outcome
            ),
            "runtime_domain_reason": (
                UNRESOLVED_TOKEN if runtime_domain_view is None else runtime_domain_view.reason
            ),
            "persist_transition_accepted": (
                None if result.persist_transition is None else result.persist_transition.accepted
            ),
        }

    regulation_surface = phase_surfaces.get("regulation")
    if isinstance(regulation_surface, dict):
        regulation_surface.update(
            _collect_regulation_observability(
                regulation_surface=regulation_surface,
                checkpoints=checkpoints,
                restrictions=restrictions_and_forbidden_shortcuts,
                final_outcome=final_outcome,
            )
        )

    verdicts = _compute_verdicts(
        route_and_scope=route_and_scope,
        checkpoints=checkpoints,
        uncertainty=uncertainty_and_fallbacks,
        final_outcome=final_outcome,
        input_summary=input_summary,
    )

    artifact = {
        "artifact_metadata": artifact_metadata,
        "input_summary": input_summary,
        "route_and_scope": route_and_scope,
        "phase_surfaces": phase_surfaces,
        "checkpoints": checkpoints,
        "restrictions_and_forbidden_shortcuts": restrictions_and_forbidden_shortcuts,
        "uncertainty_and_fallbacks": uncertainty_and_fallbacks,
        "final_outcome": final_outcome,
        "verdicts": verdicts,
        "unresolved": unresolved,
    }
    return _normalize(artifact)


def _coerce_route_class(route_class: RuntimeRouteClass | str) -> RuntimeRouteClass:
    if isinstance(route_class, RuntimeRouteClass):
        return route_class
    return RuntimeRouteClass(route_class)


def _parse_bool_token(value: str) -> bool:
    token = value.strip().lower()
    if token in {"1", "true", "yes", "y", "on"}:
        return True
    if token in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"invalid boolean token: {value!r}")


def _build_context_from_flags(context_flags: dict[str, object] | None) -> SubjectTickContext | None:
    if not context_flags:
        return None
    kwargs: dict[str, object] = {}
    for key, value in context_flags.items():
        if key in CONTEXT_BOOL_FLAGS:
            kwargs[key] = bool(value)
            continue
        if key in CONTEXT_VALUE_FLAGS:
            kwargs[key] = value
            continue
        raise ValueError(f"unsupported context flag for v1 collector: {key}")
    return SubjectTickContext(**kwargs)


def collect_turn_audit_artifact(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool,
    context_flags: dict[str, object] | None = None,
    route_class: RuntimeRouteClass | str = RuntimeRouteClass.PRODUCTION_CONTOUR,
    allow_helper_route: bool = False,
    allow_test_only_route: bool = False,
    allow_non_production_consumer_opt_in: bool = False,
    persist_via_f01: bool = False,
    runtime_state: object | None = None,
    transition_id: str | None = None,
    requested_at: str | None = None,
    cause_chain: tuple[str, ...] = ("turn-audit-collector",),
    seam_contract_path: str = DEFAULT_SEAM_CONTRACT_PATH,
) -> dict[str, object]:
    tick_input = SubjectTickInput(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
    )
    context = _build_context_from_flags(context_flags)
    route = _coerce_route_class(route_class)
    if (
        route == RuntimeRouteClass.PRODUCTION_CONTOUR
        and not allow_helper_route
        and not allow_test_only_route
        and not allow_non_production_consumer_opt_in
    ):
        result = dispatch_rt01_production_tick(
            tick_input=tick_input,
            context=context,
            persist_via_f01=persist_via_f01,
            runtime_state=runtime_state,
            transition_id=transition_id,
            requested_at=requested_at,
            cause_chain=cause_chain,
        )
    else:
        result = dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=tick_input,
                context=context,
                route_class=route,
                allow_helper_route=allow_helper_route,
                allow_test_only_route=allow_test_only_route,
                allow_non_production_consumer_opt_in=allow_non_production_consumer_opt_in,
                persist_via_f01=persist_via_f01,
                runtime_state=runtime_state,
                transition_id=transition_id,
                requested_at=requested_at,
                cause_chain=cause_chain,
            )
        )
    return build_turn_audit_artifact(result=result, seam_contract_path=seam_contract_path)


def _default_output_path(case_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in case_id)
    return Path("artifacts") / "turn_audit" / f"{safe}.turn_audit.v1.json"


def write_turn_audit_artifact(
    *,
    artifact: dict[str, object],
    output_path: str | Path | None = None,
) -> Path:
    path = Path(output_path) if output_path is not None else _default_output_path(str(artifact["input_summary"]["tick_input"]["case_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, ensure_ascii=True)
    path.write_text(f"{payload}\n", encoding="utf-8")
    return path


def collect_turn_audit_artifact_to_disk(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool,
    context_flags: dict[str, object] | None = None,
    output_path: str | Path | None = None,
    route_class: RuntimeRouteClass | str = RuntimeRouteClass.PRODUCTION_CONTOUR,
    allow_helper_route: bool = False,
    allow_test_only_route: bool = False,
    allow_non_production_consumer_opt_in: bool = False,
    persist_via_f01: bool = False,
    seam_contract_path: str = DEFAULT_SEAM_CONTRACT_PATH,
) -> tuple[Path, dict[str, object]]:
    artifact = collect_turn_audit_artifact(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
        context_flags=context_flags,
        route_class=route_class,
        allow_helper_route=allow_helper_route,
        allow_test_only_route=allow_test_only_route,
        allow_non_production_consumer_opt_in=allow_non_production_consumer_opt_in,
        persist_via_f01=persist_via_f01,
        seam_contract_path=seam_contract_path,
    )
    path = write_turn_audit_artifact(artifact=artifact, output_path=output_path)
    return path, artifact


def _parse_context_values(raw_items: list[str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for raw in raw_items:
        if "=" not in raw:
            raise ValueError(f"context value must use KEY=VALUE form: {raw!r}")
        key, value = raw.split("=", 1)
        key = key.strip()
        if key not in CONTEXT_VALUE_FLAGS:
            raise ValueError(f"unsupported context value flag: {key}")
        value = value.strip()
        out[key] = None if value.lower() in {"", "none", "null"} else value
    return out


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turn Audit Collector MVP (RT01, JSON artifact v1)")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--energy", type=float, required=True)
    parser.add_argument("--cognitive", type=float, required=True)
    parser.add_argument("--safety", type=float, required=True)
    parser.add_argument(
        "--unresolved-preference",
        required=True,
        choices=("true", "false"),
        help="whether unresolved preference is enabled for the turn input",
    )
    parser.add_argument(
        "--route-class",
        default=RuntimeRouteClass.PRODUCTION_CONTOUR.value,
        choices=tuple(item.value for item in RuntimeRouteClass),
    )
    parser.add_argument("--allow-helper-route", action="store_true")
    parser.add_argument("--allow-test-only-route", action="store_true")
    parser.add_argument("--allow-non-production-consumer-opt-in", action="store_true")
    parser.add_argument("--persist-via-f01", action="store_true")
    parser.add_argument("--transition-id")
    parser.add_argument("--requested-at")
    parser.add_argument("--context-bool", action="append", default=[], choices=CONTEXT_BOOL_FLAGS)
    parser.add_argument(
        "--context-value",
        action="append",
        default=[],
        help="context value in KEY=VALUE form (supported keys: t02_assembly_mode, t03_competition_mode)",
    )
    parser.add_argument("--output", dest="output_path")
    parser.add_argument("--seam-contract-path", default=DEFAULT_SEAM_CONTRACT_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    context_flags: dict[str, object] = {}
    for key in args.context_bool:
        context_flags[key] = True
    context_flags.update(_parse_context_values(args.context_value))
    context_flags_or_none = context_flags if context_flags else None

    artifact_path, artifact = collect_turn_audit_artifact_to_disk(
        case_id=args.case_id,
        energy=args.energy,
        cognitive=args.cognitive,
        safety=args.safety,
        unresolved_preference=_parse_bool_token(args.unresolved_preference),
        context_flags=context_flags_or_none,
        output_path=args.output_path,
        route_class=args.route_class,
        allow_helper_route=args.allow_helper_route,
        allow_test_only_route=args.allow_test_only_route,
        allow_non_production_consumer_opt_in=args.allow_non_production_consumer_opt_in,
        persist_via_f01=args.persist_via_f01,
        seam_contract_path=args.seam_contract_path,
    )

    verdicts = artifact["verdicts"]
    print(f"output_path={artifact_path}")
    print(f"route_class={artifact['route_and_scope']['route_class']}")
    print(f"final_outcome={artifact['final_outcome']['final_execution_outcome']}")
    print(
        "verdicts="
        f"mechanistic_integrity:{verdicts['mechanistic_integrity']['status']},"
        f"claim_honesty:{verdicts['claim_honesty']['status']},"
        f"path_affecting_sensitivity:{verdicts['path_affecting_sensitivity']['status']},"
        f"overall:{verdicts['overall']['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
