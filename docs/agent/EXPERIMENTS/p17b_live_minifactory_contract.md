# P17B Live Mini-Factory Contract

## Live run contract
P17B run is valid only when each live step is backed by WORLD0/AP01/effect lineage and intermediate verification.

## Step contract
Each step must include:
- need lineage
- MICRO1 candidate refs
- AP01 request refs (subject path)
- WORLD0 execution/effect refs
- expected vs observed effects
- residue/uncertainty

Missing AP01 or missing effect feedback blocks the step.

## Intermediate verification examples
- Positive: expected `intermediate:heated_ingot` present in observed effects -> verified.
- Negative: expected ref absent though execution happened -> `expected_effect_not_observed` and downstream block.

## Residue stop examples
- Failed transform with residue stops downstream if safe continuation is disabled.
- Safe continuation mode can preserve residue and still allow later partial progress without completion claim.

## Positive bounded chain example
`resource:ore -> intermediate:ore_chunk -> intermediate:heated_ingot -> target:widget`  
All steps AP01/effect-backed and intermediates verified -> `completed_bounded_fixture`.

## Negative shortcut examples
- Cost winner used as permission -> blocked.
- Provider hint asserted as truth -> blocked.
- Contact/adapter script payload (`ordered_plan`, `solution_sequence`) -> blocked.
- Hidden recipe/worldstate/scenario payload -> blocked.
- Proof-only P17 trace without WORLD0/AP01/effect lineage -> blocked as non-live.

## Why P17B is not automation/general autonomy
P17B validates one bounded live symbolic fixture family only.  
It does not select actions/goals, does not create AP01, does not bypass WORLD0, and does not claim mature recipe/skill/automation or general autonomy.

