# ADR-P04: Interpersonal counterfactual policy simulation (RT01-hosted narrow slice)

## Status
Accepted (frontier build slice)

## Date
2026-04-26

## Decision
- Introduce `P04` as RT01-hosted narrow contour stage:
  - `... -> V03 -> C06 -> P02 -> P03 -> P04 -> bounded_outcome_resolution -> ...`
  - checkpoint: `rt01.p04_counterfactual_policy_simulation_checkpoint`
- `P04` consumes typed `P02`/`P03` artifacts plus explicit typed policy-candidate simulation input.
- `P04` emits typed branch records, typed comparison matrix, typed excluded-policy records, and typed unstable-region records.
- `P04` is a simulation seam, not a selector, and never mutates policy.

## Scope (narrow and explicit)
- RT01-hosted frontier slice only.
- Load-bearing outputs:
  - typed candidate intake and branch rollout artifacts
  - typed branch-to-branch contrastive matrix
  - first-class unstable/no-clear-dominance comparison states
  - first-class excluded/hazard policy handling
  - typed gate surfaces for branch/comparison/excluded-policy consumers
- Require-path consumers:
  - `require_p04_branch_record_consumer`
  - `require_p04_comparison_consumer`
  - `require_p04_excluded_policy_consumer`
- Default detours (basis-gated):
  - `default_p04_unstable_region_detour`
  - `default_p04_no_clear_dominance_detour`
  - `default_p04_excluded_policy_hazard_detour`

## P04.1 augmentation
- Belief-conditioned interpersonal rollouts are load-bearing in this slice:
  - `belief_conditioned_rollout`
  - `incomplete_information_support`
  - `false_belief_case_support`
  - `misread_case_support`
  - `knowledge_uncertainty_support`
- Branch forecasts must change under belief-state assumptions; this is tested as a deterministic behavior, not a narrative annotation.

## Non-goals / forbidden shortcuts
- No hidden final branch selection or policy mutation inside P04.
- No narrative-only pros/cons substitution for typed branch simulation.
- No map-wide social/world prediction claim.
- No full causal discovery claim.

## Seam-honesty choices
- Direct seam kept to causally used typed artifacts in this slice:
  - `P02` result (episode continuity grounding)
  - `P03` result (bounded learned-prior modulation)
- No decorative direct upstream seams are consumed when they do not deterministically alter the P04 simulation/gate outcome in tested branches.

## Consequences
- Downstream can consume explicit branch records/comparison/exclusions instead of narrative option lists.
- `subject_tick` gate reads typed P04 semantics directly (unstable/no-clear/exclusion/readiness), not checkpoint token only.
- Disabling `disable_p04_enforcement` materially changes narrow-slice behavior.

## Intentionally left open
- Map-wide policy-selection backbone.
- Full social/world prediction architecture.
- Broad consumer ecology beyond RT01-hosted frontier slice.
