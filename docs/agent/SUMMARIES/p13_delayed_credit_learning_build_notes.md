# P13 Delayed Credit Learning Build Notes

## Inventory result
- Inspected S03/W06 seam boundaries and AB5/AB6/P12 summaries.
- Found existing substrate `P03` long-horizon credit owner; kept it untouched.
- Implemented P13 as experiment-side delayed-credit/confounder proof battery to avoid owner duplication.

## Files added/changed
- Added:
  - `experiments/embodied_playground/delayed_credit_scenarios.py`
  - `experiments/embodied_playground/delayed_credit_learning.py`
  - `experiments/embodied_playground/delayed_credit_falsifiers.py`
  - `tools/embodied_delayed_credit_demo.py`
  - `tests/experiments/test_embodied_playground_delayed_credit_learning.py`
  - `tests/experiments/test_embodied_playground_delayed_credit_falsifiers.py`
  - `tests/tools/test_embodied_delayed_credit_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p13_delayed_credit_learning.md`

## Scenario list
- immediate_clear_effect
- delayed_effect_correct_window
- delayed_effect_wrong_window
- confounded_effect_two_precursors
- confounder_disconfirmed_by_repetition
- spurious_one_shot_correlation
- disconfirming_episode
- hidden_recipe_only
- ambiguous_public_evidence
- delayed_and_confounded_mixed

## Tests
- Scenario behavior tests for required P13 cases.
- Explicit negative-control falsifier tests for each P13 falsifier.
- CLI tests for required case coverage and overclaim discipline.

## Known limitations
- Experiment-side proof only; no substrate learning owner changes.
- No durable memory consolidation in P13.
- No recipe/station learning in P13.
- No transfer-learning claim.
- Controlled scenario traces only.

## Next relation to P14/P15
- P14 can focus on station affordance shaping under explicit evidence constraints.
- P15 can own recipe/precursor learning with durable maturity gates and stronger cross-episode evidence requirements.
