# ADR-A02: Capability Gap Detection (Narrow Frontier Slice)

## Status
Accepted for narrow frontier build slice.

## Decision
A02 is added as a typed capability-gap seam in RT01 contour:

`S_MINIMAL -> rt01.a01_affordance_ontology_cleanup_checkpoint -> rt01.a02_capability_gap_detection_checkpoint -> A_LINE`

A02 consumes A01 canonical affordance ontology and typed demand packets to classify demand coverage as:
- fully covered
- partially covered
- blocked
- missing
- composition-dependent
- ownership-boundary limited
- no-clean-coverage/unknown

## Explicit non-claims
- No map-wide planner integration claim.
- No planner replacement claim.
- No affordance discovery/invention claim.
- No action execution claim.
- No world-ontology completion claim.

## Operational constraints
- A02 must read A01 typed canonical entries; raw local-label reconstruction is forbidden.
- `no_plan_found`/planner deadend markers are not capability-gap proof.
- Low confidence alone is not missing-capability proof.
- Demand legitimacy is required for strong missing/blocking claims.
- Missing vs blocked must remain distinct.
- Ownership-boundary gaps remain distinct from missing internal capability.

## Downstream contract
Subject tick consumes A02 typed counters/readiness and basis-gated detour markers.
Default detours are only applied when explicit A02 basis is present.

## Hardening notes
- Source lineage is threaded into A02 ledger/telemetry/contract views.
- Canonical ID coverage metrics are propagated into A02 result and downstream gate:
  - `canonical_id_hint_used_count`
  - `canonical_id_generated_count`
  - `canonical_id_coverage_complete`
- Planner-deadend/low-confidence demand signals are explicitly mediated as non-authoritative basis refs:
  they are visible in coverage evidence, but cannot override ontology coverage and cannot force
  `missing_affordance` when typed A01 coverage is present.
- Taxonomy branches are mechanistic in this slice:
  - `A02GapKind.LOW_RELIABILITY_AFFORDANCE`
  - `A02GapKind.RESOURCE_BLOCKED_GAP`
  - `A02CoverageStatus.CONTESTED` (narrowly gated to multi-candidate contested ambiguity, not any contested validity).

## Remaining limits
- Narrow frontier slice only.
- No map-wide consumer migration.
- No long-horizon capability acquisition semantics in this phase.
