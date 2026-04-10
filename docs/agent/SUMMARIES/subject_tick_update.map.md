# `subject_tick/update.py` map (reread substitute)

File: `src/substrate/subject_tick/update.py`

## Section anchors (keep this small)

| Section | Anchor token(s) | Key checkpoint(s) | Key require_* |
|---|---|---|---|
| Entry and contour setup | `def execute_subject_tick(` | n/a | context flags unpack |
| Core RT01 pre-T gates | `rt01.c04_mode_binding`, `rt01.c05_legality_checkpoint`, `rt01.downstream_obedience_checkpoint`, `rt01.critical_gate_checkpoint` | core RT01 checkpoints | none |
| Non-T integration gates (outside this map focus) | `rt01.world_seam_checkpoint`, `rt01.world_entry_checkpoint`, `rt01.s_minimal_contour_checkpoint`, `rt01.a_line_normalization_checkpoint`, `rt01.m_minimal_contour_checkpoint`, `rt01.n_minimal_contour_checkpoint` | non-T mandatory checkpoints | world/s/a/m/n flags |
| T01 consume + gate | `build_t01_active_semantic_field`, `t01_preverbal_view`, `rt01.t01_semantic_field_checkpoint` | `rt01.t01_semantic_field_checkpoint` | `require_t01_preverbal_scene_consumer`, `require_t01_scene_comparison_consumer` |
| T02 consume + gate | `build_t02_constrained_scene`, `t02_preverbal_view`, `rt01.t02_relation_binding_checkpoint` | `rt01.t02_relation_binding_checkpoint` | `require_t02_constrained_scene_consumer` |
| T02 integrity gate | `t02_raw_vs_propagated_distinct`, `rt01.t02_raw_vs_propagated_integrity_checkpoint` | `rt01.t02_raw_vs_propagated_integrity_checkpoint` | `require_t02_raw_vs_propagated_distinction` |
| T03 consume + gate | `build_t03_hypothesis_competition`, `t03_preverbal_view`, `rt01.t03_hypothesis_competition_checkpoint` | `rt01.t03_hypothesis_competition_checkpoint` | `require_t03_convergence_consumer`, `require_t03_frontier_consumer`, `require_t03_nonconvergence_preservation` |
| T04 adjacent consume + gate *(out-of-focus)* | `build_t04_attention_schema`, `t04_preverbal_view`, `rt01.t04_attention_schema_checkpoint` | `rt01.t04_attention_schema_checkpoint` | `require_t04_focus_ownership_consumer`, `require_t04_reportable_focus_consumer`, `require_t04_peripheral_preservation` |
| T04 require-flag state persistence *(out-of-focus)* | `t04_require_focus_ownership_consumer=`, `t04_require_reportable_focus_consumer=`, `t04_require_peripheral_preservation=` | impacts downstream contract/state snapshot exposure | none (state export anchor) |
| Outcome finalize | `execution_stance =`, `rt01.outcome_resolution_checkpoint` | `rt01.outcome_resolution_checkpoint` | none |
| Result + helper exports | `subject_tick_result_to_payload`, `persist_subject_tick_result_via_f01`, `build_subject_tick_runtime_domain_update`, `build_subject_tick_runtime_route_auth_context` | domain-write/auth context | none |

## Search anchors
- `checkpoint_id="rt01.`
- `source_contract=`
- `build_t01_active_semantic_field`
- `build_t02_constrained_scene`
- `build_t03_hypothesis_competition`
- `build_t04_attention_schema`
- `require_t01_`, `require_t02_`, `require_t03_`
- `require_t04_`
- `rt01.outcome_resolution_checkpoint`

## What not to reread if unchanged
- T03-only change: skip world/S/A/M/N + T01/T02 blocks.
- T03-only change (without T03->T04 integration edits): skip T04 block.
- T02-only change: skip T03 block and non-T blocks.
- Runtime topology-only change: reread only checkpoint ids and source contracts touched by dispatch tests.
- Doc-only change: do not reread full function; check this map + `CHECKPOINT_INDEX.md`.
