# ADR-F02: Grounding / Epistemic Substrate

## Status
Accepted for phase `F02` on top of closed `F01`.

## Canonical Seams
- Canonical grounding seam: `ground_epistemic_input(input_material, metadata, context) -> EpistemicResult`
- Canonical runtime write seam remains F01 only: `execute_transition(request, state) -> TransitionResult`
- F02 performs no direct runtime-state mutation.

## What F02 Now Claims
- Input material is transformed into typed epistemic units with explicit:
  - source class
  - modality class
  - epistemic status
  - confidence
  - support / contestation
  - conflict / unknown / abstention markers
- Content is separated from epistemic status.
- Downstream allowance is constrained by epistemic tags, not raw content alone.
- Reports are not promoted to observations.
- Recall/inference/assumption remain distinct from observation.

## What F02 Does Not Claim
- No semantic parsing or world-truth commitments.
- No intent, planning, dialogue policy, regulation, or memory reasoning.
- No belief system or ontology-heavy truth engine.

## Load-Bearing Telemetry
- `GroundingTelemetry` carries:
  - incoming material identity/content
  - classified source and modality
  - resulting status and confidence
  - support / contestation / unknown / conflict / abstention reasons
  - attempted grounding paths
  - downstream claim strength and restrictions
- `ProvenanceRecord.actual_delta` and `attempted_paths` from F01 remain the write-path reconstruction surface.

## Explicit Bounds
- F02 guarantees are scoped to trusted runtime and public operational APIs.
- If persistence of epistemic results is required, it must be routed via F01 transition engine.
- If downstream ignores `allowance/restrictions`, claim discipline can be violated; policy-surface consumption is part of the operational contract.
