# ADR-AB-INT SubjectTick Integration

## Status
Accepted

## Why AB-INT exists
AB1–AB7 were built as owner/probe/tool/test seams, but not executed inside live `subject_tick`. AB-INT adds a bounded live contour so abductive artifacts are produced in runtime under public evidence.

## Relation to AB1–AB7 owner/probe belt
- AB-INT reuses owner APIs from AB1–AB7.
- AB-INT does not duplicate owner logic.
- AB-INT does not mutate AB owner authority contracts.

## SubjectTick scheduling order
1. Collect public tick evidence refs.
2. AB1 event digest (public mismatch/residue basis).
3. AB2 hypothesis seed.
4. AB3 explanation frontier.
5. AB5 support update from correlated effects.
6. AB6 bounded attribution.
7. AB7 recipe/automation constraints (only if recipe evidence exists).
8. AB4 epistemic basis (basis-only, before ACP01 consumption path).

## AB4 before ACP01 is basis-only
AB4 output is attached as additional `relevance_basis_refs` for ACP01 input drives. AB4 never emits AP01 requests and never executes.

## AB5/AB6/AB7 boundaries
- AB5: update support; no fact closure; request-only cannot confirm.
- AB6: bounded attribution; no final cause proof.
- AB7: constraints/readiness only; no mature recipe, no automation skill.

## Authority boundaries
AB-INT is non-executing:
- no AP01 publication authority,
- no ACP01 candidate publication authority,
- no world submission authority,
- no fact/cause closure authority.

## Inputs / outputs
### Input
`ABLiveTickInput` with public refs, optional prior frontier/state refs, and optional recipe/value/factory refs.

### Output
`ABLiveTickResult` with AB stage refs, stage traces, counters, blocked/skipped reasons, and strict no-claim/no-action flags.

## Falsifiers
- ab_live_tick_claims_fact
- AB4_bypasses_ACP01
- AB5_effect_as_truth_oracle
- AB7_recipe_candidate_as_skill
- hidden_eval_in_tick
- scenario_label_in_tick
- subject_tick_performance_or_state_drift
- AB_live_emits_action_request
- AB_live_world_submission

## Ablations
- disable_ab1
- remove_public_effect_refs
- remove_prior_frontier
- remove_ap01_refs
- remove_discriminating_tests
- remove_recipe_candidate_refs
- protected_eval_only
- scenario_label_only
- disable_ab_live
- repeated_ticks_without_new_evidence

## Allowed / forbidden claims
Allowed:
- AB live contour produces bounded abductive artifacts under public evidence.

Forbidden:
- AB proves truth/final cause,
- AB chooses/publishes actions,
- AB executes world,
- AB creates mature automation,
- consciousness/general autonomy claims.
