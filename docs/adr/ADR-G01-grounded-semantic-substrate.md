# ADR-G01: Grounded Semantic Substrate

## Status
Accepted as a bounded partial implementation of phase `G01` over implemented `F01`, `F02`, `L01`, `L02`, `L03`, and `L04` contour.

## Canonical Seams
- Canonical G01 seam:
  - `build_grounded_semantic_substrate(dictum_result_or_bundle, utterance_surface=None, memory_anchor_ref=None, cooperation_anchor_ref=None) -> GroundedSemanticResult`
- Canonical downstream gate:
  - `evaluate_grounded_semantic_downstream_gate(grounded_result_or_bundle) -> GroundedSemanticGateDecision`
- Canonical runtime write seam:
  - `persist_grounded_semantic_result_via_f01(...) -> execute_transition(...)`
- Canonical role-contract helper (bounded downstream harness):
  - `derive_grounded_downstream_contract(grounded_result_or_bundle) -> GroundedDownstreamContractView`
- G01 does not mutate runtime-state directly outside F01.

## What G01 Now Claims
- Builds typed, span-grounded substrate units from typed upstream artifacts (primarily L04, with optional L01 cues).
- Builds typed phrase scaffolds with:
  - clause/phrase boundaries
  - operator attachments
  - local scope relations
  - candidate head links
  - unresolved attachments
- Projects explicit operator/scope carriers (negation, quotation, interrogation, modality, coordination/conditional/discourse cues) without semantic closure.
- Preserves dictum/modus split as distinct typed carriers.
- Preserves source/deixis anchoring as typed source anchors and unresolved placeholders.
- Preserves first-class uncertainty markers:
  - tokenization/attachment/clause-boundary ambiguity
  - operator/source scope uncertainty
  - referent unresolved
  - surface corruption markers
- Exposes typed downstream restrictions for bounded use, including explicit degraded authority marker (`downstream_authority_degraded`) when basis is weak.
- Provides a typed downstream role-contract surface so consumers can distinguish source/operator/uncertainty regimes without reparsing raw text.

## What G01 Does Not Claim
- No runtime semantics resolution.
- No semantic graph compilation.
- No proposition closure.
- No final referent/source/scope resolution.
- No parser/WSD/reference-resolution authority.
- No communicative-intent or planner logic.
- No silent phrase meaning inference from priors.
- No G02 behavior inside G01.

## Load-Bearing Telemetry
- `GroundedSemanticTelemetry` includes:
  - source lineage
  - source dictum/syntax/surface refs
  - substrate/scaffold/carrier/anchor/uncertainty counts
  - operator/uncertainty kind summaries
  - reversible span-map presence
  - low-coverage mode + reasons
  - ambiguity reasons
  - attempted paths
  - downstream gate outcome
  - causal basis

## Explicit Bounds
- G01 implementation is intentionally scaffold-level only.
- `accepted=True` at G01 gate means scaffold usability, not semantic understanding.
- Weak basis may still be accepted at scaffold level, but must carry restrictions and degraded authority semantics downstream.
- Unknown/unresolved/ambiguity/low-coverage remain first-class and must not be flattened by consumers.
- Contour-level mandatory dependency of G02 on G01 is not closed here; this ADR only establishes a bounded contract surface for that dependency.
- Hostile bypass outside typed seams is out of scope.

