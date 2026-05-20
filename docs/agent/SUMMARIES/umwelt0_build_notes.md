# UMWELT0 Build Notes

## Inspected surfaces
- `docs/seams/RT01.seam.md`
- `docs/seams/W01.seam.md`
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/ab_subject_tick_integration/*`
- `src/substrate/acp01_internal_action_candidate_production/*`
- `src/substrate/ap01_subject_action_publication/*`
- `src/substrate/world_entry_contract/*`
- `src/substrate/world_adapter/*`

## Files added
- `src/substrate/umwelt0_phenomenal_contact/__init__.py`
- `src/substrate/umwelt0_phenomenal_contact/models.py`
- `src/substrate/umwelt0_phenomenal_contact/policy.py`
- `src/substrate/umwelt0_phenomenal_contact/telemetry.py`
- `src/substrate/umwelt0_phenomenal_contact/downstream_contract.py`
- `tests/substrate/test_umwelt0_phenomenal_contact_build/test_umwelt0_phenomenal_contact_build.py`
- `tools/umwelt0_contact_demo.py`
- `docs/adr/ADR-UMWELT0-phenomenal-contact-layer.md`
- `docs/agent/EXPERIMENTS/umwelt0_contact_contract.md`

## Why this is a new seam
UMWELT0 introduces a typed contact membrane contract that does not exist in W01/W06 owners and does not mutate existing world entry/runtime contracts.

## Model and policy summary
- typed source/lossiness/uncertainty/effect/action/contact models
- strict blocked reasons for hidden/scenario/backend-truth/worldstate/recipe/full-map/identity/policy leaks
- explicit authority flags, all false for accepted contact
- conformance counters and deterministic `accepted|partial|blocked|noop` status
- downstream contract with AB-INT compatibility and no-authority guarantees

## Test scope
- 22 focused tests for membrane invariants, falsifiers, ablations, and downstream compatibility constraints.

## Limitations
- no `UMWELT-S` ContactSpec compiler
- no `WORLD0` runner
- no concrete world adapter integration
- no K-SURF1 provider integration
- no raw Sensorium/perception
- no evidence record anchoring in tracker

## Next step
Run `SUBJECT-RUNNER-READINESS-AUDIT` before WORLD0/P17B wiring.

