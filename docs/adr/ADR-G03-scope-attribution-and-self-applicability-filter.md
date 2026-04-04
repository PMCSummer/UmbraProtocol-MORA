# ADR-G03: Scope Attribution / Self-Applicability Filter

## Status
Accepted as a bounded partial implementation of phase `G03` over implemented `G02` seam.

## Canonical Seams
- Canonical G03 seam:
  - `build_scope_attribution(runtime_graph_result_or_bundle) -> ApplicabilityResult`
- Canonical downstream gate:
  - `evaluate_applicability_downstream_gate(applicability_result_or_bundle) -> ApplicabilityGateDecision`
- Canonical runtime write seam:
  - `persist_applicability_result_via_f01(...) -> execute_transition(...)`
- Canonical downstream contract helper:
  - `derive_applicability_contract_view(applicability_result_or_bundle) -> ApplicabilityContractView`
- G03 does not mutate runtime-state directly outside F01.

## Why G03 Exists
- Separates “about-self mention” from “self-applicable update license”.
- Converts G02 graph distinctions into explicit attribution/applicability records and permission mappings.
- Prevents quoted/reported/hypothetical/denied content from silently leaking into self-update pathways.

## What Is Mechanistic / Load-Bearing
- G03 accepts only typed G02 artifacts (`RuntimeGraphResult`/`RuntimeGraphBundle`).
- Builds typed attribution records with:
  - source scope class
  - target scope class
  - applicability class
  - commitment level
  - self-applicability status
  - downstream permissions
- Emits permission mappings per proposition and explicit conservative blocks.
- Gate emits bounded restrictions and usability class:
  - `usable_bounded`
  - `degraded_bounded`
  - `blocked`
- Gate now treats confidence-floor admission and actionability separately:
  - `accepted=True` requires at least one record above confidence floor.
  - context-only outputs are explicitly marked as degraded (`bounded_context_only_output`).
- Gate requires downstream to read restrictions/permissions:
  - `permissions_must_be_read` is emitted when records are present.
- `accepted=True` means applicability surface exists, not semantic settlement or self-state fact.
- Contract helper exposes routing-relevant outcomes (`self_update_allowed/blocked`, external-only handling, clarification recommendation) without reading raw text or G02 directly.

## About-Self vs Self-Applicable Distinction
- `self mention != self applicability`.
- `external claim about self != self-state fact`.
- Quoted/reported/hypothetical/denied/questioned self-related material defaults to conservative blocking for self-state update pathways.
- Generic second-person and mixed target cases remain bounded by default and must not be promoted into self-state update licenses without stronger basis.

## What G03 Explicitly Does Not Claim
- No referent finalization.
- No world-truth or self-state truth confirmation.
- No appraisal, planning, policy, or communicative-action choice.
- No discourse provenance chaining (G04 territory).
- No clarification planning strategy (G07 territory).
- No T02 relation binding propagation logic.

## Load-Bearing Telemetry
- source lineage and upstream refs
- attribution record and permission-mapping counts
- source/target/applicability class summaries
- self-applicability status summaries
- low-coverage + ambiguity reasons
- attempted paths
- downstream gate decision (including `usability_class`)
- causal basis

## Bounded Partial Status
- Current G03 provides conservative applicability filtering with coarse target attribution heuristics.
- Mixed/unresolved cases remain explicit and degraded.
- Permission surface is bounded and non-committing by design.
- `accepted` must be interpreted together with:
  - `usability_class`
  - `restrictions`
  - per-record `downstream_permissions`
  and never as standalone self-state update authority.

## Remaining Debts
- Target attribution remains coarse in sparse-role scenarios.
- Richer multi-entity disambiguation is deferred.
- Cross-turn provenance and perspective chaining are deferred.
- Distinguishing literal addressee from generic/vocative/rhetorical second-person is still bounded and conservative.
- Overblocking risk remains possible in sparse-role and source-collision cases (intentional conservative bias).

## Open Integration Obligations
- G02 mandatory upstream is closed on G03 seam.
- Late-phase enforcement of G03 permissions in G04/G07/T02 is not closed here.
- Downstream phases must treat `block_self_state_update` and related restrictions as mandatory and must not upgrade to truth/commitment.
- Downstream must treat `permissions_must_be_read` and `bounded_context_only_output` as hard interpretation requirements, not telemetry-only hints.
