# P3 — SubjectWorldBridge (Embodied Playground)

## Scope
P3 adds an orchestration bridge over existing seams:

1. `GridWorldBackend.observe(...)`
2. `execute_subject_tick(...)`
3. AP01 request extraction from `SubjectTickResult.ap01_result`
4. `PublishedActionEnvelope` creation
5. `GridWorldBackend.submit_action(...)`
6. `ActionEffectFrame` feedback into next observation

P3 is a bridge loop only.

## What P3 does
- Uses `subject_tick` as the only subject execution surface.
- Accepts optional manual candidate provider for pipe testing.
- Does not derive actions from scenario id or eval labels.
- Submits world actions only when AP01 publishes exactly one valid request.
- Rejects multiple published requests when configured.
- Preserves public/eval separation by default.

## What P3 does not do
- No autonomous action selection.
- No planning layer.
- No direct W/A/P/S policy invocation.
- No direct AP01 policy invocation in runtime path.
- No recipe/automation expansion.
- No GUI.
- No substrate/core edits.

## Candidate provider boundary
`ManualCandidateProvider` is explicit non-autonomous input for P3 testing.
It must be treated as manual/test/operator input and is surfaced in trace fields.

## Bridge trace fields
`BridgeTickRecord` captures:
- observation/action-space ids and world tick bounds
- subject_tick usage and AP01 counters
- envelope creation and world submission flags
- effect id/status/correlation
- next observation id and previous effect refs
- explicit non-autonomous markers

## Effect feedback rule
When an action is submitted and world effect is returned, the next observation must carry the effect reference through `previous_effect_refs`.

## Claim boundary
P3 claim is limited to request-bound orchestration:
- request publication
- envelope submission
- world effect collection

P3 does not claim autonomy, competence, or closed embodied control.
