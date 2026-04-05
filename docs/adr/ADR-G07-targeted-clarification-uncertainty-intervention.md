# ADR-G07: Targeted Clarification / Uncertainty Intervention

## Status
Accepted as a bounded partial implementation of phase `G07` over implemented `G05` + `G06` + `L06` seams.

## Canonical Seams
- Canonical G07 seam:
  - `build_targeted_clarification(semantic_acquisition_result_or_bundle, concept_framing_result_or_bundle, discourse_update_result_or_bundle) -> TargetedClarificationResult`
- Canonical downstream gate:
  - `evaluate_targeted_clarification_downstream_gate(targeted_clarification_result_or_bundle) -> InterventionGateDecision`
- Canonical runtime write seam:
  - `persist_targeted_clarification_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_targeted_clarification_contract_view(targeted_clarification_result_or_bundle) -> TargetedClarificationContractView`
- G07 does not mutate runtime-state directly outside F01.

## Why G07 Exists
- Separates `uncertainty presence` from `intervention decision`.
- Converts bounded uncertainty targets into inspectable intervention states and lockouts.
- Preserves answer-binding readiness and reopen hooks without simulating final response realization.

## What Is Mechanistic / Load-Bearing
- G07 accepts only typed `G05` + typed `G06` + typed `L06` artifacts.
- Decision-core fields are load-bearing:
  - `uncertainty_target_id`
  - `uncertainty_class`
  - `intervention_status`
  - `ask_policy`
  - `abstain_policy`
  - `guarded_continue_policy`
  - `minimal_question_spec`
  - `forbidden_presuppositions`
  - `expected_evidence_gain`
  - `downstream_lockouts`
  - `reopen_conditions`
  - `confidence`
  - `provenance`
- `L06` topology is load-bearing:
  - localized repair classes/refs drive target-alignment legality
  - blocked/guarded/withheld continuation signals constrain status selection
  - acceptance-required proposal boundaries block acceptance-laundering
  - target drift/incompatible localization becomes explicit degraded restrictions
- G07 intervention statuses are load-bearing:
  - `ask_now`
  - `abstain_without_question`
  - `guarded_continue_with_limits`
  - `defer_until_needed`
  - `blocked_due_to_insufficient_questionability`
  - `clarification_not_worth_cost`
- Gate restrictions are load-bearing:
  - `intervention_requires_target_binding_read`
  - `downstream_lockouts_must_be_read`
  - `minimal_question_spec_target_binding_must_be_read`
  - `intervention_object_presence_not_permission`
  - `clarification_not_equal_realized_question`
  - `asked_question_not_equal_resolved_uncertainty`
  - `accepted_intervention_not_resolution`
  - `degraded_intervention_requires_restrictions_read`
  - `answer_binding_hooks_must_be_read`
  - `ask_now_without_answer_binding_forbidden`
  - `target_drift_risk_detected`
  - `intervention_record_contract_broken`

## Hardening Delta (This Pass)
- Rewiring now makes `L06` a causal upstream in G07 runtime path (not seam-only promise).
- Policy validates lawful intervention record shape before acceptance:
  - target-bound scope check (`uncertainty_target_id` + `uncertainty_class` in `allowed_semantic_scope`)
  - mandatory forbidden-presupposition presence
  - mandatory lockout presence (`closure_blocked_until_answer` at minimum)
  - status-policy alignment (`ask/abstain/guarded` flags must match selected status)
  - ask-now legality requires answer-binding readiness + hooks + worthwhile evidence gain
- `accepted` now depends on lawful record shape, not object presence only.
- `accepted` now also depends on lawful L06-alignment shape, not only G05/G06 target shape.
- Contract view now exposes additional mandatory-read dimensions:
  - question-spec target binding
  - forbidden-presupposition readability
  - answer-binding readiness/hook-read obligations
  - L06 repair-localization and continuation-topology read obligations
  - acceptance-boundary obligations (`l06_update_not_accepted`, `intervention_not_discourse_acceptance`)
  - explicit anti-inflation marker: object presence is not permission.

## Explicit Authority Bounds
- G07 does not extract semantics from raw text.
- G07 does not replace G05 provisional acquisition.
- G07 does not replace G06 concept framing/vulnerability audit.
- G07 does not perform final semantic closure/truth commitment.
- G07 does not choose planner/appraisal/memory policy actions.
- G07 does not realize final surface question text.
- G07 does not treat accepted intervention as resolved uncertainty.

## Core Formulas (Operational)
- `uncertainty != intervention`
- `ask_now != realized question`
- `asked question != resolved ambiguity`
- `intervention object != permission to continue strongly`
- `targeted clarification != generic follow-up`
- `clarification != accepted discourse update`
- `accepted intervention != accepted update`

## L06 Rewiring (Explicitly Bounded)
- G07 now reads typed L06 update/repair/continuation artifacts in production path.
- L06 read obligations are first-class in gate/contract:
  - `l06_repair_localization_must_be_read`
  - `l06_proposal_requires_acceptance_read`
  - `l06_block_or_guard_must_be_read`
  - `l06_g07_target_alignment_required`
- G07 still does not perform discourse acceptance/mutation; L06 proposals remain `acceptance_required` and `not_accepted`.

## Missing Downstream Handling (Explicitly Bounded)
- Response realization consumer is absent:
  - `response_realization_contract_absent`
- Answer-binding consumer is absent:
  - `answer_binding_consumer_absent`
- G07 keeps answer-binding-ready surface first-class:
  - `answer_binding_ready`
  - `answer_binding_hooks`
- These markers are contract, not closure.

## Bounded Partial Status
- G07 emits inspectable, target-bound intervention records and lockouts.
- Downstream-obedience surface is explicit via contract helper and gate restrictions.
- Missing upstream/downstream components remain explicit degraded markers.
- This pass is bounded partial and anti-inflation by design.

## Remaining Debts
- Realization debt:
  - no consumer that turns minimal question spec into realized response while preserving forbidden presuppositions.
- Answer consumer debt:
  - no live downstream executor for targeted answer-binding reopen/update.
- Consumer-proof debt:
  - full causal proof with real T01/G08/P01/O04 consumers remains pending.

## Open Integration Obligations
- `T01`, `G08`, `P01`, `O04` must consume G07 typed output + lockouts, not raw G05/G06 uncertainty objects.
- Downstream must read together:
  - `intervention_status`
  - `uncertainty_target_id`
  - `minimal_question_spec`
  - `forbidden_presuppositions`
  - `downstream_lockouts`
  - gate restrictions/usability class
- Presence of intervention records alone is insufficient for strong continuation/closure/planning/memory uptake.
