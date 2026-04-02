# ADR-L02: Morphosyntax Candidate Space

## Status
Accepted for phase `L02` over closed `F01`, `F02`, and `L01` contour.

## Canonical Seams
- Canonical L02 seam: `build_morphosyntax_candidate_space(utterance_surface, context=None) -> SyntaxHypothesisResult`
- Canonical runtime write seam remains `F01.execute_transition(...)`
- L02 does not mutate runtime-state directly; optional persistence goes only through F01.

## What L02 Now Claims
- Converts typed L01 `UtteranceSurface` into typed inspectable morphosyntax candidate space:
  - per-token morphology features
  - agreement cues
  - clause graph
  - dependency-like edges
  - unresolved attachments for ambiguity-sensitive structure
- Preserves negation carriers as structural objects in clause nodes.
- Emits candidate space with `no_selected_winner=True` and keeps ambiguity as first-class state.
- Provides typed downstream gate for structure-sensitive consumption.

## What L02 Does Not Claim
- No final proposition/dictum construction.
- No lexical grounding or referent resolution.
- No illocution, commitment, policy/action selection, or world-truth claims.
- No hidden one-best semantic collapse under ambiguity.

## Load-Bearing Telemetry
- `SyntaxTelemetry` records:
  - source lineage and input surface reference
  - input segment spans
  - hypothesis count
  - unresolved edge count
  - clause count
  - agreement cue count
  - morphology feature count
  - negation carrier count
  - ambiguity reasons
  - attempted morphosyntax paths
  - downstream gate outcome/restrictions
  - causal basis

## Explicit Bounds
- Parser logic is intentionally minimal and heuristic; L02 prioritizes inspectability and honest uncertainty over fake precision.
- Hostile bypass outside typed downstream gate/public surface is out of scope.
- Available morphosyntax candidates and any later selected semantic interpretation are separate stages by contract.
- Runtime persistence of L02 artifacts is valid only via F01 transition seam.
