# ADR-L04: Dictum Candidate Construction

## Status
Accepted for phase `L04` over implemented `F01`, `F02`, `L01`, `L02`, and `L03` contour.

## Canonical Seams
- Canonical L04 seam:
  - `build_dictum_candidates(lexical_grounding_result_or_bundle, syntax_hypothesis_result_or_set, utterance_surface=None, discourse_context=None) -> DictumCandidateResult`
- Canonical downstream gate:
  - `evaluate_dictum_downstream_gate(dictum_result_or_bundle) -> DictumGateDecision`
- Canonical runtime write seam:
  - `persist_dictum_result_via_f01(...) -> execute_transition(...)`
- L04 does not mutate runtime-state directly outside F01.

## What L04 Now Claims
- Builds typed proposition-like dictum skeletons from typed L03 lexical/reference candidates and L02 syntax hypotheses.
- Preserves candidate multiplicity across syntax hypotheses; no hidden one-best dictum collapse.
- Emits inspectable predicate frames, argument slots, negation markers, temporal markers, magnitude markers, and scope markers.
- Keeps underspecified slots, unknowns, ambiguities, and conflicts as first-class outputs.
- Preserves quotation sensitivity and upstream instability as explicit bounded markers.
- Exposes typed downstream restrictions instead of settled semantics.

## What L04 Does Not Claim
- No illocution hypothesis.
- No commitment/discourse acceptance update.
- No permission/policy/self-applicability decision.
- No pragmatic implicature as literal dictum by default.
- No world-truth claim.
- No final proposition resolution.

## Load-Bearing Telemetry
- `DictumTelemetry` includes:
  - source lineage
  - input syntax refs
  - input lexical grounding ref
  - input surface ref
  - processed candidate ids
  - dictum candidate count
  - underspecified slot count
  - negation marker count
  - temporal marker count
  - magnitude marker count
  - scope ambiguity count
  - conflict count
  - blocked candidate count
  - ambiguity reasons
  - attempted construction paths
  - downstream gate outcome
  - causal basis

## Explicit Bounds
- L04 is intentionally minimal and heuristic; it produces inspectable candidate structure with honest uncertainty, not full semantic completion.
- Dictum and modus remain separated by contract.
- Implicature/pragmatic enrichment is out of scope for L04.
- Unresolved lexical/reference/scope states are mandatory outputs when evidence is weak.
- Hostile bypass outside typed seam/gate is out of scope.
