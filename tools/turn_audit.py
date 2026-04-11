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
from substrate.runtime_topology.models import (
    RuntimeEpistemicCaseInput,
    RuntimeRegulationSharedDomainInput,
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

CAUSE_FAMILY_SUBJECT_INTERNAL = "subject_internal"
CAUSE_FAMILY_EPISTEMIC_CONSTRAINT = "epistemic_constraint"
CAUSE_FAMILY_SHARED_RUNTIME_REGULATION = "shared_runtime_regulation"
CAUSE_FAMILY_LOCAL_REGULATION_CONSTRAINT = "local_regulation_constraint"
CAUSE_FAMILY_OBSERVABILITY_ONLY = "observability_only_difference"
CAUSE_FAMILY_HARNESS_INFERENCE_ONLY = "harness_inference_only"
CAUSE_FAMILY_MIXED = "mixed"
CAUSE_FAMILY_UNRESOLVED = "unresolved"

PATH_AFFECTING_CHECKPOINT_STATUSES = {"blocked", "enforced_detour"}
PATH_AFFECTING_OUTCOMES = {"repair", "revalidate", "halt"}


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


def _is_unresolved_like(value: Any) -> bool:
    return value in {None, "", UNRESOLVED_TOKEN}


def _nonempty_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _summarize_epistemic_case_input(raw: Any) -> dict[str, object] | None:
    if raw is None:
        return None
    prior_units = getattr(raw, "prior_units", None)
    prior_units_count: object = UNRESOLVED_TOKEN
    if isinstance(prior_units, tuple):
        prior_units_count = len(prior_units)
    return {
        "content": getattr(raw, "content", None),
        "source_id": getattr(raw, "source_id", None),
        "source_class": getattr(raw, "source_class", None),
        "modality": getattr(raw, "modality", None),
        "confidence_hint": getattr(raw, "confidence_hint", None),
        "support_note": getattr(raw, "support_note", None),
        "contestation_note": getattr(raw, "contestation_note", None),
        "claim_key": getattr(raw, "claim_key", None),
        "claim_polarity": getattr(raw, "claim_polarity", None),
        "require_observation": getattr(raw, "require_observation", None),
        "prior_units_count": prior_units_count,
    }


def _summarize_regulation_shared_domain_input(raw: Any) -> dict[str, object] | None:
    if raw is None:
        return None
    return {
        "pressure_level": getattr(raw, "pressure_level", None),
        "escalation_stage": getattr(raw, "escalation_stage", None),
        "override_scope": getattr(raw, "override_scope", None),
        "no_strong_override_claim": getattr(raw, "no_strong_override_claim", None),
        "gate_accepted": getattr(raw, "gate_accepted", None),
        "source_state_ref": getattr(raw, "source_state_ref", None),
    }


def _build_trigger_inventory(
    *,
    input_summary: dict[str, object],
    checkpoints: dict[str, object],
) -> list[dict[str, object]]:
    trigger_rows: list[dict[str, object]] = []
    context = input_summary.get("context_flags", {})
    if isinstance(context, dict):
        for key, value in sorted(context.items()):
            active = (
                (key.startswith("require_") and value is True)
                or (key.startswith("disable_") and value is True)
                or (key in {"t02_assembly_mode", "t03_competition_mode"} and not _is_unresolved_like(value))
            )
            if active:
                trigger_rows.append(
                    {
                        "trigger_source": f"input_summary.context_flags.{key}",
                        "trigger_class": "context_flag",
                        "active": True,
                        "value": value,
                    }
                )

    epistemic_input = input_summary.get("epistemic_case_input")
    if isinstance(epistemic_input, dict):
        require_observation = epistemic_input.get("require_observation", UNRESOLVED_TOKEN)
        if require_observation is True:
            trigger_rows.append(
                {
                    "trigger_source": "input_summary.epistemic_case_input.require_observation",
                    "trigger_class": "epistemic_input_pressure",
                    "active": True,
                    "value": True,
                }
            )
        prior_units_count = epistemic_input.get("prior_units_count", UNRESOLVED_TOKEN)
        if isinstance(prior_units_count, int) and prior_units_count > 0:
            trigger_rows.append(
                {
                    "trigger_source": "input_summary.epistemic_case_input.prior_units_count",
                    "trigger_class": "epistemic_input_pressure",
                    "active": True,
                    "value": prior_units_count,
                }
            )

    regulation_input = input_summary.get("regulation_shared_domain_input")
    if isinstance(regulation_input, dict):
        for field_name in (
            "pressure_level",
            "escalation_stage",
            "override_scope",
            "no_strong_override_claim",
            "gate_accepted",
        ):
            value = regulation_input.get(field_name, UNRESOLVED_TOKEN)
            active = not _is_unresolved_like(value)
            if active:
                trigger_rows.append(
                    {
                        "trigger_source": f"input_summary.regulation_shared_domain_input.{field_name}",
                        "trigger_class": "regulation_input_pressure",
                        "active": True,
                        "value": value,
                    }
                )

    checkpoint_rows = checkpoints.get("observed_checkpoint_results", [])
    if isinstance(checkpoint_rows, list):
        for row in checkpoint_rows:
            if not isinstance(row, dict):
                continue
            status = row.get("status", UNRESOLVED_TOKEN)
            checkpoint_id = row.get("checkpoint_id", UNRESOLVED_TOKEN)
            if status in PATH_AFFECTING_CHECKPOINT_STATUSES:
                trigger_rows.append(
                    {
                        "trigger_source": f"checkpoints.{checkpoint_id}",
                        "trigger_class": "causal_checkpoint",
                        "active": True,
                        "value": status,
                    }
                )
    return trigger_rows


def _append_causal_entry(
    *,
    entries: list[dict[str, object]],
    event_type: str,
    event_ref: str,
    cause_family: str,
    cause_source: str,
    load_bearing: bool,
    confidence: float,
    evidence_field_paths: list[str],
    competing_causes: list[str] | None = None,
    observability_gap_candidate: bool = False,
) -> None:
    entries.append(
        {
            "event_type": event_type,
            "event_ref": event_ref,
            "cause_family": cause_family,
            "cause_source": cause_source,
            "load_bearing": load_bearing,
            "confidence": confidence,
            "evidence_field_paths": evidence_field_paths,
            "competing_causes": [] if competing_causes is None else competing_causes,
            "observability_gap_candidate": observability_gap_candidate,
        }
    )


def _regulation_observability_gap_candidate(
    *,
    regulation_surface: dict[str, object],
    restrictions: dict[str, object],
    consequence_is_path_affecting: bool,
) -> bool:
    if not consequence_is_path_affecting:
        return False
    influence = regulation_surface.get("effective_regulation_influence_source", UNRESOLVED_TOKEN)
    consequence = regulation_surface.get("effective_regulation_path_consequence", UNRESOLVED_TOKEN)
    reason = regulation_surface.get("effective_regulation_causal_reason", UNRESOLVED_TOKEN)
    regulation_gate_restrictions = restrictions.get("regulation_gate_restrictions", UNRESOLVED_TOKEN)
    if influence == UNRESOLVED_TOKEN:
        return True
    if consequence == UNRESOLVED_TOKEN:
        return True
    if reason == UNRESOLVED_TOKEN and regulation_gate_restrictions == UNRESOLVED_TOKEN:
        return True
    return False


def _cause_source_covered_by_evidence(cause_source: str, evidence_field_paths: list[str]) -> bool:
    if not evidence_field_paths:
        return False
    if cause_source == "uncertainty_and_fallbacks + phase_surfaces.regulation":
        return (
            any(path.startswith("uncertainty_and_fallbacks.") for path in evidence_field_paths)
            and any(path.startswith("phase_surfaces.regulation.") for path in evidence_field_paths)
        )
    if cause_source == "phase_surfaces.regulation.regulation_*":
        return any(path.startswith("phase_surfaces.regulation.regulation_") for path in evidence_field_paths)
    if cause_source.endswith(".*"):
        prefix = cause_source[:-1]
        return any(path.startswith(prefix) for path in evidence_field_paths)
    if cause_source.endswith("*"):
        prefix = cause_source[:-1]
        return any(path.startswith(prefix) for path in evidence_field_paths)
    if "/" in cause_source:
        parts = [part for part in cause_source.split("/") if part]
        return all(
            any(path.startswith(part) for path in evidence_field_paths)
            for part in parts
        )
    if cause_source in evidence_field_paths:
        return True
    return any(path.startswith(cause_source + ".") for path in evidence_field_paths)


def _classify_shared_regulation_cause(
    *,
    regulation_surface: dict[str, object],
    restrictions: dict[str, object],
) -> tuple[str, str, list[str], bool]:
    influence_source = regulation_surface.get("effective_regulation_influence_source", UNRESOLVED_TOKEN)
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
    regulation_gate_restrictions = restrictions.get("regulation_gate_restrictions", UNRESOLVED_TOKEN)
    regulation_restrictions_missing = regulation_gate_restrictions == UNRESOLVED_TOKEN

    if influence_source == "both":
        return (
            CAUSE_FAMILY_MIXED,
            "phase_surfaces.regulation.effective_regulation_influence_source",
            [CAUSE_FAMILY_LOCAL_REGULATION_CONSTRAINT, CAUSE_FAMILY_SHARED_RUNTIME_REGULATION],
            regulation_restrictions_missing,
        )
    if influence_source == "shared_runtime_domain_precedence":
        return (
            CAUSE_FAMILY_SHARED_RUNTIME_REGULATION,
            "phase_surfaces.regulation.effective_regulation_influence_source",
            [],
            regulation_restrictions_missing and not local_surface_observed,
        )
    if influence_source == "local_regulation_surface":
        return (
            CAUSE_FAMILY_LOCAL_REGULATION_CONSTRAINT,
            "phase_surfaces.regulation.effective_regulation_influence_source",
            [],
            regulation_restrictions_missing,
        )
    if local_surface_observed:
        return (
            CAUSE_FAMILY_LOCAL_REGULATION_CONSTRAINT,
            "phase_surfaces.regulation.regulation_*",
            [CAUSE_FAMILY_SHARED_RUNTIME_REGULATION],
            regulation_restrictions_missing,
        )
    return (
        CAUSE_FAMILY_UNRESOLVED,
        "phase_surfaces.regulation.effective_regulation_influence_source",
        [CAUSE_FAMILY_SHARED_RUNTIME_REGULATION],
        True,
    )


def _collect_causal_trace(
    *,
    route_and_scope: dict[str, object],
    phase_surfaces: dict[str, object],
    checkpoints: dict[str, object],
    restrictions: dict[str, object],
    uncertainty: dict[str, object],
    final_outcome: dict[str, object],
    input_summary: dict[str, object],
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    trigger_inventory = _build_trigger_inventory(input_summary=input_summary, checkpoints=checkpoints)
    regulation_surface = phase_surfaces.get("regulation", {})
    if not isinstance(regulation_surface, dict):
        regulation_surface = {}
    epistemics = phase_surfaces.get("epistemics", {})
    if not isinstance(epistemics, dict):
        epistemics = {}

    if route_and_scope.get("accepted") is False:
        _append_causal_entry(
            entries=entries,
            event_type="dispatch_rejection",
            event_ref="route_and_scope.accepted",
            cause_family=CAUSE_FAMILY_UNRESOLVED,
            cause_source="route_and_scope.accepted",
            load_bearing=False,
            confidence=0.99,
            evidence_field_paths=[
                "route_and_scope.accepted",
                "route_and_scope.route_binding_consequence",
                "route_and_scope.decision_restrictions",
            ],
            competing_causes=[],
            observability_gap_candidate=True,
        )

    checkpoint_rows = checkpoints.get("observed_checkpoint_results", [])
    if isinstance(checkpoint_rows, list):
        for row in checkpoint_rows:
            if not isinstance(row, dict):
                continue
            status = row.get("status", UNRESOLVED_TOKEN)
            if status not in PATH_AFFECTING_CHECKPOINT_STATUSES:
                continue
            checkpoint_id = str(row.get("checkpoint_id", UNRESOLVED_TOKEN))
            cause_family = CAUSE_FAMILY_UNRESOLVED
            cause_source = f"checkpoints.{checkpoint_id}.status"
            competing_causes: list[str] = []
            observability_gap = False
            confidence = 0.55
            if checkpoint_id == "rt01.epistemic_admission_checkpoint":
                cause_family = CAUSE_FAMILY_EPISTEMIC_CONSTRAINT
                cause_source = "checkpoints.epistemic_admission_checkpoint.status"
                competing_causes = [CAUSE_FAMILY_UNRESOLVED]
                confidence = 0.97
            elif checkpoint_id == "rt01.shared_runtime_domain_checkpoint":
                (
                    cause_family,
                    cause_source,
                    competing_causes,
                    observability_gap,
                ) = _classify_shared_regulation_cause(
                    regulation_surface=regulation_surface,
                    restrictions=restrictions,
                )
                confidence = 0.88 if cause_family != CAUSE_FAMILY_UNRESOLVED else 0.55
                observability_gap = _regulation_observability_gap_candidate(
                    regulation_surface=regulation_surface,
                    restrictions=restrictions,
                    consequence_is_path_affecting=True,
                )
            else:
                competing_causes = [
                    CAUSE_FAMILY_EPISTEMIC_CONSTRAINT,
                    CAUSE_FAMILY_LOCAL_REGULATION_CONSTRAINT,
                    CAUSE_FAMILY_SHARED_RUNTIME_REGULATION,
                ]
            evidence_paths = [
                f"checkpoints.{checkpoint_id}.status",
                f"checkpoints.{checkpoint_id}.applied_action",
                f"checkpoints.{checkpoint_id}.reason",
                "final_outcome.active_execution_mode",
                "final_outcome.final_execution_outcome",
            ]
            if checkpoint_id == "rt01.epistemic_admission_checkpoint":
                evidence_paths.extend(
                    [
                        "uncertainty_and_fallbacks.epistemic_should_abstain",
                        "uncertainty_and_fallbacks.epistemic_unknown_reason",
                        "uncertainty_and_fallbacks.epistemic_conflict_reason",
                        "phase_surfaces.epistemics.epistemic_should_abstain",
                        "phase_surfaces.epistemics.epistemic_claim_strength",
                    ]
                )
            if checkpoint_id == "rt01.shared_runtime_domain_checkpoint":
                evidence_paths.extend(
                    [
                        "phase_surfaces.regulation.effective_regulation_influence_source",
                        "phase_surfaces.regulation.effective_regulation_path_consequence",
                        "phase_surfaces.regulation.effective_regulation_causal_reason",
                        "phase_surfaces.regulation.regulation_override_scope",
                        "phase_surfaces.regulation.regulation_no_strong_override_claim",
                        "restrictions_and_forbidden_shortcuts.regulation_gate_restrictions",
                    ]
                )
            _append_causal_entry(
                entries=entries,
                event_type="checkpoint_consequence",
                event_ref=checkpoint_id,
                cause_family=cause_family,
                cause_source=cause_source,
                load_bearing=True,
                confidence=confidence,
                evidence_field_paths=evidence_paths,
                competing_causes=competing_causes,
                observability_gap_candidate=observability_gap,
            )

    outcome = final_outcome.get("final_execution_outcome", UNRESOLVED_TOKEN)
    repair_needed = final_outcome.get("repair_needed")
    revalidation_needed = final_outcome.get("revalidation_needed")
    path_affecting_outcome = (
        (isinstance(outcome, str) and outcome in PATH_AFFECTING_OUTCOMES)
        or repair_needed is True
        or revalidation_needed is True
    )
    if path_affecting_outcome:
        epistemic_marked = (
            uncertainty.get("epistemic_should_abstain") is True
            or not _is_unresolved_like(uncertainty.get("epistemic_unknown_reason"))
            or not _is_unresolved_like(uncertainty.get("epistemic_conflict_reason"))
            or not _is_unresolved_like(epistemics.get("epistemic_abstain_reason", UNRESOLVED_TOKEN))
        )
        shared_checkpoint_status = regulation_surface.get(
            "effective_shared_runtime_domain_checkpoint_status",
            UNRESOLVED_TOKEN,
        )
        shared_reg_marked = shared_checkpoint_status in PATH_AFFECTING_CHECKPOINT_STATUSES
        competing: list[str] = []
        observability_gap_candidate = False
        if epistemic_marked and shared_reg_marked:
            cause_family = CAUSE_FAMILY_MIXED
            cause_source = "uncertainty_and_fallbacks + phase_surfaces.regulation"
            competing = [CAUSE_FAMILY_EPISTEMIC_CONSTRAINT, CAUSE_FAMILY_SHARED_RUNTIME_REGULATION]
            confidence = 0.7
            observability_gap_candidate = _regulation_observability_gap_candidate(
                regulation_surface=regulation_surface,
                restrictions=restrictions,
                consequence_is_path_affecting=True,
            )
        elif epistemic_marked:
            cause_family = CAUSE_FAMILY_EPISTEMIC_CONSTRAINT
            cause_source = "uncertainty_and_fallbacks.epistemic_*"
            confidence = 0.9
        elif shared_reg_marked:
            cause_family, cause_source, competing, observability_gap_candidate = _classify_shared_regulation_cause(
                regulation_surface=regulation_surface,
                restrictions=restrictions,
            )
            confidence = 0.85 if cause_family != CAUSE_FAMILY_UNRESOLVED else 0.5
        elif not _is_unresolved_like(final_outcome.get("halt_reason")):
            cause_family = CAUSE_FAMILY_HARNESS_INFERENCE_ONLY
            cause_source = "final_outcome.halt_reason"
            confidence = 0.45
        else:
            cause_family = CAUSE_FAMILY_UNRESOLVED
            cause_source = "final_outcome.final_execution_outcome"
            confidence = 0.35
            observability_gap_candidate = True
        outcome_load_bearing = cause_family not in {
            CAUSE_FAMILY_HARNESS_INFERENCE_ONLY,
            CAUSE_FAMILY_UNRESOLVED,
        }
        _append_causal_entry(
            entries=entries,
            event_type="outcome_consequence",
            event_ref="final_outcome.final_execution_outcome",
            cause_family=cause_family,
            cause_source=cause_source,
            load_bearing=outcome_load_bearing,
            confidence=confidence,
            evidence_field_paths=[
                "final_outcome.final_execution_outcome",
                "final_outcome.active_execution_mode",
                "final_outcome.repair_needed",
                "final_outcome.revalidation_needed",
                "uncertainty_and_fallbacks.epistemic_should_abstain",
                "uncertainty_and_fallbacks.epistemic_unknown_reason",
                "uncertainty_and_fallbacks.epistemic_conflict_reason",
                "phase_surfaces.regulation.effective_shared_runtime_domain_checkpoint_status",
                "phase_surfaces.regulation.effective_regulation_influence_source",
            ],
            competing_causes=competing,
            observability_gap_candidate=observability_gap_candidate,
        )

    shared_checkpoint_status = regulation_surface.get("effective_shared_runtime_domain_checkpoint_status", UNRESOLVED_TOKEN)
    regulation_observability_noted = any(
        not _is_unresolved_like(regulation_surface.get(field_name, UNRESOLVED_TOKEN))
        for field_name in (
            "effective_regulation_shared_domain_source_surface",
            "effective_regulation_causal_reason",
            "effective_regulation_influence_source",
        )
    )
    if (
        regulation_observability_noted
        and shared_checkpoint_status not in PATH_AFFECTING_CHECKPOINT_STATUSES
        and not path_affecting_outcome
    ):
        _append_causal_entry(
            entries=entries,
            event_type="regulation_observability_note",
            event_ref="phase_surfaces.regulation.effective_*",
            cause_family=CAUSE_FAMILY_OBSERVABILITY_ONLY,
            cause_source="phase_surfaces.regulation.effective_*",
            load_bearing=False,
            confidence=0.9,
            evidence_field_paths=[
                "phase_surfaces.regulation.effective_regulation_shared_domain_source_surface",
                "phase_surfaces.regulation.effective_regulation_causal_reason",
                "phase_surfaces.regulation.effective_regulation_influence_source",
                "phase_surfaces.regulation.effective_shared_runtime_domain_checkpoint_status",
                "final_outcome.final_execution_outcome",
            ],
            competing_causes=[],
            observability_gap_candidate=False,
        )

    if not entries and trigger_inventory:
        _append_causal_entry(
            entries=entries,
            event_type="trigger_without_consequence",
            event_ref="input_summary",
            cause_family=CAUSE_FAMILY_HARNESS_INFERENCE_ONLY,
            cause_source="input_summary.context_flags/epistemic_case_input/regulation_shared_domain_input",
            load_bearing=False,
            confidence=0.6,
            evidence_field_paths=[row["trigger_source"] for row in trigger_inventory if isinstance(row, dict)],
            competing_causes=[CAUSE_FAMILY_UNRESOLVED],
            observability_gap_candidate=False,
        )

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry["evidence_coverage_complete"] = True
        if entry.get("load_bearing") is not True:
            continue
        cause_source = str(entry.get("cause_source", UNRESOLVED_TOKEN))
        evidence_field_paths = _nonempty_list(entry.get("evidence_field_paths"))
        if not _cause_source_covered_by_evidence(cause_source, [str(path) for path in evidence_field_paths]):
            entry["load_bearing"] = False
            entry["cause_family"] = CAUSE_FAMILY_UNRESOLVED
            entry["competing_causes"] = list(_nonempty_list(entry.get("competing_causes"))) + [CAUSE_FAMILY_UNRESOLVED]
            entry["observability_gap_candidate"] = True
            entry["evidence_coverage_complete"] = False

    ownership_status = "resolved"
    if any(entry.get("cause_family") == CAUSE_FAMILY_UNRESOLVED for entry in entries):
        ownership_status = "unresolved"
    elif any(entry.get("cause_family") == CAUSE_FAMILY_MIXED for entry in entries):
        ownership_status = "mixed"

    return {
        "entries": entries,
        "trigger_inventory": trigger_inventory,
        "has_load_bearing_entries": any(entry.get("load_bearing") is True for entry in entries),
        "ownership_status": ownership_status,
    }


def _compute_verdicts(
    *,
    route_and_scope: dict[str, object],
    checkpoints: dict[str, object],
    uncertainty: dict[str, object],
    final_outcome: dict[str, object],
    input_summary: dict[str, object],
    causal_trace: dict[str, object],
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

    trace_entries = _nonempty_list(causal_trace.get("entries"))
    trigger_inventory = _nonempty_list(causal_trace.get("trigger_inventory"))
    trigger_paths = [
        row.get("trigger_source", UNRESOLVED_TOKEN)
        for row in trigger_inventory
        if isinstance(row, dict)
    ]
    sensitivity_trigger_inventory = [
        row
        for row in trigger_inventory
        if isinstance(row, dict)
        and row.get("trigger_class")
        in {"context_flag", "epistemic_input_pressure", "regulation_input_pressure"}
    ]
    load_bearing_trace_entries = [
        row
        for row in trace_entries
        if isinstance(row, dict) and row.get("load_bearing") is True
    ]
    unresolved_or_mixed_ownership = causal_trace.get("ownership_status") in {"mixed", "unresolved"}

    path_status = "PASS"
    path_reasons: list[str] = []
    if route_and_scope["accepted"] is False:
        path_status = "UNRESOLVED"
        path_reasons.append("dispatch rejected pre-execution; no path-affecting execution evidence")
    else:
        if sensitivity_trigger_inventory:
            if load_bearing_trace_entries:
                path_reasons.append(
                    "sensitivity-bearing triggers are paired with load-bearing checkpoint/restriction/outcome causal entries"
                )
            else:
                path_status = "FAIL"
                path_reasons.append(
                    "sensitivity-bearing triggers are present but no load-bearing causal entry is materialized"
                )
        elif load_bearing_trace_entries:
            path_status = "PARTIAL"
            path_reasons.append(
                "load-bearing baseline path evidence exists without perturbation-bearing trigger input; sensitivity is bounded"
            )
        else:
            path_status = "PARTIAL"
            path_reasons.append("single-turn artifact has no sensitivity-bearing trigger inventory; sensitivity cannot be fully proven")

        if unresolved_or_mixed_ownership and path_status == "PASS":
            path_status = "PARTIAL"
            path_reasons.append("causal ownership is mixed/unresolved; compact success-style sensitivity claim is bounded")

        if path_status in {"FAIL", "PARTIAL"} and not trace_entries:
            path_status = "UNRESOLVED"
            path_reasons.append("causal trace entry is required for contradiction-grade path verdict but is missing")

    verdicts["path_affecting_sensitivity"] = {
        "status": path_status,
        "reasons": path_reasons,
        "evidence_field_paths": [
            "causal_trace.trigger_inventory",
            "causal_trace.has_load_bearing_entries",
            *trigger_paths,
            "causal_trace.entries",
            "checkpoints.enforced_detour_checkpoint_ids",
            "checkpoints.blocked_checkpoint_ids",
        ],
    }

    for key in ("mechanistic_integrity", "claim_honesty"):
        status = verdicts[key]["status"]
        if status in {"FAIL", "PARTIAL"} and not trace_entries:
            verdicts[key]["status"] = "UNRESOLVED"
            verdicts[key]["reasons"] = list(verdicts[key]["reasons"]) + [
                "causal ownership is unresolved because no causal trace entry is materialized"
            ]
            verdicts[key]["evidence_field_paths"] = list(verdicts[key]["evidence_field_paths"]) + [
                "causal_trace.entries"
            ]

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
        "epistemic_case_input": _summarize_epistemic_case_input(
            getattr(request, "epistemic_case_input", None)
        ),
        "regulation_shared_domain_input": _summarize_regulation_shared_domain_input(
            getattr(request, "regulation_shared_domain_input", None)
        ),
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

    causal_trace = _collect_causal_trace(
        route_and_scope=route_and_scope,
        phase_surfaces=phase_surfaces,
        checkpoints=checkpoints,
        restrictions=restrictions_and_forbidden_shortcuts,
        uncertainty=uncertainty_and_fallbacks,
        final_outcome=final_outcome,
        input_summary=input_summary,
    )
    causal_entries = _nonempty_list(causal_trace.get("entries"))
    evidence_incomplete_entries = [
        entry
        for entry in causal_entries
        if isinstance(entry, dict) and entry.get("evidence_coverage_complete") is False
    ]
    if evidence_incomplete_entries:
        unresolved.append(
            _unresolved_entry(
                code="CAUSAL_TRACE_EVIDENCE_COVERAGE_INCOMPLETE",
                message="one or more causal trace entries were downgraded because evidence paths do not cover classification basis",
                blocking_surface="causal_trace.entries[].evidence_field_paths",
                severity="medium",
                impacted_sections=["causal_trace", "verdicts"],
                requires_non_v1_extension=False,
            )
        )
    if any(
        isinstance(entry, dict)
        and entry.get("event_type") in {"checkpoint_consequence", "outcome_consequence"}
        and entry.get("cause_family") == CAUSE_FAMILY_UNRESOLVED
    for entry in causal_entries):
        unresolved.append(
            _unresolved_entry(
                code="CAUSAL_OWNERSHIP_UNRESOLVED_FOR_PATH_CONSEQUENCE",
                message="path-affecting consequence is observed but causal ownership remains unresolved from available surfaces",
                blocking_surface="causal_trace.entries[].cause_family",
                severity="medium",
                impacted_sections=["causal_trace", "verdicts", "final_outcome"],
                requires_non_v1_extension=False,
            )
        )

    verdicts = _compute_verdicts(
        route_and_scope=route_and_scope,
        checkpoints=checkpoints,
        uncertainty=uncertainty_and_fallbacks,
        final_outcome=final_outcome,
        input_summary=input_summary,
        causal_trace=causal_trace,
    )

    contradiction_statuses = (
        verdicts["mechanistic_integrity"]["status"],
        verdicts["claim_honesty"]["status"],
        verdicts["path_affecting_sensitivity"]["status"],
    )
    if any(status in {"FAIL", "PARTIAL"} for status in contradiction_statuses):
        entries = _nonempty_list(causal_trace.get("entries"))
        if not entries:
            unresolved.append(
                _unresolved_entry(
                    code="CAUSAL_TRACE_MISSING_FOR_CONTRADICTION_VERDICT",
                    message="at least one causal trace entry is required when contradiction-grade verdict status is FAIL/PARTIAL",
                    blocking_surface="causal_trace.entries",
                    severity="high",
                    impacted_sections=["causal_trace", "verdicts"],
                    requires_non_v1_extension=False,
                )
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
        "causal_trace": causal_trace,
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


def _coerce_epistemic_case_input(
    payload: RuntimeEpistemicCaseInput | dict[str, object] | None,
) -> RuntimeEpistemicCaseInput | None:
    if payload is None:
        return None
    if isinstance(payload, RuntimeEpistemicCaseInput):
        return payload
    if not isinstance(payload, dict):
        raise TypeError("epistemic_case_input must be RuntimeEpistemicCaseInput, dict, or None")
    return RuntimeEpistemicCaseInput(
        content=str(payload.get("content")) if payload.get("content") is not None else None,
        source_id=str(payload.get("source_id")) if payload.get("source_id") is not None else None,
        source_class=str(payload.get("source_class")) if payload.get("source_class") is not None else None,
        modality=str(payload.get("modality")) if payload.get("modality") is not None else None,
        confidence_hint=(
            str(payload.get("confidence_hint")) if payload.get("confidence_hint") is not None else None
        ),
        support_note=str(payload.get("support_note")) if payload.get("support_note") is not None else None,
        contestation_note=(
            str(payload.get("contestation_note")) if payload.get("contestation_note") is not None else None
        ),
        claim_key=str(payload.get("claim_key")) if payload.get("claim_key") is not None else None,
        claim_polarity=(
            str(payload.get("claim_polarity")) if payload.get("claim_polarity") is not None else None
        ),
        require_observation=(
            bool(payload.get("require_observation"))
            if payload.get("require_observation") is not None
            else None
        ),
    )


def _coerce_regulation_shared_domain_input(
    payload: RuntimeRegulationSharedDomainInput | dict[str, object] | None,
) -> RuntimeRegulationSharedDomainInput | None:
    if payload is None:
        return None
    if isinstance(payload, RuntimeRegulationSharedDomainInput):
        return payload
    if not isinstance(payload, dict):
        raise TypeError(
            "regulation_shared_domain_input must be RuntimeRegulationSharedDomainInput, dict, or None"
        )
    pressure_raw = payload.get("pressure_level")
    return RuntimeRegulationSharedDomainInput(
        pressure_level=float(pressure_raw) if pressure_raw is not None else None,
        escalation_stage=(
            str(payload.get("escalation_stage")) if payload.get("escalation_stage") is not None else None
        ),
        override_scope=str(payload.get("override_scope")) if payload.get("override_scope") is not None else None,
        no_strong_override_claim=(
            bool(payload.get("no_strong_override_claim"))
            if payload.get("no_strong_override_claim") is not None
            else None
        ),
        gate_accepted=(
            bool(payload.get("gate_accepted"))
            if payload.get("gate_accepted") is not None
            else None
        ),
        source_state_ref=(
            str(payload.get("source_state_ref")) if payload.get("source_state_ref") is not None else None
        ),
    )


def collect_turn_audit_artifact(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool,
    context_flags: dict[str, object] | None = None,
    epistemic_case_input: RuntimeEpistemicCaseInput | dict[str, object] | None = None,
    regulation_shared_domain_input: RuntimeRegulationSharedDomainInput | dict[str, object] | None = None,
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
    epistemic_case_input_typed = _coerce_epistemic_case_input(epistemic_case_input)
    regulation_shared_domain_input_typed = _coerce_regulation_shared_domain_input(
        regulation_shared_domain_input
    )
    route = _coerce_route_class(route_class)
    if (
        route == RuntimeRouteClass.PRODUCTION_CONTOUR
        and not allow_helper_route
        and not allow_test_only_route
        and not allow_non_production_consumer_opt_in
        and epistemic_case_input_typed is None
        and regulation_shared_domain_input_typed is None
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
                epistemic_case_input=epistemic_case_input_typed,
                regulation_shared_domain_input=regulation_shared_domain_input_typed,
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
    epistemic_case_input: RuntimeEpistemicCaseInput | dict[str, object] | None = None,
    regulation_shared_domain_input: RuntimeRegulationSharedDomainInput | dict[str, object] | None = None,
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
        epistemic_case_input=epistemic_case_input,
        regulation_shared_domain_input=regulation_shared_domain_input,
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
    parser.add_argument(
        "--epistemic-case-input-json",
        help="JSON object for RuntimeEpistemicCaseInput-compatible fields",
    )
    parser.add_argument(
        "--regulation-shared-domain-input-json",
        help="JSON object for RuntimeRegulationSharedDomainInput-compatible fields",
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
    epistemic_case_input: dict[str, object] | None = None
    regulation_shared_domain_input: dict[str, object] | None = None
    if args.epistemic_case_input_json:
        loaded = json.loads(args.epistemic_case_input_json)
        if not isinstance(loaded, dict):
            raise ValueError("--epistemic-case-input-json must decode to a JSON object")
        epistemic_case_input = loaded
    if args.regulation_shared_domain_input_json:
        loaded = json.loads(args.regulation_shared_domain_input_json)
        if not isinstance(loaded, dict):
            raise ValueError("--regulation-shared-domain-input-json must decode to a JSON object")
        regulation_shared_domain_input = loaded

    artifact_path, artifact = collect_turn_audit_artifact_to_disk(
        case_id=args.case_id,
        energy=args.energy,
        cognitive=args.cognitive,
        safety=args.safety,
        unresolved_preference=_parse_bool_token(args.unresolved_preference),
        context_flags=context_flags_or_none,
        epistemic_case_input=epistemic_case_input,
        regulation_shared_domain_input=regulation_shared_domain_input,
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
