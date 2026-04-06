# ADR-C05: Temporal Validity / Selective Revalidation

## Status
Accepted for narrow BUILD increment of phase `C05` over implemented `C01`, `C02`, `C03`, `C04`, and `R04`.

## Canonical Seams
- Canonical build seam:
  - `build_temporal_validity(stream_state_or_result, tension_scheduler_state_or_result, diversification_state_or_result, mode_arbitration_state_or_result, regulation_state_or_result, affordance_result, preference_state_or_result, viability_state_or_result, context=None) -> TemporalValidityResult`
- Canonical downstream contract seam:
  - `derive_temporal_validity_contract_view(temporal_validity_state_or_result) -> TemporalValidityContractView`
  - `choose_temporal_reuse_execution_mode(temporal_validity_state_or_result) -> str`
  - `select_reusable_items(...) -> tuple[str, ...]`
  - `select_revalidation_targets(...) -> tuple[str, ...]`
  - `can_continue_mode_hold(...) / can_revisit_with_basis(...) / can_open_branch_access(...)`
- Canonical runtime write seam:
  - `persist_temporal_validity_result_via_f01(...) -> execute_transition(...)`
- C05 performs no direct runtime-state mutation outside F01.

## Why This Narrow Shape
- C05 introduces a first-class typed temporal-validity carrier for continuity-relevant carryover objects.
- Increment is bounded to:
  - dependency-aware status assignment
  - selective scope-bounded revalidation targeting
  - bounded invalidation propagation
  - bounded provisional carry discipline
  - narrow downstream obedience harness
- Shape explicitly avoids planner integration, full truth-maintenance, memory-policy integration, and global recompute orchestration.

## What C05 Now Claims
- Maintains explicit typed `TemporalValidityState` and typed item taxonomy:
  - `stream_anchor`
  - `carried_assumption`
  - `mode_hold_permission`
  - `revisit_basis`
  - `branch_access_gate`
  - `provisional_binding_or_permission`
- Emits per-item typed validity statuses:
  - `still_valid`
  - `conditionally_carried`
  - `needs_partial_revalidation`
  - `needs_full_revalidation`
  - `invalidated`
  - `expired`
  - `dependency_contaminated`
  - `no_safe_reuse_claim`
- Performs bounded dependency-aware invalidation and propagation to dependent permissions.
- Distinguishes selective revalidation from broad/full-scope fallback.
- Supports bounded provisional carry with grace horizon instead of infinite gray state.
- Provides narrow downstream contract where reuse permissions for mode-hold/revisit/branch access change as a function of C05 validity outcomes.

## What C05 Does Not Claim
- No full temporal truth-maintenance across the whole architecture.
- No planner-owned revalidation scheduler.
- No full memory integration or archival validity economics.
- No global recompute engine.
- No authority to choose active mode (C04), close tensions (C02), or reinterpret semantic truth.

## Seam Discipline Notes
- Upstream phases remain authoritative for semantic/continuity/scheduling/arbitration facts.
- C05 only governs bounded temporal reuse legality and revalidation requirements.
- Downstream execution/planning remains downstream responsibility.

## Explicit Anti-Shortcut Formulas
- temporal validity != TTL-only age cutoff
- temporal validity != blanket reset on any shift
- temporal validity != blanket reuse until explicit contradiction
- selective revalidation != full recompute
- provisional carry != silent strong reuse

## Open Risks (Deferred)
- Dependency graph completeness is bounded; `dependency_graph_incomplete` remains an explicit degraded marker.
- Cross-phase propagation beyond narrow harness directions (mode/revisit/branch) is intentionally not implemented.
- Heuristic prioritization bands may require future audit/hardening.

## Narrow Hardening Update (2026-04-06)

### What was hardened
- Added bounded trigger-family normalization for dependency-hit evaluation.
  - Purpose: remove obvious alias-shape false negatives such as `trigger:mode_shift` vs `trigger:modeShift` and equivalent context-marker family aliases.
  - Scope remains typed map/family folding only; no semantic parser or open-ended fuzzy interpretation.
- Refined incomplete-graph handling into bounded tiers instead of default coarse contamination.
  - `dependency_graph_incomplete + local hit` still supports strong degraded outcomes (`dependency_contaminated`) for affected scope.
  - `dependency_graph_incomplete + no local hit` now uses bounded local degraded handling (`conditionally_carried` / `needs_partial_revalidation`) with explicit weak-basis path (below), rather than near-blanket contamination.
- Narrowed root-anchor propagation severity.
  - Root anchor invalidation still load-bearing.
  - Strict dependents remain strongly degraded.
  - Non-critical dependents are downgraded to bounded review/revalidation instead of automatic equal-severity contamination.
- Materialized explicit weak-basis path to `no_safe_reuse_claim`.
  - Goal: provide an honest abstain-like reuse denial branch in weak/incomplete local basis cases, without turning it into universal fallback.

### Audit findings addressed by this hardening
- `trigger_name_coupling_brittleness`: narrowed via canonical trigger-family normalization.
- `selective scope degrades to coarse under dependency_graph_incomplete`: narrowed by local unknown tier handling.
- `root-anchor propagation fan-out`: narrowed by strict-vs-review propagation severity partition.
- `no_safe_reuse_claim weak practical reach`: improved with explicit weak-basis reachability path.

### Boundary discipline preserved
- C05 still governs temporal reuse legality only.
- No planner, no memory integration, no global truth-maintenance, no ecosystem-wide propagation rewrite.
- No authority takeover from C01/C02/C03/C04/R*.

### Still intentionally open
- Full dependency graph completeness handling is not solved.
- Trigger-family mapping remains bounded and manual, not domain-complete.
- Broad downstream obedience beyond narrow mode/revisit/branch harness remains unclaimed.
