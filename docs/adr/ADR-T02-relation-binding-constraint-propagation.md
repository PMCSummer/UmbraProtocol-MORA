# ADR-T02: Relation Binding / Constraint Propagation (First Bounded Build Slice)

## Status
Accepted for narrow `BUILD` increment.

## Decision
Introduce a typed `T02` production layer for relation binding / constraint propagation over the existing `T01` active semantic field.

This increment materializes:
- typed binding state with machine-readable statuses (`candidate`, `confirmed`, `provisional`, `blocked`, `incompatible`, `conflicted`, `retracted`);
- typed constraint objects with explicit `origin`, `scope`, `polarity`, `authority_basis`, `applicability_limits`, and `propagation_status`;
- typed propagation records with trigger lineage, scope, effect type, and explicit stop reasons;
- conflict-preserving structure with overwrite-forbidden semantics and downstream visibility;
- downstream contract that distinguishes:
  - raw scene content from `T01`,
  - relation-binding-added structure,
  - propagated consequences,
  - blocked/conflicted consequences;
- bounded pre-verbal consumer interface and RT01 checkpoint integration via `rt01.t02_relation_binding_checkpoint`.
- bounded raw-vs-propagated integrity consequence in RT01 via
  `rt01.t02_raw_vs_propagated_integrity_checkpoint`, so raw scene vs propagated/blocked consequences
  remains load-bearing under a dedicated bounded contract requirement.

This increment does **not** implement `T03`, `T04`, or `O01`.
This increment does **not** implement full silent-thought-line closure.

## Why
- `T01` provides co-activated scene substrate, but first-class relation binding and scoped propagation were still missing.
- Downstream phases need inspectable constrained-scene structure, not raw co-activation or hidden code rules.
- Conflict and uncertainty must remain first-class instead of being silently overwritten.

## Scope Implemented
- New production package: `src/substrate/t02_relation_binding/*`
  - models, policy, downstream contract, telemetry snapshot.
- Bounded RT01 integration:
  - explicit checkpoint `rt01.t02_relation_binding_checkpoint`;
  - path-affecting detour when `require_t02_constrained_scene_consumer=True` and constrained-scene consumer contract is not cleanly admissible.
- Runtime topology visibility:
  - `T02` node added to bounded production tick graph (`... T01 -> T02 -> RT01`);
  - `rt01.t02_relation_binding_checkpoint` added to mandatory checkpoint set;
  - constrained-scene surface included in source-of-truth/runtime dispatch contract snapshots.

## Anti-Creep Boundary
T02 in this pass is **not**:
- graph-edge decoration relabeled as binding,
- spreading-activation relabeled as scoped propagation,
- hidden theorem prover,
- planner/orchestrator,
- replacement for `T03`/`T04`/`O01`.

This pass is also **not**:
- full semantic closure engine,
- repo-wide T02 rollout.

## What Is Now Claimable
- A typed relation-binding and scoped-constraint-propagation layer exists in bounded RT01 contour.
- Candidate/confirmed/provisional/blocked/conflicted/incompatible distinctions are machine-readable.
- Constraint objects and propagation stop conditions are inspectable.
- Conflict-preserving structure exists and silent-overwrite shortcuts are explicitly markable.
- At least one bounded pre-verbal downstream consumer path is load-bearing before wording/final selection.
- A second bounded RT01-local consequence exists for raw-vs-propagated distinction integrity; flattening
  this distinction can enforce detour without introducing T03/T04/O01 logic.

## What Is Not Claimable
- Full silent-thought line implemented.
- `T03` implemented.
- `T04` implemented.
- `O01` implemented.
- Repo-wide T02 adoption.
