# P11 / Self-World Ownership Perturbation Battery

## Purpose
P11 adds an experiment-side perturbation battery that stress-tests ownership boundaries:
- `self_action`
- `world_process`
- `other_actor`
- `mixed`
- `unknown`

The battery checks that MORA does not overclaim "I caused it" without AP01/effect correlation evidence.

## Relation to P10
P10 proved body-action execution through:
`subject_tick -> ACP01 -> AP01 -> world effect -> next observation`.

P11 reuses that path as controlled self-action evidence and then perturbs the environment with world-only, other-actor, mixed, delayed, unknown, and mismatch cases.

## Relation to AB1/AB2/AB3
- AB1 event digest refs are optional evidence markers.
- AB2 hypothesis seed refs are optional ambiguity markers.
- AB3 frontier refs are optional unresolved-conflict markers.

P11 does not perform AB2 seed generation or AB3 frontier ranking. It consumes evidence refs only.

## Relation to S01-S05
S01-S05 already own substrate self/world mechanisms:
- S01 efference comparison
- S02 prediction boundary
- S03 ownership-weighted learning
- S05 multi-cause factorization

P11 does not replace these substrate owners. It is an experiment-side battery that audits evidence discipline and boundary honesty under perturbation.

## Why this is a battery, not AB6
P11 does not implement full attribution closure or global causal model.
It only checks whether ownership claims remain bounded and evidence-linked under perturbations.

## Scenario matrix
- `self_caused_move_effect`
- `self_caused_pickup_effect`
- `world_only_object_change`
- `other_actor_object_change`
- `mixed_self_and_world_effect`
- `delayed_self_effect`
- `unknown_unexplained_effect`
- `sensor_or_projection_mismatch`
- `blocked_self_action_no_world_delta`
- `hidden_eval_only_cause`

## Falsifiers
- `ownership_overclaim`
- `world_change_claimed_as_self_action`
- `other_action_claimed_as_self_action`
- `mixed_cause_erased`
- `unknown_cause_forced_closure`
- `delayed_effect_misattributed_immediate`
- `self_action_without_ap01_ref`
- `ap01_request_as_effect`
- `effect_without_correlation_claimed_self`
- `blocked_action_claimed_success`
- `hidden_truth_attribution`
- `scenario_label_attribution`
- `sensor_mismatch_claimed_world_fact`
- `ownership_confidence_without_evidence`
- `attribution_emits_action_request`
- `attribution_updates_hypotheses`
- `attribution_selects_epistemic_action`
- `p11_report_overclaims`

## Ablations
- `remove_ap01_request_ref`
- `remove_effect_correlation`
- `remove_external_actor_marker`
- `remove_mixed_cause_marker`
- `remove_delay_marker`
- `hidden_eval_only`
- `remove_public_observation_refs`
- `blocked_effect_without_delta`

## Allowed claim
"MORA can preserve bounded self/world/other/mixed/unknown ownership distinctions in controlled perturbation scenarios without overclaiming self-causation."

## Forbidden claims
- consciousness
- full self-model
- complete causal attribution
- general theory-of-mind
- general agency proof

## World-specific boundary
No world-specific ownership rules were added to substrate. P11 perturbations remain in experiment-side harness data.

## Run demo
```bash
python tools/embodied_ownership_perturbation_demo.py --list-scenarios
python tools/embodied_ownership_perturbation_demo.py --scenario self_caused_move_effect --report
python tools/embodied_ownership_perturbation_demo.py --scenario world_only_object_change --json
python tools/embodied_ownership_perturbation_demo.py --scenario other_actor_object_change --report
python tools/embodied_ownership_perturbation_demo.py --scenario mixed_self_and_world_effect --json
python tools/embodied_ownership_perturbation_demo.py --scenario hidden_eval_only_cause --json
```
