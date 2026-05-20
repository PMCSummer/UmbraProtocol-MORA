# ADR-MICRO1: Universal Micro-Operation Frame

## Status
Accepted for build scope (MICRO1 owner seam only).

## Why MICRO1 exists
After UMWELT0/UMWELT-S/K-SURF1, the stack can expose public contact, channelized basis, and provider hints, but lacks a portable bounded operation unit. MICRO1 provides that unit: a typed micro-operation frame and bounded composition graph.

## What MICRO1 is not
- Not action selection.
- Not AP01 request publication.
- Not world execution.
- Not WORLD0 runner.
- Not P17B factory loop.
- Not PATH1 planner.
- Not COST1 comparator.
- Not ACTLEARN1/OPTION1 maturity layer.

## Relation to ACP01/AP01
- MICRO1 may provide candidate-ready operation basis to ACP01.
- MICRO1 may reference AP01 request lineage (`ap01:*` / `request:*`) only if externally supplied.
- MICRO1 cannot create AP01 requests.

## Operation status lattice
- `proposed`
- `basis_incomplete`
- `candidate_basis_ready`
- `blocked`
- `request_published_elsewhere`
- `effect_observed`
- `succeeded`
- `failed`
- `unresolved`
- `residue_open`

## Public basis and expected-effect discipline
- Non-noop operations require public basis refs.
- Target affordance/action surface are basis only, never command/selected action.
- Expected effect refs are required for non-noop operation validity.

## AP01 lineage discipline
- `ap01_request_ref` is reference-only lineage.
- Any AP01 emission attempt is blocked.
- Any world submission attempt is blocked.

## Residue and next-pressure discipline
- Failed/blocked operations must preserve residue or next-pressure lineage.
- Missing residue in failed/blocked paths is invalid (`residue_missing_after_failure`).

## Macro-action decomposition discipline
Macro labels such as `build_factory`, `solve_quest`, `automate_line`, `follow_route` are invalid as atomic operations. They must be represented as decomposed micro-graphs with child operations and dependency edges.

## Hidden-precondition and provider-hint boundaries
- Hidden/backend/scenario/eval preconditions are blocked.
- Provider/quest/cost/recipe-script markers are blocked when used as truth/permission/script.
- Knowledge/provider hints remain basis candidates only.

## Relation to downstream phases
- WORLD0 may later run contact→tick→AP01→effect loops using MICRO1 frames/graphs.
- P17B may later consume MICRO1 decomposition for bounded chain execution tests.
- PATH1/ACTLEARN1/OPTION1/COST1 may consume MICRO1 basis/lineage artifacts, but authority remains outside MICRO1.

## Allowed claim after build
MORA can encode, validate, and compose bounded public-evidence micro-operations with strict no-command/no-publication/no-world-execution authority.

## Forbidden claims
- MICRO1 selects actions.
- MICRO1 publishes AP01 requests.
- MICRO1 runs a world.
- MICRO1 proves live factory autonomy.
- MICRO1 matures skills/options/automation.

## Falsifiers
- operation without public basis accepted.
- macro action accepted as atomic operation.
- AP01 request created by MICRO1.
- world submission created by MICRO1.
- success accepted without observed effect lineage.
- failed/blocked operation accepted without residue.
- provider hint treated as operation truth/permission/script.

## Ablations
- no public pressure.
- no target affordance.
- no expected effect.
- selected-action/route-policy payload.
- AP01 emission attempt.
- world submission attempt.
- success without effect.
- effect without request/passive marker.
- failure without residue.
- macro action as atomic.
