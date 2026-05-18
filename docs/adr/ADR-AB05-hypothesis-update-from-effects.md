# ADR-AB05: Hypothesis Update from Effects

## Why AB5 exists
AB3 provides an open explanation frontier and AB4 provides bounded epistemic basis, but no dedicated seam updated hypothesis support after public effect feedback.

## Relation to AB3/AB4
- AB5 consumes prior AB3 frontier snapshots.
- AB5 may reference AB4 basis refs for provenance.
- AB5 does not generate hypotheses (AB2), does not build frontier from scratch (AB3), and does not select epistemic actions (AB4).

## Why effect is not truth oracle
- Correlated effects can strengthen or weaken support.
- Effects never set `fact_claimed=True` or `cause_confirmed=True`.
- `closure_allowed` is bounded operational status, not fact closure.

## Why request is not confirmation
- AP01 request refs without correlated effects produce blocked/no-update outcomes.
- `request_without_effect_not_confirmation` is explicit.

## Relation to W06/T03/P04/S/P11
- AB5 may consume residue/effect refs but does not execute W06 revision policy.
- AB5 does not run T03 global convergence.
- AB5 does not run P04 counterfactual simulation.
- AB5 does not perform S/P11 ownership closure.

## Authority boundaries
- no action candidate emission
- no AP01 request emission
- no world submission
- no ownership closure
- no fact/cause closure

## Inputs
- prior AB3 frontier
- public effect refs
- public event digest refs
- optional AP01 request refs and AB4 basis refs
- uncertainty/ambiguity markers

## Outputs
- typed support deltas per hypothesis
- strengthened/weakened/disconfirmed/unresolved refs
- closure blocked/allowed status with explicit reason
- optional updated frontier snapshot with preserved non-fact boundary

## Support delta policy
- increase/decrease/disconfirm/unchanged/unresolved/blocked are evidence-bounded.
- strong update requires correlated public effect or event evidence.
- uncorrelated effects cannot drive strong increase.

## Falsifiers
- effect_as_truth_oracle
- request_as_confirmation
- explanation_updates_without_effect
- hypothesis_survives_disconfirming_evidence
- ambiguous_evidence_forces_closure
- hidden_truth_update
- scenario_label_update
- AB5_emits_action_candidate
- AB5_selects_epistemic_action
- AB5_performs_ownership_closure

## Ablations
- no_effect
- uncorrelated_effect
- ambiguous_effect
- disconfirming_effect
- request_without_effect
- remove_evidence_refs
- hidden_eval_only
- no_prior_frontier
- cause_claiming_digest

## World-specific boundary
AB5 substrate update semantics are generic and portable.
No GridWorld map logic, no station/recipe semantics, no Minecraft IDs, no scenario-label policy, and no hidden/eval truth usage.
