# AB2 Hypothesis Seed Build Notes

## Inventory result
- Inspected and reused:
  - `docs/seams/T03.seam.md`, `docs/seams/P04.seam.md`, `docs/seams/W06.seam.md`, `docs/seams/S01.seam.md`
  - `src/substrate/ab01_event_digest/*`
  - `src/substrate/t03_hypothesis_competition/*`
  - `src/substrate/w06_error_driven_revision/*`
  - `src/substrate/p04_interpersonal_counterfactual_policy_simulation/*`
  - `src/substrate/s01*` through `s05*`
  - `src/substrate/subject_tick/*` integration references
- Gap found:
  - AB1 emits non-causal event digests, but no dedicated bounded seed-generation seam exists between AB1 and T03.

## Files added
- `src/substrate/ab02_hypothesis_seed/__init__.py`
- `src/substrate/ab02_hypothesis_seed/models.py`
- `src/substrate/ab02_hypothesis_seed/policy.py`
- `src/substrate/ab02_hypothesis_seed/downstream_contract.py`
- `src/substrate/ab02_hypothesis_seed/telemetry.py`
- `tests/substrate/test_ab02_hypothesis_seed_build/test_ab02_hypothesis_seed_build.py`
- `experiments/embodied_playground/ab2_hypothesis_seed_probe.py`
- `tests/experiments/test_embodied_playground_ab2_hypothesis_seed_probe.py`
- `tools/ab2_hypothesis_seed_demo.py`
- `tests/tools/test_ab2_hypothesis_seed_demo.py`
- `docs/adr/ADR-AB02-hypothesis-seed-from-residue-anomaly.md`
- `docs/agent/EXPERIMENTS/embodied_playground_ab2_hypothesis_seed.md`

## Mechanism
- AB2 consumes AB1 digests and emits multiple provisional hypothesis seeds.
- Seeds include expected observations, possible tests, and missing evidence.
- AB2 never selects fact/cause and never emits action/request.

## Tests
- substrate owner tests for multi-seed emission, non-closure, hidden/eval rejection, scenario rejection, and ablations.
- embodied probe tests over AB1 blocked/inventory/mismatch cases.
- demo tests for case listing, JSON/report outputs, and claim-discipline language.

## Known limitations
- AB2 does not maintain a hypothesis frontier.
- AB2 does not perform ranking-as-truth.
- AB2 does not update hypotheses from later evidence.
- AB2 does not emit epistemic actions.

## Next relation (AB3)
- AB3 may consume AB2 seeds for bounded competition/frontier handling.
- AB2 remains seed generation only.
