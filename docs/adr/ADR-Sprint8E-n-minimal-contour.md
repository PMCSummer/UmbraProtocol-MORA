# ADR-Sprint8E: N-minimal Contour (Narrative Commitment Discipline)

## Status
Accepted for narrow `BUILD + AUDIT` increment.

## Decision
Introduce a typed `N-minimal` contour for bounded narrative commitment discipline in RT01 contour.

This increment materializes:
- typed narrative commitment state (`bounded`, `tentative`, `ambiguity-preserving`, `contradiction-marked`, `underconstrained`, `no-safe`);
- machine-readable forbidden narrative shortcuts;
- explicit future N-line admission surface (`N01` readiness blockers);
- bounded RT01 checkpoint consumption with path-affecting detours under narrative-safe claim pressure.

This increment does **not** implement `N01`, `N02`, `N03`, or `N04`.
This increment does **not** implement autobiographical narrative, narrative-self, or identity-story engines.

## Why
- Existing repaired contour required a minimal narrative commitment discipline that obeys already materialized W/S/A/M bases.
- Narrative surfaces must stop masquerading as stable self/world/memory/capability truth without lawful basis.
- Later N-line phases need an admission contour, not hidden pre-implementation.

## Scope Implemented
- New production package: `src/substrate/n_minimal/*`
  - typed commitment state, gate, admission, scope marker, telemetry, contract view.
- RT01 bounded integration:
  - explicit `rt01.n_minimal_contour_checkpoint`;
  - path-affecting detour when `require_narrative_safe_claim=True` and safe narrative basis is absent/ambiguous/contradictory.
- Runtime topology visibility:
  - `N_MINIMAL` node, checkpoint, and source-of-truth surface in bounded production tick graph/dispatch contract/snapshot.

## N01/N02/N03/N04 Boundary
- `N01` is **not implemented** in Sprint 8E.
- `N02` is **not implemented** in Sprint 8E.
- `N03` is **not implemented** in Sprint 8E.
- `N04` is **not implemented** in Sprint 8E.
- Sprint 8E provides enabling contour/admission surface only.

## Anti-Creep Boundary
Sprint 8E is **not**:
- autobiographical narrative system,
- self-story/identity-story engine,
- broad meaning/interpretation engine,
- prose-rich narrative generator expansion,
- repo-wide narrative rollout.

## What Is Now Claimable
- A typed, bounded narrative commitment surface exists in RT01 contour.
- Forbidden narrative shortcuts are machine-readable.
- RT01 can enforce bounded narrative-safe claim consequences via `N-minimal` checkpoint.
- Future N-line admission blockers are explicit and inspectable.

## What Is Not Claimable
- N01 implemented.
- N02 implemented.
- N03 implemented.
- N04 implemented.
- Full narrative line implemented.
- Repo-wide N-line adoption.

## Hardening Addendum (Sprint 8E Narrow Pass)
This hardening pass tightened bounded `N-minimal` behavior without opening `N01-N04`.

Materialized hardening moves:
- lawful-vs-underconstrained branching was sharpened with explicit basis quality signals and a bounded `lawful_tentative_safe` path;
- claim-pressure branches now emit runtime-falsifiable shortcut restrictions for ambiguity-hiding and contradiction-hiding attempts;
- consumer-boundary validators were added on exported `N` surfaces (n_minimal, subject_tick, runtime_topology) to enforce contour-bounded scope and reject unsafe strong narrative acceptance.

Hardening still does **not** implement:
- `N01`, `N02`, `N03`, `N04`,
- autobiographical/identity-story semantics,
- repo-wide narrative rollout.
