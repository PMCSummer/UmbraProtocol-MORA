# ADR-G01: Grounded Semantic Substrate

## Status
Accepted as a bounded partial implementation of phase `G01` over implemented `F01`, `F02`, `L01`, `L02`, `L03`, `L04`, `L05`, and `L06` contour.

## Canonical Seams
- Canonical G01 seam:
  - `build_grounded_semantic_substrate(dictum_result_or_bundle, utterance_surface=None, memory_anchor_ref=None, cooperation_anchor_ref=None, modus_hypotheses_result_or_bundle=None, discourse_update_result_or_bundle=None) -> GroundedSemanticResult`
- Canonical downstream gate:
  - `evaluate_grounded_semantic_downstream_gate(grounded_result_or_bundle) -> GroundedSemanticGateDecision`
- Canonical runtime write seam:
  - `persist_grounded_semantic_result_via_f01(...) -> execute_transition(...)`
- Canonical role-contract helper (bounded downstream harness):
  - `derive_grounded_downstream_contract(grounded_result_or_bundle) -> GroundedDownstreamContractView`
- G01 does not mutate runtime-state directly outside F01.

## What G01 Now Claims
- Builds typed, span-grounded substrate units from typed upstream artifacts (`L04` required carrier basis).
- Supports normative typed intake from `L05 + L06` to project force/addressivity/update topology into G01 without inferring it from raw surface cues.
- Builds typed phrase scaffolds with:
  - clause/phrase boundaries
  - operator attachments
  - local scope relations
  - candidate head links
  - unresolved attachments
- Projects explicit operator/scope carriers without semantic closure.
- Distinguishes runtime routes:
  - normative route: `L04 + L05 + L06`
  - degraded compatibility fallback: legacy `L04 (+surface)` path
- Preserves dictum/modus split as distinct typed carriers.
- Preserves source/deixis anchoring as typed source anchors and unresolved placeholders.
- Preserves first-class uncertainty markers:
  - tokenization/attachment/clause-boundary ambiguity
  - operator/source scope uncertainty
  - referent unresolved
  - surface corruption markers
- Exposes typed downstream restrictions for bounded use, including explicit degraded authority marker (`downstream_authority_degraded`) when basis is weak.
- Exposes explicit anti-shortcut restrictions:
  - `legacy_surface_cue_path_not_normative`
  - `l04_only_input_not_equivalent_to_l05_l06_route`
  - `legacy_fallback_requires_degraded_contract`
  - `discourse_update_not_inferred_from_surface_when_l06_available`
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
- G01 does not perform final acceptance of L06 proposals and does not execute repair.
- G01 does not mutate common ground/self state.
- Runtime rewiring is partial: normative `L05+L06` intake exists, but legacy `L04` fallback remains operational as debt.
- Hostile bypass outside typed seams is out of scope.

## Remaining Debts
- Legacy fallback `L04 -> G01` is still operational for compatibility and remains a debt path.
- Not all downstream consumers are proven to prefer normative L05/L06-fed G01 route over compatibility fallback.
- G07 still has separate L06-consumption debt and is not fully rewired by this G01 pass.
