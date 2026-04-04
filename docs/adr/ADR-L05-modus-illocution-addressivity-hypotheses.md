# ADR-L05: Modus, Illocution, and Addressivity Hypotheses

## Status
Accepted as a bounded partial implementation of phase `L05` over implemented `L04` seam.

## Canonical Seams
- Canonical L05 seam:
  - `build_modus_hypotheses(dictum_result_or_bundle) -> ModusHypothesisResult`
- Canonical downstream gate:
  - `evaluate_modus_hypothesis_downstream_gate(modus_result_or_bundle) -> ModusHypothesisGateDecision`
- Canonical runtime write seam:
  - `persist_modus_hypothesis_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_modus_hypothesis_contract_view(modus_result_or_bundle) -> ModusHypothesisContractView`
- L05 does not mutate runtime-state directly outside F01.

## Why L05 Exists
- Separates `dictum content` from `communicative force`, `modality/evidentiality packaging`, and `addressivity`.
- Preserves ambiguity in communicative function as first-class output.
- Prevents direct `L04 -> G01` coupling from silently standing in for illocution/addressivity layer authority.

## Mini-Audit Entry Point (Before L05 Pass)
- Hidden L05-like load already existed in `G01`:
  - `g01._register_surface_cues(...)` created interrogation/modality/discourse/report/speaker/deixis carriers from surface cues.
  - `G01` emitted `modus_carriers`, `operator_carriers`, and `source_anchors` with force/addressivity implications.
- Hidden L06-like load was partial, not full:
  - `G01` emitted source/scope uncertainty markers.
  - `G01` did not perform discourse update proposal generation, repair planning, or common-ground mutation.
- Therefore legacy `L04 -> G01` remained operational shortcut bridge with mixed responsibilities.

## What Is Mechanistic / Load-Bearing
- L05 accepts only typed `L04` artifacts (`DictumCandidateResult|DictumCandidateBundle`).
- Load-bearing runtime objects:
  - `IllocutionHypothesis` (weighted alternatives)
  - `ModalityEvidentialityProfile`
  - `AddressivityHypothesis`
  - `QuotedSpeechState`
  - `ModusHypothesisRecord` (with `uncertainty_entropy`, `uncertainty_markers`, `downstream_cautions`)
- Load-bearing gate restrictions:
  - `dictum_not_equal_force`
  - `likely_illocution_not_settled_intent`
  - `quoted_force_not_current_commitment`
  - `addressivity_not_self_applicability`
  - `punctuation_form_not_lawful_force_resolution`
  - `illocution_alternatives_must_be_read`
  - `uncertainty_entropy_must_be_read`
  - `modality_profile_must_be_read`
  - `evidentiality_profile_must_be_read`
  - `addressivity_hypotheses_must_be_read`
- Explicit degraded markers for not-yet-wired L06 consumption on this path:
  - `l06_downstream_not_bound_here`
  - `l06_update_consumer_not_wired_here`
  - `l06_repair_consumer_not_wired_here`
  - `downstream_authority_degraded`
- Explicit legacy coupling markers (hardening):
  - `legacy_l04_g01_shortcut_operational_debt`
  - `legacy_shortcut_bypass_risk`
  - gate restriction: `legacy_shortcut_bypass_forbidden`

## Hardening Delta (Mini-Audit Pass)
- Lawful-read obligations were tightened:
  - `l05_object_presence_not_lawful_resolution`
  - `accepted_hypothesis_not_settled_intent`
  - `downstream_cautions_must_be_read`
- Policy now validates mandatory cautions per record:
  - `likely_illocution_not_settled_intent`
  - `addressivity_not_self_applicability`
  - `dictum_not_equal_force`
- Policy now marks unresolved-slot pressure as contract-significant:
  - `unresolved_slot_pressure_must_be_read`
- Legacy `L04 -> G01` shortcut risk is now first-class in L05 gate/contract, not implicit narrative text only.

## Explicit Authority Bounds (Non-Claims)
- L05 does not perform final intent selection.
- L05 does not perform discourse/common-ground update.
- L05 does not perform repair planning.
- L05 does not produce final communicative plan or realized response text.
- L05 does not perform psychologizing/diagnosis from force hypotheses.
- L05 does not transfer quoted/reported force into current-speaker commitment.

## Core Formulas (Operational)
- `dictum != force`
- `likely illocution != settled intent`
- `quoted force != current commitment`
- `addressivity != self-applicability`
- `punctuation/form != lawful force resolution`

## Bounded Partial Status
- L05 is a bounded hypothesis layer over L04 candidates.
- Alternatives/entropy remain explicit; no single-label force closure is authorized.
- Normative downstream (`L06`) exists in-repo, but this L05 path remains not-yet-bound and degrades authority by contract.

## Legacy Coupling Note
- Current operational contour still includes historical `L04 -> G01`.
- This is not treated as final architecture.
- Normative contour for this segment is rewritten as:
  - `L04 -> L05 -> L06 -> G01`
- Until runtime rewiring is completed, historical coupling remains explicit seam debt.

## Remaining Debts
- `L06` phase exists, but live L05->L06 consumer wiring is still absent on current runtime route.
- Legacy `L04 -> G01` operational path still carries force/addressivity-like cues in G01.
- No downstream consumer currently executes discourse update/repair using L05 outputs.
- No full consumer-proof that later phases obey L05 restrictions instead of legacy shortcuts.

## Open Integration Obligations
- Bind existing `L06` runtime route to consume L05 typed hypotheses and produce:
  - discourse update proposals
  - repair triggers
  - bounded repair grounding
- Re-adapt `G01` upstream authority to consume normative `L06` outputs instead of absorbing L05-like responsibilities from `L04`/surface cues.
- Downstream phases (`G03`, `G04`, `G05`, `G06`, `G07`, `T01`, `V01`, `V02`) must consume L05 typed outputs (or L06 integrations) rather than infer force from raw form.
