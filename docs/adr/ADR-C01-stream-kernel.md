# ADR-C01: Stream Kernel

## Status
Accepted for narrow BUILD increment of phase `C01` over implemented `F01`, `F02`, `R01`, `R02`, `R03`, and `R04`.

## Canonical Seams
- Canonical build seam:
  - `build_stream_kernel(regulation_state_or_result, affordance_result, preference_state_or_result, viability_state_or_result, context=None) -> StreamKernelResult`
- Canonical downstream contract seam:
  - `derive_stream_kernel_contract_view(stream_kernel_result_or_state) -> StreamKernelContractView`
  - `choose_stream_execution_mode(stream_kernel_result_or_state) -> str`
- Canonical runtime write seam:
  - `persist_stream_kernel_result_via_f01(...) -> execute_transition(...)`
- C01 performs no direct runtime-state mutation outside F01.

## Why This Narrow Shape
- C01 introduces a first-class typed continuity carrier without implementing C02/C03/C04/C05 responsibilities.
- The increment focuses on minimal causal continuity mechanics:
  - carry-over item retention
  - interruption/resume markers
  - branch/open-vs-new distinction
  - stale/release decay
  - ambiguous/low-confidence continuity outcomes
- Narrow shape avoids phase creep into planner, memory, dialogue, or identity systems.

## What C01 Now Claims
- Maintains explicit typed `StreamKernelState` with:
  - `stream_id`
  - `sequence_index`
  - `carryover_items`
  - `unresolved_anchors`
  - `pending_operations`
  - `interruption_status`
  - `branch_status`
  - `decay_state`
  - `stale_markers`
  - `continuity_confidence`
- Computes explicit continuity decisions:
  - `continued_existing_stream`
  - `started_new_stream`
  - `resumed_interrupted_stream`
  - `opened_branch`
  - `forced_release`
  - `ambiguous_link`
  - `low_confidence_continuation`
  - `forced_new_stream`
- Enforces typed carry-over classes (minimal C01 scope):
  - survival viability anchors
  - unresolved operational process
  - held focus anchors
  - pending output/recovery
  - interruption marker
- Applies explicit stale/release semantics instead of implicit transcript continuity.
- Emits ledger events for retain/new/resume/interrupt/branch/decay/stale/release decisions.
- Provides downstream-usable typed contract view and mode selection harness so C01 is not log-only.

## What C01 Does Not Claim
- No C02 unresolved-tension scheduling.
- No C03 diversification engine.
- No C04 endogenous ticking/mode arbitration.
- No C05 selective revalidation.
- No self/nonself (S01-S05) claims.
- No planner decisions, no response realization, no discourse acceptance, no memory retrieval engine.
- No transcript replay as continuity substrate.

## R04 Seam Risk Handling
- `R04` survival pressure is treated as a strong persistence anchor when pressure/escalation is active.
- C01 adds release/de-escalation compatible handling:
  - unresolved viability anchors decay
  - stale markers become explicit
  - forced release/new stream remains available when bridge is insufficient
- This increment does not solve all long-horizon release policy; it keeps bounded typed decay/release mechanics only.

## Load-Bearing Telemetry
- `StreamKernelTelemetry` records:
  - link decision and continuity confidence
  - carry-over counts, unresolved/pending counts
  - interruption/branch/decay states
  - stale marker count
  - source refs (`R01`/`R02`/`R03`/`R04`)
  - explicit ledger events with reasons and reason codes
  - attempted computation paths
  - downstream gate decision

## Explicit Bounds / Anti-Shortcut Formulas
- continuity object presence != lawful continuity claim
- continuity != transcript replay
- continuity != memory retrieval
- continuity != planner hidden flag
- survival anchor persistence != infinite lock-in
- ambiguous link != forced continuation

## Open Risks (Deferred to Audit/Hardening)
- Threshold calibration for branch/open-vs-new may need stronger falsifier pressure.
- Release timing under mixed unresolved anchors may require tighter policy in later hardening.
- Downstream consumer proof is currently a narrow harness, not full C02+ integration.

## Hardening Update (C01 Narrow Hardening Pass)
- Consumer-obedience hardening now makes blocked/degraded topology load-bearing for the C01 consumer harness:
  - `branch_conflict` (`accepted=False`, `blocked`) no longer permits strong continue mode.
  - low-confidence continuation no longer defaults to strong continue mode.
- Confidence is now operational in consumer mode selection:
  - strong confidence permits strong continuation.
  - lower confidence produces bounded degraded continuation/hold modes.
- Weak-seed anti-stitching was tightened:
  - held-focus-only evidence is capped and cannot claim strong continuation.
- Interruption persistence was tightened:
  - interrupted-but-not-resumed state remains interruption-bearing and degrades continuation mode.
- Stale/decay signals now materially influence consumer mode:
  - stale-heavy topology cannot silently remain strong continuation.
- Survival-anchor lock-in risk was reduced (bounded C01 scope):
  - survival-only + stale pressure is confidence-capped and cannot silently claim strong continuation.

These hardening moves stay within C01 authority and do not introduce C02/C03/C04/C05 semantics, planners, or memory systems.

## Validation Surface In This Increment
- Typed generation + boundary rejection
- continuation vs false similarity contrast
- interruption/resume explicitness
- stale/release behavior
- ambiguous-link honest fallback
- metamorphic perturbation
- ablation of anchor linking
- downstream obedience via contract harness
- stage contour through `F01 -> F02 -> R01 -> R02 -> R03 -> R04 -> C01`
