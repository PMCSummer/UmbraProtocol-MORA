# ADR-N01: Narrative Commitments (Narrow Registry Slice)

## Status
Accepted for narrow frontier build slice.

## Scope
N01 introduces a typed narrative commitment registry in RT01.
It is not a full narrative identity line, not a memory lifecycle subsystem, and not a policy selector.

## Decision
N01 converts typed narrative claim candidates into bounded commitment records with:
- decision class (`statement_only`, `provisional`, `confirmed`, `contested`, `revised`, `retired`, `no_clean`)
- strength and scope
- support basis
- conflict and revision state
- downstream obligations

## Core Discipline
- A claim candidate is not a confirmed commitment just because it was expressed.
- Capability claims require capability/tool/affordance support.
- Limitation claims require typed gap/blocking support.
- Scope is capped by basis; broad requested scope is narrowed when support is local.
- Conflicting candidates do not overwrite existing records silently.
- Basis invalidation produces explicit revised/retired transitions with preserved references.

## Runtime Placement
Checkpoint placement in current contour:

`rt01.w01_bounded_world_loop_checkpoint`
-> `rt01.m01_homeostatic_salience_imprint_checkpoint`
-> `rt01.m02_predictive_relevance_checkpoint`
-> `rt01.n01_narrative_commitments_checkpoint`
-> `rt01.outcome_resolution_checkpoint`

## Downstream Contract
N01 exposes machine-readable consumer packets with:
- record id
- claim kind
- strength
- scope
- grounding basis
- conflict status
- revision action
- obligation set
- confidence/provenance

## Non-Claims
N01 does not claim:
- full identity drift reflection (N02)
- autobiographical relevance routing (N03)
- full memory lifecycle actions (M03)
- user/other model behavior (O01)
