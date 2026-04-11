# Pair summary
- baseline artifact: `artifacts\turn_audit\battery_v2_run\bounded_clean_production_turn.json` (field: baseline_ref.artifact_path)
- perturbation artifact: `artifacts\turn_audit\battery_v2_run\regulation_high_override_scope_detour.json` (field: perturbation_ref.artifact_path)
- comparison version: `turn_audit_paired_contrast_v2` (field: comparison_metadata.comparison_version)
- path-affecting assessment: `UNRESOLVED` (field: path_affecting_assessment.status)

## Input differences
- `input_summary.tick_input.case_id`: baseline=`battery-bounded-clean`, perturbation=`battery-regulation-override-nearest`, changed=`true`
- `input_summary.tick_input.energy`: baseline=`66.0`, perturbation=`66.0`, changed=`false`
- `input_summary.tick_input.cognitive`: baseline=`44.0`, perturbation=`44.0`, changed=`false`
- `input_summary.tick_input.safety`: baseline=`74.0`, perturbation=`74.0`, changed=`false`
- `input_summary.tick_input.unresolved_preference`: baseline=`false`, perturbation=`false`, changed=`false`
- `input_summary.route_class_requested`: baseline=`production_contour`, perturbation=`production_contour`, changed=`false`

Context flag differences:
- `input_summary.context_flags.disable_a_line_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_c04_mode_execution_binding`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_c05_validity_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_downstream_obedience_enforcement`: baseline=`null`, perturbation=`false`
- `input_summary.context_flags.disable_gate_application`: baseline=`null`, perturbation=`true`
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
- `input_summary.context_flags.require_s02_boundary_consumer`: baseline=`null`, perturbation=`false`
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
- `route_and_scope.accepted`: baseline=`true`, perturbation=`false`, changed=`true`
- `route_and_scope.lawful_production_route`: baseline=`true`, perturbation=`false`, changed=`true`
- `route_and_scope.route_class`: baseline=`production_contour`, perturbation=`production_contour`, changed=`false`
- `route_and_scope.route_binding_consequence`: baseline=`lawful_production_contour`, perturbation=`lawful_production_contour`, changed=`false`
- `route_and_scope.decision_restrictions`: baseline=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour']`, perturbation=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour', 'production_route_forbids_ablation_flags']`, changed=`true`
- `route_and_scope.runtime_order`: baseline=`['EPISTEMICS', 'R', 'C01', 'C02', 'C03', 'C04', 'C05', 'S01', 'S02', 'S03', 'T01', 'T02', 'T03', 'T04', 'RT01']`, perturbation=`['EPISTEMICS', 'R', 'C01', 'C02', 'C03', 'C04', 'C05', 'S01', 'S02', 'S03', 'T01', 'T02', 'T03', 'T04', 'RT01']`, changed=`false`

## Critical checkpoint differences
- `checkpoints.checkpoint_coverage_complete`: baseline=`true`, perturbation=`false`, changed=`true`
- `checkpoints.missing_mandatory_checkpoint_ids`: baseline=`[]`, perturbation=`['rt01.epistemic_admission_checkpoint', 'rt01.c04_mode_binding', 'rt01.c05_legality_checkpoint', 'rt01.downstream_obedience_checkpoint', 'rt01.world_seam_checkpoint', 'rt01.world_entry_checkpoint', 'rt01.s_minimal_contour_checkpoint', 'rt01.a_line_normalization_checkpoint', 'rt01.m_minimal_contour_checkpoint', 'rt01.n_minimal_contour_checkpoint', 'rt01.s01_efference_copy_checkpoint', 'rt01.s02_prediction_boundary_checkpoint', 'rt01.s03_ownership_weighted_learning_checkpoint', 'rt01.t01_semantic_field_checkpoint', 'rt01.t02_relation_binding_checkpoint', 'rt01.t02_raw_vs_propagated_integrity_checkpoint', 'rt01.t03_hypothesis_competition_checkpoint', 'rt01.t04_attention_schema_checkpoint', 'rt01.outcome_resolution_checkpoint']`, changed=`true`
- `checkpoints.blocked_checkpoint_ids`: baseline=`[]`, perturbation=`[]`, changed=`false`
- `checkpoints.enforced_detour_checkpoint_ids`: baseline=`['rt01.world_entry_checkpoint']`, perturbation=`[]`, changed=`true`

Explicit checkpoints:
- `rt01.epistemic_admission_checkpoint`: baseline_status=`allowed`, perturbation_status=`UNRESOLVED_FOR_V1`, baseline_action=`reported_claim:idle`, perturbation_action=`UNRESOLVED_FOR_V1`, changed=`true`
- `rt01.shared_runtime_domain_checkpoint`: baseline_status=`allowed`, perturbation_status=`UNRESOLVED_FOR_V1`, baseline_action=`idle`, perturbation_action=`UNRESOLVED_FOR_V1`, changed=`true`
- `rt01.downstream_obedience_checkpoint`: baseline_status=`allowed`, perturbation_status=`UNRESOLVED_FOR_V1`, baseline_action=`idle`, perturbation_action=`UNRESOLVED_FOR_V1`, changed=`true`
- `rt01.outcome_resolution_checkpoint`: baseline_status=`allowed`, perturbation_status=`UNRESOLVED_FOR_V1`, baseline_action=`continue_path:idle`, perturbation_action=`UNRESOLVED_FOR_V1`, changed=`true`

## Epistemic differences
- `phase_surfaces.epistemics.epistemic_status`: baseline=`report`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.epistemics.epistemic_should_abstain`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.epistemics.epistemic_claim_strength`: baseline=`reported_claim`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.epistemics.epistemic_allowance_restrictions`: baseline=`['reported_not_observed']`, perturbation=`[]`, changed=`true`
- `checkpoints.epistemic_admission_checkpoint.status`: baseline=`allowed`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `checkpoints.epistemic_admission_checkpoint.applied_action`: baseline=`reported_claim:idle`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`

## Regulation differences
- `phase_surfaces.regulation.regulation_override_scope`: baseline=`none`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.regulation.regulation_no_strong_override_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.regulation.regulation_gate_accepted`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.regulation.regulation_pressure_level`: baseline=`0.135`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `phase_surfaces.regulation.regulation_escalation_stage`: baseline=`baseline`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `checkpoints.shared_runtime_domain_checkpoint.status`: baseline=`allowed`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `checkpoints.shared_runtime_domain_checkpoint.applied_action`: baseline=`idle`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `restrictions_and_forbidden_shortcuts.regulation_gate_restrictions`: baseline=`['UNRESOLVED_FOR_V1']`, perturbation=`['UNRESOLVED_FOR_V1']`, changed=`false`

## Restrictions / forbidden shortcut differences
- `restrictions_and_forbidden_shortcuts.dispatch_restrictions`: baseline=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour']`, perturbation=`['dispatch_contract_must_be_read', 'topology_bound_to_rt01_contour', 'production_route_forbids_ablation_flags']`, changed=`true`
- `restrictions_and_forbidden_shortcuts.downstream_gate_restrictions`: baseline=`['fixed_order_must_be_read', 'r_gate_must_be_read', 'c01_gate_must_be_read', 'c02_gate_must_be_read', 'c03_gate_must_be_read', 'c04_gate_must_be_read', 'c05_gate_must_be_read', 'c04_mode_selection_must_be_enforced', 'c05_validity_action_must_be_enforced', 'c05_restrictions_must_not_be_ignored', 'outcome_must_be_bounded', 'execution_stance_must_be_read', 'checkpoint_decisions_must_be_read', 'c04_mode_claim_must_be_read', 'c05_action_claim_must_be_read', 'authority_roles_must_be_read', 'downstream_obedience_contract_must_be_read', 'downstream_obedience_restrictions_must_be_enforced', 'world_seam_contract_must_be_read', 'w_entry_contract_must_be_read', 'w_entry_forbidden_claims_must_be_read', 'w_entry_admission_criteria_must_be_read', 's_minimal_contour_contract_must_be_read', 's_forbidden_shortcuts_must_be_read', 'a_line_normalization_contract_must_be_read', 'a_forbidden_shortcuts_must_be_read', 'm_minimal_contour_contract_must_be_read', 'm_forbidden_shortcuts_must_be_read', 'n_minimal_contour_contract_must_be_read', 'n_forbidden_shortcuts_must_be_read', 't01_semantic_field_contract_must_be_read', 't01_forbidden_shortcuts_must_be_read', 't02_relation_binding_contract_must_be_read', 't02_forbidden_shortcuts_must_be_read', 't03_hypothesis_competition_contract_must_be_read', 't04_attention_schema_contract_must_be_read', 's01_efference_copy_contract_must_be_read', 's02_prediction_boundary_contract_must_be_read', 's03_ownership_weighted_learning_contract_must_be_read']`, perturbation=`[]`, changed=`true`
- `restrictions_and_forbidden_shortcuts.regulation_gate_restrictions`: baseline=`['UNRESOLVED_FOR_V1']`, perturbation=`['UNRESOLVED_FOR_V1']`, changed=`false`

Per-phase restriction differences:
- `restrictions_and_forbidden_shortcuts.phase_restrictions.a`: baseline=`['a_line_normalization_contract_must_be_read', 'sprint8c_not_a04_or_a05_build', 'capability_shortcuts_must_be_machine_readable', 'a_capability_claim_requires_world_or_self_basis', 'a_unavailable_capability_must_not_be_treated_as_available', 'a_no_safe_capability_claim_requires_repair_or_abstain']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.m`: baseline=`['m_minimal_contract_must_be_read', 'sprint8d_not_m01_m02_m03_build', 'memory_lifecycle_states_must_be_respected', 'stale_memory_requires_review_or_revalidation', 'conflict_marked_memory_must_not_be_silently_merged', 'memory_claim_requires_provenance', 'review_required_memory_must_not_support_strong_claim', 'no_safe_memory_claim_requires_repair_or_abstain']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.n`: baseline=`['n_minimal_contract_must_be_read', 'sprint8e_not_n01_n02_n03_n04_build', 'narrative_commitment_basis_must_be_load_bearing', 'narrative_commitment_requires_basis', 'narrative_ambiguity_must_be_preserved', 'narrative_contradiction_must_be_explicitly_marked', 'no_safe_narrative_claim_requires_repair_or_abstain']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.s`: baseline=`['s_minimal_contour_must_be_read', 'sprint8b_not_full_s_line', 'self_world_boundary_requires_typed_basis']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.s02`: baseline=`['s02_prediction_boundary_contract_must_be_read', 's02_controllability_vs_predictability_must_be_read', 's02_mixed_source_status_must_be_preserved', 's02_context_stale_invalidation_must_be_obeyed', 's02_boundary_consumer_not_ready', 's02_controllability_consumer_not_ready', 's02_mixed_source_consumer_not_ready']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.t01`: baseline=`['t01_semantic_field_contract_must_be_read', 't01_scene_status_must_be_read', 't01_unresolved_slots_must_be_preserved', 't01_scene_must_be_consumed_preverbal', 'no_clean_scene_commit_requires_revalidate_or_clarification', 't01_preverbal_consumer_not_ready']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.t03`: baseline=`['t03_hypothesis_competition_contract_must_be_read', 't03_authority_weighted_support_must_be_read', 't03_constraint_structure_must_be_read', 't03_convergence_state_must_be_read', 't03_publication_frontier_must_be_read', 't03_convergence_consumer_not_ready']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.t04`: baseline=`['t04_attention_schema_contract_must_be_read', 't04_focus_peripheral_split_must_be_read', 't04_attention_owner_must_be_read', 't04_reportability_vs_stability_must_be_read', 't04_focus_ownership_consumer_not_ready', 't04_reportable_focus_consumer_not_ready']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_restrictions.world_entry_w01`: baseline=`['w_entry_contract_is_admission_layer_only', 'sprint8a_not_w01_build', 'w01_admission_requires_linked_observation_action_effect_episode']`, perturbation=`[]`
Per-phase forbidden shortcut differences:
- `restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.a`: baseline=`['capability_claim_without_basis', 'affordance_claim_without_world_or_self_basis', 'unavailable_capability_reframed_as_available']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.m`: baseline=`['stale_memory_reframed_as_current_truth', 'conflict_marked_memory_silently_merged', 'no_provenance_memory_claim', 'unreviewed_memory_reused_as_safe_basis']`, perturbation=`[]`
- `restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.n`: baseline=`['prose_without_commitment_basis', 'narrative_reframed_as_self_truth_without_basis', 'narrative_reframed_as_world_truth_without_basis', 'narrative_reframed_as_memory_truth_without_basis', 'narrative_reframed_as_capability_truth_without_basis', 'contradiction_hidden_by_fluent_wording']`, perturbation=`[]`

## Uncertainty / degraded / unresolved differences
- `uncertainty_and_fallbacks.abstain`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.abstain_reason`: baseline=`null`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.downstream_obedience_status`: baseline=`allow_continue`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.downstream_obedience_fallback`: baseline=`continue`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.epistemic_should_abstain`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.epistemic_claim_strength`: baseline=`reported_claim`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.epistemic_unknown_reason`: baseline=`null`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.epistemic_conflict_reason`: baseline=`null`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.epistemic_abstain_reason`: baseline=`null`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.regulation_no_strong_override_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.regulation_gate_accepted`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.regulation_pressure_level`: baseline=`0.135`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.regulation_escalation_stage`: baseline=`baseline`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `uncertainty_and_fallbacks.regulation_override_scope`: baseline=`none`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
Uncertainty marker differences:
- `uncertainty_and_fallbacks.uncertainty_markers.a_underconstrained`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.epistemic_abstain`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.epistemic_conflict`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.epistemic_should_abstain`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.epistemic_unknown`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.m_underconstrained`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.n_ambiguity_residue`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.n_contradiction_risk`: baseline=`high`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.n_underconstrained`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.s02_boundary_uncertain`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.s02_insufficient_coverage`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.s02_no_clean_seam_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.s_underconstrained`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.t01_no_clean_scene_commit`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.t01_unresolved_slots_count`: baseline=`3`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.t03_honest_nonconvergence`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.t03_nonconvergence_preserved`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.t03_publication_open_slots`: baseline=`['slot:self_world_attribution', 'slot:memory_reuse_legitimacy', 'slot:narrative_commitment_scope']`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.uncertainty_markers.t03_publication_unresolved_conflicts`: baseline=`[]`, perturbation=`UNRESOLVED_FOR_V1`
No-safe marker differences:
- `uncertainty_and_fallbacks.no_safe_markers.a_no_safe_capability_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.no_safe_markers.m_no_safe_memory_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.no_safe_markers.n_no_safe_narrative_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.no_safe_markers.s_no_safe_self_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.no_safe_markers.s_no_safe_world_claim`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
Degraded marker differences:
- `uncertainty_and_fallbacks.degraded_markers.a_degraded`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.degraded_markers.downstream_authority_degraded_restriction`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.degraded_markers.m_degraded`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.degraded_markers.n_degraded`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.degraded_markers.s_degraded`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.degraded_markers.world_adapter_degraded`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`
- `uncertainty_and_fallbacks.degraded_markers.world_entry_degraded`: baseline=`true`, perturbation=`UNRESOLVED_FOR_V1`

## Final outcome differences
- `final_outcome.final_execution_outcome`: baseline=`continue`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `final_outcome.execution_stance`: baseline=`continue_path`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `final_outcome.active_execution_mode`: baseline=`idle`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `final_outcome.repair_needed`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `final_outcome.revalidation_needed`: baseline=`false`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `final_outcome.halt_reason`: baseline=`null`, perturbation=`UNRESOLVED_FOR_V1`, changed=`true`
- `final_outcome.persist_transition_accepted`: baseline=`null`, perturbation=`null`, changed=`false`

## Verdict differences
- `verdicts.mechanistic_integrity.status`: baseline=`PASS`, perturbation=`PARTIAL`, changed=`true`
- `verdicts.claim_honesty.status`: baseline=`PASS`, perturbation=`UNRESOLVED`, changed=`true`
- `verdicts.path_affecting_sensitivity.status`: baseline=`PARTIAL`, perturbation=`UNRESOLVED`, changed=`true`
- `verdicts.overall.status`: baseline=`PARTIAL`, perturbation=`UNRESOLVED`, changed=`true`

## Path-affecting assessment
- status: `UNRESOLVED` (field: path_affecting_assessment.status)
- reasons: baseline or perturbation artifact is structurally incomplete; path-affecting confirmation is bounded (field: path_affecting_assessment.reasons)
Load-bearing signals:
- `active_execution_mode_changed`: `false` (field: path_affecting_assessment.signals.active_execution_mode_changed)
- `checkpoint_consequence_changed`: `true` (field: path_affecting_assessment.signals.checkpoint_consequence_changed)
- `epistemic_admission_checkpoint_changed`: `true` (field: path_affecting_assessment.signals.epistemic_admission_checkpoint_changed)
- `epistemic_allowance_restrictions_changed`: `true` (field: path_affecting_assessment.signals.epistemic_allowance_restrictions_changed)
- `epistemic_claim_strength_changed`: `true` (field: path_affecting_assessment.signals.epistemic_claim_strength_changed)
- `epistemic_should_abstain_changed`: `true` (field: path_affecting_assessment.signals.epistemic_should_abstain_changed)
- `epistemic_status_changed`: `true` (field: path_affecting_assessment.signals.epistemic_status_changed)
- `execution_stance_changed`: `true` (field: path_affecting_assessment.signals.execution_stance_changed)
- `final_execution_outcome_changed`: `true` (field: path_affecting_assessment.signals.final_execution_outcome_changed)
- `regulation_escalation_stage_changed`: `true` (field: path_affecting_assessment.signals.regulation_escalation_stage_changed)
- `regulation_gate_accepted_changed`: `true` (field: path_affecting_assessment.signals.regulation_gate_accepted_changed)
- `regulation_gate_restrictions_changed`: `false` (field: path_affecting_assessment.signals.regulation_gate_restrictions_changed)
- `regulation_no_strong_override_claim_changed`: `true` (field: path_affecting_assessment.signals.regulation_no_strong_override_claim_changed)
- `regulation_override_scope_changed`: `true` (field: path_affecting_assessment.signals.regulation_override_scope_changed)
- `regulation_pressure_level_changed`: `true` (field: path_affecting_assessment.signals.regulation_pressure_level_changed)
- `restriction_envelope_changed`: `true` (field: path_affecting_assessment.signals.restriction_envelope_changed)
- `route_binding_consequence_changed`: `false` (field: path_affecting_assessment.signals.route_binding_consequence_changed)
- `shared_runtime_domain_checkpoint_changed`: `true` (field: path_affecting_assessment.signals.shared_runtime_domain_checkpoint_changed)

## Unresolved boundaries
- `ACTIVE_EXECUTION_MODE_NOT_EXPOSED`: active_execution_mode is not exposed in one or both compared artifacts | blocking_surface=`final_outcome.active_execution_mode` | severity=`low`
- `PERTURBATION_ARTIFACT_STRUCTURALLY_INCOMPLETE`: perturbation artifact does not expose complete load-bearing path evidence for paired assessment | blocking_surface=`perturbation_ref.artifact_path` | severity=`high`
