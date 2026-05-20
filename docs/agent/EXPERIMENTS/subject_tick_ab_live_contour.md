# SubjectTick AB Live Contour

## Purpose
Run AB1–AB7 inside `subject_tick` as a conditional public-evidence contour that produces bounded explanatory artifacts.

## Live cases
- `public_effect_mismatch_creates_digest_seed_frontier`
- `prior_frontier_correlated_effect_updates_support`
- `ap01_effect_creates_bounded_attribution`
- `open_frontier_creates_epistemic_basis_before_acp01`
- `recipe_candidate_creates_ab7_constraints`
- `protected_eval_input_blocked`
- `scenario_label_blocked`
- `disabled_ab_live_preserves_subject_tick_behavior`
- `repeated_ticks_without_new_evidence`

## Evidence refs
AB live input and outputs are public refs only:
- observation/effect/residue/uncertainty/conflict refs
- AP01 request/effect correlation refs
- prior frontier refs
- optional recipe/value/factory refs

## Stage traces
Each stage emits `ABLiveStageTrace` with:
- stage name
- ran/skipped
- input/output refs
- authority flags
- blocked reason if applicable

## Claim boundary
AB live contour is bounded:
- no fact closure
- no final cause proof
- no AP01 publication authority
- no world execution authority
- no automation claim

## Why this is not factory runner / automation
AB live stages produce cognitive artifacts (digest, seeds, frontier, updates, attribution, epistemic basis, constraints). They do not execute actions, publish requests, or mutate world state.
