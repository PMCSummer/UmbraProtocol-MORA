# P15 / Recipe & Precursor Learning

## Purpose
P15 forms bounded `RecipeCandidate` and `PrecursorCandidate` records from lived public traces only. It validates repetition, confounder-awareness, disconfirmation, and missing-evidence discipline before any future maturity phase.

## Relation to P13
- P13 remains owner of delayed-credit/confounder discipline.
- P15 consumes P13-style evidence gates: repeated traces, confounder records, delay windows, and disconfirming episodes.
- P15 does not relax P13 maturity constraints.

## Relation to P14
- P14 remains owner of station affordance boundaries and AP01-gated station effect path.
- P15 consumes P14 station/effect traces as learning evidence.
- P15 does not re-prove affordance and does not execute station behavior.

## Why P15 is bounded candidate learning (not mature recipe knowledge)
- `mature_recipe_count` is expected to remain `0` in this stage.
- `one_shot_mature=False` is enforced.
- `hidden_recipe_used=False` and `protected_eval_used=False` are enforced on subject path.
- Output stays provisional/blocked/repeated-trace-supported and never claims final cause truth.

## Lived trace requirements
A recipe candidate requires public lived evidence lineage:
- station ref
- public input refs
- public effect refs
- supporting trace refs
- P13 gate refs (schema/credit lineage)

Missing lineage keeps candidate `blocked`.

## Public refs requirements
Candidates require public references only:
- no protected evaluator-only rule/table input
- no scenario label as decision basis
- no hidden expected output

## Confounder / disconfirmation / maturity policy
- Active/unresolved confounder prevents clean maturity.
- Disconfirming traces reduce support or block maturity.
- Repetition can strengthen to `repeated_trace_supported` but does not force mature recipe status in P15.

## Scenario matrix
- one_success_trace_provisional_only
- repeated_consistent_traces_candidate_strengthens
- hidden_recipe_only_no_candidate
- visible_station_no_trace_no_recipe
- station_success_without_input_refs_blocked
- station_success_without_effect_refs_blocked
- confounded_station_effect
- confounder_disconfirmed_by_repetition
- disconfirming_trace_blocks_maturity
- delayed_station_effect
- ambiguous_output_effect
- recipe_candidate_does_not_emit_action

## Falsifiers
- hidden_recipe_leak
- one_shot_recipe_maturity
- recipe_without_lived_trace
- recipe_without_effect_refs
- recipe_without_input_refs
- station_visible_as_recipe_basis
- station_affordance_as_recipe_truth
- confounder_bypasses_recipe_maturity
- disconfirming_trace_ignored
- repeated_trace_without_public_refs
- delayed_effect_as_immediate_recipe
- output_as_truth_oracle
- ab5_update_as_recipe_oracle
- ab6_attribution_as_recipe_oracle
- scenario_label_recipe_learning
- protected_eval_output_used
- recipe_candidate_emits_action_request
- recipe_candidate_executes_world
- mature_schema_without_p13_gate
- P15_overclaims_recipe_learning

## Ablations
- no_lived_trace
- no_effect_refs
- no_input_refs
- one_trace_only
- remove_repetition
- remove_confounder_records
- disconfirming_trace
- hidden_eval_only_recipe
- remove_P13_gate_refs
- ambiguous_output

## Allowed claims
- MORA can form provisional recipe/precursor candidates from lived public station/effect traces under P13-style maturity gates.

## Forbidden claims
- MORA learned mature recipes.
- MORA knows hidden recipes.
- MORA has automation.
- MORA performs Minecraft crafting.
- MORA has general tool-use intelligence.
- MORA has consciousness or general intelligence.
