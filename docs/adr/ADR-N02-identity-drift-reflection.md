# ADR-N02: Identity Drift Reflection (Narrow Registry Slice)

## Status
Accepted for narrow frontier build slice.

## Scope
N02 introduces a typed identity-drift reflection layer over N01 commitment history and self-relevant substrate.
It is not a full identity model, not autobiographical relevance routing, and not a memory lifecycle subsystem.

## Decision
N02 emits typed drift-assessment entries that compare:
- explicit baseline references
- current identity-relevant evidence
- substrate change markers

The emitted classes are bounded and machine-readable:
- `stable_continuation`
- `bounded_revision`
- `gradual_shift`
- `abrupt_reorientation`
- `context_split_detected`
- `commitment_erosion`
- `capability_revision_drift`
- `self_binding_drift`
- `contradiction_driven_fracture`
- `unresolved_identity_tension`
- `no_clean_drift_claim`

## Core Discipline
- N02 does not rewrite N01 commitments.
- Drift is not inferred from text diff alone.
- Missing/stale/contested baseline is treated as uncertain/no-clean, not forced drift.
- Competing baselines for the same identity region are resolved deterministically with explicit validity-first selection; tie-breaks stay scoped and reproducible.
- Context split remains scoped and must not be flattened into global rupture.
- Tool availability updates without self-related contour impact are capped by overreflection guard.

## Runtime Placement
Current contour placement:

`rt01.w01_bounded_world_loop_checkpoint`
-> `rt01.m01_homeostatic_salience_imprint_checkpoint`
-> `rt01.m02_predictive_relevance_checkpoint`
-> `rt01.n01_narrative_commitments_checkpoint`
-> `rt01.n02_identity_drift_reflection_checkpoint`
-> `rt01.outcome_resolution_checkpoint`

## Downstream Contract
N02 provides machine-readable consumer packets containing:
- drift id
- affected region
- drift kind and magnitude
- continuity flag
- context split scope
- reflection need and revision pressure
- downstream caution
- baseline/current references
- affected commitment ids
- reason codes and confidence

## Non-Claims
N02 does not claim:
- metaphysical identity truth
- N03 autobiographical relevance
- M03 retrieval/replay/consolidation lifecycle
- O01 user/other modeling
- commitment rewriting authority
