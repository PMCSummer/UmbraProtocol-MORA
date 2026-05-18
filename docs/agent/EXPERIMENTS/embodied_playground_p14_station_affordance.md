# P14 / Station Affordance Proof

## Purpose
P14 validates station interaction as a bounded external affordance under public visibility/proximity/input/blocked constraints.

## Relation to P13
- P13 remains delayed-credit and confounder discipline owner.
- P14 does not create mature schema and does not perform recipe/precursor learning.

## Relation to P15
- P15 can later consume P13 provisional candidates for recipe/precursor maturation.
- P14 only proves bounded station-use affordance conditions and AP01-gated effect path.

## Why P14 is not recipe learning
- no mature recipe/schema output (`mature_schema_created=False`)
- no transformation-rule discovery
- no automation pipeline
- no hidden evaluator-only transformation data in subject path

## Station matrix
- station visible not usable
- station proximate no input
- station proximate with input
- station blocked
- station protected evaluator-only rule
- station action-surface only
- station far with input
- station missing station ref
- station effect without AP01 attempt
- station use effect feedback

## Falsifiers
- `station_use_without_affordance`
- `station_visible_as_usable`
- `station_use_without_proximity`
- `station_use_without_input`
- `protected_eval_rule_used_by_subject`
- `scenario_label_station_use`
- `action_space_as_station_permission`
- `station_effect_without_ap01`
- `station_request_as_success`
- `blocked_station_claimed_success`
- `missing_input_erased`
- `inventory_delta_without_station_effect`
- `world_delta_without_station_effect`
- `recipe_or_mature_rule_result_in_p14`
- `one_shot_station_schema_maturity`
- `station_affordance_report_overclaims`
- `station_use_crosses_acp01_boundary`
- `station_use_crosses_ap01_boundary`

## Ablations
- remove station ref
- remove proximity
- remove input refs
- remove action surface
- protected evaluator-only rule only
- remove AP01 ref
- remove effect ref
- blocked station
- one-shot success

## Allowed claims
- MORA can validate bounded station affordance conditions under public visibility/proximity/input/blocked constraints.

## Forbidden claims
- MORA learned recipes.
- MORA knows station mechanics as transformation truth.
- MORA has automation.
- MORA has general tool-use intelligence.
- MORA proves consciousness.
