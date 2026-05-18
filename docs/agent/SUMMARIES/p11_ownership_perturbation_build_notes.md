# P11 Ownership Perturbation Build Notes

## Inventory result
- Inspected seams/ADRs/surfaces for S01/S02/S03/S05 ownership and self/world boundaries.
- Reused existing P10, AB1, AB2, AB3 experiment probes as evidence sources.
- Chosen implementation: experiment-side battery only, no substrate owner duplication.

## Files added/changed
- Added:
  - `experiments/embodied_playground/ownership_scenarios.py`
  - `experiments/embodied_playground/ownership_perturbation.py`
  - `experiments/embodied_playground/ownership_falsifiers.py`
  - `tools/embodied_ownership_perturbation_demo.py`
  - `tests/experiments/test_embodied_playground_ownership_perturbation.py`
  - `tests/experiments/test_embodied_playground_ownership_falsifiers.py`
  - `tests/tools/test_embodied_ownership_perturbation_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p11_ownership_perturbation.md`

## Scenario list
- self-caused move/pickup
- world-only change
- other-actor change
- mixed self+world
- delayed self effect
- unknown unexplained effect
- projection mismatch
- blocked self action
- hidden eval only

## Tests
- Scenario behavior tests for required P11 cases.
- Explicit negative-control tests for each P11 falsifier.
- CLI tests for list/report/json and claim discipline.

## Known limitations
- Battery evidence only; not full AB6 attribution integration.
- Controlled perturbations only.
- No full causal model and no theory-of-mind closure.
- No epistemic action selection and no active inference in P11.

## Next relation to AB4/AB5/AB6
- AB4 can consume unresolved/missing evidence markers for epistemic candidate basis.
- AB5 can update attribution confidence with new effect evidence over time.
- AB6 can formalize deeper self/world attribution logic using P11 falsifier evidence.
