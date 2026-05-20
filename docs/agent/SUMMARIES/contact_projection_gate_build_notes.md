# CONTACT-PROJECTION-GATE Build Notes

## Inspected surfaces
- `src/substrate/umwelt0_phenomenal_contact/{models.py,policy.py,downstream_contract.py}`
- `src/substrate/ab_subject_tick_integration/{models.py,policy.py,downstream_contract.py}`
- `src/substrate/acp01_internal_action_candidate_production/{models.py,policy.py,downstream_contract.py}`
- `src/substrate/ap01_subject_action_publication/{models.py,policy.py,downstream_contract.py}`
- `src/substrate/subject_tick/{models.py,update.py}`
- `docs/seams/W01.seam.md`
- `docs/seams/RT01.seam.md`

## Exact projection targets found
- AB target: `ABLiveTickInput` public evidence fields and optional lineage refs.
- ACP01 target: basis-style surfaces compatible with candidate production constraints.
- AP01 target: request/effect/source correlation lineage passthrough only.
- `subject_tick` scheduling modification is not required.

## Files added
- `src/substrate/contact_projection_gate/__init__.py`
- `src/substrate/contact_projection_gate/models.py`
- `src/substrate/contact_projection_gate/policy.py`
- `src/substrate/contact_projection_gate/telemetry.py`
- `src/substrate/contact_projection_gate/downstream_contract.py`
- `tests/substrate/test_contact_projection_gate_build/test_contact_projection_gate_build.py`
- `tools/contact_projection_gate_demo.py`
- `docs/adr/ADR-CONTACT-PROJECTION-GATE.md`
- `docs/agent/EXPERIMENTS/contact_projection_gate_contract.md`

## Model/policy summary
- Typed multichannel projection packet.
- AB projection + ACP01 basis projection + AP01 lineage projection.
- Strict no-authority output (no action/publication/execution/fact/cause/value/recipe/skill/automation).
- Block/noop when UMWELT0 frame is blocked/rejected/noop.
- Bounded projection limits and counters/traces.

## Limitations
- No UMWELT-S ContactSpec yet.
- No WORLD0 runner yet.
- No concrete world adapter yet.
- No live symbolic progression proof.
- No P17B factory loop.
- No language parser and no raw Sensorium pipeline.

## Next step
Build `UMWELT-S` contact specification layer before `WORLD0` runner wiring.
