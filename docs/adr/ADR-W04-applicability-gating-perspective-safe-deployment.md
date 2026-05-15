# ADR-W04: Applicability Gating / Perspective-Safe Deployment

## Status
Accepted for narrow BUILD slice.

## Decision
Introduce `W04` as a bounded applicability gate that consumes typed W03 schema/prior intake plus desired-state/context/perspective/constraint profile and emits machine-readable applicability decisions.

## Scope
W04 does:
- evaluate bounded deployability of W03 priors/candidates per desired-state intersection;
- preserve hard-vs-soft constraint semantics;
- preserve perspective and authority boundaries;
- route stale/unknown/contradictory/malformed cases to block/revalidate/abstain/hint-only;
- emit typed downstream applicability permission packets.

W04 does not:
- build plans or select actions;
- authorize action execution;
- create schemas or mutate W03 content;
- inject W05 predictive priors;
- run W06 revision logic;
- assert world truth or ontology claims.

## Contour Placement
`W01 -> W02 -> W03 -> W04 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w04_applicability_gating_checkpoint`

## Authority Boundaries
- W04 consumes W03 outputs and permission markers only.
- Desired-state priority is not permission and cannot override hard constraints.
- Unknown hard feasibility is not treated as allowed.
- Perspective transfer requires explicit allowance.
- Authority scope cannot be broadened by W04.

## Hard/Soft Constraint Discipline
- hard failure => no clean deploy;
- unknown hard => revalidate/abstain path;
- soft conflicts may relax only with explicit relaxation ledger and residual-risk trace;
- hard constraints are non-relaxable.

## Intersection and Empty-Set Policy
W04 computes desired-state / schema / context / constraints intersection and must surface explicit block/narrow/revalidate/abstain when no clean feasible region exists. No silent force-fit.

## Downstream Contract
W04 packet exposes explicit boundaries:
- `may_deploy_candidate`
- `may_use_as_hint_only`
- `may_use_after_revalidation`
- `may_use_with_relaxation`
- `must_abstain`
- `must_block`
- `must_revalidate`
- `must_preserve_hard_constraints`
- `must_preserve_perspective_scope`
- `must_preserve_authority_scope`
- `action_authorization_granted` (always `False`)

Hardening note:
- W03 `prohibited_claims` are preserved into W04 `prohibited_uses` (plus W04-specific boundaries).
- Desired-state with missing provenance/source authority routes to malformed/block path (no clean deploy).
- Overbroad relaxation requests (e.g. `all`, `hard_constraints`, authority/perspective scope relaxation) are rejected as malformed for clean deployment.

## Compatibility Note
C05 compatibility must not be overstated when C05 test paths are absent; report as non-executable compatibility.

## Validation Snapshot
Required W04 pack:
- `pytest -q tests/substrate/test_w04_applicability_gating_build/test_w04_applicability_gating_build.py` -> `38 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w04_subject_tick_integration.py` -> `8 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w04_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `28 passed`
- `pytest -q tests/tools/test_w04_applicability_gating_demo.py` -> `1 passed`

Compatibility snapshot:
- W03: `33/7/5/1 passed`
- W02: `27/7/4/1 passed`
- W01: `22/8/4/1 passed`
- M01: `19/7/4/1 passed`
- M02: `19/7/4/1 passed`
- N03: `22/7/4/1 passed`

Informational:
- `pytest -q tests/substrate/test_subject_tick_build` -> `1 failed, 267 passed` (known unrelated V03 signature preserved)
