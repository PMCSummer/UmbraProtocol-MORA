# ADR-Sprint8A: W-entry Admission Contract (Not W01)

## Status
Accepted for narrow `BUILD + AUDIT` increment.

## Decision
Introduce a typed `W-entry` admission contract layer that sits between the existing minimal world seam scaffold and future W-line phases.

This increment adds:
- typed world episode representation,
- machine-readable forbidden claim classes without lawful world basis,
- explicit W01 admission criteria surface.

This increment does **not** implement W01.

## Why
- Sprint 7 added a minimal external world seam (`observation/action/effect`) and RT01 world gating.
- Without an explicit admission contract, the system still lacks a single typed answer to:
  - what counts as lawful world basis,
  - which world-grounded claims are forbidden without that basis,
  - when opening W01 is admissible.

Sprint 8A closes that entry-gap without building world intelligence.

## Scope Implemented
- New production package: `src/substrate/world_entry_contract/*`
  - `WorldEntryEpisode`
  - `WorldClaimAdmission` + claim-class taxonomy
  - `W01AdmissionCriteria`
  - typed contract view/snapshot surfaces
- RT01 integration (bounded contour):
  - world-entry contract is derived from world_adapter output,
  - explicit `rt01.world_entry_checkpoint`,
  - RT01 world seam enforcement reads admission booleans from W-entry contract.
- Runtime topology visibility:
  - world-entry checkpoint and source-of-truth surface are visible in topology graph/dispatch contract.

## Explicit Forbidden Claims Without Lawful Basis
Machine-readable claim classes are now emitted for:
- `externally_effected_change_claim`
- `world_grounded_success_claim`
- `environment_state_change_claim`
- `action_success_in_world_claim`
- `stable_world_regularization_claim`
- `world_calibration_claim`

## W01 Admission Criteria (Sprint 8A Surface)
`W01AdmissionCriteria` is now explicit and inspectable:
- typed world episode exists,
- observation/action/effect linkage is present,
- basis is provenance-aware and inspectable,
- missing-world fallback is explicit,
- forbidden claim classes are machine-readable,
- RT01 consumption remains seam-level (no W01 relabeling).

`admission_ready` remains case-dependent and does not imply W01 closure.

## Authority Boundaries Preserved
- C04 remains arbitration authority.
- C05 remains legality/invalidation authority.
- R04 remains survival/gating authority.
- RT01 remains execution spine (consumer/enforcer only).
- F01 remains transition/provenance seam.

No authority is moved into RT01 as world semantics ownership.

## Anti-Creep Boundary
Sprint 8A is **only** admission scaffolding for W-line entry.

It is **not**:
- W01 implementation,
- W02–W06 implementation,
- world model,
- environment simulator,
- embodiment stack,
- repo-wide world rollout.

## What Is Now Claimable
- A typed W-entry admission contract exists in production for bounded RT01 contour.
- Forbidden world-grounded claim classes are machine-readable when basis is insufficient.
- W01 admission readiness is explicit and inspectable per episode.

## Narrow Hardening Update (Scope Marker Discipline)
- Added machine-readable bounded scope marker to public contract surfaces:
  - `scope = rt01_contour_only`
  - `admission_layer_only = true`
  - `w01_implemented = false`
  - `w_line_implemented = false`
  - `repo_wide_adoption = false`
- Marker is propagated through:
  - world_entry downstream contract/snapshot,
  - RT01 subject_tick contract/snapshot/telemetry surfaces,
  - runtime_topology dispatch contract/snapshot surfaces.
- Goal: prevent semantic drift where Sprint 8A could be misread as W01 or W-line closure.

## What Is Still Not Claimable
- W-line implemented.
- W01 closed.
- Rich world dynamics or embodied world cognition.
- Repo-wide world-entry adoption beyond bounded RT01 contour.
