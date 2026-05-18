# AB4 Epistemic Candidate Basis Build Notes

## Inventory results
- Inspected AB1/AB2/AB3 substrate owners and probes.
- Inspected ACP01/AP01 boundaries and existing inspect candidate behavior.
- Result: AB4 mechanism was missing as typed owner seam; implemented AB4 as basis-only substrate owner without modifying ACP01/AP01 behavior.

## Files added/changed
- Added:
  - `src/substrate/ab04_epistemic_candidate_basis/__init__.py`
  - `src/substrate/ab04_epistemic_candidate_basis/models.py`
  - `src/substrate/ab04_epistemic_candidate_basis/policy.py`
  - `src/substrate/ab04_epistemic_candidate_basis/downstream_contract.py`
  - `src/substrate/ab04_epistemic_candidate_basis/telemetry.py`
  - `tests/substrate/test_ab04_epistemic_candidate_basis_build/test_ab04_epistemic_candidate_basis_build.py`
  - `experiments/embodied_playground/ab4_epistemic_candidate_basis_probe.py`
  - `tests/experiments/test_embodied_playground_ab4_epistemic_candidate_basis_probe.py`
  - `tools/ab4_epistemic_candidate_basis_demo.py`
  - `tests/tools/test_ab4_epistemic_candidate_basis_demo.py`
  - `docs/adr/ADR-AB04-epistemic-candidate-basis.md`
  - `docs/agent/EXPERIMENTS/embodied_playground_ab4_epistemic_candidate_basis.md`

## Mechanism
- AB4 consumes AB3 frontier only.
- Emits bounded epistemic basis with:
  - frontier/hypothesis refs
  - discriminating test refs
  - uncertainty/missing-evidence refs
  - bounded qualitative EIG
- No publication, no execution, no hypothesis update.

## Tests
- substrate owner tests for AB4 contracts/falsifier-like constraints.
- probe tests for AB3->AB4 cases and no-authority behavior.
- CLI tests for case coverage and claim-discipline.

## Known limitations
- AB4 does not choose/publish actions.
- AB4 does not route through ACP01/AP01 by default in probe.
- AB4 does not update hypotheses from effects (AB5).
- AB4 is not full active inference.

## Next relation (AB5)
- AB5 may consume effect outcomes after ACP01/AP01/world path and update hypothesis/frontier support under explicit evidence discipline.
