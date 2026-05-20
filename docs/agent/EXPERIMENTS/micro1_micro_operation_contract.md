# MICRO1 Micro-Operation Contract

## Purpose
Demonstrate bounded micro-operation framing and validation under public-evidence discipline, without action selection, AP01 publication, or world execution.

## Demo cases
- `inspect_unknown_resource`
- `move_toward_resource`
- `use_station_candidate`
- `store_resource`
- `repair_check`
- `provider_hint_basis`
- `quest_permission_blocked`
- `macro_factory_action_blocked`
- `ap01_lineage_reference`
- `failed_operation_residue`
- `effect_without_request_unresolved`
- `bounded_operation_graph`
- `success_requires_effect`
- `hidden_precondition_rejected`

## Valid examples
- Public pressure + affordance + action surface + expected effect => `candidate_basis_ready`.
- External AP01 request ref present => `request_published_elsewhere` lineage reference only.
- Observed effect + valid lineage => `effect_observed` / `succeeded` only when requirements hold.

## Blocked examples
- Macro action (`build_factory`) as atomic operation.
- Command/policy payload (`selected_action`, `route_plan`, `if_then_policy`).
- Hidden/backend precondition markers.
- Quest/cost/provider/recipe-script payload used as permission or script.
- World submission attempt.

## Status lattice examples
- Proposed path: `proposed -> candidate_basis_ready -> request_published_elsewhere -> effect_observed -> succeeded`.
- Failure path: `candidate_basis_ready -> failed/residue_open` with residue + next-pressure retained.
- Unresolved path: observed effect without request/passive marker => `unresolved`.

## Graph/decomposition examples
- Bounded graph with edges and one unverified intermediate produces partial graph with blocked edge markers.
- Macro task metadata allowed only when decomposed into child micro-operations.

## Residue examples
- Failure/residue frame captures failed preconditions, missing evidence, observed mismatch, and next-pressure refs.

## Why MICRO1 is not runner/selector/AP01/factory automation
- MICRO1 encodes candidate operation structure and evidence discipline only.
- It has no authority to select actions/goals, emit AP01 requests, execute world actions, assign value, mature recipe/skill/automation, or claim factory completion.
