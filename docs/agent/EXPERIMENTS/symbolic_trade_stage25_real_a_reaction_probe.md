# Symbolic Trade Stage 2.5 Real-A Reaction Probe

## Scope
Stage 2.5 adds a bounded A-side reaction probe over Stage 0/1 symbolic scenarios with scripted counterpart B.

This stage does not implement autonomous exchange behavior and does not modify core substrate phases.

## What Stage 2.5 does
- probes the highest currently executable A-side surface per scenario
- reports execution level explicitly:
  - `full_subject_tick_execution`
  - `partial_subject_tick_execution`
  - `owner_surface_execution`
  - `adapter_projection_only`
  - `non_executable`
- records:
  - execution surface report (attempted/successful/failed/fallback)
  - typed self-side computational internal resource state
  - world event reactions
  - counterpart claim reactions
  - W01->W06 reaction summary
  - falsifier outcomes

## Boundary discipline
- self-side resource state is computational internal state, not world evidence
- self-side deficit/surplus markers do not authorize action
- scripted B resource status remains counterpart claim, not fact
- hidden/eval-only truth stays outside subject-visible and phase-visible sections by default
- correction candidate execution remains prohibited

## Provenance discipline
Stage 2.5 reports whether the trace came from:
- real subject tick execution
- owner-surface callable probe
- adapter projection fallback

No adapter projection is labeled as full real subject execution.

## Coverage honesty
- W01->W06 coverage is marked as verified only when tick-derived phase artifacts are present.
- If per-phase tick artifacts are unavailable, coverage is downgraded and reported as non-verified contour-level execution.
- Stage 2.5 does not fabricate full phase coverage from constant tuples.

## What Stage 2.5 does not prove
- autonomous trade
- negotiation competence
- natural-language competence
- economic agency
- theory of mind or social cognition
- subjective need awareness

## Falsifiers added in Stage 2.5
- `a_self_state_hidden_as_world_fact`
- `a_deficit_as_permission`
- `a_surplus_as_trade_offer`
- `b_claim_as_fact`
- `mirrored_complementarity_as_oracle`
- `usefulness_as_permission`
- `desired_as_observed`
- `predicted_as_permitted`
- `blocked_aperture_clean_route`
- `noisy_claim_cleaned_into_fact`
- `false_claim_no_residue`
- `correction_candidate_executed`
- `hidden_truth_leakage_stage25`
- `adapter_projection_labeled_real`
- `execution_level_overclaim`
- `core_contamination`
- `trade_specific_signal`
- `one_shot_regularization`
- `phase_coverage_fake`
- `claim_boundary_missing`

## Known limitations
- Stage 2.5 is still an experiment-layer probe and not a competence proof.
- Callable surface level can vary by environment/runtime availability.
- Scripted B remains simple; no semi-scripted FSM or two-subject autonomy is introduced at this stage.
