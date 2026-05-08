# ADR-A01: Internal affordance ontology cleanup (frontier-hosted narrow slice)

## Status
Accepted (frontier build slice)

## Date
2026-05-08

## Decision
- Introduce `A01` as a typed ontology-cleanup seam in the existing A-line frontier segment.
- Lawful narrow insertion point in RT01 execution path:
  - `... -> S05 -> S_MINIMAL -> A01 -> A_LINE_NORMALIZATION -> ...`
  - checkpoint: `rt01.a01_affordance_ontology_cleanup_checkpoint`
- `A01` consumes typed raw affordance candidates plus direct upstream constraints already present in this slice (`C04/C05` execution claims, `S04` self-binding, `S05` factorization quality state).
- `A01` emits canonical affordance entries with explicit class separation, merge/split discipline, contested states, granularity handling, validity narrowing/deprecation, and typed gate surfaces.

## Scope (narrow and explicit)
- Frontier-hosted narrow slice only.
- Load-bearing outputs:
  - stable canonical affordance IDs and alias linkage
  - class-separated canonical entries
  - merge/split/contested/granularity decision ledger
  - validity status records (`valid/narrowed/deprecated/contested/unavailable`)
  - require/default checkpoint actions consumed by `subject_tick` gate
- Require-path consumers:
  - `require_a01_canonical_affordance_consumer`
  - `require_a01_contested_affordance_consumer`
  - `require_a01_deprecated_affordance_consumer`
- Default detours (basis-gated):
  - `default_a01_contested_canonicalization_detour`
  - `default_a01_deprecated_affordance_detour`
  - `default_a01_legacy_label_bypass_forbidden`

## Non-goals / forbidden shortcuts
- No hidden planner/action selection inside A01.
- No map-wide planner migration claim.
- No full world ontology claim.
- No affordance discovery claim.
- No string-dedup masquerading as ontology cleanup.
- No manual whitelist masquerading as canonical ontology.

## Seam-honesty choices
- Direct inputs are kept only where they materially affect canonicalization in deterministic branches:
  - `S04` no-stable-core state can force contested validity for self-relevant controllability claims.
  - `S05` contamination/high residual can force contested controllability validity.
  - `C05` revalidation action can narrow validity.
  - `C04` execution mode can narrow world-directed/communication affordances.
- No decorative direct seam added for unused upstream objects.

## Consequences
- Downstream now has explicit canonical affordance IDs and typed contested/deprecated handling in this slice.
- `subject_tick` downstream gate consumes typed A01 semantics directly (contested/deprecated/legacy-bypass/granularity effects), not checkpoint token only.
- Disabling `disable_a01_enforcement` is materially observable in narrow integration behavior.

## Bounded limitations
- Dual-ontology risk outside this narrow slice remains open (map-wide migration is not part of this decision).
- Full planner integration over canonical affordances remains open.
- Canonicalization quality is bounded by explicit typed input quality; no claim of complete affordance discovery.
