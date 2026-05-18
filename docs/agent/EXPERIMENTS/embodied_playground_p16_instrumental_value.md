# P16 Instrumental Value (Embodied Playground)

## Purpose
P16 validates bounded instrumental value assignment for intermediate resources as means only.

## Relation to P13/P14/P15
- P13 provides delayed-credit/confounder/disconfirmation discipline.
- P14 provides station affordance boundaries.
- P15 provides provisional recipe/precursor candidate traces.

## Relation to AB7
AB7 constraints and readiness states are consumed so value assignment cannot turn into executable automation.

## Why P16 is bounded means-value
P16 does not assign intrinsic value. A resource gets value only through public need/effect/candidate chains.

## Evidence/effect chain requirements
- public need refs
- public resource refs
- public effect-chain refs
- AB7 constraint refs
- station affordance refs for station-linked chains
- confounder/disconfirmation handling

## iron_magic_value and filter_without_water_problem examples
- `iron_magic_value_guard`: no name-only resource value.
- `filter_without_water_problem`: no value without linked need/problem/effect chain.

## Scenario matrix
- resource_with_need_and_recipe_chain
- resource_without_need_no_value
- iron_magic_value_guard
- filter_without_water_problem
- resource_with_recipe_candidate_but_missing_effect_chain
- resource_with_station_affordance_missing
- confounded_resource_value
- disconfirmed_resource_value
- repeated_trace_strengthens_instrumental_value
- AB7_blocks_automation_readiness
- hidden_eval_value_rule_rejected
- value_candidate_does_not_emit_action

## Falsifiers
Implemented in `experiments/embodied_playground/instrumental_value_falsifiers.py`:
- iron_magic_value
- filter_without_water_problem
- resource_value_without_need
- value_without_effect_chain
- instrumental_value_becomes_intrinsic_goal
- recipe_candidate_as_automation_value
- ab7_constraint_ignored
- p13_confounder_ignored_for_value
- p14_affordance_ignored_for_value
- ab5_support_as_value_oracle
- ab6_attribution_as_value_oracle
- hidden_eval_value_rule_used
- scenario_label_value_assignment
- value_without_resource_refs
- value_without_evidence_refs
- missing_evidence_erased
- disconfirmation_ignored
- value_emits_action_request
- value_executes_world
- P16_overclaims_automation_or_value_learning

## Ablations
- remove_need_refs
- remove_resource_refs
- remove_effect_chain_refs
- remove_recipe_candidate_refs
- remove_AB7_constraint_refs
- remove_P13_gate_refs
- remove_P14_affordance_refs
- active_confounder
- disconfirming_trace
- hidden_eval_only_value_rule
- name_only_resource

## Allowed claims
- bounded instrumental value assignment through public chains
- revocation/blocking on missing/confounded/disconfirmed chains

## Forbidden claims
- intrinsic value learning
- automation execution
- mature resource policy
- Minecraft crafting/tool-use intelligence
- consciousness/general intelligence
