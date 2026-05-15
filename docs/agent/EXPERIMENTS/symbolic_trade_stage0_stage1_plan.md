# Symbolic Trade Stage 0/1 Plan

## Scope
This experiment layer builds Stage 0 and Stage 1 symbolic trade-through-wall harness coverage without modifying core subject phases.

- Stage 0: packet dry-run contracts.
- Stage 1: Subject A plus scripted counterpart B.

This is a harness-only build. It does not add trade cognition to W01-W06.

## Why scripted B first
A scripted counterpart keeps attribution clean for first contact and resource asymmetry checks. Two full subjects would add attribution noise and reduce falsifiability in the first pass.

## Claim discipline
This harness proves only deterministic symbolic scenario execution and seam-obedience instrumentation.
It does not prove human-like trade understanding, negotiation competence, economic agency, theory of mind, or natural-language communication.

## Harness truth vs subject-visible observation
Harness truth remains eval-only:
- A hidden inventory truth
- B hidden inventory truth
- aperture topology and transfer ground truth

Subject receives only bounded typed packets:
- presence_ping
- resource_status_signal
- object_seen_at_aperture
- object_transfer_attempt
- object_transfer_result
- absence_signal
- blocked_signal
- contradiction_signal

Counterpart reports are claims, not facts. Every resource self-report uses claim markers.

## Why offer/request/ack are deferred
Offer/request/ack semantics are intentionally deferred because they can act as disguised trade-specific shortcuts. Stage 0/1 uses weaker generic symbolic acts only.

## Phase responsibility map
- Harness/world: hidden truth, scripted B behavior, scheduler, eval labels, falsifier setup.
- W01: typed packet admission, authority preservation, claim/fact separation.
- W02: repeated trace regularity signals only.
- W03: bounded schema/prior candidates only with support.
- W04: applicability gating only, not action selection.
- W05: desired/predicted/observed/permitted separation and mismatch routing only.
- W06: revision consequences, claim block, residue retention, correction candidate with execution prohibited.

## Safe surfaces
Implemented in:
- `experiments/symbolic_trade/*`
- `tests/experiments/*`
- `tools/symbolic_trade_experiment.py`
- `tests/tools/test_symbolic_trade_experiment.py`

Core subject and runtime files are out-of-scope and unchanged.

## Do-not-touch list
Do not modify W01-W06 owner packages, `subject_tick`, runtime topology, or runtime tap trace for this harness.
Do not add trade-specific channels or action-planning shortcuts.
Do not leak hidden counterpart state as subject facts.

## Falsifier matrix (implemented categories)
- hidden_state_leakage
- trade_specific_shortcut_signal
- claim_promoted_to_fact
- desired_as_evidence
- mutual_benefit_oracle_leak
- one_shot_regularization
- blocked_aperture_ignored
- false_claim_truth_laundering
- noisy_signal_cleaned
- transfer_result_as_permission
- correction_candidate_executed
- phase_core_modification

## Stage roadmap
- Stage 0: packet contracts and visibility boundary checks.
- Stage 1: scripted B deterministic scenarios.
- Stage 2: transfer-response loops.
- Stage 3: semi-scripted B finite state machine.
- Stage 4: two symbolic subjects.
- Stage 5: stress + falsifier battery.

## Compatibility notes
- W01-W06 core is untouched by this harness build.
- S03/C05/M03 compatibility is not claimed from this harness alone.
- Missing integration/runtime paths remain non-executable compatibility.
