# ADR-G01: Grounded Semantic Substrate

## Status
Accepted as a bounded partial implementation of phase `G01` over implemented `F01`, `F02`, `L01`, `L02`, `L03`, `L04`, `L05`, and `L06` contour.

## Canonical Seams
- Canonical G01 seam:
  - `build_grounded_semantic_substrate(dictum_result_or_bundle, utterance_surface=None, memory_anchor_ref=None, cooperation_anchor_ref=None, modus_hypotheses_result_or_bundle=None, discourse_update_result_or_bundle=None) -> GroundedSemanticResult`
  - production path requires typed `L05+L06` intake; no compatibility shim and no silent fallback to `L04`-only route
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
- Preserves source-ref class distinction on normative route:
  - phase-native refs (`source_modus_ref`, `source_discourse_update_ref`)
  - upstream lineage refs (`source_modus_lineage_ref`, `source_discourse_update_lineage_ref`)
  - ref classes are non-interchangeable and must be read downstream.
- Builds typed phrase scaffolds with:
  - clause/phrase boundaries
  - operator attachments
  - local scope relations
  - candidate head links
  - unresolved attachments
- Projects explicit operator/scope carriers without semantic closure.
- Runtime route for construction is canonical only: `L04 + L05 + L06`.
- Preserves dictum/modus split as distinct typed carriers.
- Preserves source/deixis anchoring as typed source anchors and unresolved placeholders.
- Preserves first-class uncertainty markers:
  - tokenization/attachment/clause-boundary ambiguity
  - operator/source scope uncertainty
  - referent unresolved
  - surface corruption markers
- Exposes typed downstream restrictions for bounded use, including explicit degraded authority marker (`downstream_authority_degraded`) when basis is weak.
- Exposes explicit anti-shortcut restrictions:
  - `discourse_update_not_inferred_from_surface_when_l06_available`
  - `source_modus_ref_class_must_be_read`
  - `source_discourse_update_ref_class_must_be_read`
  - `phase_native_source_refs_required_on_normative_route`
  - `source_ref_relabeling_without_notice`
- Rejects typed-binding mismatch on entrypoint instead of any downgrade/fallback.
- Enforces L06 acceptance boundary on normative route:
  - rejects `acceptance_required=False` proposals
  - rejects `acceptance_status=accepted` proposals
  - does not treat accepted-looking proposal objects as authorized update state.
- Treats L05 factorized evidence as load-bearing on normative route:
  - modality/quotation/addressivity projections require corresponding L05 evidence classes
  - missing evidence classes are surfaced as explicit uncertainty/evidence-gap markers.
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
  - source ref class markers (`*_ref_kind`) and lineage refs (`*_lineage_ref`)
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
- Legacy `L04 -> G01` compatibility route is retired from runtime API.
- Production entrypoint requires typed `L05+L06` and treats mismatch as contract error.
- Hostile bypass outside typed seams is out of scope.

## Remaining Debts
- Not all downstream consumers are proven to obey G01 restrictions beyond harness scope.
- G07 still has separate L06-consumption debt and is not fully rewired by this G01 pass.
