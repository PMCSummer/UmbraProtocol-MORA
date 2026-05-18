# P17 Mini-Factory Chain Build Notes

## Files added/changed
- Added:
  - `experiments/embodied_playground/mini_factory_scenarios.py`
  - `experiments/embodied_playground/mini_factory_chain.py`
  - `experiments/embodied_playground/mini_factory_falsifiers.py`
  - `tools/embodied_mini_factory_demo.py`
  - `tests/experiments/test_embodied_playground_mini_factory_chain.py`
  - `tests/experiments/test_embodied_playground_mini_factory_falsifiers.py`
  - `tests/tools/test_embodied_mini_factory_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p17_mini_factory_chain.md`
  - `docs/agent/SUMMARIES/p17_mini_factory_chain_build_notes.md`

## Inventory result
- Reused P13/P14/P15/P16/AB7 experiment outputs.
- Implemented P17 as experiment-side chain proof; no substrate edits.

## Scenario list
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

## Tests
- Added behavior tests for all required P17 scenarios.
- Added explicit negative-control tests for each required P17 falsifier.
- Added CLI tests for required scenarios and overclaim guard.

## Known limitations
- Controlled mini-factory proof only.
- No general automation or planner.
- No mature durable factory skill memory.
- No Minecraft adapter.

## Next relation to P18/P19
- P18/P19 can extend recovery and larger-chain durability/transfer while preserving P17 per-step verification and residue propagation boundaries.
