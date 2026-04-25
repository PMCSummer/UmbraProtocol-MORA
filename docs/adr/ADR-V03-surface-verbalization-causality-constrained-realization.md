# ADR-V03 Surface Verbalization Causality / Constrained Realization

## Status
Accepted (frontier RT01-hosted first slice)

## Context
Before V03, RT01 had V02 typed utterance-plan state but no explicit typed constrained-realization layer proving that surface output remains a causal continuation of plan constraints.

This left an open seam where fluent surface realization could drift from:
- segment ordering requirements,
- mandatory qualifier locality,
- blocked expansion / protected omission constraints,
- commitment-denial boundaries.

## Decision
Introduce `v03_surface_verbalization_causality_constrained_realization` as a distinct RT01 segment after `V02` and before bounded outcome resolution.

This slice provides:
- typed realization artifact + span alignment map;
- typed hard-constraint report (ordering/locality/omission/leak checks);
- structured failure/narrowed-realization fallback;
- explicit checkpoint + require/default detour effects;
- downstream policy consumption of typed V03 semantics (not token-only).

Seam discipline note:
- `R05` influence is consumed in this slice through upstream `V02` plan shape and constraints.
- `V03` does not claim a direct `R05 -> V03` decision input seam in this frontier build.

## Scope Boundary (What This Slice Does Not Claim)
This ADR does **not** claim:
- map-wide decoder-token enforcement,
- full V03/V-line realization rollout outside RT01 hosted contour,
- broad V03 replacement of downstream verbalization subsystems,
- planner-wide or discourse-memory-wide realization governance.

## Mechanistically Real in Code
- Typed surfaces:
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
- Checkpoint:
  - `rt01.v03_constrained_realization_checkpoint`
- Require path:
  - `require_v03_realization_consumer`
  - `require_v03_alignment_consumer`
  - `require_v03_constraint_report_consumer`
- Default path (basis-gated):
  - `default_v03_realization_failure_detour`
  - `default_v03_alignment_violation_detour`
  - `default_v03_boundary_order_detour`
- Hard constraints over soft fluency:
  - qualifier locality violations are detected and surfaced;
  - blocked expansion leakage is detected and surfaced;
  - boundary-before-explanation ordering is enforced;
  - implicit commitment leak is detected when V01 denied promise-like acts.

## Explicit Shortcut Prohibitions in This Slice
- No decoder-side silent replanning beyond V02 plan/constraints.
- No qualifier presence-only pass: locality is checked per aligned segment.
- No blocked expansion / protected omission leakage accepted for fluency.
- No silent hard-constraint relaxation.
- No telemetry-only realization shim.

## Open Seams Intentionally Left Open
- Full token-level realization enforcement across map-wide consumers.
- Mature V03-to-V-line realization ecosystem beyond RT01 hosted gate.
- Rich discourse-memory realization dependencies outside current frontier slice.
