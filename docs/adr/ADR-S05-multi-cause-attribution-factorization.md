# ADR-S05 Multi-Cause Attribution Factorization

## Status
Accepted (narrow RT01-hosted frontier slice, hardened)

## Context
S01-S04 provide comparator, seam, ownership-weighted, and interoceptive evidence, but mixed outcomes still risk forced single-cause projection (`self` or `world`) during bounded runtime handling. RT01 needed a typed factorization layer that can keep multi-cause structure explicit, preserve residual uncertainty, and expose a minimal downstream consequence without claiming global causal truth.

## Decision
Introduce and keep `s05_multi_cause_attribution_factorization` as a distinct RT01 segment (`S04 -> S05 -> S_MINIMAL`) that emits a typed factorization packet and gate:
- explicit cause slots;
- bounded shares / bounded intervals;
- compatibility-gated eligibility;
- temporal-fit gating;
- explicit unexplained residual;
- bounded late-evidence re-attribution with packet history.

This increment is load-bearing at RT01 level via narrow contour consequences, not via a broad downstream ecosystem.

## Inputs
S05 consumes typed upstream evidence only:
- `S01` intended-vs-observed comparison outcomes;
- `S02` prediction-boundary/seam state;
- `S03` ownership-weighted learning packet;
- `S04` interoceptive self-binding ledger/state;
- `C04` selected mode;
- `C05` validity/revalidation pressure;
- world presence/effect-correlation signals;
- context-shift / contradicted / withdrawn late-evidence markers.

## Outputs
S05 emits:
- `S05FactorizationPacket`;
- `S05MultiCauseAttributionState` (packet ledger window);
- `S05AttributionGateDecision`;
- `S05Telemetry`;
- `S05` checkpoint in RT01 contour.

## Cause Taxonomy
The current operational taxonomy is:
- `self_initiated_act`
- `endogenous_mode_contribution`
- `interoceptive_or_regulatory_drift`
- `external_or_world_contribution`
- `observation_or_channel_artifact`
- `unexplained_residual`

Internal slots remain separate and are not merged into one `self` bucket.

## Compatibility / Temporal / Residual / Re-attribution Discipline
- Compatibility filtering is eligibility-bearing (`eligible/capped/incompatible/insufficient_basis`) and affects allocation.
- Temporal fit is part of slot eligibility and confidence.
- Residual is first-class and is not forced to zero.
- Late-evidence re-attribution is bounded (blended revision), keeps packet lineage, and does not silently rewrite prior packet ids.

## RT01 Downstream Effect Implemented Now
Hardened narrow effect:
- default RT01 applies split-sensitive caution for `mixed_internal_external` shape (enforced detour to `revalidate_scope` when not already halted and no explicit consumer override is requested);
- checkpoint `required_action` now carries shape markers (`mixed_internal_external`, `world_or_artifact_heavy`, `internal_multi_cause`);
- `S05_SINGLE_CAUSE_COLLAPSE_FORBIDDEN` is shape-aware (emitted only for mixed internal+external collapse-risk profile), not blanket on every S05 checkpoint.

This is intentionally minimal and does not claim full downstream semantic rollout.

## Authority Boundary
S05 is an operational factorization layer. It does not:
- claim global/physical causal truth;
- assign moral blame/responsibility;
- replace S01-S04 authority;
- serve as narrative explanation engine;
- implement global learner or repo-wide attribution policy.

## Non-Claims
This ADR does **not** claim:
- full A/M/N/O/T downstream split-aware ecosystem;
- closure of all oscillation/fossilization regimes;
- high-fidelity probabilistic causal inference;
- repo-wide default adoption beyond RT01 contour.

## Current Limitations / Open Falsifiers
- Split-sensitive downstream use is still narrow (RT01-local guard and restrictions), not broad consumer ecosystem.
- Some route semantics are still consumed through checkpoint contracts rather than deep per-consumer packet semantics.
- Long-horizon stress beyond bounded packet window remains open for future hardening.
