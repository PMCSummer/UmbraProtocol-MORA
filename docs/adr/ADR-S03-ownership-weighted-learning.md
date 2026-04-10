# ADR-S03 Ownership-Weighted Learning

## Status
Accepted (first bounded RT01-local production slice)

## Context
S01 materializes intended-vs-observed comparison and S02 materializes prediction-boundary evidence, but there was no dedicated layer that converts this evidence into typed learning-routing decisions. Without S03, mismatch handling can collapse into uniform update pressure, binary self/world blame, or telemetry-only routing.

## Decision
Introduce `s03_ownership_weighted_learning` as a separate typed layer that converts:
- S01 comparison outcomes,
- S02 boundary/seam evidence,
- C05 validity/revalidation pressure,
- current mode/context constraints,

into bounded executable ownership-weighted update packets.

This first slice is RT01-local and packet-routing only. It does not update global model parameters and does not introduce a repo-wide learner stack.

## Bounded Target Taxonomy
S03 packet routing uses explicit typed classes:
- Candidate targets:
  - `internal_control_prediction`
  - `world_side_prediction`
  - `observation_calibration`
  - `anomaly_channel`
- Update classes:
  - `self_update_dominant`
  - `world_update_dominant`
  - `mixed_split_update`
  - `no_safe_update`
  - `observation_channel_recalibration_candidate`
  - `anomaly_only_routing`
- Commit/gating classes:
  - `commit_update`
  - `cap_update_magnitude`
  - `defer_until_revalidation`
  - `route_to_world_model_only`
  - `route_to_internal_model_only`
  - `split_across_targets`
  - `block_due_to_conflict`

## Policy Rules in This Slice
- Same raw mismatch magnitude can route differently depending on ownership evidence.
- Mixed-source evidence does not collapse to binary self/world blame.
- Stale/invalidated/contaminated basis weakens routing via cap, freeze, defer, or no-safe-update.
- Repeated convergent support can strengthen bounded update pressure; one-shot events remain capped.
- Observation-suspicion can route to observation/anomaly channels instead of default self-blame.

## RT01 Integration
S03 is consumed in RT01 through:
- checkpoint: `rt01.s03_ownership_weighted_learning_checkpoint`
- consumer requirements:
  - `require_s03_learning_packet_consumer`
  - `require_s03_mixed_update_consumer`
  - `require_s03_freeze_obedience_consumer`

Unmet required readiness is path-affecting and detours runtime outcome (`repair`/`revalidate`) through existing RT01-local enforcement mechanics.

## Runtime Topology
S03 is integrated after S02 and before T-line in RT01-local contour:
- order segment: `S01 -> S02 -> S03 -> T01`
- topology node: `node.s03_ownership_weighted_learning`
- SoT surfaces:
  - `s03_ownership_weighted_learning.learning_attribution_ledger`
  - `s03_ownership_weighted_learning.target_update_routes`
  - `s03_ownership_weighted_learning.freeze_or_defer_state`

## Non-Goals / Anti-Creep Boundary
This ADR does **not** claim:
- full learner stack or global optimizer,
- repo-wide learning discipline,
- S04 interoceptive self-binding,
- S05 multi-cause factorization,
- full self-model or global attribution engine.

S03 in this slice is strictly bounded to typed ownership-weighted packet routing and RT01-local checkpoint consumption.

