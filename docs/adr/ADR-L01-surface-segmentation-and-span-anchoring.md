# ADR-L01: Surface Segmentation and Span Anchoring

## Status
Accepted for phase `L01` over closed `F01`, `F02`, `R01`, and `R02` contour.

## Canonical Seams
- Canonical L01 seam: `build_utterance_surface(epistemic_unit, turn_metadata=None, context=None) -> UtteranceSurfaceResult`
- Canonical runtime write seam remains `F01.execute_transition(...)`
- L01 does not mutate runtime-state directly; optional persistence goes only through F01.

## What L01 Now Claims
- Converts typed F02 `EpistemicUnit` into typed inspectable surface substrate:
  - raw spans
  - token anchors
  - segment anchors
  - quoted spans
  - insertion spans (parenthetical/code/repair)
  - normalization records with provenance
  - ambiguity markers and alternative segmentations
- Preserves traceability from any downstream language claim back to raw span.
- Preserves unstable boundaries as explicit ambiguity state instead of hidden one-best collapse.

## What L01 Does Not Claim
- No final semantics, no truth commitments, no illocution, no commitments/policy/appraisal.
- No hidden winner parse and no semantic enrichment.
- No irreversible cleanup that silently drops punctuation carriers, quotes, parentheticals, or repairs.

## Load-Bearing Telemetry
- `UtteranceSurfaceTelemetry` logs:
  - source lineage from epistemic input
  - raw length and normalization operations
  - produced token/segment ids and spans
  - quote and insertion counts
  - ambiguity count and reasons
  - alternative segmentation presence
  - attempted surface paths
  - downstream gate outcome and restrictions

## Explicit Bounds
- L01 only produces surface-grounded substrate.
- Hostile raw-text bypass outside typed surface gate is out of scope.
- Segmentation heuristics are intentionally minimal/rule-based; ambiguity preservation is mandatory.
- Runtime persistence of L01 artifacts is valid only via F01 transition seam.
