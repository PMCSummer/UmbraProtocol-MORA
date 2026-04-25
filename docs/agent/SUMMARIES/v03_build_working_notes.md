# V03 Build Working Notes

## Contour Placement
- RT01 hosted order (current): `... -> O04 -> R05 -> V01 -> V02 -> V03 -> RT01 outcome resolution`
- Checkpoint: `rt01.v03_constrained_realization_checkpoint`

## Typed Surfaces
- Package: `src/substrate/v03_surface_verbalization_causality_constrained_realization/`
- Core typed objects:
  - `V03RealizationInput`
  - `V03RealizedUtteranceArtifact`
  - `V03SurfaceSpanAlignment`
  - `V03RealizationAlignmentMap`
  - `V03ConstraintSatisfactionReport`
  - `V03RealizationFailureState`
  - `V03RealizationGateDecision`
  - `V03ScopeMarker`
  - `V03Telemetry`
  - `V03ConstrainedRealizationResult`
  - `V03RealizationContractView`
  - `V03RealizationConsumerView`

## Require / Default Paths (RT01)
- Require:
  - `require_v03_realization_consumer`
  - `require_v03_alignment_consumer`
  - `require_v03_constraint_report_consumer`
- Default (basis-gated):
  - `default_v03_realization_failure_detour`
  - `default_v03_alignment_violation_detour`
  - `default_v03_boundary_order_detour`
- No-basis path remains `v03_optional` and does not add default friction.

## Mechanistically Real in Current Slice
- Plan-faithful surface realization from typed V02 segments.
- Segment-to-surface span alignment map with index ranges.
- Per-segment `ordering_pass` is now computed from V02 ordering edges (no hardcoded truthy alignment flag).
- Hard constraint checks:
  - qualifier locality,
  - ordering / boundary-before-explanation,
  - blocked expansion leakage,
  - protected omission violation,
  - implicit commitment leakage under denied promise-like path.
- Structured narrowed failure path (`partial_realization_only` / `replan_required`) on hard violations.
- Downstream policy branching reads typed V03 fields (not only checkpoint token).
- R05 modulation reaches V03 through V02 plan structure; no direct R05 policy input seam in V03.

## Shortcut Closures in This Build
- No prose-only draft masquerading as plan realization object.
- Qualifier-locality failures are machine-detected, not reason-text-only.
- Blocked expansion leak is machine-detected.
- Protected omission leak is machine-detected.
- Boundary order violations force constrained detour/failure handling.
- V03 no-basis path does not create blanket default friction.
- No-bypass contrast strengthened: enabling/disabling V03 changes deterministic downstream execution mode under the same broad RT01 contour.

## Open Limitations (Narrow, Honest)
- V03 remains RT01-hosted first slice; no map-wide realization guarantees.
- Token/checkpoint architecture remains globally present; this pass adds narrow typed-semantic branches only.
- No full decoder architecture rewrite and no broad V03 consumer rollout.

## Test Commands Used (This Pass)
- `pytest -q tests/substrate/test_v03_surface_verbalization_causality_constrained_realization_build/test_v03_surface_verbalization_causality_constrained_realization_build.py`
- `pytest -q tests/substrate/test_subject_tick_build/test_v03_subject_tick_integration.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_v03_runtime_topology_integration.py`
- `pytest -q tests/tools/test_tick_observability_trace.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `pytest -q tests/substrate/test_subject_tick_build`
