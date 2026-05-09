# ADR-M01: Homeostatic Salience Imprint (Narrow Frontier Slice)

## Status
Accepted for narrow frontier build slice.

## Scope
M01 implements a typed homeostatic salience imprint seam in RT01 only.
It is not a full memory stack and does not implement M02/M03.

## Decision
M01 emits typed imprint packets only when trace evidence is coupled to observed regulatory perturbation/strain/relief/recovery/stabilization under temporal and attribution limits.

M01 explicitly does not claim:
- general importance
- reward function semantics
- narrative/autobiographical relevance
- policy selection authority
- global value or full-memory correctness

## Mechanistic Surface
Owner package: `src/substrate/m01_homeostatic_salience_imprint/*`

Typed surfaces include:
- trace input
- regulatory axis deltas
- temporal coupling evidence
- attribution evidence
- imprint decision type
- imprint packet with retention/replay/retrieval bias
- transfer limits and allowed memory-use constraints
- ledger, gate decision, telemetry, scope marker

Downstream contract includes machine-readable consumer views and require guards for:
- imprint-packet consumer readiness
- axis-scope preserving consumption

## Runtime Placement
Narrow contour placement in subject tick/runtime topology:

`rt01.w01_bounded_world_loop_checkpoint`
-> `rt01.m01_homeostatic_salience_imprint_checkpoint`
-> `rt01.outcome_resolution_checkpoint`

## Load-Bearing Effects
M01 is not telemetry-only:
- subject tick checkpoint required actions include M01 require/default routes
- downstream gate consumes typed M01 state (`m01_*` fields)
- same checkpoint id/required-action envelope can diverge downstream by typed M01 shape

## Guardrails
M01 preserves first-class uncertainty and refuses shortcut promotion:
- novelty/recency/outcome-only signals do not create strong homeostatic imprint without regulatory linkage
- out-of-window/missing timing downgrades to stale-basis/no-safe paths
- contested timing is explicitly capped and cannot promote strong imprint decisions
- externally dominated/artifact-risk attribution downgrades imprint confidence/strength
- transfer limits are always preserved for anti-overgeneralization
- repeated-pattern reinforcement is bounded to structural overlap (axis + sign), with non-overlap prevented from reinforcement promotion
- downstream consumer packets expose affected axis scope and transfer limits as typed fields

## Known Limits
- No retention/retrieval/replay/consolidation subsystem implementation.
- No map-wide memory migration.
- No M02/M03 behavior claim.
