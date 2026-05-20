# WORLD0 Build Notes

## Scope
Strict WORLD0 build only. No mutation of subject_tick/AP01/ACP01/AB-INT/UMWELT0/CONTACT-PROJECTION-GATE/UMWELT-S/K-SURF1/MICRO1/COST1.

## Files added/changed
- `src/substrate/world0_generic_runner/__init__.py`
- `src/substrate/world0_generic_runner/models.py`
- `src/substrate/world0_generic_runner/policy.py`
- `src/substrate/world0_generic_runner/telemetry.py`
- `src/substrate/world0_generic_runner/downstream_contract.py`
- `src/substrate/world0_generic_runner/fixtures.py`
- `tests/substrate/test_world0_generic_runner_build/test_world0_generic_runner_build.py`
- `tools/world0_generic_runner_demo.py`
- `docs/adr/ADR-WORLD0-generic-subject-world-runner.md`
- `docs/agent/EXPERIMENTS/world0_runner_contract.md`

## Inspected surfaces
- UMWELT-S ContactSpec/IR validation + construction plan.
- UMWELT0 contact/effect validation and blocked reason semantics.
- CONTACT-PROJECTION-GATE projected AB/ACP/AP lineage packet.
- subject_tick `execute_subject_tick` entrypoint and AP01 result surface.
- AP01 request packet and publication boundary.
- MICRO1/COST1 authority boundaries (no selection authority lift).
- W01 seam constraints and downstream no-overreach obligations.

## Model/policy summary
- Added WORLD0 adapter spec, observation packet, runner config, execution request/result, effect feedback, cycle trace, loop result, counters and hard-false authority flags.
- Added policy for adapter/spec validation, contact construction, projection, tick execution, AP01-only execution, effect correlation, residue preservation, and bounded loop stops.
- Explicitly blocked worldstate/scenario/plan/factory markers and runner-created AP01 attempts.

## Fixtures
- noop cycle
- AP01 execution
- blocked contact
- passive event
- failed backend execution
- adapter action-selection blocked
- ContactSpec plan blocked
- backend worldstate blocked
- scenario label blocked
- two backend families through same runner contract
- factory solution blocked
- max-tick bounded loop
- replay trace path
- no AP01 -> no execution
- uncorrelated effect blocked

## Tests
Added WORLD0 suite with required orchestration, boundary, and adversarial checks for AP01-only execution, blocked/noop visibility, worldstate/scenario/plan blocking, residue preservation, and backend-agnostic runner behavior.

## Limitations
- No concrete Minecraft/tech-pack adapter.
- No P17B live factory scenario.
- No EXP1/PATH1/ACTLEARN1/OPTION1 behavior.
- No durable runtime memory policy in WORLD0.

## Next recommended phase
P17B if live mini-factory proof is next; EXP1 if unknown-resource inquiry is next.
