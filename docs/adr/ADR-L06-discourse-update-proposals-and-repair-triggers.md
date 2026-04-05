# ADR-L06: Discourse Update Proposals and Repair Triggers

## Status
Accepted as a bounded partial implementation of phase `L06` over implemented `L05` seam.

## Canonical Seams
- Canonical L06 seam:
  - `build_discourse_update(modus_result_or_bundle) -> DiscourseUpdateResult`
- Canonical downstream gate:
  - `evaluate_discourse_update_downstream_gate(discourse_update_result_or_bundle) -> DiscourseUpdateGateDecision`
- Canonical runtime write seam:
  - `persist_discourse_update_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_discourse_update_contract_view(discourse_update_result_or_bundle) -> DiscourseUpdateContractView`
- L06 does not mutate runtime-state directly outside F01.

## Why L06 Exists
- Separates `interpretation` from `accepted discourse update`.
- Converts L05 interpretation hypotheses into:
  - acceptance-required `UpdateProposal`
  - localized `RepairTrigger`
  - explicit blocked/guarded continuation state
- Prevents silent update-like consequences from likely interpretation alone.

## Mini-Audit Entry Point
- `docs/seams/L06.seam.md` exists and requires:
  - typed-only upstream from `L05`
  - typed status/bounds downstream surface
  - no hidden side effects
- Hidden/partial L06-like behavior before this pass:
  - `G01` carried uncertainty/source markers and surface cue branching.
  - `G01` did not provide acceptance-required proposal layer, localized repair topology, or acceptance boundary gate.
- Therefore legacy shortcut risk remained:
  - historical `L04 -> G01` path could bypass explicit L06 acceptance/repair reading.

## What Is Mechanistic / Load-Bearing
- L06 accepts only typed `L05` artifacts (`ModusHypothesisResult|ModusHypothesisBundle`).
- Load-bearing objects:
  - `UpdateProposal`
  - `RepairTrigger`
  - `GuardedContinuationState`
  - `DiscourseUpdateBundle`
- Load-bearing fields:
  - `bundle_ref`
  - `source_modus_ref` (phase-native `L05` bundle ref)
  - `source_modus_ref_kind`
  - `source_modus_lineage_ref` (upstream lineage ref, non-authority class)
  - `acceptance_required`
  - `acceptance_status`
  - `proposal_basis`
  - `uncertainty_markers`
  - `localized_trouble_source`
  - `localized_ref_ids`
  - `blocked_updates`
  - `guarded_continue_allowed/forbidden`
  - continuation status (`blocked/guarded/proposal-allowed/abstain`)
- Load-bearing gate restrictions:
  - `proposal_requires_acceptance`
  - `acceptance_required_must_be_read`
  - `accepted_proposal_not_accepted_update`
  - `interpretation_not_equal_accepted_update`
  - `proposal_effects_not_yet_authorized`
  - `repair_trigger_must_be_localized`
  - `repair_localization_must_be_read`
  - `generic_clarification_forbidden`
  - `blocked_update_must_be_read`
  - `guarded_continue_not_acceptance`
  - `guarded_continue_requires_limits_read`
  - `proposal_not_truth`
  - `proposal_not_self_update`
  - `update_record_not_state_mutation`
  - `downstream_must_read_block_or_repair`
  - `l06_object_presence_not_acceptance`
  - `object_presence_not_permission`
  - `l06_source_modus_ref_must_be_read`
  - `l06_source_modus_ref_kind_must_be_read`
  - `l06_source_modus_lineage_ref_must_be_read`
  - `source_ref_relabeling_without_notice`

## Hardening Delta (Mini-Audit Pass)
- Acceptance inflation hardening:
  - proposals are emitted with `acceptance_status=not_accepted` and stricter mandatory restrictions shape.
  - gate enforces proposal restriction shape and rejects malformed near-acceptance proposals.
- Repair inflation hardening:
  - gate now rejects nominally localized but generic repair forms (`generic` trouble source / non-`bounded_*` clarification types).
- Guarded continuation hardening:
  - guarded continuation now requires explicit limit-read restrictions and stays non-authorizing.
  - entropy-only soft path now includes explicit withheld state marker (`abstain_update_withheld_must_be_read`) instead of implicit soft-success interpretation.
- Object-presence hardening:
  - explicit anti-inflation restrictions now include:
    - `l06_object_presence_not_acceptance`
    - `accepted_proposal_not_accepted_update`
    - `proposal_effects_not_yet_authorized`
    - `update_record_not_state_mutation`
- Legacy bypass readability hardening:
  - `legacy_bypass_risk_must_be_read` added as explicit gate restriction.
- Lineage/source hardening:
  - phase-native source ref class is separated from upstream lineage ref class.
  - relabeling/collapse (`source_modus_ref == source_modus_lineage_ref`) is treated as degraded contract state.
- Consumer-obedience hardening on `L05 -> L06`:
  - `L05` evidence/caution surfaces are now load-bearing in L06 build decisions.
  - missing `L05` force/addressivity evidence now yields localized repair triggers and blocked continuation.
  - missing quote-commitment caution under quoted force now yields localized force-owner repair.
  - high-entropy force without `force_alternatives_must_be_read` caution now yields localized repair instead of soft carry-through.

## Core Formulas
- `interpretation != accepted update`
- `proposal != truth`
- `proposal != self-state mutation`
- `repair trigger != generic clarification`
- `guarded continue != acceptance`
- `phase-native source ref != upstream lineage ref`

## Explicit Authority Bounds (Non-Claims)
- L06 does not perform final acceptance.
- L06 does not mutate common ground.
- L06 does not mutate self-state.
- L06 does not implement dialogue manager behavior.
- L06 does not implement planner/policy selection.
- L06 does not realize final response text.
- L06 does not simulate downstream phases (`G07`, `G08`, `T01`, `V01`, `V02`, `L07`).

## Degraded Markers and Debt Surface
- Missing downstream consumers are first-class:
  - `downstream_update_acceptor_absent`
  - `repair_consumer_absent`
  - `discourse_state_mutation_consumer_absent`
  - `downstream_authority_degraded`
- Legacy shortcut debt is first-class:
  - `legacy_g01_bypass_risk_present`
  - gate restrictions:
    - `legacy_bypass_risk_present`
    - `legacy_bypass_risk_must_be_read`
    - `legacy_bypass_forbidden`

## Normative Contour
- Normative contour for this segment is:
  - `L04 -> L05 -> L06 -> G01`
- `G01` now has a live typed intake route for `L05+L06`.
- Historical direct `L04 -> G01` path is no longer default and is available only via explicit degraded compatibility shim.

## Remaining Debts
- No live downstream acceptor for update acceptance.
- No live downstream repair executor.
- No live consumer for discourse state mutation contract (intentionally absent in this phase).
- Legacy `L04 -> G01` fallback still exists and can bypass L06 unless callers choose normative intake path.

## Integration Obligations
- Downstream phases (`G04`, `G05`, `G06`, `G07`, `T01`, `G08`, `V01`, `V02`, `L07`) must consume typed L06 outputs and restrictions.
- Future rewiring should ensure update-like effects require explicit acceptance consumer, not implicit interpretation carryover.
- `G01` integration is now partially rewired to support normative `L05+L06` intake; remaining obligation is to retire degraded fallback usage where safe.
