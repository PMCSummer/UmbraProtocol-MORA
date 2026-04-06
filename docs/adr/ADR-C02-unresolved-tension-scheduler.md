# ADR-C02: Unresolved Tension Scheduler

## Status
Accepted for narrow BUILD increment of phase `C02` over implemented `C01`, `R01`, `R02`, `R03`, and `R04`.

## Canonical Seams
- Canonical build seam:
  - `build_tension_scheduler(stream_state_or_result, regulation_state_or_result, affordance_result, preference_state_or_result, viability_state_or_result, context=None) -> TensionSchedulerResult`
- Canonical downstream contract seam:
  - `derive_tension_scheduler_contract_view(tension_scheduler_result_or_state) -> TensionSchedulerContractView`
  - `choose_tension_execution_mode(tension_scheduler_result_or_state) -> str`
  - `select_revisit_tensions(tension_scheduler_result_or_state) -> tuple[str, ...]`
- Canonical runtime write seam:
  - `persist_tension_scheduler_result_via_f01(...) -> execute_transition(...)`
- C02 performs no direct runtime-state mutation outside F01.

## Why This Narrow Shape
- C02 introduces a first-class typed lifecycle/scheduling carrier for unresolved tensions.
- This increment is intentionally minimal and does not implement C03/C04/C05 responsibilities.
- The design keeps unresolved tension fate explicit and typed:
  - revisit now
  - bounded defer
  - passive monitoring
  - temporary suppression
  - trigger-based wake/reactivation
  - stale/release
  - closure/reopen
- Shape avoids phase creep into planner backlogs, memory retrieval scheduling, or narrative reminders.

## What C02 Now Claims
- Maintains explicit typed `TensionSchedulerState` with:
  - tension entries (`tension_id`, `tension_kind`, `causal_anchor`, provenance)
  - lifecycle status (`active`, `deferred`, `dormant`, `reactivated`, `stale`, `closed`)
  - scheduling mode (`revisit_now`, `defer_until_condition`, `monitor_passively`, `hold_in_background`, `suppress_temporarily`, `release_as_stale`, `reopen_due_to_trigger`, `no_safe_defer_claim`, `unschedulable_tension`)
  - revisit priority + earliest revisit step
  - wake conditions + matched wake triggers
  - suppression budget bookkeeping
  - decay/staleness state and stale markers
  - closure/reopen criteria, confidence, and uncertainty markers
- Normalizes unresolved carry-over anchors from C01 into typed schedule entries without erasing source lineage.
- Enforces closure/reopen discipline:
  - closure requires explicit closure evidence
  - reopen requires explicit reopen condition or wake trigger
  - retrieval-only signal is not lawful reopen.
- Emits lifecycle ledger events for registered/deferred/suppressed/reactivated/closed/reopened/stale/released.
- Provides bounded downstream consumer harness so C02 is not log-only.

## What C02 Does Not Claim
- No planner/executor decisions.
- No resolution of tensions themselves.
- No C03 diversification policy.
- No C04 endogenous ticking/mode arbitration.
- No C05 selective revalidation engine.
- No self/nonself line.
- No memory retrieval integration as scheduler core.
- No closure-by-silence claim.

## Seam Discipline Notes
- C01 supplies continuity/carry-over anchors, but does not decide unresolved tension temporal fate.
- R01-R04 provide pressure context, but do not substitute C02 scheduling contract.
- C02 emits lifecycle/scheduling facts and revisit constraints only; it does not emit semantic reinterpretation or planner directives.

## Explicit Anti-Shortcut Formulas
- carry-over presence != unresolved tension scheduling claim
- retrieval != reopen
- suppression != drop
- closure requires evidence
- scheduler object presence != lawful revisit permission
- C02 != planner backlog

## Open Risks (Deferred)
- Priority calibration and wake-threshold tuning remain bounded and may require audit hardening.
- This increment proves a narrow downstream path only; no broad C03+ consumer obedience claim.
- Long-horizon suppression/decay optimality is intentionally out of scope for this build step.

## Hardening Update (C02 Narrow Hardening Pass)
- Wake/reactivation is now stricter and anchor-scoped:
  - explicit wake trigger is honored only when causal anchor is explicitly scoped.
  - broad generic trigger fan-out is blocked.
  - closed tension does not reopen from generic wake; lawful reopen cause is required.
- Signal-origin authority gate is now explicit:
  - weak/untrusted wake/closure/reopen signals are ignored and surfaced as typed restrictions.
  - C02 remains protected from planner-like external backfill via unlabeled reminder signals.
- Reactivation-cause discipline is now typed and inspectable:
  - `reactivation_cause` is explicit (`none` / `explicit_signal` / `defer_window_expiry` / `reopen_condition`).
  - downstream contract must read wake cause/scope and cannot treat any active-looking item as lawful reactivation.
- Threshold-edge behavior is tightened:
  - revisit/defer/suppress edges now include bounded degradation on near-threshold zones, reducing abrupt flips.
- Kind-sensitive consequences were strengthened in bounded form:
  - viability/recovery/interruption tensions are less suppressible than focus-drift tensions.
  - focus-drift cannot silently claim strong revisit in edge zones.
- Stale-vs-closed separation remains explicit:
  - stale/release lifecycle does not imply closure.
  - closure still requires evidence.

These changes remain inside C02 authority and do not introduce C03/C04/C05 semantics, planner logic, or broad downstream rewiring.
