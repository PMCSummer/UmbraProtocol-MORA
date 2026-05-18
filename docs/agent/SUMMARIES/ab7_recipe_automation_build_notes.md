# AB7 Recipe-Automation Build Notes

## Inventory results
- Inspected AB1-AB6 substrate packages, P13/P14/P15 experiment outputs, and existing probes/tools/tests.
- Reused P15 candidate lineage and P13/P14 gating evidence surfaces.
- Added AB7 as a narrow integration seam; no duplication of P13/P14/P15 generation/affordance logic.

## Files added/changed
- Added substrate owner package:
  - `src/substrate/ab07_recipe_automation_integration/__init__.py`
  - `src/substrate/ab07_recipe_automation_integration/models.py`
  - `src/substrate/ab07_recipe_automation_integration/policy.py`
  - `src/substrate/ab07_recipe_automation_integration/downstream_contract.py`
  - `src/substrate/ab07_recipe_automation_integration/telemetry.py`
- Added substrate tests:
  - `tests/substrate/test_ab07_recipe_automation_integration_build/test_ab07_recipe_automation_integration_build.py`
- Added experiment probe:
  - `experiments/embodied_playground/ab7_recipe_automation_probe.py`
  - `tests/experiments/test_embodied_playground_ab7_recipe_automation_probe.py`
- Added tool:
  - `tools/ab7_recipe_automation_demo.py`
  - `tests/tools/test_ab7_recipe_automation_demo.py`
- Added docs:
  - `docs/adr/ADR-AB07-recipe-automation-abductive-integration.md`
  - `docs/agent/SUMMARIES/ab7_recipe_automation_build_notes.md`
  - `docs/agent/EXPERIMENTS/embodied_playground_ab7_recipe_automation.md`

## Mechanism
- AB7 builds `RecipeAutomationAbductiveFrame` from P15 candidate records + AB/P13/P14 refs.
- Emits explicit constraints/bindings/readiness; enforces non-execution boundaries.
- Preserves unresolved conflicts and missing evidence.
- Rejects protected evaluator-only rule basis.

## Tests
- Substrate AB7 build tests cover required AB7 owner behaviors.
- Probe tests verify P15/P13/P14/AB usage and no action/world emission.
- Tool tests verify case listing, JSON/report output, and overclaim guardrails.

## Known limitations
- AB7 integrates evidence and gating only.
- No executable automation pipeline.
- No mature durable recipe memory.
- Controlled scenario/probe coverage only.

## Next relation to P16-P19
- P16-P19 can extend durability/transfer/consolidation, but must preserve AB7 non-execution and non-fact closure constraints.
