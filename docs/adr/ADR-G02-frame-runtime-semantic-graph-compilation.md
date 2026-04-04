# ADR-G02: Frame Runtime / Semantic Graph Compilation

## Status
Accepted as a bounded partial implementation of phase `G02` over implemented `G01` seam.

## Canonical Seams
- Canonical G02 seam:
  - `build_runtime_semantic_graph(grounded_result_or_bundle) -> RuntimeGraphResult`
- Canonical downstream gate:
  - `evaluate_runtime_graph_downstream_gate(runtime_graph_result_or_bundle) -> RuntimeGraphGateDecision`
- Canonical runtime write seam:
  - `persist_runtime_graph_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_runtime_graph_contract_view(runtime_graph_result_or_bundle) -> RuntimeGraphContractView`
- G02 does not mutate runtime-state directly outside F01.

## Why G02 Exists
- Creates a typed runtime semantic graph layer between G01 scaffold artifacts and later semantic phases.
- Prevents late phases from jumping directly from scaffold/text-like evidence to proposition/fact-like outcomes.
- Forces explicit graph-level preservation of unresolved/competing/incomplete structure.

## What Is Mechanistic / Load-Bearing
- G02 accepts only typed G01 artifacts (`GroundedSemanticResult`/`GroundedSemanticBundle`).
- Compiles frame-centered graph state:
  - semantic units (frame/operator/modus nodes),
  - role bindings,
  - graph edges,
  - proposition candidates,
  - graph alternatives.
- Operator/source cues change runtime graph topology and candidate classes (polarity/certainty), not only telemetry labels.
- Missing arguments remain unresolved via explicit role placeholders (no silent hallucinated slot fill).
- Ambiguity/uncertainty propagate into alternatives/restrictions.
- Gate emits bounded restrictions and explicit usability class:
  - `usable_bounded`
  - `degraded_bounded`
  - `blocked`
- `accepted=True` is graph usability only, never semantic settlement.

## What G02 Explicitly Does Not Claim
- No final semantic closure.
- No world-truth or commitment state.
- No self-applicability, appraisal, planning, or policy decisions.
- No final referent/source/scope resolution.
- No G03/T02 logic inside G02.

## Load-Bearing Telemetry
- source lineage and upstream refs
- semantic unit / role binding / edge / proposition / alternative counts
- polarity/certainty class summaries
- unresolved role slot count
- low-coverage markers + reasons
- ambiguity reasons
- attempted paths
- downstream gate decision (including `usability_class`)
- causal basis

## Bounded Partial Status
- Current G02 is a bounded runtime graph compiler, not a full semantic runtime.
- Graph can be accepted while degraded; restrictions remain mandatory for downstream interpretation.
- Contract helper requires restriction-aware reading; strong settlement is always disallowed.

## Remaining Debts
- Ambiguity preservation is bounded; competing graph fragments are represented minimally.
- Predicate-role depth is intentionally shallow for this increment.
- No advanced embedding/scope settlement beyond bounded graph markers.

## Open Integration Obligations
- G01 mandatory upstream is closed on G02 seam.
- Mandatory G02 consumption by later phases (G03/T02 and onward) is not closed in this ADR.
- Late-phase orchestration must enforce restriction-aware use of `RuntimeGraphGateDecision` and must not treat accepted graph as settled semantics.

