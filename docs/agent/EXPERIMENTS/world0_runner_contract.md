# WORLD0 Runner Contract

## Runner contract
WORLD0 composes:
1. adapter observation packet
2. UMWELT0 contact construction
3. CONTACT-PROJECTION-GATE projection
4. subject_tick execution
5. AP01 request collection
6. backend execution from AP01 only
7. effect feedback + residue/uncertainty trace

## Adapter contract
Adapter provides only:
- `observe(cycle_id)` public observation packet
- `execute_ap01_envelope(request)` backend execution result

Adapter must not select action/goal and must not expose hidden worldstate to subject path.

## AP01-only execution examples
- `ap01_execution`: backend runs only when AP01 request exists.
- `no_ap01_no_execution`: runner skips execution and emits noop/skipped status.

## Blocked/noop examples
- `blocked_contact`: contact invalid -> blocked cycle, no execution.
- `adapter_action_selection_blocked`: adapter selection markers -> blocked.
- `contactspec_plan_blocked`: ContactSpec plan markers -> blocked.
- `backend_worldstate_blocked`: worldstate payload -> blocked.

## Effect feedback examples
- request-correlated backend effect -> correlated feedback
- passive public event -> passive marker, no cause proof
- uncorrelated backend effect -> blocked/partial with residue

## Trace/replay examples
WORLD0 trace preserves:
- contact frame refs
- projection refs
- subject_tick ref
- AP01 request refs
- backend execution refs
- world effect refs
- residue/uncertainty refs

Replay ref is emitted when replay mode is enabled.

## Two-backend fixture explanation
`two_backend_grid` and `two_backend_inventory` run through identical runner policy and data contract; no backend-specific branch logic is required in subject path.

## Why WORLD0 is not autonomous progression
WORLD0 does not:
- select actions/goals/candidates
- create AP01 requests
- execute without AP01
- assert fact/cause/value/recipe/skill/automation maturity
- implement factory planning/scheduling

It is orchestration glue with explicit uncertainty, residue, and blocked/noop transparency.
