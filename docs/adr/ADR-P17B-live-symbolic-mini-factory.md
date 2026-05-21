# ADR-P17B: Live Symbolic Mini-Factory Run

## Status
Accepted for P17B owner seam build.

## Why P17B exists after P17 and WORLD0
P17 provided proof-side chain discipline. WORLD0 provided AP01-gated generic live orchestration.  
P17B is the first bounded live validation that combines both: multi-step symbolic chain with live WORLD0/AP01/effect lineage and strict residue/verification gates.

## Why P17B is not general factory automation
P17B is fixture-bounded. It does not include planner, pathfinder, inventory optimizer, route solver, Minecraft/tech-pack adapter, or autonomous factory control.

## Relation to WORLD0
P17B consumes WORLD0 cycle traces and AP01/effect lineage.  
P17B cannot bypass WORLD0 and cannot execute adapter steps directly.

## Relation to MICRO1
P17B carries MICRO1 refs as candidate operation structure only.  
MICRO1 refs do not imply selection/permission.

## Relation to COST1
P17B carries COST1 refs as comparison evidence only.  
COST1 winner/cheapness cannot authorize a step.

## Relation to P15/P16/AB7/P17
P17B preserves candidate discipline from P15, no-value-authority from P16, and no-automation closure from AB7.  
P17 proof traces are explicitly blocked as live execution substitutes.

## Relation to K-SURF1
Provider hints may be present as non-authoritative traces.  
Provider hint cannot become recipe truth or action permission.

## Core rules
- AP01-only execution rule: step execution requires AP01 lineage from subject path.
- Verified intermediate rule: downstream step requires verified intermediate refs.
- Residue stop rule: failed/unresolved steps preserve residue and block/partial the chain.
- No hidden recipe rule: hidden/true recipe payloads are blocked.
- No provider/cost permission rule: provider truth and cost-winner permissions are blocked.
- Trace/replay rule: need -> step -> WORLD0/AP01/effect -> verification -> residue/advance decisions must remain replayable.

## Allowed claim after build
MORA can run a bounded live symbolic mini-factory fixture chain with AP01-gated WORLD0 lineage and intermediate verification, while preserving residue/uncertainty and blocking shortcut authorities.

## Forbidden claims
- General factory automation
- Minecraft/tech-pack competence
- Planner/action-selector behavior
- Mature recipe/skill/automation closure
- General autonomy proof

## Falsifiers
- step_selected_without_need
- downstream_without_verified_intermediate
- factory_runner_bypasses_AP01
- hidden_recipe_as_plan
- cost_winner_as_action_permission
- provider_hint_as_recipe_truth
- p17_proof_as_live_execution
- noop_or_blocked_run_claims_completion

## Ablations
- remove need/AP01/effect/verification/residue
- inject hidden recipe/worldstate/scenario payload
- inject ContactSpec script / adapter solution sequence
- inject cost winner permission / provider truth
- use proof-only trace as live execution

