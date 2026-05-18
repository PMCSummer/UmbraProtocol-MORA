# Embodied Playground AB2 Hypothesis Seed

## Purpose
Demonstrate bounded competing hypothesis-seed generation from public AB1 anomaly/event digests.

## Relation to AB1, P10, P9
- AB1 provides non-causal event digests.
- P10 provides AP01-gated embodied effect traces.
- P9 provides strict no-auto-builder/no hidden-substitution constraints.
- AB2 consumes these public artifacts and emits seed-only explanatory candidates.

## Demo cases
- `blocked_movement_effect`
- `pickup_inventory_delta`
- `effect_mismatch`
- `hidden_eval_only`
- `no_event_digest`

## Allowed claim
"MORA can generate bounded competing explanatory hypothesis seeds from public anomaly/residue/event signals without selecting a fact."

## Forbidden claims
- final cause confirmation
- full abduction
- hypothesis frontier closure
- active inference
- epistemic action selection
- consciousness/general reasoning claims

## How to run
```bash
python tools/ab2_hypothesis_seed_demo.py --list-cases
python tools/ab2_hypothesis_seed_demo.py --case blocked_movement_effect --report
python tools/ab2_hypothesis_seed_demo.py --case effect_mismatch --json
python tools/ab2_hypothesis_seed_demo.py --case hidden_eval_only --json
python tools/ab2_hypothesis_seed_demo.py --case no_event_digest --report
```
