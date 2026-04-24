# V02 Build Working Notes

## Contour Placement
- RT01 hosted order (current): `... -> O04 -> R05 -> V01 -> V02 -> RT01 outcome resolution`
- Checkpoint: `rt01.v02_utterance_plan_checkpoint`

## Typed Surfaces
- Package: `src/substrate/v02_communicative_intent_utterance_plan_bridge/`
- Core typed objects:
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

## Require / Default Paths (RT01)
- Require:
  - `require_v02_plan_consumer`
  - `require_v02_ordering_consumer`
  - `require_v02_realization_contract_consumer`
- Default (basis-gated):
  - `default_v02_partial_plan_detour`
  - `default_v02_clarification_first_detour`
  - `default_v02_protective_boundary_first_detour`
- No-basis path remains `v02_optional` and does not add default friction.

## Mechanistically Real in Current Slice
- Act-to-plan transformation from V01 licensed/denied surfaces.
- Segment-role graph + typed ordering edges.
- Mandatory qualifier attachment + exact qualifier identity surface (`mandatory_qualifier_ids`).
- Protected omission / blocked expansion carried as typed plan constraints.
- Branch ambiguity represented via `primary_branch_id`, alternatives, and `unresolved_branching`.
- Protective/history-sensitive shaping:
  - `clarification_first_required`
  - `refusal_dominant`
  - `protective_boundary_first`
  - `partial_plan_only`

## Shortcut Closures in This Build
- Plan object is not a prose draft.
- Branch ambiguity is not silently collapsed into one fluent sequence.
- Mandatory qualifier handling is structural (segment/edge), not reason-text-only.
- V02 is downstream-consumed via typed fields in `subject_tick/policy.py`, not only checkpoint token.
- Qualifier identity tamper is detectable even when qualifier count/checkpoint envelope is unchanged.
- P01 seam mismatch narrowed: blocked handoff basis now modulates V02 structure (`clarification_first_required`).

## Open Limitations (Narrow, Honest)
- V02 remains RT01-hosted first slice; no map-wide consumer rollout.
- V03 realization guarantees are out of scope.
- Rich discourse-memory substrate is intentionally not claimed.
- Token mediation remains part of global RT01 architecture; hardening only added one narrow semantic contrast branch.

## Test Commands Used (This Pass)
- `pytest -q tests/substrate/test_v02_communicative_intent_utterance_plan_bridge_build/test_v02_communicative_intent_utterance_plan_bridge_build.py`
- `pytest -q tests/substrate/test_subject_tick_build/test_v02_subject_tick_integration.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_v02_runtime_topology_integration.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `pytest -q tests/tools/test_tick_observability_trace.py`
