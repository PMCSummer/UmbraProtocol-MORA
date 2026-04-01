# ADR-R01: Vital / Allostatic Foundation

## Status
Accepted for phase `R01` over closed `F01` and `F02`.

## Canonical Seams
- Canonical regulation seam: `update_regulation_state(signals, prior_state, context) -> RegulationResult`
- Canonical runtime write seam remains `F01.execute_transition(...)`
- R01 performs no direct runtime mutation outside F01.

## What R01 Now Claims
- Tracks multiple vital axes (`energy`, `cognitive_load`, `safety`, `social_contact`, `novelty`).
- Keeps explicit preferred ranges and computes axis-level deviations.
- Accumulates unresolved burden over time (`load_accumulated`, `pressure`, `unresolved_steps`).
- Represents competing pressures as explicit `TradeoffState`.
- Emits typed downstream modulation surface (`RegulationBias`) that changes with pressure history.
- Emits honest `partial_known` / `abstention` / low-confidence markers when basis is weak.

## What R01 Does Not Claim
- No semantic interpretation, communicative intent, or action selection.
- No dialogue policy, planning, or narrative self-report logic.
- No world-truth assertions.

## Load-Bearing Telemetry
- `RegulationTelemetry` includes:
  - tracked axes and source lineage
  - used preferred ranges
  - computed deviations
  - pressure/load accumulation per axis
  - trade-off result and dominant/suppressed pressures
  - downstream urgency/salience bias surface
  - confidence, partial-known, abstention reasons
  - causal basis and attempted regulation paths

## Explicit Bounds
- Guarantees are scoped to trusted runtime and public API usage.
- If R01 outputs need persistence in runtime-state, it must be routed through F01 transition seam.
- Downstream must consume R01 through bias/gate contract surfaces; bypass outside that surface is out of scope.
- Current competing-needs tradeoff is intentionally minimal and rule-based; richer strategic regulation is deferred.
