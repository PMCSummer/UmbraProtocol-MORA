# ADR-RT01: Narrow Subject Tick Runtime Contour

## Status
Accepted for narrow BUILD increment that materializes runtime execution obedience across `R -> C01 -> C02 -> C03 -> C04 -> C05`.

## Why This Layer Exists
- Existing C01-C05 phase contracts were strongly typed but mostly exercised through isolated phase tests.
- This increment introduces a minimal runtime execution spine that makes C04 mode arbitration and C05 temporal-validity legality load-bearing in one production contour.

## Canonical Seams
- Runtime build seam:
  - `execute_subject_tick(tick_input, context=None) -> SubjectTickResult`
- Runtime downstream contract seam:
  - `derive_subject_tick_contract_view(...) -> SubjectTickContractView`
  - `choose_runtime_execution_outcome(...) -> str`
- Runtime persistence seam:
  - `persist_subject_tick_result_via_f01(...) -> execute_transition(...)`

## Fixed Runtime Order
- `R update -> C01 -> C02 -> C03 -> C04 -> C05`
- The layer enforces bounded gate/contract obedience at each phase boundary and returns bounded runtime outcomes only:
  - `continue`
  - `repair`
  - `revalidate`
  - `halt`

## Authority Boundary
- This layer is execution-only.
- It does not:
  - reinterpret phase semantics,
  - pick mode semantics instead of C04,
  - declare validity instead of C05,
  - act as planner or global orchestrator.

## What Is Claimed
- Minimal production-grade runtime contour exists as a typed stateful layer.
- C04 selected mode causally affects runtime execution stance.
- C05 legality/revalidation causally affects runtime execution outcome.
- Contract-obedience is load-bearing in runtime, not only in isolated helpers.

## What Is Not Claimed
- No planner-grade orchestration.
- No full ecosystem-wide downstream integration.
- No global truth-maintenance/memory/policy runtime.
- No authority expansion beyond existing phase seams.

## Narrow Hardening Update (Post-Audit)
- Scope: RT01-only execution hardening with no phase-authority transfer.
- Findings addressed:
  - gate enforcement looked too late-bound in some paths;
  - `continue` vs `repair` could share near-identical runtime stance;
  - C04 vs RT01 vs C05 role boundary required explicit runtime evidence.

### Runtime changes
- Added explicit RT01 critical checkpoints in runtime state/telemetry:
  - `rt01.c04_mode_binding`
  - `rt01.c05_legality_checkpoint`
  - `rt01.critical_gate_checkpoint`
  - `rt01.outcome_resolution_checkpoint`
- Added typed `execution_stance`:
  - `continue_path | repair_path | revalidate_path | halt_path`
- Repair-path distinction tightened:
  - `repair` outcome now exposes explicit RT01 repair stance surface (`repair_runtime_path`) instead of relying on outcome label/flags only.
- Role-boundary explicitness tightened:
  - C04 contribution is stored as consumed claim (`c04_execution_mode_claim`).
  - C05 contribution is stored as consumed legality action claim (`c05_execution_action_claim`).
  - RT01 enforces consequences but does not reinterpret C04/C05 semantics.

### Authority boundary after hardening
- C04 remains authority for mode arbitration and mode legitimacy.
- C05 remains authority for temporal legality/revalidation restrictions.
- RT01 remains authority only for runtime contour execution and contract enforcement.
- No planner/orchestrator rewrite, no new mode semantics, no C05 reasoning moved into RT01.

## Narrow Hardening Update (Route Authenticity + Source-of-Truth)
- Scope: one contour-bounded hardening pass for shared runtime domains, without architecture-wide propagation/security redesign.

### Route authenticity hardening
- `runtime_domain_update` now requires typed `runtime_route_auth` context for `rt01_subject_tick_contour` claims.
- Engine enforces:
  - origin phase must be `RT01`,
  - transition kind must match,
  - claimed domain paths/checkpoints must match route-auth context,
  - one-time nonce must be issued by lawful RT01 persistence path.
- Result: spoofed external/manual transitions that only reuse route token/claims are rejected.

### Source-of-truth precedence hardening
- Runtime domain contract view explicitly declares:
  - `source_of_truth_surface = runtime_state.domains`,
  - `packet_snapshot_precedence_blocked = true`.
- In conflicting packet/snapshot vs domains cases, runtime outcome follows shared domains.

### Bound preserved
- Hardening is RT01 contour-local only.
- No map-wide authenticated propagation claim is introduced.

## Build Update (Sprint 5: Downstream Obedience Contract)
- Added first production slice of typed downstream obedience protocol for RT01 contour consumption.
- New runtime decision surface distinguishes:
  - `allow_continue`
  - `allow_continue_with_restriction`
  - `must_repair`
  - `must_revalidate`
  - `must_halt`
  - `insufficient_authority_basis`
  - `invalidated_upstream_surface`
  - `blocked_by_survival_override`
- RT01 now applies this protocol as a binding checkpoint (`rt01.downstream_obedience_checkpoint`) before resolving runtime outcome.
- Shared `runtime_state.domains` remains source-of-truth where materialized; conflicting packet-local snapshot surfaces do not override obedience enforcement.

### Non-claims preserved
- No map-wide downstream obedience rollout.
- No planner/global orchestration migration.
- No authority transfer from R04/C04/C05 to RT01.

## Narrow Hardening Update (Sprint 5 Checkpoint Coherence)
- Scope: RT01/downstream-obedience contour only; no authority or planner semantics expansion.
- `rt01.downstream_obedience_checkpoint.applied_action` now records post-enforcement runtime action.
- When obedience fallback changes runtime action, checkpoint reason now exposes explicit action transition.
- Enforcement chain remains auditable as:
  - obedience decision (`required_action`)
  - obedience checkpoint (`applied_action`)
  - final runtime stance/outcome.
