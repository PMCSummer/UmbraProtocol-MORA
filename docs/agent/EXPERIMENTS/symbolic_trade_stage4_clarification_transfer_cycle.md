# Symbolic Trade Stage 4 Clarification-to-Transfer-Affordance Cycle

## Scope
Stage 4 is a harness-only extension over Stage 3.  
It adds a bounded clarification/readiness layer and an external transfer-affordance cycle with scripted counterpart B.

## What Stage 4 does
- keeps A-side execution rooted in existing Stage 2.5/Stage 3 reaction surfaces
- evaluates targeted clarification/readiness using visible packets + A computational self-state
- emits bounded offer readiness only when decision-critical fields are sufficiently visible
- binds an A04-compatible external affordance record (`aperture_transfer`) as harness metadata
- emits transfer invocation candidates and executes transfer only with explicit `--execute-transfer-affordance`
- records P02-compatible episode boundaries:
  - candidate
  - attempted
  - world executed by harness
  - observed result
  - verified/unverified
- tracks scripted counterpart response provenance explicitly:
  - passive scenario packet observation
  - causally-after-invocation response linkage
  - invocation/attempt id lineage when causal
- preserves W06-style residue/revalidation markers on failed/noisy/false paths

## What Stage 4 does not prove
- no autonomous trade understanding
- no negotiation competence
- no natural-language communication
- no economic agency
- no theory of mind or social cognition
- no subjective need awareness
- no learning/update execution

## Responsibility alignment
- A01-compatible: affordance identity metadata only (no core A01 mutation)
- A02-compatible: blocked/missing/contested transfer gaps are emitted explicitly
- A03: not used for external transfer semantics
- A04-compatible: external affordance binding metadata for aperture transfer
- G07-compatible: clarification is target-bound, budgeted, and non-looping
- V01/V02-compatible: offer stays communicative candidate; not execution
- P02-compatible: candidate/attempt/execution/verification are separated

## Clarification calibration
- clarification only when missing field is decision-critical
- no generic clarification without explicit target field
- budget exhaustion routes to revalidation/observe/abstain
- counterpart answer remains claim unless observed independently

## Transfer-affordance boundary
- offer candidate never executes transfer directly
- transfer invocation candidate is distinct from world attempt
- transfer world execution requires explicit CLI flag
- transfer result is observation/evidence, not a trade-success oracle
- transfer result success is not completion authority by itself
- exchange completion requires explicit typed episode verification boundary
- passive transfer packets in no-execution mode are not A-caused responses
- hidden B inventory is never used in visible offer/transfer basis

## Narrow hardening addendum
- clarification/readiness progression is structural and typed-signal driven; scenario id is not authority for readiness transitions
- no-execution mode (`--stage4-cycle` without `--execute-transfer-affordance`) keeps:
  - `transfer_invoked=False`
  - `transfer_result=NOT_ATTEMPTED`
  - transfer packets marked passive/non-causal
- execution mode marks causal transfer responses only when explicit invocation occurred and linkage is present
- W06 correction boundary is normalized into typed fields:
  - candidate created vs executed
  - execution prohibited guard
  - residue/revalidation retention
- stage claims remain bounded to harness instrumentation; no autonomous trade/economic-agency claim

## Stage 4 scenarios
- presence_only
- resource_claim_contact
- mirrored_resource_asymmetry
- false_counterpart_claim
- blocked_aperture
- noisy_signal
- transfer_seen_without_trade_token
- eval_label_leak_attack
- a_deficit_only
- b_surplus_claim_only
- b_surplus_only
- b_need_only
- clarification_resolves_missing_need
- clarification_loop_guard
- claim_then_confirmed_transfer
- claim_then_failed_transfer
- transfer_affordance_failure
- successful_scripted_exchange_cycle

## Falsifier contour
Stage 4 adds structural falsifiers for:
- clarification overreach/looping
- offer-without-basis
- transfer-without-affordance/flag
- claim->fact promotion
- hidden/eval/oracle leakage
- W06 residue erasure on failed paths
- A04 authority gaps
- A02 gap suppression
- P02 completion inflation
- forbidden core contamination

## CLI examples
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage4-cycle`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage4-cycle --show-clarification-state`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage4-cycle --execute-transfer-affordance`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage4-cycle --execute-transfer-affordance --json`
- `python tools/symbolic_trade_experiment.py --scenario mirrored_resource_asymmetry --stage4-cycle --execute-transfer-affordance --json --include-eval-only --run-falsifiers`
