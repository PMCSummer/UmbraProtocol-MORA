# ADR-R04: Regulation Becomes a True Survival Force

## Status
Accepted for phase `R04` over implemented `F01`, `F02`, `R01`, `R02`, and `R03`.

## Canonical Seams
- Canonical viability seam:
  - `compute_viability_control_state(regulation_state_or_result, affordance_result, preference_result_or_state, context=None, boundary_spec=None, calibration_spec=None) -> ViabilityControlResult`
- Canonical downstream gate:
  - `evaluate_viability_downstream_gate(viability_result_or_state) -> ViabilityGateDecision`
- Canonical runtime write seam:
  - `persist_viability_control_result_via_f01(...) -> execute_transition(...)`
- R04 performs no direct runtime-state mutation outside F01.

## What R04 Now Claims
- Maintains an explicit typed viability-control state, distinct from R01 need tracking and R03 preference ledger.
- Computes bounded viability pressure using:
  - deviation/boundary severity
  - worsening sensitivity
  - persistence/unresolved duration
  - predicted time-to-boundary (when attributable)
  - recoverability estimate (from available means + preference support, without collapsing threat into preference)
- Uses typed/versioned calibration and compatibility guards (`ViabilityCalibrationSpec`) so threshold/weight changes are explicit and traceable.
- Stores recoverability as factorized components (`ViabilityRecoverabilityComponents`) instead of one opaque score.
- Emits explicit escalation stages and override scope.
- Emits typed control directives:
  - `priority_raise`
  - `task_permissiveness_reduction`
  - `interrupt_recommendation`
  - `focus_retention`
  - `protective_mode_request`
- Preserves uncertainty as first-class outputs:
  - `insufficient_observability`
  - `boundary_uncertain`
  - `mixed_deterioration`
  - `unresolved_conflict`
  - `degraded_mode_only`
  - `no_strong_override_claim`
- Supports recovery-sensitive de-escalation and persistence tracking.

## What R04 Does Not Claim
- No planner or policy action selection.
- No affordance invention.
- No preference formation replacement.
- No world-truth, semantic, social, moral, or narrative-survival claims.
- No illocution/commitment/discourse acceptance fields.
- No universal reward-system replacement.

## Load-Bearing Telemetry
- `ViabilityTelemetry` records:
  - source lineage
  - input regulation snapshot reference
  - input affordance reference
  - input preference reference
  - affected need ids
  - computed pressure level
  - computed escalation stage
  - predicted time-to-boundary
  - recoverability estimate
  - recoverability components
  - calibration id/schema version
  - override scope
  - persistence status
  - de-escalation condition markers
  - blocked reasons and uncertainty reasons
  - downstream gate outcome
  - attempted computation paths
  - recent failed recovery count
  - boundary compatibility markers

## Explicit Bounds
- R04 does not select concrete action; it only emits typed viability-control directives and restrictions.
- `preference != survival threat` is enforced by contract: preference affects recoverability hints, not boundary threat definition.
- recoverability evidence quality gates strong override; weak basis degrades claims instead of faking precision.
- When observability/boundary compatibility is weak, R04 must cap claims via uncertainty markers and `no_strong_override_claim`.
- Hostile bypass outside typed seam/gate remains out of scope.
- Current mechanism is intentionally minimal/rule-based; claim is operational viability control, not full survival cognition.
- Calibration is explicit and versioned, but still manually specified rule-based configuration (not adaptive calibration).
- Recoverability remains bounded proxy evidence over currently available R02/R03 artifacts; it is not a full causal model of restoration dynamics.

## Validation Surface
- Includes an isolated typed downstream obedience harness in tests to verify non-decorative causal effect:
  - with viability directives -> reduced permissiveness / interrupt/protective signals
  - ablation of directives/state -> degraded downstream effect
