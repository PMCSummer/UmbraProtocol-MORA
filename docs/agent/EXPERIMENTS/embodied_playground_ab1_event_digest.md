# Embodied Playground AB1 Event Digest

## Purpose
Demonstrate bounded anomaly/event digest generation from public embodied traces without causal closure.

## Relation to P10 and P9
- P10 provides AP01-gated embodied effect traces.
- P9 provides strict no-auto-builder constraints and no hidden substitution discipline.
- AB1 consumes these public signals and emits digest-only outputs.

## Demo cases
- `blocked_movement_effect`
- `pickup_inventory_delta`
- `effect_mismatch`
- `hidden_eval_only`

## Claim allowed
"MORA can produce bounded public event digests for anomaly/effect/residue signals without causal closure."

## Claims forbidden
- cause explanation/confirmation
- abduction/hypothesis frontier
- active inference
- action request generation
- consciousness/general reasoning claims

## How to run
```bash
python tools/ab1_event_digest_demo.py --list-cases
python tools/ab1_event_digest_demo.py --case blocked_movement_effect --report
python tools/ab1_event_digest_demo.py --case pickup_inventory_delta --json
python tools/ab1_event_digest_demo.py --case hidden_eval_only --json
```
