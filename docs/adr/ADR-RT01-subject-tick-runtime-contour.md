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
