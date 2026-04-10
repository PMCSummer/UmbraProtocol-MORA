# ADR-T04: Attention Schema / Focus Ownership Model (First Bounded Build Slice)

## Status
Accepted for narrow `BUILD` increment.

## Decision
Introduce a typed `T04` production layer for attention schema / focus ownership over existing `T03` competition output, with bounded RT01-local consumption.

This increment materializes:
- a first-class typed attention schema state with:
  - `focus_targets`
  - `peripheral_targets`
  - `attention_owner`
  - `focus_mode`
  - `control_estimate`
  - `stability_estimate`
  - `redirect_cost`
  - `reportability_status`
  - `provenance`;
- explicit separation of attention ownership from pure salience/frontrunner prominence;
- explicit peripheral/mixed/provisional preservation for unresolved/competing targets;
- explicit gate/readiness surfaces for RT01-local consumers:
  - focus-ownership consumer,
  - reportable-focus consumer,
  - peripheral-preservation consumer;
- explicit forbidden-shortcut markers for T04-specific collapse risks;
- RT01-local checkpoint integration:
  - `rt01.t04_attention_schema_checkpoint`;
- runtime topology placement:
  - `... T03 -> T04 -> RT01`.

## Why
- `T03` provides competition/frontier structure but does not model focus ownership as its own typed layer.
- Downstream pre-verbal consumers need ownership/control/reportability surfaces, not only winner/salience surfaces.
- Peripheral uncertainty must remain visible instead of being silently collapsed.

## Scope Implemented
- New package: `src/substrate/t04_attention_schema/*`
  - models, policy, downstream contract, telemetry snapshot.
- Subject tick RT01-local integration:
  - T04 built from T03 + bounded C04/C05 conditioning,
  - path-affecting enforcement when explicit T04 consumer requirements are requested.
- Runtime topology integration:
  - T04 node, edge, mandatory checkpoint, and source-of-truth visibility.
- Owner and direct integration tests for bounded T04 behavior.

## Anti-Creep Boundary
This pass is **not**:
- planner,
- global workspace engine,
- theorem prover,
- final verbalizer,
- final action selector,
- emotion layer,
- `O01/O02/O03` implementation,
- full T04 downstream rollout,
- repo-wide adoption.

This pass does **not** claim full silent-thought line completion.

## What Is Now Claimable
- A first bounded RT01-local T04 attention schema layer exists as a typed surface.
- Ownership/control/reportability are inspectable and distinct from raw salience.
- Peripheral/mixed competition residue can be preserved in T04 state.
- T04 checkpoint can be path-affecting under explicit RT01-local T04 consumer requirements.
- Runtime topology now includes T04 between T03 and RT01.

## What Is Not Claimable
- Full T04 completion.
- Full attention line completion.
- O-line/V-line/N-line/D01 downstream implementations.
- Planner/global-workspace semantics.
- Repo-wide T04 adoption.

