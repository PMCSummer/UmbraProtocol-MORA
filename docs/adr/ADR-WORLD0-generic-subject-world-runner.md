# ADR-WORLD0: Generic Subject World Runner

## Status
Accepted for WORLD0 owner seam build.

## Why WORLD0 exists after UMWELT-S/UMWELT0/projection
WORLD0 is the first generic orchestration loop that connects existing contact construction, projection, and subject execution seams without adding planner authority.

## WORLD0 role
WORLD0 is runner/orchestrator only:
- load adapter spec and contact surface input
- construct/validate UMWELT contact
- project with CONTACT-PROJECTION-GATE
- run subject_tick
- execute backend only from AP01-published envelopes
- wrap backend results into effect feedback
- preserve blocked/noop/replay trace

## Why WORLD0 is not P17B
WORLD0 does not hardcode factory chains, recipes, route plans, or station sequences. P17B remains the first live mini-factory proof.

## Relation to subject_tick
WORLD0 calls subject_tick and cannot mark a successful completed cycle without a subject_tick result.

## Relation to AP01
AP01 is the only action publication path. WORLD0 cannot create AP01 requests and cannot execute backend actions without AP01 envelopes.

## Relation to UMWELT-S / UMWELT0 / projection
- UMWELT-S ContactSpec remains declaration-only.
- UMWELT0 remains contact/effect conformance layer.
- CONTACT-PROJECTION-GATE remains projection-only compatibility seam.
WORLD0 composes them and must preserve their authority bounds.

## Relation to MICRO1 and COST1
MICRO1 and COST1 may provide candidate/context artifacts, but WORLD0 cannot select MICRO1 operations or COST1 winners.

## Relation to future phases
WORLD0 does not implement P17B/EXP1/PATH1/P18/ACTLEARN1 behavior; it only exposes bounded orchestration and trace points those phases can consume.

## AP01-only execution rule
Backend execution requires AP01 request envelopes. No AP01 means noop/skipped/blocked cycle.

## Effect correlation rule
Execution feedback requires request correlation or explicit passive event marker. Uncorrelated effects are blocked/partial with residue.

## Blocked/noop visibility rule
Blocked and noop cycles are first-class outcomes with explicit reasons. WORLD0 does not silently recover or promote partial data to completion.

## Trace/replay rule
WORLD0 emits cycle traces and replay references containing contact/projection/tick/AP01/execution/effect/residue/uncertainty lineage.

## No backend WorldState to subject rule
Backend worldstate/full-map/hidden labels/raw backend payload are blocked on subject-facing path.

## No factory script rule
ContactSpec/adapter metadata containing ordered plans, factory steps, or hardcoded sequences are blocked.

## Allowed claim after build
MORA can orchestrate generic world cycles through UMWELT-S/UMWELT0/projection/subject_tick/AP01-bounded execution and effect feedback with explicit blocked/noop/residue handling.

## Forbidden claims
- WORLD0 selects actions/goals/candidates.
- WORLD0 creates AP01 requests.
- WORLD0 executes without AP01.
- WORLD0 implements P17B factory behavior.
- WORLD0 proves autonomy or symbolic progression.

## Falsifiers
- runner_bypasses_subject_tick
- runner_executes_without_ap01
- runner_creates_ap01_request
- contact_spec_as_planner
- scenario_label_decision
- worldstate_passed_to_subject
- factory_runner_hardcodes_solution

## Ablations
- remove AP01 request
- remove request/effect correlation
- inject selected_action/selected_goal
- inject ordered_plan/factory_steps
- inject worldstate/full_map/hidden labels
- failed backend without residue
