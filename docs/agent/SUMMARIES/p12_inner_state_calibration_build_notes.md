# P12 Inner-State Calibration Build Notes

## Inventory result
- Inspected AB1-AB6 and P11 experiment/probe outputs, plus S05/W06 seam boundaries.
- Reused existing public outputs from AB6 (attribution) and AB5 (support updates).
- Implemented P12 as evaluator-side calibration battery only; no cognition mutation and no substrate edit.

## Files added/changed
- Added:
  - `experiments/embodied_playground/inner_state_calibration_scenarios.py`
  - `experiments/embodied_playground/inner_state_calibration.py`
  - `experiments/embodied_playground/inner_state_calibration_falsifiers.py`
  - `tools/embodied_inner_state_calibration_demo.py`
  - `tests/experiments/test_embodied_playground_inner_state_calibration.py`
  - `tests/experiments/test_embodied_playground_inner_state_calibration_falsifiers.py`
  - `tests/tools/test_embodied_inner_state_calibration_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p12_inner_state_calibration.md`

## Scenario list
- clear self-caused effect
- world-only change
- other-actor change
- mixed cause
- delayed effect
- sensor/projection mismatch
- unknown cause
- conflicting evidence
- residue present
- hidden-eval-only cause

## Tests
- Scenario behavior tests for P12 required cases.
- Explicit negative-control falsifier tests for each P12 falsifier.
- CLI tests for list/report/json and overclaim boundaries.

## Known limitations
- Evaluator-side calibration only.
- Hidden sealed labels are never available to subject report generation.
- Controlled scenarios only.
- Not a full introspection proof and not a cognition-expansion phase.

## Next relation to P13
- P13 can extend calibration with delayed-credit/confounder learning diagnostics over longer horizons.
