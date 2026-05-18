# Embodied Playground P10: Body Action Proof under Internal Candidates

## Purpose
Prove that turn, movement, pickup, and drop effects are produced through the internal subject path:

`observation -> subject_tick -> ACP01 candidate -> AP01 publication -> envelope -> world submit -> effect -> next observation`

## Scope
- Internal candidate mode only (`use_internal_candidate_producer=True`)
- No manual provider in normal P10 runs
- AP01 remains publication authority
- ACP01 remains candidate-only

## Why this matters
P10 closes the gap between candidate-only internal logic and real embodied world effects by proving that body/inventory/world deltas are effect-correlated and AP01-gated.

## Action basis requirements
- Movement/turn: body basis + movement/orientation surface + explicit typed internal drive refs
- Pickup: typed drive-target refs + visible object + pickup surface + proximity + capacity
- Drop: typed drive-target refs + inventory item + drop surface
- No hidden/eval/scenario action basis

## Repeated publish semantics (multi-tick)
- P10 keeps basis-persistent repeat behavior for turn/move in multi-tick proofs.
- `ticks=2` can legitimately produce `AP01=2` and `submit=2` when basis remains valid.
- This is reported explicitly as:
  - `repeated_body_action_policy=basis_persistent_repeat_allowed`
  - `repeated_publish_expected=true`
  - `stale_candidate_detected=false` when request refs/effects are fresh and correlated.

## Scenario matrix
- `internal_turn_left_orientation_change`
- `internal_turn_right_orientation_change`
- `internal_move_forward_open`
- `internal_move_forward_blocked_wall`
- `internal_pickup_visible_reachable_item`
- `internal_pickup_no_drive_no_publish`
- `internal_pickup_no_visible_object_no_publish`
- `internal_pickup_no_proximity_no_publish`
- `internal_pickup_no_capacity_no_publish`
- `internal_drop_inventory_item`
- `internal_drop_without_inventory_no_publish`
- `internal_body_action_effect_feedback_next_tick`

## Falsifiers
P10 includes falsifiers for:
- manual-provider leakage
- missing action basis for pickup/move/turn/drop
- body/inventory/world deltas without correlated effect
- AP01 bypass
- hidden/eval targeting
- scenario-label action selection
- overclaiming in report text

## Ablation checks
P10 reuses P9 ablation surfaces for:
- no drive/object/proximity/capacity/surface basis
- suppress ACP01/AP01
- suppress effect feedback

## Allowed claim
“MORA demonstrates body-action effects in controlled GridWorld through internal ACP01 candidate production, AP01 publication, world execution, correlated ActionEffectFrame, and next-tick feedback.”

## Forbidden claims
- planning or motor intelligence
- general autonomy
- consciousness
- recipe/automation competence

## Substrate neutrality
World-specific mechanics remain in `experiments/embodied_playground`. ACP01 additions are generic action-intent vocabulary and basis checks, without world-map or scenario policy.

## Demo
```bash
python tools/embodied_body_action_demo.py --list-scenarios
python tools/embodied_body_action_demo.py --scenario internal_move_forward_open --ticks 2 --report
python tools/embodied_body_action_demo.py --scenario internal_move_forward_blocked_wall --ticks 2 --json
python tools/embodied_body_action_demo.py --scenario internal_pickup_visible_reachable_item --ticks 2 --report
python tools/embodied_body_action_demo.py --scenario internal_pickup_no_drive_no_publish --ticks 1 --json
python tools/embodied_body_action_demo.py --scenario internal_drop_inventory_item --ticks 2 --report
```
