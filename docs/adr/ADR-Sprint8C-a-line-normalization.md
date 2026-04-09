# ADR-Sprint8C: A-line Normalization (A01–A03 Only)

## Status
Accepted for narrow `BUILD + AUDIT` increment.

## Decision
Introduce a typed A-line normalization substrate for `A01–A03` in bounded RT01 contour.

This increment materializes:
- typed capability/affordance basis state,
- machine-readable capability shortcut forbiddance,
- bounded RT01 checkpoint consumption for capability claim pressure,
- explicit `A04` readiness criteria and blockers.

This increment does **not** implement `A04`.
This increment keeps `A05` untouched.

## Why
- After foundation repair + W-entry + S-minimal contour, capability/affordance handling must be inspectable and bounded.
- A01–A03 should not remain implicit helper behavior or roadmap labels.
- Later A-line phases need lawful admission surfaces instead of hidden capability inflation.

## Scope Implemented
- New production package: `src/substrate/a_line_normalization/*`
  - typed capability basis state and status taxonomy,
  - forbidden capability shortcuts (machine-readable),
  - `A04` readiness surface with explicit blockers,
  - bounded scope marker and contract/snapshot surfaces.
- RT01 bounded integration:
  - explicit `rt01.a_line_normalization_checkpoint`,
  - path-affecting detour when required capability claim lacks lawful basis.
- Runtime topology visibility:
  - A-line checkpoint and source-of-truth surface added to minimal runtime graph and dispatch views.

## A04 / A05 Boundary
- `A04` is **not implemented** in Sprint 8C.
- Sprint 8C only exposes `A04` admission/readiness criteria.
- `A05` is deliberately **untouched**.

## Anti-Creep Boundary
Sprint 8C is **not**:
- planner upgrade,
- external means justification engine,
- full agency stack,
- broad repo-wide action architecture rollout.

## What Is Now Claimable
- A typed, inspectable A-line normalization substrate exists for A01–A03 in bounded RT01 contour.
- Capability inflation shortcuts are machine-readable and can trigger bounded detours under claim pressure.
- A04 admission blockers/readiness are explicitly surfaced.

## What Is Not Claimable
- A04 implemented.
- A05 implemented or partially opened.
- Full agency stack implemented.
- Repo-wide A-line rollout.

## Hardening Addendum (Sprint 8C Narrow Pass)
- `A04` readiness was tightened from structural visibility to bounded quality gates with explicit negative-control blockers:
  - `capability_basis_missing`
  - `world_dependency_unmet`
  - `self_dependency_unmet`
  - `policy_legitimacy_unmet`
  - `underconstrained_capability_surface`
  - `external_means_not_justified`
  - `structurally_present_but_not_ready`
- Consumer-facing A-line scope truth is now machine-readable across public contract surfaces:
  - `scope=rt01_contour_only`
  - `a_line_normalization_only=true`
  - `readiness_gate_only=true`
  - `a04_implemented=false`
  - `a05_touched=false`
  - `full_agency_stack_implemented=false`
  - `repo_wide_adoption=false`
- Adversarial capability distinctions were tightened and tested:
  - `available_capability` vs `policy_conditioned_capability`
  - `available_capability` vs `underconstrained_capability`
  - `underconstrained_capability` vs `no_safe_capability_claim`
- Scope remains unchanged:
  - no A04 implementation,
  - no A05 change,
  - no planner expansion,
  - no repo-wide rollout.
