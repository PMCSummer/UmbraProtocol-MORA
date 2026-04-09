# ADR-T01: Active Semantic Field / Active Non-Verbal Scene (First Bounded Build Slice)

## Status
Accepted for narrow `BUILD` increment.

## Decision
Introduce a typed `T01` production layer for an active semantic field / active non-verbal scene.

This increment materializes:
- typed scene state (entities, relations, role bindings, predicates, unresolved slots, attention/salience, temporal and expectation links);
- typed scene statuses (`assembled`, `fragment`, `provisional`, `competing`, `no-clean`, `authority-insufficient`);
- bounded field dynamics hooks (`assemble`, `update`, `decay`, `recenter`, `split`, `merge`, `slot_fill`, `relation_reweight`);
- provenance and source-authority tagging;
- pre-verbal downstream consumer contract and checkpoint integration in RT01 (`rt01.t01_semantic_field_checkpoint`);
- machine-readable forbidden shortcut markers for hidden-text, bag-of-tags, token-graph rebranding, premature closure, memory pollution, and immediate verbalization shortcuts.

This increment does **not** implement `T02`, `T03`, `T04`, or `O01`.
This increment does **not** implement full silent-thought line closure.

## Why
- The contour needed a typed non-verbal scene surface that exists independently from wording text.
- Downstream seams require pre-verbal inspectable state instead of telemetry-only decoration.
- Ambiguity and unresolved structure must remain first-class instead of being silently collapsed into fluent wording.

## Scope Implemented
- New production package: `src/substrate/t01_semantic_field/*`
  - models, assembly policy, downstream contract, telemetry snapshot.
- Bounded RT01 integration:
  - explicit `rt01.t01_semantic_field_checkpoint`;
  - path-affecting detour when `require_t01_preverbal_scene_consumer=True` and scene is not cleanly pre-verbal consumable.
- Runtime topology visibility:
  - `T01` node added to bounded production tick graph and dispatch/public contract snapshots.

## Anti-Creep Boundary
T01 in this pass is **not**:
- hidden text buffer surrogate,
- bag-of-tags relabeling,
- token-graph relabeling,
- planner/orchestrator,
- verbalizer,
- replacement for memory/self/narrative/world lines.

This pass is also **not**:
- `T02` relation binding propagation,
- `T03` hypothesis competition closure,
- `T04` attention schema execution,
- `O01` entity-model implementation.

## What Is Now Claimable
- A typed active non-verbal semantic field exists in bounded RT01 contour.
- Scene ambiguity/provisional/contested/unresolved states are explicitly preserved.
- At least one pre-verbal downstream consumer path is load-bearing before verbalization.
- T01 shortcut baselines can be falsified by targeted tests.

## What Is Not Claimable
- Full silent-thought line implemented.
- T02/T03/T04 implemented.
- O01 implemented.
- Repo-wide T01 adoption.

## Hardening Addendum (Bounded)
- Tightened unresolved-laundering discipline for weak-edge evidence:
  - `premature_scene_closure` now remains detectable under weaker unresolved basis signals when unresolved-slot maintenance is ablated.
  - RT01 pre-verbal consumer pressure enforces revalidation detour when laundering marker is present.
- Added second bounded downstream consequence in RT01 contour:
  - `require_t01_scene_comparison_consumer` requires scene-comparison readiness from T01 pre-verbal contract.
  - Not comparison-ready scenes now enforce bounded detour, without introducing T02/T03/T04 logic.

This addendum remains RT01-bounded and does not change the anti-creep boundary above.
