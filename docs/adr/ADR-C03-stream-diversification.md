# ADR-C03: Stream Diversification

## Status
Accepted for narrow BUILD increment of phase `C03` over implemented `C01`, `C02`, and `R04` constraints.

## Canonical Seams
- Canonical build seam:
  - `build_stream_diversification(stream_state_or_result, tension_scheduler_state_or_result, regulation_state_or_result, affordance_result, preference_state_or_result, viability_state_or_result, context=None) -> StreamDiversificationResult`
- Canonical downstream contract seam:
  - `derive_stream_diversification_contract_view(diversification_state_or_result) -> StreamDiversificationContractView`
  - `choose_diversification_execution_mode(diversification_state_or_result) -> str`
  - `select_alternative_path_candidates(diversification_state_or_result) -> tuple[str, ...]`
- Canonical runtime write seam:
  - `persist_stream_diversification_result_via_f01(...) -> execute_transition(...)`
- C03 performs no direct runtime-state mutation outside F01.

## Why This Narrow Shape
- C03 introduces a first-class typed diversification carrier without implementing planner arbitration or C04/C05 behavior.
- This increment focuses on structural anti-rumination mechanics:
  - detect stagnation signatures on typed C01/C02 topology
  - estimate progress-sensitive redundancy
  - gate repetition with explicit justification requirement
  - open bounded typed alternative-path classes
  - protect justified recurrence (survival pressure, active revisit, new causal input)
  - decay/reset diversification pressure after real shift/progress
- Shape explicitly avoids text anti-repeat heuristics, randomness-based novelty, and planner-grade branch orchestration.

## What C03 Now Claims
- Maintains explicit typed `StreamDiversificationState` with:
  - stagnation signatures
  - path-level redundancy scores
  - diversification pressure
  - repeat-justification targets
  - protected recurrence classes
  - allowed alternative classes
  - no-safe-diversification and survival-conflict markers
- Computes path assessments from C02 lifecycle topology (plus C01 continuity/R04 pressure context), not from lexical similarity.
- Distinguishes productive recurrence from ruminative loops through progress-sensitive pressure updates.
- Provides bounded downstream harness effect via execution mode and alternative candidate selection.
- Emits typed ledger/telemetry for assessment, stagnation, protected recurrence, alternative openings, and pressure shift/reset.

## What C03 Does Not Claim
- No planner final-choice authority.
- No tension closure authority (C02 remains owner).
- No endogenous ticking (C04).
- No selective temporal revalidation (C05).
- No semantic reinterpretation of content.
- No text generation policy.
- No global cross-phase arbitration engine.

## Seam Discipline Notes
- C01 continuity and C02 scheduling remain authoritative upstream sources.
- R04 survival pressure can protect recurrence, but cannot silently force false diversification claims.
- C03 emits diversification constraints/openings only; downstream selection/arbitration remains downstream responsibility.

## Explicit Anti-Shortcut Formulas
- diversification != text anti-repeat
- diversification != randomness/temperature tweak
- repetition != automatic suppression
- recurrence with progress/new causal input != stagnation
- survival-protected recurrence != free branching requirement
- no-safe-diversification != random branch opening

## Open Risks (Deferred)
- Threshold calibration for near-boundary pressure remains heuristic and may need hardening.
- Alternative-path class ontology is intentionally compact and bounded.
- Consumer obedience proof is narrow harness-level, not full downstream ecosystem proof.
- Cross-tension arbitration beyond local bounded rules is intentionally deferred.

## Hardening Update (Narrow C03 Pass)
This ADR is updated for a bounded hardening pass that stays inside C03 authority.

### What Changed Mechanistically
- Edge-band discipline is now explicit in C03 assessments:
  - progress evidence is tiered (`weak` / `moderate` / `strong`) with evidence-axis counting
  - edge-zone cases are marked and treated as degraded/ambiguous rather than hard flipping
- Repeat-justification is stricter against weak-progress noise:
  - single weak perturbations do not clear recurrence justification by default
  - repeat gating now depends on richer progress basis, not marginal status bumps
- Alternative openings are split into:
  - allowed alternatives
  - actionable alternatives
  so downstream harness behavior can depend on actionable readiness rather than metadata-only presence.
- Survival-protected mixed topology is tightened:
  - protected survival recurrence can force diversification conflict in mixed topologies
  - actionable alternatives are filtered/degraded when survival protection dominates.

### Audit Findings Closed By This Update
- threshold brittleness reduced with edge-band handling and ambiguity degradation
- weak-progress noise reduced as false justification source
- alternative openings made less decorative via actionable contract surfaces
- survival-protected recurrence now constrains unsafe candidate exposure more strongly
- productive recurrence no longer over-penalized in matched small-real-progress cases

### Authority Boundary Check
- C03 still does not perform planner arbitration, final branch selection, tension closure, C04 ticking, or C05 revalidation.
- Hardening only affects bounded diversification classification, gating, and candidate usability shaping.

### Still Open (Intentionally)
- Calibration remains heuristic (bounded, inspectable thresholds).
- Alternative ontology remains compact by design.
- Downstream obedience proof remains narrow harness-level (not global ecosystem proof).
- No cross-tension executive arbitration beyond local bounded conflict handling.
