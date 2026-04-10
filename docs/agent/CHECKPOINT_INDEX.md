# Checkpoint Index (RT01/T01/T02/T03 contour)

Source basis:
- `src/substrate/runtime_topology/policy.py` (`mandatory_checkpoint_ids`)
- `src/substrate/subject_tick/update.py` (checkpoint producers + path effects)
- direct tests in:
  - `tests/substrate/test_subject_tick_build/test_subject_tick_build.py`
  - `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
  - `tests/substrate/test_t03_hypothesis_competition_build/test_t03_hypothesis_competition_build.py`
  - `tests/substrate/test_stage_contour/test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_c04_c05_subject_tick.py`

## A) Core RT01 load-bearing checkpoints

| checkpoint_id | source_contract | owner file(s) | producer phase | consumer trigger(s) | path-affecting behavior | direct tests | confidence |
|---|---|---|---|---|---|---|---|
| `rt01.c04_mode_binding` | `c04.mode_arbitration` | `src/substrate/subject_tick/update.py` | `C04` consumed by `RT01` | none | invalid mode binding causes detour | `test_subject_tick_role_boundary_c04_claim_consumed_without_reselection` | EXPLICIT |
| `rt01.c05_legality_checkpoint` | `c05.temporal_validity` | `src/substrate/subject_tick/update.py` | `C05` consumed by `RT01` | none | legality/revalidation/no-safe-reuse maps to bounded outcome branch | `test_subject_tick_basic_revalidate_path_from_c05`, `test_subject_tick_basic_halt_path_from_c05_legality_block` | EXPLICIT |
| `rt01.downstream_obedience_checkpoint` | `rt01.downstream_obedience` | `src/substrate/subject_tick/update.py` | `RT01` | none | fallback applies `repair/revalidate/halt` before final resolution | `test_subject_tick_adversarial_telemetry_claim_without_behavior_change_fails` | EXPLICIT |
| `rt01.critical_gate_checkpoint` | `rt01.phase_contract_gates` | `src/substrate/subject_tick/update.py` | `RT01` | none | critical gate mismatch enforces detour | `test_subject_tick_critical_gate_checkpoint_is_path_affecting_not_label_only` | EXPLICIT |
| `rt01.outcome_resolution_checkpoint` | `rt01.runtime_outcome` | `src/substrate/subject_tick/update.py` | `RT01` | none | final bounded stance/outcome mapping (`continue/repair/revalidate/halt`) | `test_subject_tick_basic_continue_path`, `test_subject_tick_basic_revalidate_path_from_c05`, `test_subject_tick_basic_halt_path_from_c05_legality_block` | EXPLICIT |

## B) Direct T01/T02/T03 integration checkpoints

| checkpoint_id | source_contract | owner file(s) | producer phase | consumer trigger(s) | path-affecting behavior | direct tests | confidence |
|---|---|---|---|---|---|---|---|
| `rt01.t01_semantic_field_checkpoint` | `t01_semantic_field.active_non_verbal_scene` | `src/substrate/subject_tick/update.py` | `T01` consumed by `RT01` | `require_t01_preverbal_scene_consumer`, `require_t01_scene_comparison_consumer` | non-consumable scene/comparison or unresolved laundering under pressure enforces detour | `test_subject_tick_t01_unresolved_laundering_under_consumer_pressure_forces_detour`, `test_subject_tick_t01_second_scene_comparison_consumer_requirement_is_path_affecting`, `test_dispatch_t01_scene_comparison_consumer_requirement_is_load_bearing` | EXPLICIT |
| `rt01.t02_relation_binding_checkpoint` | `t02_relation_binding.constraint_propagation` | `src/substrate/subject_tick/update.py` | `T02` consumed by `RT01` | `require_t02_constrained_scene_consumer` | no-clean/non-consumable constrained scene enforces `repair/revalidate` detour | `test_subject_tick_t02_constrained_scene_consumer_requirement_is_path_affecting`, `test_dispatch_t02_constrained_scene_consumer_requirement_is_load_bearing` | EXPLICIT |
| `rt01.t02_raw_vs_propagated_integrity_checkpoint` | `t02_relation_binding.raw_vs_propagated_distinction` | `src/substrate/subject_tick/update.py` | `T02` consumed by `RT01` | `require_t02_raw_vs_propagated_distinction` | collapsed raw-vs-propagated distinction enforces `revalidate` detour | `test_subject_tick_t02_raw_vs_propagated_integrity_requirement_is_second_load_bearing_consequence`, `test_dispatch_t02_raw_vs_propagated_integrity_requirement_is_load_bearing` | EXPLICIT |
| `rt01.t03_hypothesis_competition_checkpoint` | `t03_hypothesis_competition.silent_convergence` | `src/substrate/subject_tick/update.py` | `T03` consumed by `RT01` | `require_t03_convergence_consumer`, `require_t03_frontier_consumer`, `require_t03_nonconvergence_preservation` | non-consumable convergence/frontier/nonconvergence preservation enforces detour; frontier readiness also fails under shortcut-marked frontier (`t03_frontier_shortcut_detected`) | `test_subject_tick_t03_convergence_consumer_requirement_is_path_affecting`, `test_subject_tick_t03_frontier_consumer_requirement_is_path_affecting`, `test_subject_tick_t03_nonconvergence_preservation_requirement_is_path_affecting`, `test_dispatch_t03_convergence_consumer_requirement_is_load_bearing`, `test_dispatch_t03_frontier_consumer_requirement_is_load_bearing`, `test_dispatch_t03_nonconvergence_preservation_requirement_is_load_bearing` | EXPLICIT |

## C) Appendix: other mandatory RT01 contour checkpoints (outside this focused index)

These are mandatory in `runtime_topology/policy.py`, but not core T01/T02/T03 integration rows above:
- `rt01.world_seam_checkpoint`
- `rt01.world_entry_checkpoint`
- `rt01.s_minimal_contour_checkpoint`
- `rt01.a_line_normalization_checkpoint`
- `rt01.m_minimal_contour_checkpoint`
- `rt01.n_minimal_contour_checkpoint`
- `rt01.s01_efference_copy_checkpoint` *(direct adjacent to T01 in runtime order; out-of-focus for this index)*
- `rt01.t04_attention_schema_checkpoint` *(direct adjacent to T03 in runtime order; out-of-focus for this index)*

Direct-adjacent hardening note (EXPLICIT):
- `rt01.s01_efference_copy_checkpoint` has explicit path-affecting proof in owner tests for:
  - `require_s01_comparison_consumer`
  - `require_s01_unexpected_change_consumer` *(including non-ablation production-route test pair)*
  - `require_s01_prediction_validity_consumer`
- Direct tests:
  - `test_subject_tick_s01_comparison_consumer_requirement_is_path_affecting`
  - `test_subject_tick_s01_unexpected_change_consumer_requirement_is_path_affecting_without_ablation_registration_toggle`
  - `test_subject_tick_s01_prediction_validity_consumer_requirement_is_path_affecting`
  - `test_dispatch_s01_comparison_consumer_requirement_is_load_bearing`
  - `test_dispatch_s01_unexpected_change_consumer_requirement_is_load_bearing_without_ablation_registration_toggle`
  - `test_dispatch_s01_prediction_validity_consumer_requirement_is_load_bearing`
- `rt01.t04_attention_schema_checkpoint` now has state-backed consumer flags in RT01/dispatch contract views:
  - `t04_require_focus_ownership_consumer`
  - `t04_require_reportable_focus_consumer`
  - `t04_require_peripheral_preservation`
- Path-affecting proof for the third flag is now explicit in owner tests:
  - `test_subject_tick_t04_peripheral_preservation_requirement_is_path_affecting`
  - `test_dispatch_t04_peripheral_preservation_requirement_is_load_bearing`

Confidence: EXPLICIT for presence in mandatory graph and direct-adjacent T04 hardening behavior; detailed T04 semantics remain out of this index scope.
