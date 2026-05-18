# P17 Mini-Factory Chain (Embodied Playground)

## Purpose
P17 proves bounded multi-step chain validation with per-step verification and residue propagation.

## Relation to P13/P14/P15/P16
- P13: confounder/disconfirmation gates remain active.
- P14: station affordance refs required for station-linked steps.
- P15: recipe/precursor candidates are constraints, not mature skills.
- P16: value/means chains justify intermediates as means.

## Relation to AB7
AB7 constraints/readiness are required. Candidate readiness never becomes automation execution in P17.

## Why P17 is bounded chain proof
P17 verifies each step via public refs and effect correlation; no general automation/planner claim.

## Per-step verification requirement
Every required transformation step must include:
- preconditions
- AP01/effect refs (if attempted)
- verification record for expected intermediate

## Residue propagation requirement
Failed/missing/blocked intermediate emits residue that blocks downstream steps and completion.

## Scenario matrix
- full_chain_verified
- missing_first_input_blocks_chain
- failed_plate_step_blocks_filter
- filter_step_without_plate_rejected
- clean_water_without_filter_chain_rejected
- partial_chain_no_completion
- blocked_station_preserves_residue
- confounded_intermediate_blocks_completion
- disconfirming_intermediate_blocks_completion
- evaluator_only_chain_rule_rejected
- chain_candidate_does_not_become_mature_automation
- chain_effect_feedback_preserved

## Falsifiers
Implemented in `mini_factory_falsifiers.py`:
- completion_without_full_chain
- failed_intermediate_erased
- downstream_step_without_verified_input
- clean_water_without_filter_chain
- factory_chain_bypasses_AP01
- chain_uses_hidden_transformation_rule
- scenario_label_chain_completion
- resource_name_implies_intermediate
- recipe_candidate_as_executable_skill
- AB7_constraint_ignored_in_chain
- P16_value_as_action_permission
- P14_affordance_ignored_in_station_step
- P13_confounder_erased_in_chain
- disconfirming_trace_ignored_in_chain
- request_as_step_success
- effect_as_completion_oracle
- missing_input_erased
- residue_not_propagated_downstream
- chain_emits_unbounded_automation
- chain_emits_action_request_directly
- chain_executes_world_directly
- P17_overclaims_factory_intelligence

## Ablations
- remove_first_input
- remove_plate_effect_ref
- remove_filter_effect_ref
- remove_AP01_ref_for_step
- remove_AB7_constraint_refs
- remove_P16_value_chain_refs
- remove_P14_affordance_refs
- active_confounder_on_intermediate
- disconfirming_intermediate
- evaluator_only_chain_rule
- partial_chain_only

## Allowed claims
- bounded chain validation with verified intermediates and residue propagation

## Forbidden claims
- general automation
- mature factory skill
- Minecraft crafting
- long-horizon planning
- consciousness/general intelligence
