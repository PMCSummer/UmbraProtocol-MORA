# ADR-G05: Semantic Acquisition / Provisional Meaning Stabilization

## Status
Accepted as a bounded partial implementation of phase `G05` over implemented `G04` seam.
Hardened for accepted/degraded readability and downstream-contract obedience.

## Canonical Seams
- Canonical G05 seam:
  - `build_semantic_acquisition(perspective_chain_result_or_bundle) -> SemanticAcquisitionResult`
- Canonical downstream gate:
  - `evaluate_semantic_acquisition_downstream_gate(semantic_acquisition_result_or_bundle) -> SemanticAcquisitionGateDecision`
- Canonical runtime write seam:
  - `persist_semantic_acquisition_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_semantic_acquisition_contract_view(semantic_acquisition_result_or_bundle) -> SemanticAcquisitionContractView`
- G05 does not mutate runtime-state directly outside F01.

## Why G05 Exists
- Separates candidate-level semantics from provisional acquired meaning state.
- Preserves competing/blocked/context-only readings as first-class instead of forcing top-1 winner.
- Provides explicit reopen conditions for correction/repair/rebinding/clarification events.

## What Is Mechanistic / Load-Bearing
- G05 accepts only typed G04 artifacts (`PerspectiveChainResult`/`PerspectiveChainBundle`).
- Builds typed provisional acquisition objects:
  - `ProvisionalAcquisitionRecord`
  - `AcquisitionClusterLink`
  - `SupportConflictProfile`
  - `RevisionCondition`
- Runtime status discipline is load-bearing:
  - `stable_provisional`
  - `weak_provisional`
  - `competing_provisional`
  - `blocked_pending_clarification`
  - `context_only`
  - `discarded_as_incoherent`
- Gate restrictions are load-bearing:
  - `no_final_semantic_closure`
  - `accepted_provisional_not_final_meaning`
  - `acquisition_status_must_be_read`
  - `restrictions_must_be_read`
  - `competing_meanings_preserved`
  - `revision_hooks_must_be_read`
  - `memory_uptake_blocked`
  - `closure_blocked_pending_clarification`
  - `context_only_output`
  - `support_conflict_trace_required`
  - `downstream_authority_degraded`
  - `accepted_provisional_not_commitment`
  - `accepted_degraded_requires_restrictions_read`
- Cluster compatibility now requires typed semantic-unit compatibility; lexical/suffix similarity is not treated as merge evidence.

## Candidate vs Acquisition vs Closure
- `candidate meaning != acquired provisional meaning != final closure`.
- `accepted` means bounded provisional acquisition exists above confidence floor.
- `accepted` never upgrades to final semantic truth.

## What G05 Explicitly Does Not Claim
- No semantic graph rebuild.
- No self-applicability re-resolution.
- No provenance/perspective rewrite beyond consuming G04 result.
- No final closure or world/discourse truth.
- No appraisal/planning/policy/memory policy decisions.

## Bounded Partial Status
- Current implementation is a bounded stabilization layer with explicit support/conflict profiles.
- Competition and blocked states are preserved instead of collapsed.
- Reopen hooks are explicit but remain local and marker-driven.
- `accepted=True` may coexist with degraded bounded usability; this is explicitly constrained and must not be interpreted as settled meaning.

## Remaining Debts
- Support/conflict profiling remains heuristic and bounded by upstream quality.
- Rich paraphrase-level support beyond typed chain compatibility is limited.
- Deep correction replay across long discourse chains remains coarse.
- Some corrections may stay status-stable while still requiring revision-hook handling; downstream must not infer no-op from unchanged top-level status alone.

## Open Integration Obligations
- G04 mandatory upstream is closed on G05 seam.
- G06/G07 must read G05 statuses + restrictions + revision hooks as mandatory inputs.
- Downstream must not treat `accepted` as final meaning.
- `confidence` must not replace acquisition mechanism and status discipline.
- Lexical repetition must not be treated as stabilization evidence without support profile compatibility.
- Downstream must read `usability_class`, `acquisition_status`, and restrictions together; presence of acquisition objects alone is insufficient.
- `revision_hooks_must_be_read` is contractual: correction/repair-sensitive content remains reopenable even when top-level acquisition remains provisional.
