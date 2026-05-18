# P15 Recipe/Precursor Learning Build Notes

## Inventory result
- Inspected prior phase summaries/seams and reused experiment-side outputs from:
  - `experiments/embodied_playground/station_affordance.py` (P14 affordance/effect lineage)
  - `experiments/embodied_playground/delayed_credit_learning.py` (P13 credit/confounder/schema gating)
- No existing dedicated P15 recipe/precursor candidate owner was found.
- Implemented P15 as experiment-side battery only, with no substrate edits.

## Files added/changed
- Added:
  - `experiments/embodied_playground/recipe_precursor_scenarios.py`
  - `experiments/embodied_playground/recipe_precursor_learning.py`
  - `experiments/embodied_playground/recipe_precursor_falsifiers.py`
  - `tools/embodied_recipe_precursor_demo.py`
  - `tests/experiments/test_embodied_playground_recipe_precursor_learning.py`
  - `tests/experiments/test_embodied_playground_recipe_precursor_falsifiers.py`
  - `tests/tools/test_embodied_recipe_precursor_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p15_recipe_precursor_learning.md`
  - `docs/agent/SUMMARIES/p15_recipe_precursor_learning_build_notes.md`

## Scenario list
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

## Tests
- Added scenario behavior tests covering required P15 cases.
- Added explicit negative-control tests for each required P15 falsifier.
- Added CLI tests for list/report/json and overclaim discipline.

## Known limitations
- Experiment-side candidate proof only.
- No mature durable recipe memory in P15.
- No automation or station execution planning.
- No Minecraft adapter.
- Controlled scenario coverage only.

## Next relation
- AB7 can consume P15 candidate lineage as bounded evidence input.
- P16-P19 can own durability, transfer, and broader consolidation beyond P15 provisional candidate discipline.
