# ADR-Sprint7: Minimal World Adapter External Seam Scaffold

## Status
Accepted for narrow BUILD increment.

## Decision
Introduce a minimal production `world_adapter` seam scaffold that materializes typed external observation/action/effect surfaces and a bounded world-link contract consumable by RT01 contour.

## Why
- RT01 contour already has internal authority enforcement (R04/C04/C05 + domains + obedience), but lacked an explicit external seam carrier.
- Without this seam, world-grounded transition claims could drift into packet/telemetry narratives without typed observation/effect evidence.
- This increment adds a required external seam contract without pretending W-line implementation exists.

## What Was Added
- New production package: `src/substrate/world_adapter/*`
  - typed packets: `WorldObservationPacket`, `WorldActionPacket`, `WorldEffectObservationPacket`
  - typed adapter input/state/gate/result/telemetry
  - minimal loop: observation -> action candidate -> effect feedback
  - claim gate:
    - `world_grounded_transition_allowed`
    - `externally_effected_change_claim_allowed`
    - `world_action_success_claim_allowed`
- RT01 contour integration (subject_tick):
  - explicit `rt01.world_seam_checkpoint`
  - context flags for bounded enforcement:
    - `require_world_grounded_transition`
    - `require_world_effect_feedback_for_success_claim`
    - `emit_world_action_candidate`
    - `disable_world_seam_enforcement` (ablation only)
  - when required grounding is missing, runtime detours (repair/revalidate) are enforced.
- Runtime topology enrichment:
  - `WORLD_SEAM` node + `WORLD_SEAM -> RT01` edge
  - mandatory checkpoint includes `rt01.world_seam_checkpoint`
  - source-of-truth surfaces include `world_adapter.state`

## Authority Boundaries Preserved
- C04 remains mode arbitration authority.
- C05 remains validity/invalidation authority.
- R04 remains survival/regulatory authority.
- RT01 remains execution spine and only consumes seam outputs.
- F01 remains transition/provenance spine and does not become world authority owner.

## Explicit Non-Claims
This increment is **not**:
- W-line implementation,
- W01–W06 realization,
- world model,
- embodied cognition architecture,
- full sensorimotor stack,
- environment simulator.

It is only a minimal external seam scaffold for bounded runtime causality discipline.

## What Is Now Claimable
- A typed external world seam exists in production.
- RT01 contour can consume world presence/effect feedback as load-bearing input.
- A bounded class of claims/transitions is now blocked without world presence/effect feedback when such grounding is explicitly required.

## What Is Still Not Claimable
- W-line readiness.
- Repo-wide world grounding adoption.
- Rich environment interaction semantics.
- Planner-grade world orchestration.

## Remaining Debts / Integration Obligations
- Future W01–W06 must define richer world semantics on top of this seam (not inside RT01).
- Future S-line/self-world boundary layers must consume this seam without collapsing to binary presence flags.
- Downstream layers beyond current RT01 contour must adopt world-seam obedience explicitly before broader claims are made.

