# ADR-W01: Bounded World-Loop / Sensorimotor Closure (Narrow Staged Scaffold Slice)

## Status
Accepted for narrow frontier build slice.

## Scope
- Frontier-hosted only (`RT01` narrow slice).
- Operational contour placement in this build: `A04 -> W01 -> bounded outcome resolution`.
- No map-wide world/object pipeline claim.

## Decision
W01 defines a typed world-admission boundary for authority-tagged world packets.

W01 does:
- accept typed world packets and normalize presence/integrity/authority into explicit admission states;
- emit entity-centric scaffold tokens and downstream permission packets;
- preserve contradiction, absence, partial/degraded, and revocation markers;
- link observation/action/effect only through typed lineage checks;
- keep object metadata staged and non-mature in this slice.

W01 does not:
- implement mature object perception or stable object identity;
- claim object permanence, scene-graph maturity, or world truth;
- perform policy selection or action execution;
- replace W-line downstream phases.

## Authority Boundaries
- Admission requires explicit packet authority/integrity basis.
- `LANGUAGE_CONTEXT`, missing authority, malformed/revoked packets, and contradictory packets are not promoted as clean world claims.
- Object labels/stream ids remain provider scaffold metadata only.
- `object_authority_tags` are load-bearing for object-scaffold admission: when object metadata is present and tags are missing/invalid/revoked/incompatible, W01 degrades/rejects/contests the object-scaffold path instead of promoting clean grounded transition permission.
- Trusted packet source alone is not treated as a substitute for object authority tags.

## Mechanistic Notes
- No world packet => explicit no-clean/absence path.
- Present trusted packet can be admitted as scaffold permission, while `may_claim_object_presence=false` remains enforced.
- Contradictions create ledger entries and preserve unresolved conflict refs.
- Revocation invalidates active packet evidence.
- Observation/action/effect linkage requires action ref, temporal fit, authority compatibility, and valid packet integrity.

## Downstream Narrow Migration
- Checkpoint: `rt01.w01_bounded_world_loop_checkpoint`.
- Subject-tick gate consumes typed W01 counters/readiness/linkage directly.
- Default W01 detours are basis-gated (`w01_explicit_basis_present`).

## Observability
Compact runtime tap fields only:
- `w01_admission_state`
- `w01_presence_mode`
- `w01_source_authority`
- `w01_consumer_ready`
- `w01_must_abstain`
- `w01_must_preserve_uncertainty`
- `w01_non_mature_object_claim_count`
- `w01_contradiction_count`
- `w01_linked_effect_count`
- `w01_no_link_count`

## CLI Harness
`tools/w01_packet_world_demo.py` is an external observer/test harness over W01 owner policy. It is not an internal cognition layer.

## Known Limits (Intentional)
- no W02 regularity extraction
- no mature object pipeline
- no GUI observer panel
- no autonomous exploration
- no E01/E02 attractor pressure implementation
