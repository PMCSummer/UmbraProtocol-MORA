# ADR-L03: Lexical Grounding And Reference Hypotheses

## Status
Accepted for phase `L03` over closed `F01`, `F02`, `L01`, and `L02` contour.

## Canonical Seams
- Canonical L03 seam:
  - `build_lexical_grounding_hypotheses(syntax_hypothesis_result_or_set, utterance_surface=None, discourse_context=None) -> LexicalGroundingResult`
- Canonical downstream gate:
  - `evaluate_lexical_grounding_downstream_gate(lexical_grounding_result_or_bundle) -> LexicalGroundingGateDecision`
- Canonical runtime write seam remains `F01.execute_transition(...)`
- L03 performs no direct runtime-state mutation outside F01.

## What L03 Now Claims
- Converts typed L02 syntax outputs into explicit lexical and referential candidate bundles.
- Preserves sense/entity/reference/deixis ambiguity as inspectable candidates, not hidden top-1 resolution.
- Emits pronoun/indexical/discourse-link reference hypotheses with unresolved states when evidence is weak.
- Emits first-class unknown and conflict states for lexical/reference grounding.
- Keeps token/span traceability via mention anchors linked to L01/L02 anchors.
- Exposes typed downstream gate with restrictions instead of accepted discourse facts.

## What L03 Does Not Claim
- No final lexical or referential resolution under high ambiguity.
- No accepted discourse fact update.
- No dictum/proposition construction.
- No illocution, commitment, repair policy, or world-truth claim.

## Load-Bearing Telemetry
- `LexicalGroundingTelemetry` includes:
  - source lineage
  - input syntax/surface refs
  - processed mention ids
  - generated candidate ids and typed counts (sense/entity/reference)
  - unknown and conflict counts
  - ambiguity reasons
  - discourse context keys used
  - attempted grounding paths
  - blocked grounding reasons
  - downstream gate outcome
  - causal basis

## Explicit Bounds
- L03 is typed candidate generation, not semantic commitment.
- L03 is intentionally minimal and heuristic/rule-based; honesty of uncertainty is prioritized over forced completeness.
- Unknown/conflict/unresolved outputs are mandatory and first-class.
- Persistence is valid only through F01 transition seam.
- Hostile bypass outside typed gate/public seam is out of scope.
