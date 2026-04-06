# ADR-C04: Endogenous Mode Arbitration / Subject Ticking

## Status
Accepted for narrow BUILD increment of phase `C04` over implemented `C01`, `C02`, `C03`, and `R04`.

## Canonical Seams
- Canonical build seam:
  - `build_mode_arbitration(stream_state_or_result, tension_scheduler_state_or_result, diversification_state_or_result, regulation_state_or_result, affordance_result, preference_state_or_result, viability_state_or_result, context=None) -> ModeArbitrationResult`
- Canonical downstream contract seam:
  - `derive_mode_arbitration_contract_view(mode_arbitration_state_or_result) -> ModeArbitrationContractView`
  - `choose_subject_execution_mode(mode_arbitration_state_or_result) -> str`
  - `eligible_mode_candidates(mode_arbitration_state_or_result) -> tuple[str, ...]`
  - `can_run_mode_candidate(mode_arbitration_state_or_result, candidate_mode) -> bool`
- Canonical runtime write seam:
  - `persist_mode_arbitration_result_via_f01(...) -> execute_transition(...)`
- C04 performs no direct runtime-state mutation outside F01.

## Why This Narrow Shape
- C04 introduces a first-class typed mode-arbitration carrier and explicit endogenous tick contract.
- This increment is bounded to:
  - typed internal mode arbitration
  - hold/switch governance
  - dwell recheck
  - interruption/survival constraints
  - safe idle fallback
  - narrow downstream harness obedience
- Shape explicitly avoids planner arbitration, C05 temporal validity, and S* self/nonself machinery.

## What C04 Now Claims
- Maintains explicit typed `ModeArbitrationState` with:
  - `active_mode`
  - `candidate_modes`
  - `arbitration_basis`
  - `mode_priority_vector`
  - `hold_or_switch_decision`
  - `interruptibility`
  - `dwell_budget_remaining`
  - `forced_rearbitration`
  - `endogenous_tick_kind`
  - `endogenous_tick_allowed`
  - `arbitration_confidence`
- Computes mode selection from typed C01/C02/C03/R04 pressures plus bounded resource/runtime context.
- Distinguishes endogenous tick vs external-reactive handling vs quiescent safe idle.
- Enforces bounded hold/switch and survival-protected constraints.
- Emits typed ledger/telemetry for assessed/hold/switch/forced-hold/safe-idle/rearbitration events.
- Provides narrow downstream governance harness where selected mode changes execution mode and candidate eligibility.

## What C04 Does Not Claim
- No planner final arbitration.
- No task-manager or reasoner ownership.
- No C05 selective revalidation.
- No S01-S05 self/nonself machinery.
- No semantic reinterpretation of tensions/diversification/survival.
- No background timer loop as endogenous ticking substitute.

## Seam Discipline Notes
- C01 continuity, C02 unresolved scheduling, C03 diversification pressure, and R04 survival pressure remain authoritative upstream facts.
- C04 only arbitrates bounded internal mode governance.
- Downstream route choice/execution remains downstream responsibility.

## Explicit Anti-Shortcut Formulas
- endogenous ticking != background loop/timer noise
- mode arbitration != planner backfill
- external turn != endogenous tick substitute
- diversification pressure != forced switching
- survival pressure != infinite monopolization without recheck
- no internal basis != fake activity

## Open Risks (Deferred)
- Priority calibration remains heuristic and may need hardening.
- Consumer obedience proof is narrow harness-level, not global downstream ecosystem proof.
- Cross-phase arbitration with C05/S* is intentionally not implemented in this build.

## Hardening Update (Post-Audit, Narrow Scope)
- Hardening targets addressed in C04-only scope:
  - `safe_idle_overfires_under_weak_real_basis`
  - `near_equal_multi_tick_scores_produce_brittle_flips`
  - `external_turn_fully_substitutes_internal_tick` (partial residue)
  - `survival_monopoly_on_ticks` (partial residue)

### Runtime Changes Applied
- Weak-basis discrimination tightened:
  - when internal basis is lawful but weak and endogenous ticking is allowed, low-confidence mode selection now prefers bounded `passive_monitoring` / `hold_current_stream` fallback before `safe_idle`.
- Anti-thrashing stabilization added:
  - repeated dwell exhaustion without viable alternative no longer emits endless `forced_rearbitration`; outcome stabilizes to bounded `no_clear_mode_winner` hold with reset dwell window.
- External-reactive vs endogenous separation tightened:
  - in `EXTERNAL_REACTIVE` path (`endogenous_tick_allowed == false`), `hold_current_stream` continuation now requires extra lawful basis (continuity + actionable pressure + closure progress + resource floor), otherwise arbitration degrades to `passive_monitoring`.
- Survival monopoly de-escalation guard added:
  - if prior survival-forced hold exists but current survival pressure is no longer strong, C04 performs explicit recheck and can release monopoly to viable alternatives; hold persistence is no longer sticky by default.

### Falsifier Status After This Hardening
- Closed:
  - safe-idle overfire on weak lawful basis (bounded triad behavior)
  - repeated forced-rearbitration spin without governance shift
  - external-reactive path mimicking strong endogenous stream-continue without extra basis
- Partially closed:
  - survival monopoly residue under longer/more complex chains (reduced with local de-escalation recheck; not eliminated globally)

### Authority Boundary Preservation
- C04 authority remains unchanged:
  - bounded typed endogenous mode arbitration only.
- No planner integration, no C05 temporal validity logic, no cross-phase executive framework, no mode ontology expansion beyond bounded C04 set.

### Intentionally Left Open
- Heuristic threshold tuning is still local/compact, not globally calibrated.
- Downstream obedience remains proven at narrow harness level, not broad ecosystem level.
