# Turn summary
- artifact path: `artifacts\turn_audit\battery_run\route_boundary_or_nonproduction_case.json` (field: input artifact file)
- artifact version: `turn_audit_artifact_v1` (field: artifact_metadata.artifact_version)
- route class: `helper_path` (field: route_and_scope.route_class)
- route binding consequence: `non_lawful_helper_route` (field: route_and_scope.route_binding_consequence)
- final execution outcome: `UNRESOLVED_FOR_V1` (field: final_outcome.final_execution_outcome)
- overall verdict: `UNRESOLVED` (field: verdicts.overall.status)
- mechanistic_integrity: `PARTIAL` (field: verdicts.mechanistic_integrity.status)
- claim_honesty: `UNRESOLVED` (field: verdicts.claim_honesty.status)
- path_affecting_sensitivity: `UNRESOLVED` (field: verdicts.path_affecting_sensitivity.status)

## Route / legality / scope
- dispatch accepted: `false` (field: route_and_scope.accepted)
- lawful production route: `false` (field: route_and_scope.lawful_production_route)
- decision restrictions: dispatch_contract_must_be_read, topology_bound_to_rt01_contour, helper_route_not_lawful_production, production_route_required (field: route_and_scope.decision_restrictions)
- runtime order: R, C01, C02, C03, C04, C05, S01, S02, S03, T01, T02, T03, T04, RT01 (field: route_and_scope.runtime_order)
- mandatory checkpoint count: `18` (field: checkpoints.mandatory_checkpoint_ids)

Scope table:
| Surface | Scope | rt01_contour_only |
| --- | --- | --- |
| UNRESOLVED_FOR_V1 | UNRESOLVED_FOR_V1 | UNRESOLVED_FOR_V1 |

## Critical checkpoints
- checkpoint coverage complete: `false` (field: checkpoints.checkpoint_coverage_complete)
- missing mandatory checkpoint ids: rt01.c04_mode_binding, rt01.c05_legality_checkpoint, rt01.downstream_obedience_checkpoint, rt01.world_seam_checkpoint, rt01.world_entry_checkpoint, rt01.s_minimal_contour_checkpoint, rt01.a_line_normalization_checkpoint, rt01.m_minimal_contour_checkpoint, rt01.n_minimal_contour_checkpoint, rt01.s01_efference_copy_checkpoint, rt01.s02_prediction_boundary_checkpoint, rt01.s03_ownership_weighted_learning_checkpoint, rt01.t01_semantic_field_checkpoint, rt01.t02_relation_binding_checkpoint, rt01.t02_raw_vs_propagated_integrity_checkpoint, rt01.t03_hypothesis_competition_checkpoint, rt01.t04_attention_schema_checkpoint, rt01.outcome_resolution_checkpoint (field: checkpoints.missing_mandatory_checkpoint_ids)
- blocked checkpoint ids: [] (explicit empty list) (field: checkpoints.blocked_checkpoint_ids)
- enforced detour checkpoint ids: [] (explicit empty list) (field: checkpoints.enforced_detour_checkpoint_ids)

Explicit checkpoint rows:
| Checkpoint | Status | Required action | Applied action | Reason |
| --- | --- | --- | --- | --- |
| `rt01.downstream_obedience_checkpoint` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` |
| `rt01.outcome_resolution_checkpoint` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` |

## Restrictions and forbidden shortcuts
- dispatch restrictions: dispatch_contract_must_be_read, topology_bound_to_rt01_contour, helper_route_not_lawful_production, production_route_required (field: restrictions_and_forbidden_shortcuts.dispatch_restrictions)
- downstream gate restrictions: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.downstream_gate_restrictions)

Per-phase restrictions:
- `a`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.a)
- `m`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.m)
- `n`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.n)
- `s`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.s)
- `s02`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.s02)
- `t01`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t01)
- `t02`: UNRESOLVED_FOR_V1 (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t02)
- `t03`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t03)
- `t04`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.t04)
- `world_entry_w01`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_restrictions.world_entry_w01)

Per-phase forbidden shortcuts:
- `a`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.a)
- `m`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.m)
- `n`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.n)
- `s`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.s)
- `s02`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.s02)
- `t01`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t01)
- `t02`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t02)
- `t03`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t03)
- `t04`: [] (explicit empty list) (field: restrictions_and_forbidden_shortcuts.phase_forbidden_shortcuts.t04)

## Uncertainty / degraded / abstain / mixed / unresolved
- abstain: `UNRESOLVED_FOR_V1` (field: uncertainty_and_fallbacks.abstain)
- abstain_reason: `UNRESOLVED_FOR_V1` (field: uncertainty_and_fallbacks.abstain_reason)

Active uncertainty/no_safe/degraded markers:
- none (no active markers in artifact)

Unresolved entries from artifact:
- `PRE_EXECUTION_DISPATCH_REJECTION`: dispatch rejected before subject_tick execution; phase-level artifact is structurally incomplete (field: unresolved[])
- `T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD`: t02 restrictions are not exposed as a stable dedicated field in current contract projection (field: unresolved[])
- `RUNTIME_DOMAIN_VIEW_NOT_MATERIALIZED_IN_ARTIFACT_RUN`: runtime domain contract view is unavailable without accepted persistence transition in the same run (field: unresolved[])

## Final execution outcome
- execution stance: `UNRESOLVED_FOR_V1` (field: final_outcome.execution_stance)
- active execution mode: `UNRESOLVED_FOR_V1` (field: final_outcome.active_execution_mode)
- repair_needed: `UNRESOLVED_FOR_V1` (field: final_outcome.repair_needed)
- revalidation_needed: `UNRESOLVED_FOR_V1` (field: final_outcome.revalidation_needed)
- halt_reason: `UNRESOLVED_FOR_V1` (field: final_outcome.halt_reason)
- persist_transition_accepted: `null` (field: final_outcome.persist_transition_accepted)

## Verdicts

### mechanistic_integrity
- status: `PARTIAL` (field: verdicts.mechanistic_integrity.status)
- reasons: dispatch rejected pre-execution; legality evaluated but execution checkpoints absent (field: verdicts.mechanistic_integrity.reasons)
- evidence_field_paths: route_and_scope.accepted, route_and_scope.lawful_production_route, checkpoints.missing_mandatory_checkpoint_ids, final_outcome.final_execution_outcome (field: verdicts.mechanistic_integrity.evidence_field_paths)

### claim_honesty
- status: `UNRESOLVED` (field: verdicts.claim_honesty.status)
- reasons: subject_tick state is absent due to pre-execution dispatch rejection (field: verdicts.claim_honesty.reasons)
- evidence_field_paths: uncertainty_and_fallbacks.abstain, uncertainty_and_fallbacks.uncertainty_markers, uncertainty_and_fallbacks.no_safe_markers, final_outcome.final_execution_outcome (field: verdicts.claim_honesty.evidence_field_paths)

### path_affecting_sensitivity
- status: `UNRESOLVED` (field: verdicts.path_affecting_sensitivity.status)
- reasons: dispatch rejected pre-execution; no path-affecting execution evidence (field: verdicts.path_affecting_sensitivity.reasons)
- evidence_field_paths: input_summary.context_flags, checkpoints.enforced_detour_checkpoint_ids, checkpoints.blocked_checkpoint_ids (field: verdicts.path_affecting_sensitivity.evidence_field_paths)

### overall
- status: `UNRESOLVED` (field: verdicts.overall.status)
- reasons: aggregated from load-bearing verdict statuses without laundering (field: verdicts.overall.reasons)
- evidence_field_paths: verdicts.mechanistic_integrity.status, verdicts.claim_honesty.status, verdicts.path_affecting_sensitivity.status (field: verdicts.overall.evidence_field_paths)

## Non-v1 / unresolved boundaries
Unresolved entries:
- `PRE_EXECUTION_DISPATCH_REJECTION` | severity=`high` | blocking_surface=`runtime_topology.evaluate_runtime_dispatch_decision` | impacted=phase_surfaces, checkpoints, uncertainty_and_fallbacks, final_outcome, verdicts | requires_non_v1_extension=`false`
- `T02_RESTRICTIONS_NOT_EXPOSED_AS_CANONICAL_FIELD` | severity=`medium` | blocking_surface=`runtime_topology.downstream_contract.RuntimeDispatchContractView` | impacted=restrictions_and_forbidden_shortcuts, phase_surfaces | requires_non_v1_extension=`false`
- `RUNTIME_DOMAIN_VIEW_NOT_MATERIALIZED_IN_ARTIFACT_RUN` | severity=`low` | blocking_surface=`subject_tick.persist_subject_tick_result_via_f01` | impacted=final_outcome, uncertainty_and_fallbacks | requires_non_v1_extension=`false`
- non-v1 exclusions: UNRESOLVED_FOR_V1 (field not present in artifact)
- boundary note: report is rendered strictly from artifact JSON and does not extend beyond artifact scope
