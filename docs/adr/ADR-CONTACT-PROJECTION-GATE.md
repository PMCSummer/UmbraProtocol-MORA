# ADR CONTACT-PROJECTION-GATE

## Status
Accepted (technical compatibility gate).

## Why it exists
UMWELT0 closes the contact membrane contract but existing `subject_tick` subsystems consume AB-INT and ACP01-facing structures. CONTACT-PROJECTION-GATE provides narrow, typed projection glue from validated UMWELT0 public contact into existing subject-side input surfaces.

## What it is not
- Not `UMWELT-S` ContactSpec/DSL.
- Not `WORLD0` runner.
- Not a world adapter.
- Not a planner, selector, or executor.
- Not AP01 request emission.

## Projection discipline
The gate preserves source-bound, uncertainty-preserving public evidence across channel kinds:
- `symbolic_world`
- `knowledge_affordance`
- `language_contact`
- `sensory_candidate`
- `body_internal`
- `social_external_actor`
- `system_status`
- `unknown_public`

Unknown channels are preserved only as bounded public basis refs when safe.

## Authority boundaries
Projection outputs must keep all authority flags false:
- no action selection
- no AP01 publication
- no world execution
- no fact/cause confirmation
- no value/recipe/skill/automation claims

## AB-INT / ACP01 / AP01 relation
- AB-INT: projected `public_observation_refs`, `public_effect_refs`, residue/uncertainty/conflict, optional effect/request correlation refs.
- ACP01: action surfaces projected as **basis only** plus context/hint/constraint refs.
- AP01: lineage passthrough (`request_ref`, `effect_ref`, source/correlation refs) only; no envelope emission.

## Allowed downstream uses
- AB public evidence ingestion.
- ACP01 candidate-basis ingestion.
- AP01 lineage/correlation continuity.
- Future WORLD0 packet handoff.

## Forbidden downstream uses
- treat projection as WorldState
- treat action surfaces as commands
- treat knowledge/language/sensory channels as truth or mature skill
- bypass AP01 via projection

## Falsifiers
- contact frame unwrapped to worldstate
- action surface treated as command
- knowledge/language hints treated as truth
- hidden eval/scenario labels projected
- projection emits AP01/world action
- multichannel collapse into oracle truth
- unbounded oversized projection

## Ablations
- blocked UMWELT0 frame
- no source refs
- hidden eval only
- scenario label only
- action policy surfaces
- unknown channels (safe/unsafe)
- oversized frame bounds

## Allowed claim
"CONTACT-PROJECTION-GATE projects validated public contact into existing AB/ACP/AP lineage-compatible input surfaces without action/publication/execution authority."

## Forbidden claims
- autonomous symbolic progression
- world runner implemented
- UMWELT-S implemented
- planner/adapter/factory execution implemented
