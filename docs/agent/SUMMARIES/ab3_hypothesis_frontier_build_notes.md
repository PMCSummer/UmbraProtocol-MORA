# AB3 Hypothesis Frontier Build Notes

## Inventory result
- Inspected:
  - `AB1` event digest owner
  - `AB2` hypothesis seed owner
  - `T03` hypothesis competition seam/surface
  - `P04`, `W06`, `S01-S05`, `subject_tick` integration references
- Reused:
  - AB2 seed set contract as direct AB3 input.
- Gap implemented:
  - local abductive explanation frontier over AB2 seeds with bounded provisional ranking and unresolved conflict preservation.

## Files added
- `src/substrate/ab03_hypothesis_frontier/__init__.py`
- `src/substrate/ab03_hypothesis_frontier/models.py`
- `src/substrate/ab03_hypothesis_frontier/policy.py`
- `src/substrate/ab03_hypothesis_frontier/downstream_contract.py`
- `src/substrate/ab03_hypothesis_frontier/telemetry.py`
- `tests/substrate/test_ab03_hypothesis_frontier_build/test_ab03_hypothesis_frontier_build.py`
- `experiments/embodied_playground/ab3_hypothesis_frontier_probe.py`
- `tests/experiments/test_embodied_playground_ab3_hypothesis_frontier_probe.py`
- `tools/ab3_hypothesis_frontier_demo.py`
- `tests/tools/test_ab3_hypothesis_frontier_demo.py`
- `docs/adr/ADR-AB03-hypothesis-frontier-competition.md`
- `docs/agent/EXPERIMENTS/embodied_playground_ab3_hypothesis_frontier.md`

## Mechanism
- AB3 consumes AB2 seeds and materializes an explanation frontier.
- Frontier keeps competing hypotheses alive, marks unresolved conflicts, and lists discriminating tests.
- Optional leader is provisional only and never treated as fact.

## Tests
- owner tests for frontier behavior, falsifiers, and ablations
- embodied probe tests for AB2->AB3 path
- CLI demo tests for report/json and claim-discipline

## Known limitations
- AB3 does not update hypotheses from new effects (AB5)
- AB3 does not select epistemic actions (AB4)
- AB3 does not perform active inference
- AB3 does not perform self/world attribution closure (AB6)

## Next relation (AB4)
- AB4 may consume AB3 discriminating tests/missing evidence and transform them into bounded epistemic candidate basis.
