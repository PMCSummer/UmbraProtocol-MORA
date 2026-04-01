# ADR-R02: Internal Self-Regulation Affordances

## Status
Accepted for phase `R02` over closed `F01`, `F02`, and `R01`.

## Canonical Seams
- Canonical affordance seam: `generate_regulation_affordances(regulation_state, capability_state, context) -> AffordanceResult`
- Canonical runtime write seam remains `F01.execute_transition(...)`
- R02 performs no direct runtime-state mutation outside F01.

## What R02 Now Claims
- Transforms typed R01 regulation state into typed internal regulation affordance candidates.
- Produces candidate landscape (not hidden winner) with per-candidate:
  - target axes
  - expected effect and effect class (immediate relief / delayed recovery / preventive regulation / protective suppression)
  - cost / latency / duration / risk
  - applicability and blockers
  - tradeoff profile
  - confidence and uncertainty markers
- Distinguishes `available`, `blocked`, `unavailable`, `unsafe`, and `provisional`.
- Exposes downstream gate surface that consumes typed candidates and returns restrictions/bias hints.

## What R02 Does Not Claim
- No final action selection or policy commitment.
- No semantics, world-truth assertions, or dialogue logic.
- No planner/executive arbitration.
- No guaranteed intervention success claim.

## Load-Bearing Telemetry
- `AffordanceTelemetry` includes:
  - regulation input snapshot and source lineage
  - capability constraints snapshot
  - generated candidate IDs and statuses
  - candidate causal/provenance basis
  - expected effect surface
  - cost/risk surface
  - tradeoff surface
  - downstream gate decision (accepted/rejected IDs, restrictions, bias hints)
  - confidence, abstention reason, and attempted affordance paths

## Explicit Bounds
- Guarantees are scoped to trusted runtime and public API usage.
- If persistence is required, R02 outputs are handed off only through F01 transition seam.
- Downstream bypass outside typed gate/policy surface is not prevented by hostile runtime controls and is out of scope.
- Current tradeoff estimation is intentionally minimal and rule-based; richer strategy learning is deferred to later phases.
- `available` candidates and any later selected action remain separate stages by contract.
