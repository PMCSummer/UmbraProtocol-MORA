# C06 Build Working Notes (Anti-Rescan Anchor)

## Contour Placement
- RT01 hosted order: `... -> V03 -> C06 -> bounded_outcome_resolution -> ...`
- Checkpoint: `rt01.c06_surfacing_candidates_checkpoint`

## Owner Surface
- `src/substrate/c06_surfacing_candidates/models.py`
- `src/substrate/c06_surfacing_candidates/policy.py`
- `src/substrate/c06_surfacing_candidates/downstream_contract.py`
- `src/substrate/c06_surfacing_candidates/telemetry.py`
- `src/substrate/c06_surfacing_candidates/__init__.py`

## Core Typed Outputs
- `C06SurfacedCandidateSet` + `C06CandidateSetMetadata`
- `C06SuppressionReport` + `C06SuppressedItem`
- `C06SurfacingGateDecision`
- contract/consumer views for downstream gate usage
- candidate identity stabilizer facet: `identity_stabilizer` (typed merge stabilizer)

## Require / Default Paths
- Require flags:
  - `require_c06_candidate_set_consumer`
  - `require_c06_suppression_report_consumer`
  - `require_c06_identity_merge_consumer`
- Default (basis-gated) detours:
  - `default_c06_candidate_ambiguity_detour`
  - `default_c06_commitment_carryover_detour`
  - `default_c06_protective_monitor_detour`

## C06.1 Embedded Contract
- `published_frontier_requirement`
- `unresolved_ambiguity_preserved`
- `confidence_residue_preserved`
- publication filtering is seam-honest: unpublished workspace refs are suppressed as `frontier_not_published`; published refs are not suppressed through contradictory publication reasons

## Shortcut Closures in This Slice
- explicit suppression report (no silent drops),
- salience-only suppression reasoning,
- identity merge trace + false-merge guard,
- same-envelope typed-shape downstream divergence (checkpoint token unchanged, downstream outcome class differs),
- alignment-backed provenance branch (C06 consumes V03 alignment anchors/violations, not only raw surface presence),
- no-basis no-default-friction guard.

## Open Limitations (Narrow Slice Honesty)
- RT01 consumer ecology only; no map-wide rollout claim,
- no retention-write ownership,
- no planner authority.

## Test Commands
- `pytest -q tests/substrate/test_c06_surfacing_candidates_build/test_c06_surfacing_candidates_build.py`
- `pytest -q tests/substrate/test_subject_tick_build/test_c06_subject_tick_integration.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_c06_runtime_topology_integration.py`
- `pytest -q tests/tools/test_tick_observability_trace.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `pytest -q tests/substrate/test_subject_tick_build`
