# UMWELT-S Build Notes

## Inspected surfaces
- `src/substrate/umwelt0_phenomenal_contact/*`
- `src/substrate/contact_projection_gate/*`
- `src/substrate/ab_subject_tick_integration/*`
- `src/substrate/acp01_internal_action_candidate_production/*`
- `src/substrate/ap01_subject_action_publication/*`
- `src/substrate/subject_tick/{models.py,update.py}`
- `docs/seams/{RT01.seam.md,W01.seam.md}`
- `docs/agent/SUMMARIES/{umwelt0_build_notes.md,contact_projection_gate_build_notes.md}`

## Files added
- `src/substrate/umwelts_symbolic_contact/__init__.py`
- `src/substrate/umwelts_symbolic_contact/models.py`
- `src/substrate/umwelts_symbolic_contact/policy.py`
- `src/substrate/umwelts_symbolic_contact/telemetry.py`
- `src/substrate/umwelts_symbolic_contact/downstream_contract.py`
- `src/substrate/umwelts_symbolic_contact/fixtures.py`
- `tests/substrate/test_umwelts_symbolic_contact_build/test_umwelts_symbolic_contact_build.py`
- `tools/umwelts_contact_spec_demo.py`
- `docs/adr/ADR-UMWELT-S-symbolic-contact-spec.md`
- `docs/agent/EXPERIMENTS/umwelts_contact_ir_contract.md`

## Model/policy summary
- `ContactSpec` authoring schema.
- `ContactIR` normalized backend-agnostic representation.
- strict validator set for planner/recipe-oracle/worldstate/hidden-label rejection.
- `UMWELT0ConstructionPlan` for membrane-compatible downstream construction.
- authority flags remain hard-false.

## Fixtures
- `generic_grid_fixture`
- `symbolic_factory_fixture`
- `language_sensor_fixture`

## Tests
- 25 UMWELT-S build tests (mechanism + falsifier + ablation coverage).
- regression checks for UMWELT0 / CONTACT-PROJECTION-GATE / AB-INT / subject_tick / observability / claim constitution.

## Limitations
- no final human-friendly DSL syntax yet
- no WORLD0 runner yet
- no concrete adapter yet
- no K-SURF1 provider behavior yet
- no raw Sensorium pipeline
- no live symbolic progression proof
- no P17B factory loop

## Next recommended phase
K-SURF1 or MICRO1 before WORLD0; keep WORLD0 behind validated contact/provider-operation boundaries.
