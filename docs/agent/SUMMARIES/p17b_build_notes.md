# P17B Build Notes

## Files added/changed
- `src/substrate/p17b_live_symbolic_minifactory/__init__.py`
- `src/substrate/p17b_live_symbolic_minifactory/models.py`
- `src/substrate/p17b_live_symbolic_minifactory/policy.py`
- `src/substrate/p17b_live_symbolic_minifactory/fixtures.py`
- `src/substrate/p17b_live_symbolic_minifactory/telemetry.py`
- `src/substrate/p17b_live_symbolic_minifactory/downstream_contract.py`
- `tests/substrate/test_p17b_live_symbolic_minifactory_build/test_p17b_live_symbolic_minifactory_build.py`
- `tools/p17b_live_symbolic_minifactory_demo.py`
- `docs/adr/ADR-P17B-live-symbolic-mini-factory.md`
- `docs/agent/EXPERIMENTS/p17b_live_minifactory_contract.md`

## Inspected surfaces
- WORLD0 run/cycle/trace/AP01-effect gating surfaces.
- MICRO1 operation trace and non-selection authority.
- COST1 comparison trace and non-permission authority.
- K-SURF1 provider hint non-truth boundary.
- UMWELT-S / UMWELT0 / projection contact/effect contracts.
- AP01 request packet boundary.
- P15/P16/P17/AB7 proof-side constraints from existing summaries and experiment modules.

## Model/policy summary
- Added P17B typed models for need, step spec, step trace, intermediate verification, chain advance decision, residue stop frame, run object, counters, and hard-false authority flags.
- Added validators for:
  - AP01/effect requirement;
  - downstream verified-intermediate requirement;
  - no hidden recipe/worldstate/scenario payload;
  - no ContactSpec/adapter script payload;
  - no cost-winner/provider-truth permission;
  - no proof-only trace accepted as live.
- Added replayable run summary/telemetry.

## Fixtures
- successful bounded chain
- missing AP01 blocks step
- failed intermediate stops chain
- unverified intermediate blocks downstream
- missing resource/station blocks
- hidden recipe blocked
- adapter solution sequence blocked
- contact spec script blocked
- cost winner permission blocked
- provider hint truth blocked
- proof-not-live blocked
- noop-not-completion
- residue recovery partial
- replay trace fixture

## Tests
- Added P17B build suite covering required bounded-live semantics and hardening cases for shortcut authorities and proof-vs-live separation.

## Limitations
- No general factory automation.
- No Minecraft/tech-pack adapter.
- No EXP1 unknown resource inquiry behavior.
- No PATH1 routing/layout behavior.
- No ACTLEARN1/OPTION1 maturity behavior.
- No durable runtime memory.
- No raw Sensorium integration.

## Next recommended phase
- `EXP1` if unknown resource inquiry is next.
- `PATH1` if spatial routing/layout validation is next.
- `ACTLEARN1/OPTION1` if schema/option learning is next.
- Memory design discussion if durable continuity is next.

