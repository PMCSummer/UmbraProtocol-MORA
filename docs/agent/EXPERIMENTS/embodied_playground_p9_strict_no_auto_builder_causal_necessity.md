# P9 — Strict No-Auto-Builder & Causal Necessity Mode

## Purpose
P9 adds experiment-side causal-necessity evaluation. It verifies that removing critical seams or basis paths changes behavior in expected, claim-honest directions.

## Strict No-Auto-Builder
Strict mode rejects silent downstream fabrication:
- candidate/request/effect paths must be supported by upstream public basis.
- missing basis must lead to abstain/block/revalidation, not fabricated continuation.

## Ablation specs
Implemented ablations:
- no_acp01
- no_ap01
- no_drive_basis
- no_public_object_basis
- no_action_surface_basis
- no_proximity_basis
- no_capacity_basis
- no_effect_feedback
- no_residue_feedback
- no_permission_basis
- no_prediction_permission_separation
- hidden_eval_substitution_attempt

## Expected degradation table (compact)
- `no_acp01` => no candidate/publication/submission
- `no_ap01` => no publication/submission
- `no_drive_basis` => visible object alone must not publish
- `no_public_object_basis` => drive alone must not publish
- `no_action_surface_basis` => no fabricated action surface path
- `no_proximity_basis` => no pickup publication
- `no_capacity_basis` => no pickup publication
- `no_effect_feedback` => no effect-feedback claim
- `no_residue_feedback` => blocked/failure must not be silently erased
- `no_permission_basis` => no clean publication
- `no_prediction_permission_separation` => desire/prediction not permission
- `hidden_eval_substitution_attempt` => no hidden/eval substitution

## Falsifiers
- silent_bundle_fabrication
- ablation_no_effect
- candidate_without_acp01
- world_submission_without_ap01
- visible_object_alone_becomes_action
- drive_alone_becomes_action
- action_surface_fabricated
- pickup_without_proximity_basis
- pickup_without_capacity_basis
- permission_without_w04_like_basis
- prediction_or_desire_as_permission
- failure_erased_without_w06_like_residue
- effect_feedback_fabricated
- hidden_basis_substitution
- forbidden_fallback_after_ablation
- strict_mode_not_enforced
- causal_necessity_report_overclaims
- diagnostic_success_counted_as_causal_necessity

## Metrics
- ablation_sensitivity_score
- silent_fabrication_count
- unexpected_success_count
- boundary_integrity_score
- basis_flow_integrity_score
- degradation_match_rate
- hidden_substitution_count
- no_effect_ablation_count

## What P9 supports
P9 supports causal-load-bearing evidence for the current embodied contour under controlled GridWorld scenarios.

## What P9 does not prove
P9 does not prove consciousness, general autonomy, general intelligence, open-ended planning, or real-world competence.

## Demo
```bash
python tools/embodied_causal_necessity_demo.py --list-ablations
python tools/embodied_causal_necessity_demo.py --scenario visible_item_pickup_available --ablation no_acp01 --strict --report
python tools/embodied_causal_necessity_demo.py --scenario visible_item_pickup_available --ablation no_ap01 --strict --json
python tools/embodied_causal_necessity_demo.py --scenario hidden_map_not_visible --ablation hidden_eval_substitution_attempt --strict --json
python tools/embodied_causal_necessity_demo.py --matrix --strict --report
```
