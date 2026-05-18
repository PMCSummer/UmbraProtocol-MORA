# AB5 Hypothesis Update Build Notes

## Inventory results
- Inspected AB1/AB2/AB3/AB4 owner seams and probes.
- Inspected T03 and W06 ADR/seam boundaries.
- Result: no dedicated typed owner existed for post-effect hypothesis support update under explicit non-truth-oracle rules.

## Files added/changed
- Added:
  - `src/substrate/ab05_hypothesis_update/__init__.py`
  - `src/substrate/ab05_hypothesis_update/models.py`
  - `src/substrate/ab05_hypothesis_update/policy.py`
  - `src/substrate/ab05_hypothesis_update/downstream_contract.py`
  - `src/substrate/ab05_hypothesis_update/telemetry.py`
  - `tests/substrate/test_ab05_hypothesis_update_build/test_ab05_hypothesis_update_build.py`
  - `experiments/embodied_playground/ab5_hypothesis_update_probe.py`
  - `tests/experiments/test_embodied_playground_ab5_hypothesis_update_probe.py`
  - `tools/ab5_hypothesis_update_demo.py`
  - `tests/tools/test_ab5_hypothesis_update_demo.py`
  - `docs/adr/ADR-AB05-hypothesis-update-from-effects.md`
  - `docs/agent/EXPERIMENTS/embodied_playground_ab5_hypothesis_update.md`

## Mechanism
- AB5 consumes prior frontier + correlated public effect/event evidence.
- Emits typed support deltas (`increase/decrease/disconfirm/unchanged/unresolved/blocked`).
- Preserves missing evidence and non-fact boundaries.
- Request without effect is explicitly non-confirming.

## Tests
- substrate owner tests for update semantics, falsifier-like boundaries, and ablations
- probe tests for AB3/AB4-linked update flows
- CLI tests for case coverage and claim discipline

## Known limitations
- AB5 does not select epistemic actions (AB4 role).
- AB5 does not perform self/world attribution closure (AB6/P11 relation).
- AB5 does not claim final cause or fact resolution.
- update taxonomy is bounded and generic.

## Next relation (AB6)
- AB6 may consume AB5 support updates alongside ownership evidence to model bounded self/world attribution updates.
