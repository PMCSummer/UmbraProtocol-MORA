# Consumer Requirement Index (`require_*`)

Scope: load-bearing flags for RT01/T01/T02/T03 contour only.

Primary sources:
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- tests:
  - `tests/substrate/test_subject_tick_build/test_subject_tick_build.py`
  - `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
  - `tests/substrate/test_t03_hypothesis_competition_build/test_t03_hypothesis_competition_build.py`

## A) Load-bearing in this contour

| flag name | phase/package | owner file | checkpoint(s) affected | contract/consumer view used | likely outcome when unmet | direct tests | confidence |
|---|---|---|---|---|---|---|---|
| `require_t01_preverbal_scene_consumer` | `T01` | `src/substrate/subject_tick/update.py` | `rt01.t01_semantic_field_checkpoint` | `derive_t01_preverbal_consumer_view(...).can_consume_scene` | detour (`repair`/`revalidate` depending on cause) | `test_subject_tick_t01_unresolved_laundering_under_consumer_pressure_forces_detour` | EXPLICIT |
| `require_t01_scene_comparison_consumer` | `T01` | `src/substrate/subject_tick/update.py` | `rt01.t01_semantic_field_checkpoint` | `derive_t01_preverbal_consumer_view(...).comparison_consumer_ready` | detour when comparison surface not consumable | `test_subject_tick_t01_second_scene_comparison_consumer_requirement_is_path_affecting`, `test_dispatch_t01_scene_comparison_consumer_requirement_is_load_bearing` | EXPLICIT |
| `require_t02_constrained_scene_consumer` | `T02` | `src/substrate/subject_tick/update.py` | `rt01.t02_relation_binding_checkpoint` | `derive_t02_preverbal_constraint_consumer_view(...).can_consume_constrained_scene` | `repair`/`revalidate` detour | `test_subject_tick_t02_constrained_scene_consumer_requirement_is_path_affecting`, `test_dispatch_t02_constrained_scene_consumer_requirement_is_load_bearing` | EXPLICIT |
| `require_t02_raw_vs_propagated_distinction` | `T02` | `src/substrate/subject_tick/update.py` | `rt01.t02_raw_vs_propagated_integrity_checkpoint` | `derive_t02_preverbal_constraint_consumer_view(...).raw_vs_propagated_distinct` | `revalidate` detour when distinction collapsed | `test_subject_tick_t02_raw_vs_propagated_integrity_requirement_is_second_load_bearing_consequence`, `test_dispatch_t02_raw_vs_propagated_integrity_requirement_is_load_bearing` | EXPLICIT |
| `require_t03_convergence_consumer` | `T03` | `src/substrate/subject_tick/update.py` | `rt01.t03_hypothesis_competition_checkpoint` | `derive_t03_preverbal_competition_consumer_view(...).can_consume_convergence` | `repair`/`revalidate` detour | `test_subject_tick_t03_convergence_consumer_requirement_is_path_affecting`, `test_dispatch_t03_convergence_consumer_requirement_is_load_bearing` | EXPLICIT |
| `require_t03_frontier_consumer` | `T03` | `src/substrate/subject_tick/update.py` | `rt01.t03_hypothesis_competition_checkpoint` | `derive_t03_preverbal_competition_consumer_view(...).frontier_consumer_ready`; shortcut-marked frontier blocks readiness in `t03_hypothesis_competition.policy._build_gate` | `repair` detour | `test_subject_tick_t03_frontier_consumer_requirement_is_path_affecting`, `test_dispatch_t03_frontier_consumer_requirement_is_load_bearing`, `test_t03_downstream_preverbal_consumer_is_load_bearing` | EXPLICIT |
| `require_t03_nonconvergence_preservation` | `T03` | `src/substrate/subject_tick/update.py` | `rt01.t03_hypothesis_competition_checkpoint` | `derive_t03_preverbal_competition_consumer_view(...).nonconvergence_preserved` | `revalidate` detour | `test_subject_tick_t03_nonconvergence_preservation_requirement_is_path_affecting`, `test_dispatch_t03_nonconvergence_preservation_requirement_is_load_bearing` | EXPLICIT |

## B) Non-load-bearing or unresolved for this narrowed index

These flags are explicit in `SubjectTickContext`, but outside this RT01/T01/T02/T03-focused requirement index:
- direct-adjacent out-of-focus flags:
  - `require_t04_focus_ownership_consumer`
  - `require_t04_reportable_focus_consumer`
  - `require_t04_peripheral_preservation`
- world-entry flags:
  - `require_world_grounded_transition`
  - `require_world_effect_feedback_for_success_claim`
- S/A/M/N flags:
  - `require_self_side_claim`
  - `require_world_side_claim`
  - `require_self_controlled_transition_claim`
  - `require_a_line_capability_claim`
  - `require_memory_safe_claim`
  - `require_narrative_safe_claim`
- unresolved/no explicit enforcement branch in current read scope:
  - `require_available_affordance` (TODO)
  - `require_strong_regulation_claim` (TODO)

Note (EXPLICIT): the three `require_t04_*` flags are now state-backed in RT01/dispatch contract views and have direct owner tests, but remain out-of-scope for this T01/T02/T03-focused index.

Reason: kept out to prevent contour expansion and keep index operational for T01/T02/T03 passes.
