# P14 Station Affordance Build Notes

## Inventory result
- Inspected seam and owner context (`docs/seams/P03.seam.md`, `docs/seams/P04.seam.md`) and existing summaries for P13.
- Reused existing experiment-side station minimum in `experiments/embodied_playground/grid_world.py` (`use_station` blocked/missing-input/partial semantics).
- Reused AP01 publication seam as gate; no substrate mutation performed.
- Implemented P14 as experiment-side proof battery, not as recipe learning owner.

## Files added/changed
- Added:
  - `experiments/embodied_playground/station_scenarios.py`
  - `experiments/embodied_playground/station_affordance.py`
  - `experiments/embodied_playground/station_falsifiers.py`
  - `tools/embodied_station_affordance_demo.py`
  - `tests/experiments/test_embodied_playground_station_affordance.py`
  - `tests/experiments/test_embodied_playground_station_falsifiers.py`
  - `tests/tools/test_embodied_station_affordance_demo.py`
  - `docs/agent/EXPERIMENTS/embodied_playground_p14_station_affordance.md`

## Scenario list
- station_visible_not_usable
- station_proximate_no_input
- station_proximate_with_input
- station_blocked
- station_protected_eval_only_rule
- station_action_surface_only
- station_far_with_input
- station_missing_station_ref
- station_effect_without_ap01_attempt
- station_use_effect_feedback

## Tests
- Scenario behavior tests for all required P14 cases.
- Explicit negative-control tests for every required P14 falsifier.
- CLI tests for required scenario rendering and overclaim constraints.

## Known limitations
- Controlled experiment-side proof only.
- No recipe/precursor learning in P14.
- No durable station schema/maturity in P14.
- No automation policy.
- No Minecraft adapter.

## Next relation to P15
- P15 can own recipe/precursor candidate maturation with repeated trace/disconfirmation/confounder constraints inherited from P13 discipline.
