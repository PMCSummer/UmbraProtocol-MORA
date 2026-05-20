# ADR-COST1: Action Cost & Efficiency Comparison

## Status
Accepted for COST1 owner seam build.

## Why COST1 exists after MICRO1
MICRO1 provides bounded operation candidates and lineage. COST1 adds bounded multidimensional comparison artifacts over those candidates without taking selection authority.

## Why COST1 is not action selection
COST1 reports per-dimension lower/higher/unknown cost relations and uncertainty. It does not choose action/candidate/goal, does not publish AP01, and does not execute world actions.

## Relation to MICRO1
- Input: MICRO1 candidate refs/micro-operation refs.
- Output: cost vectors/comparisons that remain evidence-bound annotations.
- No permission lift from cost to action.

## Relation to K-SURF1 provider-declared costs
- Provider-declared costs stay `provider_declared`.
- Provider cost hints cannot be coerced into `observed`.
- Declared-vs-observed mismatch produces residue, never silent overwrite.

## Relation to P16/P17/PATH1/WORLD0/ACTLEARN1/OPTION1
- COST1 may supply bounded comparative evidence.
- It does not bypass P16/P17 gates, does not do PATH1 planning, and does not implement WORLD0 runtime or ACTLEARN1/OPTION1 maturity.

## Multidimensional vector discipline
Each candidate preserves explicit dimensions: material, energy, time, tool_wear, setup, throughput, station_occupation, route, risk, opportunity, uncertainty, evidence_quality.

## Evidence classification discipline
Every dimension is explicitly classified as one of:
- observed
- estimated
- provider_declared
- inferred
- unknown

## Throughput repetition discipline
Throughput support status requires repeated traces. Single observation remains provisional (`single_observation_only`), not final support.

## Declared-vs-observed mismatch residue
When observed and declared costs diverge, COST1 preserves mismatch residue refs and delta artifacts.

## No scalar hiding
Scalar-only scoring without inspectable dimension breakdown is blocked.

## No value assignment
Low cost/efficiency does not imply intrinsic value assignment or action permission.

## No AP01/action permission
COST1 cannot emit AP01 requests, select actions/goals, or submit world actions.

## Allowed claim after build
MORA can build evidence-classified multidimensional cost vectors and bounded comparison artifacts with uncertainty and mismatch residue preservation.

## Forbidden claims
- COST1 chooses best action.
- COST1 proves final efficiency truth.
- COST1 publishes AP01.
- COST1 executes the world.
- COST1 provides optimizer/planner/pathfinder/factory scheduler behavior.

## Falsifiers
- declared cost treated as observed
- scalar score hides dimensions
- throughput support claimed from single trace
- comparison outputs selected action/candidate
- hidden backend/scenario costs accepted
- cost comparison assigns intrinsic value

## Ablations
- no source refs
- observed without effect/observation refs
- provider-declared marked observed
- hidden backend cost payload
- unknown dimension defaulted to zero
- mismatch without residue
- selected action/AP01/world/value attempts
