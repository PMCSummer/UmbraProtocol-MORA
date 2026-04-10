# `runtime_topology/policy.py` section map

File: `src/substrate/runtime_topology/policy.py`

## Graph / bundle / dispatch sections

| Section | Function | What it owns |
|---|---|---|
| Tick graph build | `build_minimal_runtime_tick_graph()` | runtime order, nodes, edges, mandatory checkpoints, source-of-truth surfaces |
| Bundle build | `build_minimal_runtime_topology_bundle()` | runtime entry, execution spine phase, enforcement hooks, f01 route |
| Dispatch decision | `evaluate_runtime_dispatch_decision(request, bundle)` | route-class legality, non-production opt-in rules, f01 persistence constraints |
| Ablation detection | `_context_has_ablation_flags(context)` | production-route rejection conditions for ablation-like contexts |

## Route classes (EXPLICIT)
From `evaluate_runtime_dispatch_decision(...)` branches:
- `production_contour`
- `helper_path`
- `test_only_ablation`

## Mandatory checkpoints (EXPLICIT)
Declared in `build_minimal_runtime_tick_graph()`:
- `rt01.c04_mode_binding`
- `rt01.c05_legality_checkpoint`
- `rt01.downstream_obedience_checkpoint`
- `rt01.world_seam_checkpoint`
- `rt01.world_entry_checkpoint`
- `rt01.s_minimal_contour_checkpoint`
- `rt01.a_line_normalization_checkpoint`
- `rt01.m_minimal_contour_checkpoint`
- `rt01.n_minimal_contour_checkpoint`
- `rt01.s01_efference_copy_checkpoint`
- `rt01.s02_prediction_boundary_checkpoint`
- `rt01.s03_ownership_weighted_learning_checkpoint`
- `rt01.t01_semantic_field_checkpoint`
- `rt01.t02_relation_binding_checkpoint`
- `rt01.t02_raw_vs_propagated_integrity_checkpoint`
- `rt01.t03_hypothesis_competition_checkpoint`
- `rt01.t04_attention_schema_checkpoint` *(direct adjacent, out-of-focus for T01/T02/T03 work)*
- `rt01.outcome_resolution_checkpoint`

## Source-of-truth surfaces (EXPLICIT)
- `runtime_state.domains`
- `rt01.downstream_obedience_checkpoint`
- `world_adapter.state`
- `world_entry_contract.episode`
- `s_minimal_contour.boundary_state`
- `a_line_normalization.capability_state`
- `m_minimal.lifecycle_state`
- `n_minimal.commitment_state`
- `s01_efference_copy.latest_comparison`
- `s01_efference_copy.pending_predictions`
- `s01_efference_copy.prediction_validity`
- `s02_prediction_boundary.seam_ledger`
- `s02_prediction_boundary.controllability_vs_predictability`
- `s03_ownership_weighted_learning.learning_attribution_ledger`
- `s03_ownership_weighted_learning.target_update_routes`
- `s03_ownership_weighted_learning.freeze_or_defer_state`
- `t01_semantic_field.active_scene`
- `t02_relation_binding.constrained_scene`
- `t02_relation_binding.raw_vs_propagated_distinction`
- `t03_hypothesis_competition.competition_ledger`
- `t03_hypothesis_competition.publication_frontier`
- `t04_attention_schema.focus_ownership` *(direct adjacent, out-of-focus for T01/T02/T03 work)*
- `t04_attention_schema.focus_targets` *(direct adjacent, out-of-focus for T01/T02/T03 work)*

## Search anchors (fast)
- Runtime order: `runtime_order=(`
- S01/S02/S03/T01/T02/T03/T04 nodes: `node.s01_efference_copy`, `node.s02_prediction_boundary`, `node.s03_ownership_weighted_learning`, `node.t01_semantic_field`, `node.t02_relation_binding`, `node.t03_hypothesis_competition`, `node.t04_attention_schema`
- S01/S02/S03/T01/T02/T03/T04 edges: `C04", target_phase="S01"`, `C05", target_phase="S01"`, `S01", target_phase="S02"`, `S02", target_phase="S03"`, `C04", target_phase="S03"`, `C05", target_phase="S03"`, `S03", target_phase="T01"`, `T01", target_phase="T02"`, `T02", target_phase="T03"`, `T03", target_phase="T04"`, `T04", target_phase="RT01"`
- Mandatory checkpoints: `mandatory_checkpoint_ids=`
- SoT surfaces: `source_of_truth_surfaces=`
- Route restrictions: `RuntimeDispatchRestriction.`
- Route consequences: `RuntimeRouteBindingConsequence.`
- Non-production + persistence rules: `allow_non_production_consumer_opt_in`, `persist_via_f01`
