# Symbolic Trade Stage 2 Subject Trace-Through

## Stage 2 scope
Stage 2 extends the Stage 0/1 harness with an experiment-layer subject-adapter trace-through that projects subject-visible symbolic packets across W01->W06-compatible reaction surfaces.

This stage does not modify core substrate phases and does not execute learning, policy changes, or trade actions.

## What Stage 2 does
For each scenario packet, Stage 2 emits per-step phase records:

- W01-like admission projection
- W02 bounded regularity projection
- W03 bounded prior/schema candidate projection
- W04 applicability gating projection
- W05 predictive channel/mismatch routing projection
- W06 revision consequence projection

The Stage 2 trace explicitly marks adapter source type:
- real_surface_compatible_projection
- adapter_projection
- compatibility fallback markers in adapter_limitations when needed

## What Stage 2 does not prove
- autonomous trade
- negotiation ability
- natural-language communication
- economic agency
- theory of mind
- two-agent social cognition

## Packet flow and boundaries
`subject_visible_packet -> phase_adapters (W01..W06 compatible) -> SubjectTraceRun`

Boundaries preserved:
- counterpart resource status remains claim, not fact
- hidden/eval truth remains outside subject-visible packet and phase-visible sections
- no trade-specific shortcut channel is introduced
- correction-candidate route remains execution prohibited

## Falsifier coverage in Stage 2
Added Stage 2 trace falsifiers:
- subject_trace_hidden_truth_leakage
- phase_adapter_core_contamination
- one_shot_claim_promoted_by_w02_or_w03
- w04_usefulness_as_permission
- w05_desired_or_predicted_as_permission
- w06_correction_candidate_executed
- blocked_aperture_still_allows_clean_applicability
- noisy_signal_cleaned_into_fact
- false_counterpart_claim_becomes_truth
- eval_label_in_phase_trace
- trade_specific_phase_shortcut
- phase_trace_without_w01_to_w06_coverage

Hardening notes:
- forbidden-core contamination detector now checks full forbidden prefixes (including `src/substrate/subject_tick/`) across tracked and untracked paths
- dedicated adversarial mutation checks added for:
  - W05 desired/predicted pressure treated as permission
  - blocked aperture incorrectly routed as clean W04 applicability
  - false counterpart claim promoted to truth in W01 trace
- Stage 2 visibility boundary check now scans full serialized `PhaseTraceRecord` payloads for eval-only/hidden-truth leakage markers

## Known limitations
- Phase outputs are experiment-layer compatibility projections, not full owner execution for every phase.
- This stage is trace-through instrumentation, not behavior competence proof.

## Next stage proposal
Stage 3 can expand controlled transfer-response loops with richer adapter strictness and contested-path replay, while still avoiding core contamination.
