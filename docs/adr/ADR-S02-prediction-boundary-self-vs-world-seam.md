# ADR-S02: Prediction Boundary / Self-vs-World Seam (First Bounded Build Slice)

## Status
Accepted for narrow `BUILD` increment.

## Decision
Introduce a typed `S02` production layer for prediction boundary / self-vs-world seam over repeated `S01` comparator outcomes, with bounded RT01-local checkpoint consumption.

This increment materializes:
- a first-class typed seam ledger with per-channel entries:
  - `seam_entry_id`
  - `channel_or_effect_class`
  - `boundary_status`
  - `controllability_estimate`
  - `prediction_reliability_estimate`
  - `external_dominance_estimate`
  - `mixed_source_score`
  - `context_scope`
  - `validity_marker`
  - `boundary_confidence`
  - `evidence_counters`
  - `last_boundary_update`;
- explicit controllability-vs-predictability distinction;
- explicit mixed-source preservation (`mixed_source_boundary`) and no-clean fallbacks;
- explicit invalidation/weakening under context shift, effector-loss with internal history, degraded observation, and C05 revalidation pressure;
- explicit RT01-local checkpoint:
  - `rt01.s02_prediction_boundary_checkpoint`;
- explicit RT01-local consumer requirements:
  - `require_s02_boundary_consumer`
  - `require_s02_controllability_consumer`
  - `require_s02_mixed_source_consumer`.

## Why
- `S01` provides intended-vs-observed comparator signals, but does not maintain a repeated seam ledger across channels/effect classes.
- RT01-local routing needs a bounded seam contract that can distinguish controllable from merely predictable channels.
- Mixed and uncertain cases must stay explicit instead of collapsing into binary self/world.

## Scope Implemented
- New package: `src/substrate/s02_prediction_boundary/*`
  - models, policy, downstream contract, telemetry snapshot.
- Subject tick RT01-local integration:
  - S02 built from S01 + C04/C05/context signals,
  - path-affecting enforcement under explicit `require_s02_*` flags.
- Runtime topology integration:
  - runtime order now includes `S02` between `S01` and `T01`,
  - S02 node/checkpoint/source-of-truth surfaces added.
- Owner and direct integration tests for S02 behavior and RT01-local detours.

## Anti-Creep Boundary
This pass is **not**:
- `S03` ownership-weighted learning,
- `S04` interoceptive self-binding,
- `S05` multi-cause attribution factorization,
- full self-model stack,
- full attribution engine,
- planner/global world-model expansion,
- repo-wide rollout.

This pass does **not** claim full self/nonself seam completion.

## What Is Now Claimable
- A first bounded RT01-local `S02` seam ledger exists and is typed.
- Repeated S01 outcomes can update channel/effect boundary entries.
- Controllability can be separated from predictability in S02 output.
- Mixed-source/uncertain/no-clean boundary states are explicit.
- S02 checkpoint can be path-affecting under explicit RT01-local `require_s02_*` consumers.

## What Is Not Claimable
- Full S-line completion.
- S03/S04/S05 implementation.
- Strong ownership routing beyond this bounded seam.
- Repo-wide S02 adoption.
