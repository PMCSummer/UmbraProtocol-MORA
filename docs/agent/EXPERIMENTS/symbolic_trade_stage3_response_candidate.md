# Symbolic Trade Stage 3 Response-Candidate Probe

## Scope
Stage 3 adds a real-A first-contact / exchange-candidate emergence probe on top of Stage 2.5.

This stage does not modify core substrate phases and does not execute transfer, learning, or correction.

## What Stage 3 does
- runs a Stage 0/1 symbolic scenario with scripted counterpart B
- executes Stage 2.5 real-A reaction probe
- extracts bounded `AResponseCandidate` records from visible-only trace evidence
- classifies a selected response kind and response verdict
- runs Stage 3 falsifiers for hidden-truth/oracle/permission/shortcut/core-contamination seams

## What Stage 3 does not prove
- autonomous trade
- negotiation competence
- natural-language communication
- economic agency
- theory of mind or mature social cognition
- subjective need awareness

## Response candidate boundary
- candidates are non-executing: `execution_prohibited=true`
- candidate extraction uses visible packet refs and candidate-specific phase evidence refs only
- hidden truth and eval labels are disallowed in candidate evidence
- counterpart resource status remains claim, not fact
- desired/predicted signals do not become permission
- run-level phase coverage is not sufficient by itself: each offer/transfer-adjacent candidate must carry its own phase evidence chain and explicit forbidden-basis markers

## Scenario matrix
Stage 3 supports:
- `presence_only`
- `resource_claim_contact`
- `mirrored_resource_asymmetry`
- `false_counterpart_claim`
- `blocked_aperture`
- `noisy_signal`
- `transfer_seen_without_trade_token`
- `eval_label_leak_attack`
- `a_deficit_only`
- `b_surplus_claim_only`
- `claim_then_confirmed_transfer`
- `claim_then_failed_transfer`

## Falsifier matrix (Stage 3)
- `stage3_hidden_truth_used_for_response`
- `stage3_eval_label_used_for_response`
- `stage3_deficit_as_permission`
- `stage3_surplus_as_offer_shortcut`
- `stage3_b_claim_as_fact`
- `stage3_mirrored_complementarity_oracle`
- `stage3_usefulness_as_permission`
- `stage3_desired_as_observed`
- `stage3_predicted_as_permitted`
- `stage3_blocked_aperture_transfer_candidate`
- `stage3_noisy_claim_cleaned_into_fact`
- `stage3_false_claim_clean_offer`
- `stage3_one_shot_exchange_schema`
- `stage3_trade_specific_response_kind`
- `stage3_response_without_phase_causality`
- `stage3_candidate_executes_transfer`
- `stage3_w05_routing_as_execution_permission`
- `stage3_w06_correction_as_executed`
- `stage3_control_scenario_same_as_mirrored`
- `stage3_core_contamination`
- `stage3_phase_coverage_fake`
- `stage3_claim_boundary_missing`

## CLI examples
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage3-response`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage3-response --json`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage3-response --run-falsifiers`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage3-response --json --include-eval-only --run-falsifiers`

## Execution-level honesty
Stage 3 reuses Stage 2.5 execution-surface reporting and does not relabel projection as full subject execution.
Offer/transfer-adjacent candidates are rejected if invariants are violated (`execution_prohibited=false`, hidden/eval/trade-shortcut usage, empty claim boundary, missing candidate phase evidence, or executed-action markers).

## Known limitations
- Stage 3 is still an experiment-layer response-candidate probe.
- Candidate emergence is not equivalent to executed exchange behavior.
- Stage 3 does not introduce Stage 3+ semi-scripted counterpart logic.
- Stage 3 does not prove autonomous trade understanding, negotiation competence, economic agency, subjective need awareness, or learning/update execution.
