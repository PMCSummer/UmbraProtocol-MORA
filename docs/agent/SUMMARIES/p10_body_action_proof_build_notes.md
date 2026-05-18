# P10 Body Action Proof Build Notes

## Files added/changed
- Added:
  - `experiments/embodied_playground/body_action_scenarios.py`
  - `experiments/embodied_playground/body_action_proof.py`
  - `experiments/embodied_playground/body_action_falsifiers.py`
  - `tests/experiments/test_embodied_playground_body_action_scenarios.py`
  - `tests/experiments/test_embodied_playground_body_action_proof.py`
  - `tests/experiments/test_embodied_playground_body_action_falsifiers.py`
  - `tools/embodied_body_action_demo.py`
  - `tests/tools/test_embodied_body_action_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p10_body_action_proof.md`
- Updated:
  - `experiments/embodied_playground/subject_bridge.py` (ACP01 input projection only)
  - `src/substrate/acp01_internal_action_candidate_production/models.py` (generic typed drive/basis refs + observation inventory basis fields)
  - `src/substrate/acp01_internal_action_candidate_production/policy.py` (generic turn/move/drop candidate production + typed drive relevance, no lexical drive-token shortcut)

## Scenario list
- internal turn left/right orientation changes
- internal move forward open/blocked
- internal pickup success + missing basis gates
- internal drop success + missing inventory gate
- effect-feedback-next-tick scenario

## Tests
- P10 proof/scenario/falsifier tests + CLI tests.
- Regressions run across P9/P8/P4/P3/P2 and governance/core smoke.
- Repeated multi-tick movement/turn semantics explicitly validated as basis-persistent with fresh per-tick request refs and per-effect correlation.

## Known limitations
- GridWorld-bound evidence only.
- No pathfinding.
- No motor hierarchy.
- No recipe/automation logic.

## Next stage dependencies
- Suitable input for future P11 self/world boundary and later explanatory/abductive extensions.
