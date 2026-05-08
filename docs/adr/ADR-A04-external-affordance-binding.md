# ADR-A04: External Affordance Binding (Narrow Frontier Slice)

## Status
Accepted for narrow staged scaffold build slice.

## Scope
- Frontier-hosted only (`RT01` narrow slice).
- Operational contour placement in this build: `P04 -> A04 -> bounded outcome resolution`.
- No map-wide world/object migration claim.

## Decision
A04 defines a typed external affordance binding seam over authority-tagged world scaffold input.

A04 does:
- bind external affordance candidates to `entity_ref`/optional `object_ref` only through authority-tagged scaffold packets;
- require admission discipline before promotion to admitted/provisional binding packets;
- preserve authority, scope, contradiction, and revocation markers in owner result, gate, contract view, telemetry, and checkpoint;
- keep object-scaffold intake staged (object scaffold only), without mature object-identity claims.

A04 does not:
- perform mature object perception or full world modeling;
- resolve object identity globally;
- choose policy or execute actions;
- replace W-line embodiment phases;
- emit world-truth guarantees.

## Authority Boundaries
- A04 accepts only authority-scoped scaffold evidence and emits staged binding status.
- Unsupported candidates, no authority path, contradictory scaffold packets, and revocation stay explicit as blocked/contested/revoked outputs.
- No object-level affordance promotion without admission path.

## Mechanistic Notes
- Entity-centric binding is valid even when `object_ref` is absent.
- `object_ref` intake remains scaffold-scoped and keeps `object_maturity_claim_blocked=true`.
- Contradictory scaffold packets are not silently collapsed; they remain contested/blocked with preserved refs.
- Revocation invalidates active binding packets and is downstream-visible.

## Downstream Narrow Migration
- Checkpoint: `rt01.a04_external_affordance_binding_checkpoint`.
- Basis-gated detours are emitted only when explicit A04 candidate basis exists.
- Subject-tick gate consumes typed A04 counters/readiness directly (not checkpoint token only).

## Observability
Compact runtime tap fields only:
- `a04_binding_count`
- `a04_contested_count`
- `a04_blocked_count`
- `a04_revoked_count`
- `a04_authority_missing_count`
- `a04_object_overclaim_blocked_count`
- `a04_consumer_ready`
- `a04_staged_scaffold_only`
- `a04_no_map_wide_claim`

## Falsifiers Closed in this Slice
- object/name string shortcut promoted as admitted binding
- authority-less candidate promoted as external affordance claim
- contradictory scaffold packets silently collapsed
- object scaffold treated as mature object claim
- telemetry-only seam without downstream gate effect

## Known Limits (Intentional)
- no map-wide planner/world migration
- no full W01/E01 implementation in this phase
- no object identity resolution completion
- no external action execution/runtime orchestration
