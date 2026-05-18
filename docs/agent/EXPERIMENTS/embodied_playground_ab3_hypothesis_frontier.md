# Embodied Playground AB3 Hypothesis Frontier

## Purpose
Show that AB3 can maintain a bounded explanation frontier over AB2 seeds without forced closure.

## Relation to AB1 / AB2
- AB1: non-causal event digest source.
- AB2: bounded hypothesis seed source.
- AB3: frontier maintenance and provisional competition over AB2 seeds.

## Relation to P10 / P9
- P10 provides AP01-gated embodied effect traces.
- P9 strict-mode discipline constrains hidden/eval/fabrication shortcuts.
- AB3 consumes public evidence-chain artifacts only.

## Demo cases
- `blocked_movement_effect`
- `effect_mismatch`
- `inventory_delta`
- `ambiguous_evidence`
- `hidden_eval_only`
- `single_hypothesis_ambiguous`

## Allowed claim
"MORA can maintain a bounded explanation frontier over competing hypothesis seeds under uncertainty without selecting a fact."

## Forbidden claims
- final cause confirmed
- anomaly resolved as truth
- active inference performed
- epistemic action selected
- consciousness/general reasoning proven

## How to run
```bash
python tools/ab3_hypothesis_frontier_demo.py --list-cases
python tools/ab3_hypothesis_frontier_demo.py --case blocked_movement_effect --report
python tools/ab3_hypothesis_frontier_demo.py --case effect_mismatch --json
python tools/ab3_hypothesis_frontier_demo.py --case ambiguous_evidence --report
python tools/ab3_hypothesis_frontier_demo.py --case hidden_eval_only --json
python tools/ab3_hypothesis_frontier_demo.py --case single_hypothesis_ambiguous --report
```
