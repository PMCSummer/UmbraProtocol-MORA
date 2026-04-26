# P04 Build Working Notes (RT01-hosted frontier slice)

## Contour placement
- Runtime order insertion: `... -> V03 -> C06 -> P02 -> P03 -> P04 -> bounded_outcome_resolution`
- Checkpoint: `rt01.p04_counterfactual_policy_simulation_checkpoint`

## Exact targeted falsifiers
- `narrative-pros-cons-substitutes-simulation`
- `other-agent-stereotype-projection`
- `downstream-preference-backflow`
- `reward-memory-masquerades-as-forecast`
- `unlicensed-policy-leakage`
- `uncertainty-suppression-in-ranking`
- `no-bypass in RT01 slice`

## Why this is not prose option ranking
- Owner surface emits typed `P04BranchRecord`, `P04ComparisonMatrix`, `P04ExcludedPolicyRecord`, `P04UnstableRegion`.
- Branch rollouts contain typed transitions/risk-benefit/protective-load/commitment/uncertainty, not only summaries.
- Comparison readiness can be `comparison_only` or `blocked` when uncertainty dominates; no forced winner.

## Where P04.1 changed mechanism
- Belief-conditioned assumptions are first-class input and telemetry.
- Rollout deltas vary across `incomplete_information`, `false_belief`, `misread`, and `knowledge_uncertainty`.
- Supports are exposed in telemetry + consumer view and tested by deterministic forecast divergence.

## Anti-rescan notes
- For P04 follow-ups, reread only:
  - `src/substrate/p04_interpersonal_counterfactual_policy_simulation/*`
  - `src/substrate/subject_tick/update.py` block around `rt01.p04_counterfactual_policy_simulation_checkpoint`
  - `src/substrate/subject_tick/policy.py` block around P04 typed gate semantics
  - `src/substrate/runtime_topology/policy.py` P03->P04->RT01 order/node/edge/checkpoint/surfaces
  - `src/substrate/runtime_tap_trace.py` P04 allowlist block
- Keep tests focused on:
  - belief-conditioned rollout deltas
  - excluded-policy handling
  - unstable-region/no-clear-dominance detours
  - same-envelope typed-shape downstream divergence

## Known narrow limits
- No map-wide selector or adaptive policy backbone.
- No full social/world predictive certainty claims.
- No claim beyond RT01-hosted narrow frontier slice.
