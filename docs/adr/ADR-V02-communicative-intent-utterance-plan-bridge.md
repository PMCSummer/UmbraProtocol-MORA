# ADR-V02 Communicative Intent / Utterance Plan Bridge

## Status
Accepted (frontier RT01-hosted first slice)

## Context
Before V02, RT01 had V01 licensing surfaces but no explicit typed utterance-plan bridge between:
- licensed communicative acts and
- downstream bounded outcome handling.

That gap made ordering/qualifier/omission structure vulnerable to fluent but non-auditable sequencing.

## Decision
Introduce `v02_communicative_intent_utterance_plan_bridge` as a distinct RT01 segment after `V01` and before bounded outcome resolution.

This slice provides:
- typed utterance plan state with segment graph and ordering edges;
- source-act references and role-typed segments (`answer`, `qualification`, `boundary`, `clarification_request`, `refusal`, `warning`, `commitment_limiter`, `next_step_handoff`);
- mandatory qualifier attachment as segment-level hard plan surface;
- blocked expansions and protected omissions as explicit typed plan constraints;
- bounded branch ambiguity representation (`primary` + `alternatives` + `unresolved_branching`);
- protective/history-sensitive structural shaping (clarification-first, refusal-dominant, protective-boundary-first, partial-plan-only);
- explicit checkpoint + require/default detour consequences.

## Scope Boundary (What This Slice Does Not Claim)
This ADR does **not** claim:
- V03 realization correctness guarantees;
- map-wide discourse planning rollout;
- full discourse-memory substrate;
- planner-wide episode orchestration.

V02 remains a narrow RT01-hosted typed planning shim.

## Mechanistically Real in Code
- Typed surfaces:
  - `V02UtterancePlanInput`
  - `V02PlanSegment`
  - `V02OrderingEdge`
  - `V02UtterancePlanState`
  - `V02PlanGateDecision`
  - `V02ScopeMarker`
  - `V02Telemetry`
  - `V02UtterancePlanResult`
  - `V02UtterancePlanContractView`
  - `V02UtterancePlanConsumerView`
- Checkpoint:
  - `rt01.v02_utterance_plan_checkpoint`
- Require path:
  - `require_v02_plan_consumer`
  - `require_v02_ordering_consumer`
  - `require_v02_realization_contract_consumer`
- Default path (basis-gated):
  - `default_v02_partial_plan_detour`
  - `default_v02_clarification_first_detour`
  - `default_v02_protective_boundary_first_detour`
- Downstream policy consumes typed V02 fields directly (not only checkpoint token), including:
  - plan shape counts,
  - exact mandatory qualifier identity set (`v02_mandatory_qualifier_ids`) against expected V01 qualifier identities,
  - qualifier attachment count,
  - ordering readiness,
  - protected omission / blocked expansion surfaces,
  - discourse-history-sensitive marker.

## Narrow Hardening Additions (Post-Audit)
- Added narrow qualifier-identity enforcement seam in RT01 downstream gate:
  - same checkpoint envelope can still diverge downstream when exact qualifier IDs mismatch, even when qualifier count is preserved.
- Added lawful minimal P01 modulation branch:
  - blocked/candidate-only/no-safe project handoff basis in P01 can force `clarification_first_required` and discourse-history-sensitive V02 plan shaping.
- Scope remains unchanged:
  - no V03 realization expansion,
  - no map-wide consumer rollout,
  - no planner substitution.

## Explicit Shortcut Prohibitions in This Slice
- No draft-masquerade as plan state (`list[str]`/outline is insufficient).
- No universal `answer-then-caveat` template substitution.
- No silent branch suppression under unresolved ambiguity.
- No qualifier detachment from constrained plan segments.
- No expansion of denied/blocked material via fluency-only fallback.

## Open Seams Intentionally Left Open
- V03 wording realization remains downstream.
- P02 intervention episode integration remains downstream.
- Rich long-horizon discourse-memory dependence remains out of scope.
