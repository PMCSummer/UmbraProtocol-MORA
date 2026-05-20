# ADR-UMWELT0 Phenomenal Contact Layer

## Status
Proposed (build pass complete, audit pending).

## Why UMWELT0 exists
`UMWELT0` defines a strict subject/world membrane: subject-facing runtime can consume only typed public contact artifacts, never backend truth payloads or worldstate dumps.

## Relation to AB-INT
- AB-INT consumes public refs, uncertainty and residue.
- UMWELT0 provides source-bound contact/effect surfaces that AB-INT can consume.
- UMWELT0 does not change AB1-AB7 behavior or scheduling.

## What UMWELT0 is not
- Not `UMWELT-S` (no ContactSpec/DSL/compiler).
- Not `WORLD0` (no live runner loop).
- Not `K-SURF1` provider integration.
- Not raw Sensorium/perception.
- Not action selection/publication/execution.

## Inputs
- public observation/effect/passive-event refs
- residue/uncertainty/conflict refs
- action-surface declarations (possibility surfaces only)
- effect frames (request-correlated or passive-event based)
- source/provenance refs
- lossiness markers
- protected/scenario/backend markers

## Outputs
- `PhenomenalContactFrame`
- `WorldContactFrame`
- `WorldEffectFrame` (validated)
- conformance counters
- blocked reasons
- downstream contract surface

## Authority boundary
- no action authority
- no AP01 publication authority
- no world execution authority
- no fact/cause closure
- no value assignment
- no mature recipe/skill/automation claim

## Key invariants
- accepted contact must remain public/source-bound
- hidden/protected eval basis is blocked
- scenario-label-only basis is blocked
- backend truth/worldstate/true recipe/full map/hidden identity are blocked
- effect frame requires `request_ref` or `passive_event_ref`
- lossy/partial contact requires explicit lossiness markers when declared

## Falsifiers addressed
- `worldstate_passed_to_subject`
- `backend_truth_in_contact_frame`
- `contact_frame_selects_action`
- `AP01_bypass_from_contact`
- `hidden_eval_public`
- `scenario_label_public_basis`
- `no_source_refs`
- `lossiness_unmarked`
- `true_recipe_in_contact`
- `full_map_in_contact`
- `hidden_identity_in_contact`
- `effect_without_request_or_passive_marker`
- `backend_specific_subject_field`
- `contact_claims_fact_or_cause`
- `contact_assigns_value_by_name`
- `contact_matures_recipe_or_skill`
- `contact_erases_residue`
- `contact_omits_authority_flags`

## Ablations
- no source refs
- protected eval only
- scenario label only
- action-policy payload
- true recipe payload
- effect without request/passive marker
- lossy contact without marker
- empty contact

## Allowed post-build claim
MORA can build typed public contact/effect frames with explicit uncertainty/lossiness and hard no-authority boundaries before downstream cognition.

## Forbidden claims
- world understanding proof
- recipe/skill/automation maturity
- planner/runner capability
- Minecraft competence
- consciousness/general intelligence

