# Turn summary
- artifact path: `artifacts\turn_audit\battery_v2_run\t02_raw_vs_propagated_integrity_pressure.json` (field: input artifact file)
- artifact version: `turn_audit_artifact_v1` (field: artifact_metadata.artifact_version)
- route class: `production_contour` (field: route_and_scope.route_class)
- route binding consequence: `lawful_production_contour` (field: route_and_scope.route_binding_consequence)
- final execution outcome: `revalidate` (field: final_outcome.final_execution_outcome)
- overall verdict: `PASS` (field: verdicts.overall.status)
- mechanistic_integrity: `PASS` (field: verdicts.mechanistic_integrity.status)
- claim_honesty: `PASS` (field: verdicts.claim_honesty.status)
- path_affecting_sensitivity: `PASS` (field: verdicts.path_affecting_sensitivity.status)

## Route / legality / scope
- dispatch accepted: `true` (field: route_and_scope.accepted)
- lawful production route: `true` (field: route_and_scope.lawful_production_route)
- decision restrictions: dispatch_contract_must_be_read, topology_bound_to_rt01_contour (field: route_and_scope.decision_restrictions)
- runtime order: EPISTEMICS, R, C01, C02, C03, C04, C05, S01, S02, S03, T01, T02, T03, T04, RT01 (field: route_and_scope.runtime_order)
- mandatory checkpoint count: `19` (field: checkpoints.mandatory_checkpoint_ids)
- epistemic status: `report` (field: phase_surfaces.epistemics.epistemic_status)
- epistemic confidence: `medium` (field: phase_surfaces.epistemics.epistemic_confidence)
- epistemic source_class: `reporter` (field: phase_surfaces.epistemics.epistemic_source_class)
- epistemic modality: `user_text` (field: phase_surfaces.epistemics.epistemic_modality)
- regulation pressure level: `0.135` (field: phase_surfaces.regulation.regulation_pressure_level)
- regulation escalation stage: `baseline` (field: phase_surfaces.regulation.regulation_escalation_stage)
- regulation override scope: `none` (field: phase_surfaces.regulation.regulation_override_scope)
- regulation no_strong_override_claim: `true` (field: phase_surfaces.regulation.regulation_no_strong_override_claim)
- regulation gate_accepted: `false` (field: phase_surfaces.regulation.regulation_gate_accepted)
- regulation source_state_ref: `regulation-step-1` (field: phase_surfaces.regulation.regulation_source_state_ref)

Scope table:
| Surface | Scope | rt01_contour_only |
| --- | --- | --- |
| `a_line_normalization` | `rt01_contour_only` | `true` |
| `m_minimal` | `rt01_contour_only` | `true` |
| `n_minimal` | `rt01_contour_only` | `true` |
| `s02_prediction_boundary` | `rt01_contour_only` | `true` |
| `s03_ownership_weighted_learning` | `rt01_contour_only` | `true` |
| `s_minimal` | `rt01_contour_only` | `true` |
| `t01_semantic_field` | `rt01_contour_only` | `true` |
| `t02_relation_binding` | `rt01_contour_only` | `true` |
| `t03_hypothesis_competition` | `rt01_contour_only` | `true` |
| `t04_attention_schema` | `rt01_contour_only` | `true` |
| `world_entry` | `rt01_contour_only` | `UNRESOLVED_FOR_V1` |

## Critical checkpoints
- checkpoint coverage complete: `true` (field: checkpoints.checkpoint_coverage_complete)
- missing mandatory checkpoint ids: [] (explicit empty list) (field: checkpoints.missing_mandatory_checkpoint_ids)
- blocked checkpoint ids: [] (explicit empty list) (field: checkpoints.blocked_checkpoint_ids)
- enforced detour checkpoint ids: rt01.world_entry_checkpoint, rt01.t02_raw_vs_propagated_integrity_checkpoint, rt01.outcome_resolution_checkpoint (field: checkpoints.enforced_detour_checkpoint_ids)

Explicit checkpoint rows:
| Checkpoint | Status | Required action | Applied action | Reason |
| --- | --- | --- | --- | --- |
| `rt01.epistemic_admission_checkpoint` | `allowed` | `consume_epistemic_allowance_and_preserve_abstain_unknown_conflict_markers` | `reported_claim:idle` | `report cannot be promoted to observation` |
| `rt01.shared_runtime_domain_checkpoint` | `allowed` | `consume_shared_regulation_continuity_validity_domains` | `idle` | `no prior shared runtime state supplied; contour followed phase-local contracts` |
| `rt01.downstream_obedience_checkpoint` | `allowed` | `allow_continue` | `idle` | `downstream obedience allows bounded continuation` |
| `rt01.outcome_resolution_checkpoint` | `enforced_detour` | `bounded_outcome_must_be_resolved` | `revalidate_path:revalidate_scope` | `runtime contour resolved bounded outcome from enforced contracts` |

## Restrictions and forbidden shortcuts
- dispatch restrictions: dispatch_contract_must_be_read, topology_bound_to_rt01_contour (field: restrictions_and_forbidden_shortcuts.dispatch_restrictions)
- downstream gate restrictions: fixed_order_must_be_read, r_gate_must_be_read, c01_gate_must_be_read, c02_gate_must_be_read, c03_gate_must_be_read, c04_gate_must_be_read, c05_gate_must_be_read, c04_mode_selection_must_be_enforced, c05_validity_action_must_be_enforced, c05_restrictions_must_not_be_ignored, outcome_must_be_bounded, execution_stance_must_be_read, checkpoint_decisions_must_be_read, c04_mode_claim_must_be_read, c05_action_claim_must_be_read, authority_roles_must_be_read, downstream_obedience_contract_must_be_read, downstream_obedience_restrictions_must_be_enforced, world_seam_contract_must_be_read, w_entry_contract_must_be_read, w_entry_forbidden_claims_must_be_read, w_entry_admission_criteria_must_be_read, s_minimal_contour_contract_must_be_read, s_forbidden_shortcuts_must_be_read, a_line_normalization_contract_must_be_read, a_forbidden_shortcuts_must_be_read, m_minimal_contour_contract_must_be_read, m_forbidden_shortcuts_must_be_read, n_minimal_contour_contract_must_be_read, n_forbidden_shortcuts_must_be_read, t01_semantic_field_contract_must_be_read, t01_forbidden_shortcuts_must_be_read, t02_relation_binding_contract_must_be_read, t02_forbidden_shortcuts_must_be_read, t03_hypothesis_competition_contract_must_be_read, t04_attention_schema_contract_must_be_read, s01_efference_copy_contract_must_be_read, s02_prediction_boundary_contract_must_be_read, s03_ownership_weighted_learning_contract_must_be_read, downstream_authority_degraded, t02_raw_vs_propagated_distinction_required (field: restrictions_and_forbidden_shortcuts.downstream_gate_restrictions)
- epistemic allowance restrictions: reported_not_observed (field: restrictions_and_forbidden_shortcuts.epistemic_allowance_restrictions)
- regulation gate restrictions: UNRESOLVED_FOR_V1 (field: restrictions_and_forbidden_shortcuts.regulation_gate_restrictions)

Per-phase restrictions:
- `a`: a_line_normalization_contract_must_be_read, sprint8c_not_a04_or_a05_build, capability_shortcuts_must_be_machine_readable, a_capability_claim_requires_world_or_self_basis, a_unavailable_capability_must_not_be_treated_as_available, a_no_safe_capability_claim_requires_repair_or_abstain (field: restrictions_and_forbidden_shortcuts.phase_restrictions.a)
- `m`: m_minimal_contract_must_be_read, sprint8d_not_m01_m02_m03_build, memory_lifecycle_states_must_be_respected, stale_memory_requires_review_or_revalidation, conflict_marked_memory_must_not_be_silently_merged, memory_claim_requires_provenance, review_required_memory_must_not_support_strong_claim, no_safe_memory_claim_requires_repair_or_abstain (field: restrictions_and_forbidden_shortcuts.phase_restrictions.m)
- `n`: n_minimal_contract_must_be_read, sprint8e_not_n01_n02_n03_n04_build, narrative_commitment_basis_must_be_load_bearing, narrative_commitment_requires_basis, narrative_ambiguity_must_be_preserved, narrative_contradiction_must_be_explicitly_marked, no_safe_narrative_claim_requires_repair_or_abstain (field: restrictions_and_forbidden_shortcuts.phase_restrictions.n)
- `s`: s_minimal_contour_must_be_read, sprint8b_not_full_s_line, self_world_boundary_requires_typed_basis (field: restrictions_and_forbidden_shortcuts.phase_restrictions.s)
- `s02`: s02_prediction_boundary_contract_must_be_read, s02_controllability_vs_predictability_must_be_read, s02_mixed_source_status_must_be_preserved, s02_context_stale_invalidation_must_be_obeyed, s02_boundary_consumer_not_ready, s02_controllability_consumer_not_ready, s02_mixed_source_consumer_not_ready (field: restrictions_and_forbidden_shortcuts.phase_restrictions.s02)
- `t01`: t01_semantic_field_contract_must_be_read, t01_scene_status_must_be_read, t01_unresolved_slots_must_be_preserved, t01_scene_must_be_consumed_preverbal, no_clean_scene_commit_requires_revalidate_or_clarification, t01_preverbal_consumer_not_ready (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t01)
- `t02`: UNRESOLVED_FOR_V1 (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t02)
- `t03`: t03_hypothesis_competition_contract_must_be_read, t03_authority_weighted_support_must_be_read, t03_constraint_structure_must_be_read, t03_convergence_state_must_be_read, t03_publication_frontier_must_be_read, t03_convergence_consumer_not_ready (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t03)
- `t04`: t04_attention_schema_contract_must_be_read, t04_focus_peripheral_split_must_be_read, t04_attention_owner_must_be_read, t04_reportability_vs_stability_must_be_read, t04_focus_ownership_consumer_not_ready, t04_reportable_focus_consumer_not_ready (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t04)
- `world_entry_w01`: w_entry_contract_is_admission_layer_only, sprint8a_not_w01_build, w01_admission_requires_linked_observation_action_effect_episode (field: restrictions_and_forbidden_shortcuts.phase_restrictions.world_entry_w01)

Per-phase forbidden shortcuts:
- `a`: capability_claim_without_basis, affordance_claim_without_world_or_self_basis, unavailable_capability_reframed_as_available (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.a)
- `m`: stale_memory_reframed_as_current_truth, conflict_marked_memory_silently_merged, no_provenance_memory_claim, unreviewed_memory_reused_as_safe_basis (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.m)
- `n`: prose_without_commitment_basis, narrative_reframed_as_self_truth_without_basis, narrative_reframed_as_world_truth_without_basis, narrative_reframed_as_memory_truth_without_basis, narrative_reframed_as_capability_truth_without_basis, contradiction_hidden_by_fluent_wording (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.n)
- `s`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.s)
- `s02`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.s02)
- `t01`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t01)
- `t02`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t02)
- `t03`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t03)
- `t04`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t04)

## Uncertainty / degraded / abstain / mixed / unresolved
- abstain: `true` (field: uncertainty_and_fallbacks.abstain)
- abstain_reason: `revalidation_required` (field: uncertainty_and_fallbacks.abstain_reason)
- epistemic_should_abstain: `false` (field: uncertainty_and_fallbacks.epistemic_should_abstain)
- epistemic_claim_strength: `reported_claim` (field: uncertainty_and_fallbacks.epistemic_claim_strength)
- epistemic_allowance_reason: `report cannot be promoted to observation` (field: uncertainty_and_fallbacks.epistemic_allowance_reason)
- epistemic_unknown_reason: `null` (field: uncertainty_and_fallbacks.epistemic_unknown_reason)
- epistemic_conflict_reason: `null` (field: uncertainty_and_fallbacks.epistemic_conflict_reason)
- epistemic_abstain_reason: `null` (field: uncertainty_and_fallbacks.epistemic_abstain_reason)
- regulation_no_strong_override_claim: `true` (field: uncertainty_and_fallbacks.regulation_no_strong_override_claim)
- regulation_gate_accepted: `false` (field: uncertainty_and_fallbacks.regulation_gate_accepted)

Active uncertainty/no_safe/degraded markers:
- `uncertainty_markers.s_underconstrained`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.s_underconstrained)
- `uncertainty_markers.m_underconstrained`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.m_underconstrained)
- `uncertainty_markers.n_underconstrained`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.n_underconstrained)
- `uncertainty_markers.n_ambiguity_residue`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.n_ambiguity_residue)
- `uncertainty_markers.t01_no_clean_scene_commit`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.t01_no_clean_scene_commit)
- `uncertainty_markers.s02_boundary_uncertain`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.s02_boundary_uncertain)
- `uncertainty_markers.s02_no_clean_seam_claim`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.s02_no_clean_seam_claim)
- `uncertainty_markers.t03_honest_nonconvergence`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.t03_honest_nonconvergence)
- `uncertainty_markers.t03_nonconvergence_preserved`: `true` (field: uncertainty_and_fallbacks.uncertainty_markers.t03_nonconvergence_preserved)
- `uncertainty_markers.t03_publication_open_slots`: `['slot:self_world_attribution', 'slot:memory_reuse_legitimacy', 'slot:narrative_commitment_scope']` (field: uncertainty_and_fallbacks.uncertainty_markers.t03_publication_open_slots)
- `no_safe_markers.s_no_safe_self_claim`: `true` (field: uncertainty_and_fallbacks.no_safe_markers.s_no_safe_self_claim)
- `no_safe_markers.s_no_safe_world_claim`: `true` (field: uncertainty_and_fallbacks.no_safe_markers.s_no_safe_world_claim)
- `no_safe_markers.a_no_safe_capability_claim`: `true` (field: uncertainty_and_fallbacks.no_safe_markers.a_no_safe_capability_claim)
- `no_safe_markers.m_no_safe_memory_claim`: `true` (field: uncertainty_and_fallbacks.no_safe_markers.m_no_safe_memory_claim)
- `no_safe_markers.n_no_safe_narrative_claim`: `true` (field: uncertainty_and_fallbacks.no_safe_markers.n_no_safe_narrative_claim)
- `degraded_markers.world_entry_degraded`: `true` (field: uncertainty_and_fallbacks.degraded_markers.world_entry_degraded)
- `degraded_markers.s_degraded`: `true` (field: uncertainty_and_fallbacks.degraded_markers.s_degraded)
- `degraded_markers.a_degraded`: `true` (field: uncertainty_and_fallbacks.degraded_markers.a_degraded)
- `degraded_markers.m_degraded`: `true` (field: uncertainty_and_fallbacks.degraded_markers.m_degraded)
- `degraded_markers.n_degraded`: `true` (field: uncertainty_and_fallbacks.degraded_markers.n_degraded)
- `degraded_markers.downstream_authority_degraded_restriction`: `true` (field: uncertainty_and_fallbacks.degraded_markers.downstream_authority_degraded_restriction)

Unresolved entries from artifact:
- `T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD`: t02 restrictions are not exposed as a stable dedicated field in current contract projection (field: unresolved[])
- `REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD`: regulation gate restrictions are not exposed as a dedicated typed field in current RT01 contract projection (field: unresolved[])
- `RUNTIME_DOMAIN_VIEW_NOT_MATERIALIZED_IN_ARTIFACT_RUN`: runtime domain contract view is unavailable without accepted persistence transition in the same run (field: unresolved[])

## Final execution outcome
- execution stance: `revalidate_path` (field: final_outcome.execution_stance)
- active execution mode: `revalidate_scope` (field: final_outcome.active_execution_mode)
- repair_needed: `false` (field: final_outcome.repair_needed)
- revalidation_needed: `true` (field: final_outcome.revalidation_needed)
- halt_reason: `null` (field: final_outcome.halt_reason)
- persist_transition_accepted: `null` (field: final_outcome.persist_transition_accepted)

## Verdicts

### mechanistic_integrity
- status: `PASS` (field: verdicts.mechanistic_integrity.status)
- reasons: route legality and checkpoint coherence are bounded (field: verdicts.mechanistic_integrity.reasons)
- evidence_field_paths: route_and_scope.accepted, route_and_scope.lawful_production_route, checkpoints.missing_mandatory_checkpoint_ids, checkpoints.epistemic_admission_checkpoint, final_outcome.final_execution_outcome (field: verdicts.mechanistic_integrity.evidence_field_paths)

### claim_honesty
- status: `PASS` (field: verdicts.claim_honesty.status)
- reasons: uncertainty/no-safe markers are preserved with bounded detour/halt outcome (field: verdicts.claim_honesty.reasons)
- evidence_field_paths: uncertainty_and_fallbacks.abstain, uncertainty_and_fallbacks.epistemic_should_abstain, uncertainty_and_fallbacks.epistemic_unknown_reason, uncertainty_and_fallbacks.epistemic_conflict_reason, uncertainty_and_fallbacks.uncertainty_markers, uncertainty_and_fallbacks.no_safe_markers, final_outcome.final_execution_outcome (field: verdicts.claim_honesty.evidence_field_paths)

### path_affecting_sensitivity
- status: `PASS` (field: verdicts.path_affecting_sensitivity.status)
- reasons: triggered requirement/ablation flags produced explicit detour/block checkpoints (field: verdicts.path_affecting_sensitivity.reasons)
- evidence_field_paths: input_summary.context_flags, checkpoints.enforced_detour_checkpoint_ids, checkpoints.blocked_checkpoint_ids (field: verdicts.path_affecting_sensitivity.evidence_field_paths)

### overall
- status: `PASS` (field: verdicts.overall.status)
- reasons: aggregated from load-bearing verdict statuses without laundering (field: verdicts.overall.reasons)
- evidence_field_paths: verdicts.mechanistic_integrity.status, verdicts.claim_honesty.status, verdicts.path_affecting_sensitivity.status (field: verdicts.overall.evidence_field_paths)

## Non-v1 / unresolved boundaries
Unresolved entries:
- `T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD` | severity=`medium` | blocking_surface=`runtime_topology.downstream_contract.RuntimeDispatchContractView` | impacted=restrictions_and_forbidden_shortcuts, phase_surfaces | requires_non_v1_extension=`false`
- `REGULATION_GATE_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD` | severity=`medium` | blocking_surface=`runtime_topology.downstream_contract.RuntimeDispatchContractView` | impacted=restrictions_and_forbidden_shortcuts, phase_surfaces, uncertainty_and_fallbacks | requires_non_v1_extension=`false`
- `RUNTIME_DOMAIN_VIEW_NOT_MATERIALIZED_IN_ARTIFACT_RUN` | severity=`low` | blocking_surface=`subject_tick.persist_subject_tick_result_via_f01` | impacted=final_outcome, uncertainty_and_fallbacks | requires_non_v1_extension=`false`
- non-v1 exclusions: UNRESOLVED_FOR_V1 (field not present in artifact)
- boundary note: report is rendered strictly from artifact JSON and does not extend beyond artifact scope
