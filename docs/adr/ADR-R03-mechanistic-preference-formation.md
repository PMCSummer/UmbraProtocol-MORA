# ADR-R03: Mechanistic Preference Formation

## Status
Accepted for phase `R03` over closed `R01` and `R02` contour.

## Canonical Seams
- Canonical preference seam:
  - `update_regulatory_preferences(regulation_state, affordance_result, outcome_traces, preference_state=None, context=None) -> PreferenceUpdateResult`
- Canonical downstream gate:
  - `evaluate_preference_downstream_gate(preference_update_result_or_state) -> PreferenceGateDecision`
- Canonical runtime write seam remains `F01.execute_transition(...)`
- R03 performs no direct runtime-state mutation outside F01.

## What R03 Now Claims
- Maintains explicit typed preference ledger over existing `R02` option classes.
- Updates per-entry preference state with:
  - `target_need_or_set`
  - `preference_sign`
  - `preference_strength`
  - expected short-term and long-term regulatory deltas
  - `confidence`
  - `context_scope`
  - `time_horizon`
  - `conflict_state`
  - evidence support count
  - staleness/decay markers
  - update provenance and status
- Preserves blocked/frozen updates when attribution is not reliable.
- Preserves conflict as first-class state instead of silent scalar collapse.
- Emits typed downstream restrictions without hidden final action selection.

## What R03 Does Not Claim
- No action selection, planner decision, or policy execution.
- No affordance invention beyond typed `R02` option classes.
- No language/semantic/illocution/identity/value claims.
- No reward-system replacement claim.
- No forced one-best ranking under unresolved ambiguity/conflict.

## Load-Bearing Telemetry
- `PreferenceTelemetry` captures:
  - source lineage
  - input regulation snapshot reference
  - input affordance ids
  - processed episode ids
  - updated entry ids
  - blocked/frozen/conflict counters
  - short-term and long-term signal counts
  - attribution blocked reasons
  - context keys used
  - decay events
  - downstream gate outcome
  - causal basis
  - attempted update paths

## Explicit Bounds
- R03 is not action selection.
- R03 is not reward-system replacement.
- Separation of short-term relief vs long-term regulation is load-bearing.
- Persistence of R03 artifacts is valid only via F01 transition seam.
- Hostile runtime bypass outside typed gate/public surface is out of scope.
- Current update logic is intentionally minimal and heuristic/rule-based; ambiguity, conflict, blocked attribution, and freeze/no-claim are mandatory outputs, not optional heuristics.
