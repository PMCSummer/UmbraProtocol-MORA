# ADR-T03: Hypothesis Competition / Silent Convergence (First Bounded Build Slice)

## Status
Accepted for narrow `BUILD` increment.

## Decision
Introduce a typed `T03` production layer for bounded hypothesis competition and silent convergence over `T01` active semantic field + `T02` constrained scene.

This increment materializes:
- first-class typed hypothesis candidates with authority profile, constraint load, unresolved burden, stability, divergence signature, and provenance;
- explicit competition ledger semantics:
  - current leader,
  - provisional frontrunner,
  - tied competitors,
  - blocked/eliminated/reactivated candidates,
  - honest nonconvergence,
  - bounded plurality;
- transparent authority-weighted comparison with explicit bounded inputs:
  - authority-weighted support,
  - constraint satisfaction/violation,
  - unresolved burden,
  - conflict load,
  - bounded practical pressure (tie-shaping only);
- explicit convergence stopping states:
  - `continue_competing`,
  - `provisional_convergence`,
  - `stable_local_convergence`,
  - `honest_nonconvergence`;
- reactivation path for previously weakened candidates when lawful new support appears;
- `T03.1` publication frontier snapshot as load-bearing T03 surface:
  - `current_leader`,
  - `competitive_neighborhood`,
  - `unresolved_conflicts`,
  - `open_slots`,
  - `authority_profile`,
  - `stability_status`;
- bounded RT01 integration with explicit checkpoint:
  - `rt01.t03_hypothesis_competition_checkpoint`;
- bounded RT01-local consumer requirements:
  - `require_t03_convergence_consumer`,
  - `require_t03_frontier_consumer`,
  - `require_t03_nonconvergence_preservation`.

## Why
- T01/T02 provide structured alternatives and constraints, but a dedicated typed competition/convergence substrate was still missing.
- Downstream layers need inspectable convergence/frontier structure, not hidden top-1 collapse.
- Ambiguity and conflict must remain preservable without forced single-winner shortcuts.

## Scope Implemented
- New production package: `src/substrate/t03_hypothesis_competition/*`
  - models, policy, downstream contract, telemetry snapshot.
- RT01-bounded integration in `subject_tick`:
  - T03 build/evaluation before final outcome resolution,
  - path-affecting checkpoint enforcement under T03 consumer requirements.
- Runtime topology integration:
  - explicit `T03` node in production runtime order (`... T01 -> T02 -> T03 -> RT01`),
  - mandatory `rt01.t03_hypothesis_competition_checkpoint`,
  - public contract/snapshot visibility for competition ledger + publication frontier.

## Anti-Creep Boundary
This pass is **not**:
- `T04` implementation,
- `O01/O02/O03` implementation,
- planner,
- theorem prover,
- final verbalizer,
- full silent-thought line,
- repo-wide rollout.

T03 here does **not** invent new evidence, does **not** choose final action, and does **not** perform final closure.

## What Is Now Claimable
- A bounded RT01-local typed T03 competition layer exists.
- Competition is first-class and inspectable (not hidden top-1).
- Convergence vs nonconvergence/plural frontier is machine-readable.
- T03.1 publication frontier is materialized as load-bearing contract surface.
- RT01 path can change based on T03 consumer requirements/checkpoint outcomes.
- Shortcut ablations (greedy argmax, hidden-text reranking, no-revival, convenience bias, forced single winner, authority-weight disable) are machine-readable and test-falsifiable.

## What Is Not Claimable
- Full silent-thought line implemented.
- `T04` implemented.
- `O01/O02/O03` implemented.
- Planner/theorem-prover-grade reasoning implemented.
- Repo-wide T03 adoption completed.
