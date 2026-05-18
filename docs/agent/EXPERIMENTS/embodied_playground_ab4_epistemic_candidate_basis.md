# Embodied Playground AB4 Epistemic Candidate Basis

## Purpose
AB4 transforms unresolved AB3 frontier state into bounded epistemic candidate basis.
AB4 stops at basis; it does not publish or execute.

## Relation to AB1 / AB2 / AB3
- AB1: event digest source (non-causal).
- AB2: competing hypothesis seeds.
- AB3: frontier with unresolved conflicts/missing evidence/discriminating tests.
- AB4: evidence-seeking basis built from AB3 frontier.

## Relation to P10 / P11 / P9
- P10 validates AP01-gated embodied effects.
- P11 validates bounded ownership distinctions.
- P9 strict-mode discipline aligns with AB4 no-hidden/no-scenario basis checks.

## Demo cases
- `open_frontier_inspect`
- `ambiguous_frontier_wait`
- `hidden_eval_only`
- `no_frontier`
- `no_discriminating_test`

## Allowed claim
"MORA can generate bounded evidence-seeking candidate basis from unresolved explanation frontiers without bypassing ACP01/AP01."

## Forbidden claims
- full active inference
- direct epistemic action selection
- cause/fact closure
- scientific reasoning proof
- consciousness/general reasoning proof

## Run demo
```bash
python tools/ab4_epistemic_candidate_basis_demo.py --list-cases
python tools/ab4_epistemic_candidate_basis_demo.py --case open_frontier_inspect --report
python tools/ab4_epistemic_candidate_basis_demo.py --case ambiguous_frontier_wait --json
python tools/ab4_epistemic_candidate_basis_demo.py --case hidden_eval_only --json
python tools/ab4_epistemic_candidate_basis_demo.py --case no_frontier --report
python tools/ab4_epistemic_candidate_basis_demo.py --case no_discriminating_test --report
```
