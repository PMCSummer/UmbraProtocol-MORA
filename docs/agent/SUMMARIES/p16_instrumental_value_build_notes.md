# P16 Instrumental Value Build Notes

## Files added/changed
- Added:
  - `experiments/embodied_playground/instrumental_value_scenarios.py`
  - `experiments/embodied_playground/instrumental_value.py`
  - `experiments/embodied_playground/instrumental_value_falsifiers.py`
  - `tools/embodied_instrumental_value_demo.py`
  - `tests/experiments/test_embodied_playground_instrumental_value.py`
  - `tests/experiments/test_embodied_playground_instrumental_value_falsifiers.py`
  - `tests/tools/test_embodied_instrumental_value_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p16_instrumental_value.md`
  - `docs/agent/SUMMARIES/p16_instrumental_value_build_notes.md`

## Inventory result
- Inspected P13/P14/P15/AB7 summaries and current experiment/probe owners.
- Reused P15 candidate outputs and AB7 constraint/readiness outputs.
- Kept implementation experiment-side; no substrate owner mutation.

## Scenario list
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

## Tests
- Added scenario behavior tests for required P16 cases.
- Added explicit negative-control falsifier tests for all required P16 falsifiers.
- Added CLI tests for required cases and overclaim discipline.

## Known limitations
- Experiment-side proof only.
- No executable automation.
- No mature durable value memory.
- No long-horizon planning policy.
- Controlled scenario traces only.

## Next relation to P17-P19
- P17-P19 can extend durability/transfer/planning layers while preserving P16 no-intrinsic/no-automation boundaries.
