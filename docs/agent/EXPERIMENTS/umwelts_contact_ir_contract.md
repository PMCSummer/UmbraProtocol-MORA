# UMWELT-S Contact IR Contract

## Demo cases
- minimal symbolic world
- generic grid fixture
- symbolic factory fixture
- mixed multichannel spec
- knowledge provider hint
- language contact testimony
- sensory candidate channel
- selected action rejected
- true recipe rejected
- full map rejected
- backend worldstate rejected
- unknown channel bounded
- provider truth rejected

## Fixture descriptions
- `generic_grid_fixture`: symbolic world + body + system channels.
- `symbolic_factory_fixture`: symbolic world + knowledge affordance + system status.
- `language_sensor_fixture`: language + sensory candidate + social channels.

## Accepted vs blocked
Accepted:
- typed channels, source-bound refs, bounded counts, no authority leakage.
Blocked:
- planner payloads, recipe oracle payloads, worldstate/full-map/hidden-label payloads, missing source requirements, unknown unbounded channel.

## Multi-channel IR examples
Channel groups are preserved in `ContactIR.normalized_channels`; hints/testimony/candidates remain typed and do not become world truth.

## UMWELT0 conformance examples
`UMWELT0ConstructionPlan` emits:
- public observation/effect refs
- action/effect surface refs
- source/lossiness/uncertainty/residue/conflict refs
- hard-false authority/claim flags

## Non-claim boundary
This layer is not:
- WORLD0 runner
- concrete backend adapter
- provider behavior implementation
- planner/action selector
- autonomous symbolic progression proof
