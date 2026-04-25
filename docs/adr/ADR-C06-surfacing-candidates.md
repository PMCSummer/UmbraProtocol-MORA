# ADR-C06: Surfacing Candidates (Narrow RT01-Hosted Slice)

## Status
Accepted (frontier build slice)

## Context
RT01 now includes V03 constrained realization. The runtime still needs a typed, auditable seam that surfaces continuity-relevant candidates from realized output and upstream deltas, without collapsing into:
- retention/memory write policy,
- next-turn planning,
- summary/highlight extraction.

## Decision
Introduce `C06` as a dedicated typed seam:
- package: `src/substrate/c06_surfacing_candidates/`
- contour placement: `... -> V03 -> C06 -> bounded_outcome_resolution -> ...`
- checkpoint: `rt01.c06_surfacing_candidates_checkpoint`

C06 builds a first-class `C06SurfacedCandidateSet` with:
- typed candidate classes (open question, commitment carryover, repair obligation, protective monitor, etc.),
- provenance/source refs and identity hints,
- explicit uncertainty and horizon hints,
- explicit suppression report with reasons,
- identity-merge accounting and false-merge flags.

Embedded C06.1 contract in this slice:
- `published_frontier_requirement`,
- `unresolved_ambiguity_preserved`,
- `confidence_residue_preserved`.

## Load-Bearing Contract
C06 is not telemetry-only in this slice.

Require-path flags:
- `require_c06_candidate_set_consumer`
- `require_c06_suppression_report_consumer`
- `require_c06_identity_merge_consumer`

Default basis-gated detours:
- `default_c06_candidate_ambiguity_detour`
- `default_c06_commitment_carryover_detour`
- `default_c06_protective_monitor_detour`

`subject_tick` policy consumes typed C06 semantics directly (counts, ambiguity flags, merge discipline, C06.1 contract markers), not only checkpoint token strings.

## Explicit Non-Claims
This ADR does **not** claim:
- map-wide continuity rollout,
- memory retention/write ownership,
- project reformation/planning authority,
- full downstream consumer ecosystem outside current RT01-hosted slice.

## Consequences
Positive:
- continuity surfacing is typed and auditable;
- suppression is explicit (examined-but-not-surfaced remains visible);
- RT01 gate has deterministic, basis-gated C06 effects.
- C06.1 publication semantics are non-contradictory (`frontier_not_published` applies only to unpublished workspace refs);
- identity merge now includes a typed stabilizer facet (`identity_stabilizer`) to reduce false merges across same-class/same-hint candidates;
- V03 alignment structure is directly consumed for project-continuation provenance selection and underconstrained-alignment fallback.

Bounded limitations:
- consumer ecology remains narrow/RT01-hosted;
- extraction remains frontier heuristic, not a global continuity engine.
