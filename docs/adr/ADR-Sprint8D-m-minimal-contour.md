# ADR-Sprint8D: M-minimal Contour (Safe Memory Lifecycle Economy)

## Status
Accepted for narrow `BUILD + AUDIT` increment.

## Decision
Introduce a typed `M-minimal` contour for bounded memory lifecycle economy in RT01 contour.

This increment materializes:
- typed lifecycle state for memory economy (`temporary_carry`, `bounded_retained`, `review_required`, `stale/conflict`, `decay/pruning`, `no_safe_memory_claim`);
- machine-readable forbidden memory shortcuts;
- explicit future M-line admission surface (`M01` readiness blockers);
- bounded RT01 checkpoint consumption with path-affecting detours under memory-safe claim pressure.

This increment does **not** implement `M01`, `M02`, or `M03`.
This increment does **not** implement autobiographical/narrative/full retrieval memory.

## Why
- Existing repaired contour needed a minimal memory lifecycle discipline to avoid "store everything" behavior.
- Memory surfaces must stop masquerading as stable truth/identity basis without lawful lifecycle basis.
- Later M-line phases need an admission contour, not hidden pre-implementation.

## Scope Implemented
- New production package: `src/substrate/m_minimal/*`
  - typed lifecycle state, gate, admission, scope marker, telemetry, contract view.
- RT01 bounded integration:
  - explicit `rt01.m_minimal_contour_checkpoint`;
  - path-affecting detour when `require_memory_safe_claim=True` and safe lifecycle basis is absent/stale/conflicted.
- Runtime topology visibility:
  - `M_MINIMAL` node, checkpoint, and source-of-truth surface in bounded production tick graph/dispatch snapshots.

## Hardening Addendum (Sprint 8D, Narrow)
This hardening pass tightened the same bounded contour without expanding phase scope:
- `M01` admission gate moved from coarse structural checks to stronger negative-control blockers for borderline lifecycle cases (`stale/conflict/reactivation/temporary/provenance/underconstrained`).
- exported M surfaces now carry explicit machine-readable bounded scope truth, including `readiness_gate_only=true` and explicit non-claims (`m01/m02/m03/full stack/repo-wide = false`).
- adversarial lifecycle distinctions were tightened so `temporary_carry`, `reactivation_candidate`, `stale/conflict`, and `no_safe_memory_claim` are harder to collapse into a pseudo-retained basis.

This remains an admission gate for future M-line, not M01 semantics.

## M01/M02/M03 Boundary
- `M01` is **not implemented** in Sprint 8D.
- `M02` is **not implemented** in Sprint 8D.
- `M03` is **not implemented** in Sprint 8D.
- Sprint 8D only provides enabling contour/admission surface.

## Anti-Creep Boundary
Sprint 8D is **not**:
- autobiographical memory system,
- narrative memory stack,
- semantic memory engine,
- broad retrieval architecture,
- broad persistence rewrite.

## What Is Now Claimable
- A typed, bounded memory lifecycle economy surface exists in RT01 contour.
- Forbidden memory shortcuts are machine-readable.
- RT01 can enforce bounded memory-safe claim consequences via `M-minimal` checkpoint.
- Future M-line admission blockers are explicit and inspectable.
- Bounded-scope/non-claim truth for M-minimal is machine-readable in contract/snapshot surfaces.

## What Is Not Claimable
- M01 implemented.
- M02 implemented.
- M03 implemented.
- Full memory stack implemented.
- Repo-wide memory contour rollout.
