# ADR UMWELT-S Symbolic Contact Spec / Contact IR

## Status
Accepted for build-scope implementation.

## Why UMWELT-S exists after UMWELT0
UMWELT0 defines runtime contact membrane invariants and forbidden truth leaks. UMWELT-S adds a backend-agnostic symbolic declaration layer (ContactSpec + ContactIR) that can be validated before any runtime wiring.

## Not WORLD0 / Not final DSL / Not provider behavior
- Not WORLD0 runner/scheduler/executor.
- Not final human DSL parser/compiler; typed Python dataclasses are enough in this build.
- Not K-SURF1 provider behavior implementation.

## Core model
- Authoring artifact: `ContactSpec`.
- Normalized artifact: `ContactIR`.
- Runtime-facing conformance artifact: `UMWELT0ConstructionPlan`.

## Multi-channel discipline
Channels:
- `symbolic_world`
- `knowledge_affordance`
- `language_contact`
- `sensory_candidate`
- `body_internal`
- `social_external_actor`
- `system_status`
- `unknown_public`

Channel identities are preserved and not collapsed into world truth.

## Allowed fields and forbidden fields
Allowed:
- public refs, action/effect surfaces, provider declarations, source/lossiness/uncertainty policies.
Forbidden:
- selected action, route policy, planner payloads.
- recipe oracle payloads.
- worldstate/full-map/hidden-label/eval-label payloads.

## Authority boundaries
All authority flags remain false:
- no action selection/publication/execution
- no fact/cause confirmation
- no value assignment
- no mature recipe/skill/automation claims

## Relation to adjacent phases
- UMWELT0: target conformance surface.
- CONTACT-PROJECTION-GATE: consumes validated contact artifacts downstream.
- WORLD0: future runner that may consume ContactIR/plan.
- K-SURF1: future provider affordance semantics.
- MICRO1/COST1: future operational/action-economy layers.

## Fixture strategy
- `generic_grid_fixture`
- `symbolic_factory_fixture`
- optional `language_sensor_fixture`

Different backend families normalize through the same ContactIR contract.

## Falsifiers
- contact_spec_as_planner
- recipe_oracle_in_config
- selected_action_in_contact_spec
- route_truth_in_contact_spec
- worldstate_encoded_as_ir
- hidden_label_in_symbolic_ref
- source_refs_optional
- lossiness_unmarked
- unknown_channel_unbounded
- contact_spec_creates_ap01_request

## Ablations
- remove source refs
- remove lossiness under partial policy
- inject selected action policy
- inject true recipe / full map / hidden label / worldstate
- unknown channel without bounded/source/uncertainty discipline

## Allowed claim
"UMWELT-S can validate and normalize symbolic contact declarations into a backend-agnostic ContactIR and UMWELT0-compatible construction plan without planner, oracle, or action authority."

## Forbidden claims
- WORLD0 implemented
- concrete backend adapter implemented
- K-SURF1 provider behavior implemented
- autonomous symbolic progression proven
