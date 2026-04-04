# ADR-G04: Discourse Provenance / Perspective Chaining

## Status
Accepted as a bounded partial implementation of phase `G04` over implemented `G03` seam.

## Canonical Seams
- Canonical G04 seam:
  - `build_discourse_provenance_chain(applicability_result_or_bundle) -> PerspectiveChainResult`
- Canonical downstream gate:
  - `evaluate_perspective_chain_downstream_gate(perspective_chain_result_or_bundle) -> PerspectiveChainGateDecision`
- Canonical runtime write seam:
  - `persist_perspective_chain_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_perspective_chain_contract_view(perspective_chain_result_or_bundle) -> PerspectiveChainContractView`
- G04 does not mutate runtime-state directly outside F01.

## Why G04 Exists
- Prevents flattening perspective ownership into one source label.
- Separates:
  - utterer
  - source class
  - perspective owner
  - commitment owner
- Carries perspective-sensitive lineage so downstream cannot treat reported/quoted/hypothetical content as direct current commitment.

## What Is Mechanistic / Load-Bearing
- G04 accepts only typed G03 artifacts (`ApplicabilityResult`/`ApplicabilityBundle`).
- Builds typed perspective-chain records, commitment lineages, wrapped propositions, and cross-turn links.
- Emits explicit chain-level constraints used by downstream:
  - `closure_requires_chain_consistency_check`
  - `response_should_not_echo_as_direct_user_belief`
  - `clarification_recommended_on_owner_ambiguity`
  - `narrative_binding_blocked_without_commitment_owner`
  - `response_should_not_flatten_owner`
- Gate emits bounded restrictions and usability classes:
  - `usable_bounded`
  - `degraded_bounded`
  - `blocked`
- Gate-level restrictions include:
  - `chain_consistency_required`
  - `owner_ambiguity_present`
  - `broken_provenance_chain`
  - `cross_turn_repair_pending`
  - `response_should_not_flatten_owner`
  - `perspective_chain_must_be_read`
  - `usability_must_be_read`
  - `accepted_chain_not_owner_truth`
  - `shallow_owner_chain_risk`
  - `downstream_authority_degraded`
  - `no_truth_upgrade`

## Flat Label Is Not a Chain
- `source_class` alone is insufficient.
- G04 chain uses:
  - `provenance_path`
  - `perspective_stack`
  - owner separation (`perspective_owner` vs `commitment_owner`)
  - cross-turn attachment state

## About Cross-Turn Repairs
- Cross-turn attribution repairs are represented as lineage rewrite signals (`REATTACHED` / `REPAIR_PENDING`), not flat relabeling.
- `cross_turn_repair_pending` is a hard degraded marker for downstream handling.
- Denial/correction turns may force `REPAIR_PENDING` instead of silent lineage append.

## What G04 Explicitly Does Not Claim
- No world-truth or discourse-truth closure.
- No trust/social judgment.
- No irony/deception final resolution.
- No narrative commitment layer.
- No appraisal/planning/policy decisions.
- No response generation.

## Bounded Partial Status
- G04 currently provides bounded perspective-chaining with conservative owner handling.
- Depth is bounded; deeper nesting beyond current reliable basis degrades explicitly.
- Cross-turn repair support is shallow and marker-driven.
- `accepted` means chain artifacts are present above confidence floor; it does not mean clean ownership truth.

## Remaining Debts
- Deep (>2-3) nested perspective semantics remain coarse.
- Attributed belief / remembered / ironic meta-perspective are partial classifications.
- Cross-turn reattachment quality depends on upstream repair hints availability.

## Open Integration Obligations
- G03 mandatory upstream is closed on G04 seam.
- Downstream enforcement is still required in G05/G07/G08:
  - must obey chain constraints and degraded markers.
- No downstream phase may treat G04 `accepted` as commitment truth settlement.
- `response_should_not_echo_as_direct_user_belief` and owner-ambiguity constraints must remain mandatory.
- Downstream must read both `restrictions` and `usability_class`; chain object presence alone is insufficient for closure.
