# Pair summary
- baseline artifact: `artifacts\turn_audit\battery_v2_run\bounded_clean_production_turn.json` (field: baseline_ref.artifact_path)
- perturbation artifact: `artifacts\turn_audit\battery_v2_run\epistemic_unknown_abstain_detour.json` (field: perturbation_ref.artifact_path)
- comparison version: `turn_audit_paired_contrast_v2` (field: comparison_metadata.comparison_version)
- path-affecting assessment: `CONFIRMED` (field: path_affecting_assessment.status)

## Input differences
- `input_summary.tick_input.case_id`: baseline=`battery-bounded-clean`, perturbation=`battery-epi-unknown-nearest`, changed=`true`
- `input_summary.tick_input.energy`: baseline=`66.0`, perturbation=`66.0`, changed=`false`
- `input_summary.tick_input.cognitive`: baseline=`44.0`, perturbation=`44.0`, changed=`false`
- `input_summary.tick_input.safety`: baseline=`74.0`, perturbation=`74.0`, changed=`false`
- `input_summary.tick_input.unresolved_preference`: baseline=`false`, perturbation=`true`, changed=`true`
- `input_summary.route_class_requested`: baseline=`production_contour`, perturbation=`production_contour`, changed=`false`

Context flag differences:
- `input_summary.context_flags.disable_a_line_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_c04_mode_execution_binding`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_c05_validity_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_downstream_obedience_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_gate_application`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_m_minimal_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_n_minimal_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_s_minimal_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_t01_field_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_t01_unresolved_slot_maintenance`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_t02_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_t03_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_t04_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.emit_world_action_candidate`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s01_comparison_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s01_prediction_validity_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s01_unexpected_change_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s02_boundary_consumer`: baseline=`null`, perturbation=`true`
- `input_summary.context_flags.require_s02_controllability_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s02_mixed_source_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s03_freeze_obedience_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s03_learning_packet_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_s03_mixed_update_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t01_preverbal_scene_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t01_scene_comparison_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t02_constrained_scene_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t02_raw_vs_propagated_distinction`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t03_convergence_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t03_frontier_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t03_nonconvergence_preservation`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t04_focus_ownership_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t04_peripheral_preservation`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_t04_reportable_focus_consumer`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_world_effect_feedback_for_success_claim`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.require_world_grounded_transition`: baseline=`null`, perturbation=`false`

## Route / legality / scope differences
- `route_and_scope.accepted`: baseline=`true`, perturbation=`true`, changed=`false`
- `route_and_scope.lawful_production_route`: baseline=`true`, perturbation=`true`, changed=`false`
- `route_and_scope.route_class`: baseline=`production_contour`, perturbation=`production_contour`, changed=`false`
- `route_and_scope.route_binding_consequence`: baseline=`lawful_production_contour`, perturbation=`lawful_production_contour`, changed=`false`
- `route_and_scope.decision_restrictions`: baseline=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour']`, perturbation=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour']`, changed=`false`
- `route_and_scope.runtime_order`: baseline=`['EPISTEMICS', 'R', 'C01', 'C02', 'C03', 'C04', 'C05', 'S01', 'S02', 'S03', 'T01', 'T02', 'T03', 'T04', 'RT01']`, perturbation=`['EPISTEMICS', 'R', 'C01', 'C02', 'C03', 'C04', 'C05', 'S01', 'S02', 'S03', 'T01', 'T02', 'T03', 'T04', 'RT01']`, changed=`false`

## Critical checkpoint differences
- `checkpoints.checkpoint_coverage_complete`: baseline=`true`, perturbation=`true`, changed=`false`
- `checkpoints.missing_mandatory_checkpoint_ids`: baseline=`[]`, perturbation=`[]`, changed=`false`
- `checkpoints.blocked_checkpoint_ids`: baseline=`[]`, perturbation=`[]`, changed=`false`
- `checkpoints.enforced_detour_checkpoint_ids`: baseline=`['rt01.world_entry_checkpoint']`, perturbation=`['rt01.critical_gate_checkpoint', 'rt01.world_entry_checkpoint', 'rt01.s02_prediction_boundary_checkpoint', 'rt01.outcome_resolution_checkpoint']`, changed=`true`

Explicit checkpoints:
- `rt01.epistemic_admission_checkpoint`: baseline_status=`allowed`, perturbation_status=`allowed`, baseline_action=`reported_claim:idle`, perturbation_action=`reported_claim:continue_stream`, changed=`true`
- `rt01.shared_runtime_domain_checkpoint`: baseline_status=`allowed`, perturbation_status=`allowed`, baseline_action=`idle`, perturbation_action=`continue_stream`, changed=`true`
- `rt01.downstream_obedience_checkpoint`: baseline_status=`allowed`, perturbation_status=`allowed`, baseline_action=`idle`, perturbation_action=`continue_stream`, changed=`true`
- `rt01.outcome_resolution_checkpoint`: baseline_status=`allowed`, perturbation_status=`enforced_detour`, baseline_action=`continue_path:idle`, perturbation_action=`revalidate_path:revalidate_scope`, changed=`true`

## Epistemic differences
- `phase_surfaces.epistemics.epistemic_status`: baseline=`report`, perturbation=`report`, changed=`false`
- `phase_surfaces.epistemics.epistemic_should_abstain`: baseline=`false`, perturbation=`false`, changed=`false`
- `phase_surfaces.epistemics.epistemic_claim_strength`: baseline=`reported_claim`, perturbation=`reported_claim`, changed=`false`
- `phase_surfaces.epistemics.epistemic_allowance_restrictions`: baseline=`['reported_not_observed']`, perturbation=`['reported_not_observed']`, changed=`false`
- `checkpoints.epistemic_admission_checkpoint.status`: baseline=`allowed`, perturbation=`allowed`, changed=`false`
- `checkpoints.epistemic_admission_checkpoint.applied_action`: baseline=`reported_claim:idle`, perturbation=`reported_claim:continue_stream`, changed=`true`

## Regulation differences
- `phase_surfaces.regulation.regulation_override_scope`: baseline=`none`, perturbation=`none`, changed=`false`
- `phase_surfaces.regulation.regulation_no_strong_override_claim`: baseline=`true`, perturbation=`true`, changed=`false`
- `phase_surfaces.regulation.regulation_gate_accepted`: baseline=`false`, perturbation=`false`, changed=`false`
- `phase_surfaces.regulation.regulation_pressure_level`: baseline=`0.135`, perturbation=`0.135`, changed=`false`
- `phase_surfaces.regulation.regulation_escalation_stage`: baseline=`baseline`, perturbation=`baseline`, changed=`false`
- `checkpoints.shared_runtime_domain_checkpoint.status`: baseline=`allowed`, perturbation=`allowed`, changed=`false`
- `checkpoints.shared_runtime_domain_checkpoint.applied_action`: baseline=`idle`, perturbation=`continue_stream`, changed=`true`
- `restrictions_and_forbidden_shortcuts.regulation_gate_restrictions`: baseline=`['UNRESOLVED_FOR_V1']`, perturbation=`['UNRESOLVED_FOR_V1']`, changed=`false`

## Restrictions / forbidden shortcut differences
- `restrictions_and_forbidden_shortcuts.dispatch_restrictions`: baseline=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour']`, perturbation=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour']`, changed=`false`
- `restrictions_and_forbidden_shortcuts.downstream_gate_restrictions`: baseline=`['fixed_order_must_be_read', 'r_gate_must_be_read', 'c01_gate_must_be_read', 'c02_gate_must_be_read', 'c03_gate_must_be_read', 'c04_gate_must_be_read', 'c05_gate_must_be_read', 'c04_mode_selection_must_be_enforced', 'c05_validity_action_must_be_enforced', 'c05_restrictions_must_not_be_ignored', 'outcome_must_be_bounded', 'execution_stance_must_be_read', 'checkpoint_decisions_must_be_read', 'c04_mode_claim_must_be_read', 'c05_action_claim_must_be_read', 'authority_roles_must_be_read', 'downstream_obedience_contract_must_be_read', 'downstream_obedience_restrictions_must_be_enforced', 'world_seam_contract_must_be_read', 'w_entry_contract_must_be_read', 'w_entry_forbidden_claims_must_be_read', 'w_entry_admission_criteria_must_be_read', 's_minimal_contour_contract_must_be_read', 's_forbidden_shortcuts_must_be_read', 'a_line_normalization_contract_must_be_read', 'a_forbidden_shortcuts_must_be_read', 'm_minimal_contour_contract_must_be_read', 'm_forbidden_shortcuts_must_be_read', 'n_minimal_contour_contract_must_be_read', 'n_forbidden_shortcuts_must_be_read', 't01_semantic_field_contract_must_be_read', 't01_forbidden_shortcuts_must_be_read', 't02_relation_binding_contract_must_be_read', 't02_forbidden_shortcuts_must_be_read', 't03_hypothesis_competition_contract_must_be_read', 't04_attention_schema_contract_must_be_read', 's01_efference_copy_contract_must_be_read', 's02_prediction_boundary_contract_must_be_read', 's03_ownership_weighted_learning_contract_must_be_read']`, perturbation=`['fixed_order_must_be_read', 'r_gate_must_be_read', 'c01_gate_must_be_read', 'c02_gate_must_be_read', 'c03_gate_must_be_read', 'c04_gate_must_be_read', 'c05_gate_must_be_read', 'c04_mode_selection_must_be_enforced', 'c05_validity_action_must_be_enforced', 'c05_restrictions_must_not_be_ignored', 'outcome_must_be_bounded', 'execution_stance_must_be_read', 'checkpoint_decisions_must_be_read', 'c04_mode_claim_must_be_read', 'c05_action_claim_must_be_read', 'authority_roles_must_be_read', 'downstream_obedience_contract_must_be_read', 'downstream_obedience_restrictions_must_be_enforced', 'world_seam_contract_must_be_read', 'w_entry_contract_must_be_read', 'w_entry_forbidden_claims_must_be_read', 'w_entry_admission_criteria_must_be_read', 's_minimal_contour_contract_must_be_read', 's_forbidden_shortcuts_must_be_read', 'a_line_normalization_contract_must_be_read', 'a_forbidden_shortcuts_must_be_read', 'm_minimal_contour_contract_must_be_read', 'm_forbidden_shortcuts_must_be_read', 'n_minimal_contour_contract_must_be_read', 'n_forbidden_shortcuts_must_be_read', 't01_semantic_field_contract_must_be_read', 't01_forbidden_shortcuts_must_be_read', 't02_relation_binding_contract_must_be_read', 't02_forbidden_shortcuts_must_be_read', 't03_hypothesis_competition_contract_must_be_read', 't04_attention_schema_contract_must_be_read', 's01_efference_copy_contract_must_be_read', 's02_prediction_boundary_contract_must_be_read', 's03_ownership_weighted_learning_contract_must_be_read', 'downstream_authority_degraded', 's02_boundary_consumer_required']`, changed=`true`
- `restrictions_and_forbidden_shortcuts.regulation_gate_restrictions`: baseline=`['UNRESOLVED_FOR_V1']`, perturbation=`['UNRESOLVED_FOR_V1']`, changed=`false`

Per-phase restriction differences:
- none
Per-phase forbidden shortcut differences:
- none

## Uncertainty / degraded / unresolved differences
- `uncertainty_and_fallbacks.abstain`: baseline=`false`, perturbation=`true`, changed=`true`
- `uncertainty_and_fallbacks.abstain_reason`: baseline=`null`, perturbation=`revalidation_required`, changed=`true`
- `uncertainty_and_fallbacks.downstream_obedience_status`: baseline=`allow_continue`, perturbation=`allow_continue`, changed=`false`
- `uncertainty_and_fallbacks.downstream_obedience_fallback`: baseline=`continue`, perturbation=`continue`, changed=`false`
- `uncertainty_and_fallbacks.epistemic_should_abstain`: baseline=`false`, perturbation=`false`, changed=`false`
- `uncertainty_and_fallbacks.epistemic_claim_strength`: baseline=`reported_claim`, perturbation=`reported_claim`, changed=`false`
- `uncertainty_and_fallbacks.epistemic_unknown_reason`: baseline=`null`, perturbation=`null`, changed=`false`
- `uncertainty_and_fallbacks.epistemic_conflict_reason`: baseline=`null`, perturbation=`null`, changed=`false`
- `uncertainty_and_fallbacks.epistemic_abstain_reason`: baseline=`null`, perturbation=`null`, changed=`false`
- `uncertainty_and_fallbacks.regulation_no_strong_override_claim`: baseline=`true`, perturbation=`true`, changed=`false`
- `uncertainty_and_fallbacks.regulation_gate_accepted`: baseline=`false`, perturbation=`false`, changed=`false`
- `uncertainty_and_fallbacks.regulation_pressure_level`: baseline=`0.135`, perturbation=`0.135`, changed=`false`
- `uncertainty_and_fallbacks.regulation_escalation_stage`: baseline=`baseline`, perturbation=`baseline`, changed=`false`
- `uncertainty_and_fallbacks.regulation_override_scope`: baseline=`none`, perturbation=`none`, changed=`false`
Uncertainty marker differences:
- none
No-safe marker differences:
- none
Degraded marker differences:
- `uncertainty_and_fallbacks.degraded_markers.downstream_authority_degraded_restriction`: baseline=`false`, perturbation=`true`

## Final outcome differences
- `final_outcome.final_execution_outcome`: baseline=`continue`, perturbation=`revalidate`, changed=`true`
- `final_outcome.execution_stance`: baseline=`continue_path`, perturbation=`revalidate_path`, changed=`true`
- `final_outcome.active_execution_mode`: baseline=`idle`, perturbation=`revalidate_scope`, changed=`true`
- `final_outcome.repair_needed`: baseline=`false`, perturbation=`true`, changed=`true`
- `final_outcome.revalidation_needed`: baseline=`false`, perturbation=`true`, changed=`true`
- `final_outcome.halt_reason`: baseline=`null`, perturbation=`null`, changed=`false`
- `final_outcome.persist_transition_accepted`: baseline=`null`, perturbation=`null`, changed=`false`

## Verdict differences
- `verdicts.mechanistic_integrity.status`: baseline=`PASS`, perturbation=`PASS`, changed=`false`
- `verdicts.claim_honesty.status`: baseline=`PASS`, perturbation=`PASS`, changed=`false`
- `verdicts.path_affecting_sensitivity.status`: baseline=`PARTIAL`, perturbation=`PASS`, changed=`true`
- `verdicts.overall.status`: baseline=`PARTIAL`, perturbation=`PASS`, changed=`true`

## Path-affecting assessment
- status: `CONFIRMED` (field: path_affecting_assessment.status)
- reasons: load-bearing path signal changed across compared artifacts (field: path_affecting_assessment.reasons)
Load-bearing signals:
- `active_execution_mode_changed`: `true` (field: path_affecting_assessment.signals.active_execution_mode_changed)
- `checkpoint_consequence_changed`: `true` (field: path_affecting_assessment.signals.checkpoint_consequence_changed)
- `epistemic_admission_checkpoint_changed`: `true` (field: path_affecting_assessment.signals.epistemic_admission_checkpoint_changed)
- `epistemic_allowance_restrictions_changed`: `false` (field: path_affecting_assessment.signals.epistemic_allowance_restrictions_changed)
- `epistemic_claim_strength_changed`: `false` (field: path_affecting_assessment.signals.epistemic_claim_strength_changed)
- `epistemic_should_abstain_changed`: `false` (field: path_affecting_assessment.signals.epistemic_should_abstain_changed)
- `epistemic_status_changed`: `false` (field: path_affecting_assessment.signals.epistemic_status_changed)
- `execution_stance_changed`: `true` (field: path_affecting_assessment.signals.execution_stance_changed)
- `final_execution_outcome_changed`: `true` (field: path_affecting_assessment.signals.final_execution_outcome_changed)
- `regulation_escalation_stage_changed`: `false` (field: path_affecting_assessment.signals.regulation_escalation_stage_changed)
- `regulation_gate_accepted_changed`: `false` (field: path_affecting_assessment.signals.regulation_gate_accepted_changed)
- `regulation_gate_restrictions_changed`: `false` (field: path_affecting_assessment.signals.regulation_gate_restrictions_changed)
- `regulation_no_strong_override_claim_changed`: `false` (field: path_affecting_assessment.signals.regulation_no_strong_override_claim_changed)
- `regulation_override_scope_changed`: `false` (field: path_affecting_assessment.signals.regulation_override_scope_changed)
- `regulation_pressure_level_changed`: `false` (field: path_affecting_assessment.signals.regulation_pressure_level_changed)
- `restriction_envelope_changed`: `true` (field: path_affecting_assessment.signals.restriction_envelope_changed)
- `route_binding_consequence_changed`: `false` (field: path_affecting_assessment.signals.route_binding_consequence_changed)
- `shared_runtime_domain_checkpoint_changed`: `true` (field: path_affecting_assessment.signals.shared_runtime_domain_checkpoint_changed)

## Unresolved boundaries
- []
