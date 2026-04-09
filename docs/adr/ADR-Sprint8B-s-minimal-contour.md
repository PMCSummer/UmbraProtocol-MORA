# ADR-Sprint8B: S-minimal Contour (Not Full S-line)

## Status
Accepted for narrow `BUILD + AUDIT` increment.

## Decision
Introduce a typed `S-minimal contour` layer for bounded RT01 contour consumption.

This increment adds:
- typed self/world boundary state,
- ownership/controllability-weighted attribution classes,
- machine-readable forbidden self/world collapse shortcuts,
- explicit S-line admission relation surface for later S01–S05.

This increment does **not** implement S01–S05.

## Why
- Foundation repair, runtime topology, world seam, and W-entry admission are already materialized.
- RT01 still needed a minimal self/world attribution substrate that is not prose-only and not identity overreach.
- Sprint 8B closes this with a bounded path-affecting contour gate, without building a full self model.

## Scope Implemented
- New production package: `src/substrate/self_contour/*`
  - typed boundary state (`self/world basis`, `controllability`, `ownership`, `confidence`, `source-status`, `breach-risk`),
  - typed gate decision with forbidden shortcut taxonomy,
  - typed admission relation (`S-minimal now` vs `future S01–S05`),
  - typed scope marker and contract snapshot surfaces.
- RT01 bounded integration:
  - explicit `rt01.s_minimal_contour_checkpoint`,
  - path-affecting detours when required self/world claims are unlawful/underconstrained.
- Runtime topology visibility:
  - S-minimal checkpoint and source-of-truth surface are visible in tick graph/dispatch contract.

## Forbidden Shortcuts (Machine-Readable)
The contour now marks at least:
- `self_claim_without_self_basis`
- `ownership_claim_without_action_or_boundary_basis`
- `control_claim_without_controllability_basis`
- `external_event_reframed_as_self_owned`
- `self_state_reframed_as_world_fact`
- `mixed_attribution_without_uncertainty_marking`

## Authority Boundary Preservation
- C04 remains arbitration authority.
- C05 remains legality/invalidation authority.
- R04 remains survival/gating authority.
- RT01 remains execution spine and consumer of contour results.
- F01 remains transition/provenance spine.

No self-semantics ownership is transferred into RT01/F01.

## Relation to Future S-line
Sprint 8B provides enabling contour only.

Still open for future S01–S05:
- richer prediction boundary,
- ownership-weighted learning,
- interoceptive self-binding,
- multi-cause attribution factorization,
- any broad self-model closure.

## Anti-Creep Boundary
Sprint 8B is **not**:
- full S-line implementation,
- identity engine,
- autobiographical or narrative self,
- global self-theory,
- repo-wide self/world rollout.

## Narrow Hardening Addendum (Sprint 8B)
This hardening pass tightened bounded contour discipline without expanding S-line scope:

- `s01_admission_ready` is now quality-gated, not just structural.
  - Admission requires sufficient self-attribution/controllability/ownership basis.
  - Underconstrained, mixed-instable, and no-safe-basis cases now materialize explicit readiness blockers.
- Mixed self/world ambiguity enforcement is stricter under S-claim pressure.
  - Mixed instability now forces bounded revalidation when required self/world/control claim classes are requested.
  - This is bounded to RT01 S-minimal consumption and does not change phase authority semantics.
- Consumer-facing scope truth is machine-readable in public contract surfaces.
  - `rt01_contour_only=true`
  - `s_minimal_only=true`
  - `s01_implemented=false`
  - `s_line_implemented=false`
  - `repo_wide_adoption=false`

## What Is Now Claimable
- A typed, inspectable S-minimal self/world boundary and attribution contour exists in bounded RT01 runtime contour.
- Forbidden self/world shortcuts are machine-readable.
- Required self/world claim classes can causally force bounded detours (`repair`/`revalidate`) in RT01.

## What Is Not Claimable
- S01–S05 implemented.
- Full self model implemented.
- Narrative/autobiographical self implemented.
- Repo-wide self/world contour adoption.
