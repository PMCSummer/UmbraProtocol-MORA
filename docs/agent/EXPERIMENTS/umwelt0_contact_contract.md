# UMWELT0 Contact Contract Demo Notes

## Purpose
Demonstrate that UMWELT0 contact frames remain source-bound, uncertainty-preserving, and non-executing.

## Demo cases
- `valid_public_contact`
- `missing_source_refs`
- `protected_eval_blocked`
- `scenario_label_blocked`
- `action_surface_no_authority`
- `action_policy_rejected`
- `request_correlated_effect`
- `passive_public_event_effect`
- `effect_without_request_or_passive_blocked`
- `true_recipe_blocked`
- `full_map_blocked`
- `lossy_partial_contact`
- `empty_contact_noop`

## Accepted contact characteristics
- public refs are retained
- source refs are explicit
- residue and uncertainty refs are preserved
- authority flags remain false

## Blocked contact characteristics
- protected/scenario-only basis
- backend truth/worldstate-like payload
- true recipe/full map/hidden identity leaks
- action-policy payload in action surface
- effect frame without request/passive lineage

## Authority examples
- `can_select_action=false`
- `can_publish_ap01=false`
- `can_execute_world_action=false`
- `can_claim_fact=false`
- `can_confirm_cause=false`
- `can_assign_value=false`
- `can_mature_recipe=false`
- `can_mature_skill=false`
- `can_claim_automation=false`

## Claim boundary
UMWELT0 is a membrane contract only: not runner, not adapter, not DSL, not perception, not planner.

