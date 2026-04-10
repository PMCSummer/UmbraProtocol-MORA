# RT01 Contour Map (RT01/S02/T01/T02/T03 focus)

## Runtime Order (EXPLICIT)
Source: `src/substrate/runtime_topology/policy.py::build_minimal_runtime_tick_graph`

| Order |
|---|
| `R -> C01 -> C02 -> C03 -> C04 -> C05 -> S01 -> S02 -> T01 -> T02 -> T03 -> T04 -> RT01` |

## Route Classes
Source: `src/substrate/runtime_topology/policy.py::evaluate_runtime_dispatch_decision` (+ dispatch tests)

| Route class token | Meaning | confidence |
|---|---|---|
| `production_contour` | Lawful production route. | EXPLICIT |
| `helper_path` | Non-lawful helper route, explicit bounded allowance + non-production opt-in required. | EXPLICIT |
| `test_only_ablation` | Test-only route, explicit allow + ablation basis + non-production opt-in required. | EXPLICIT |

## Mandatory Checkpoints (EXPLICIT)
Source: `src/substrate/runtime_topology/policy.py::mandatory_checkpoint_ids`

- `rt01.c04_mode_binding`
- `rt01.c05_legality_checkpoint`
- `rt01.downstream_obedience_checkpoint`
- `rt01.world_seam_checkpoint`
- `rt01.world_entry_checkpoint`
- `rt01.s_minimal_contour_checkpoint`
- `rt01.a_line_normalization_checkpoint`
- `rt01.m_minimal_contour_checkpoint`
- `rt01.n_minimal_contour_checkpoint`
- `rt01.s01_efference_copy_checkpoint` *(direct adjacent, out-of-focus for this map)*
- `rt01.s02_prediction_boundary_checkpoint` *(direct adjacent, now tracked in this map)*
- `rt01.t01_semantic_field_checkpoint`
- `rt01.t02_relation_binding_checkpoint`
- `rt01.t02_raw_vs_propagated_integrity_checkpoint`
- `rt01.t03_hypothesis_competition_checkpoint`
- `rt01.t04_attention_schema_checkpoint` *(direct adjacent, out-of-focus for this map)*
- `rt01.outcome_resolution_checkpoint`

## Source-of-Truth Surfaces
Source: `src/substrate/runtime_topology/policy.py::source_of_truth_surfaces`

- `runtime_state.domains`
- `rt01.downstream_obedience_checkpoint`
- `s01_efference_copy.latest_comparison` *(direct adjacent, out-of-focus for this map)*
- `s01_efference_copy.pending_predictions` *(direct adjacent, out-of-focus for this map)*
- `s01_efference_copy.prediction_validity` *(direct adjacent, out-of-focus for this map)*
- `s02_prediction_boundary.seam_ledger` *(direct adjacent, now tracked in this map)*
- `s02_prediction_boundary.controllability_vs_predictability` *(direct adjacent, now tracked in this map)*
- `t01_semantic_field.active_scene`
- `t02_relation_binding.constrained_scene`
- `t02_relation_binding.raw_vs_propagated_distinction`
- `t03_hypothesis_competition.competition_ledger`
- `t03_hypothesis_competition.publication_frontier`
- `t04_attention_schema.focus_ownership` *(direct adjacent, out-of-focus for this map)*
- `t04_attention_schema.focus_targets` *(direct adjacent, out-of-focus for this map)*
- Other contour dependencies (outside T01/T02/T03 focus): `world_adapter.state`, `world_entry_contract.episode`, `s_minimal_contour.boundary_state`, `a_line_normalization.capability_state`, `m_minimal.lifecycle_state`, `n_minimal.commitment_state`

## Owner Files (EXPLICIT)
- Runtime topology graph/dispatch policy:
  - `src/substrate/runtime_topology/policy.py`
  - `src/substrate/runtime_topology/models.py`
  - `src/substrate/runtime_topology/dispatch.py`
  - `src/substrate/runtime_topology/downstream_contract.py`
  - `src/substrate/runtime_topology/telemetry.py`
- RT01 execution contour integration:
  - `src/substrate/subject_tick/update.py`
  - `src/substrate/subject_tick/policy.py`
  - `src/substrate/subject_tick/downstream_contract.py`
  - `src/substrate/subject_tick/models.py`
  - `src/substrate/subject_tick/telemetry.py`
- Phase packages:
  - `src/substrate/s02_prediction_boundary/*` *(direct adjacent, now tracked in this map)*
  - `src/substrate/t01_semantic_field/*`
  - `src/substrate/t02_relation_binding/*`
  - `src/substrate/t03_hypothesis_competition/*`
  - `src/substrate/t04_attention_schema/*` *(direct adjacent, out-of-focus for this map)*

## Direct Tests (EXPLICIT)
- Runtime topology owner tests:
  - `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- RT01 owner tests:
  - `tests/substrate/test_subject_tick_build/test_subject_tick_build.py`
- T03 owner tests:
  - `tests/substrate/test_t03_hypothesis_competition_build/test_t03_hypothesis_competition_build.py`
- S02 direct-adjacent owner tests:
  - `tests/substrate/test_s02_prediction_boundary_build/test_s02_prediction_boundary_build.py`
- Stage contour checks:
  - `tests/substrate/test_stage_contour/test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_c04_c05_subject_tick.py`
- Direct-adjacent S01 hardening checks (same owner packs, out-of-focus for this map):
  - `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k s01`
  - `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k s01`
- Direct-adjacent S02 hardening/build checks (same owner packs + owner pack):
  - `pytest -q tests/substrate/test_s02_prediction_boundary_build/test_s02_prediction_boundary_build.py`
  - `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k s02`
  - `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k s02`
- Direct-adjacent T04 hardening checks (same owner packs, out-of-focus for this map):
  - `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k t04`
  - `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k t04`

## Forbidden Broadening Notes
- RT01 seam: do not move mode semantics from C04 or validity semantics from C05 into RT01.
- T01/T02/T03 seams: do not implement downstream phases (`T02/T03/O01` from T01, `T03/O01` from T02, `O01/O02/O03` from T03).
- ADR-T03 boundary: first bounded T03 slice only; no `T04`, no `O*`, no planner/theorem prover.
- S01/T04 presence in runtime order/checkpoints is a direct adjacency; do not widen this map to S01/T04 phase semantics unless explicitly requested.
- S02 presence in runtime order/checkpoints is a direct adjacency; keep S02 claims RT01-local and do not expand into S03/S04/S05 semantics from this map.
- Do not claim repo-wide rollout from this contour map.
