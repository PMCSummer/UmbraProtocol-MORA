# ADR-W05: Predictive Prior Injection Into Interpretation And Policy

## Status
Accepted for narrow BUILD slice.

## Decision
Introduce `W05` as a bounded seam that consumes W04 applicability permissions plus W03 prior context and builds a typed four-channel predictive stack (`desired`, `predicted`, `observed`, `permitted`) for mismatch classification and route-only update pressure emission.

## Scope
W05 does:
- inject W04-approved prior influence into bounded interpretation/policy interfaces via typed gain control (`W05.1`);
- preserve strict channel separation with provenance/authority/precision markers;
- classify mismatch classes and emit `UpdateRoutingPacket` entries;
- enforce constitutional/protected-target boundaries;
- emit downstream routing packets with explicit execution prohibition.

W05 does not:
- execute updates;
- mutate weights, memory, policy, schemas, priors, or constitutional guardrails;
- implement W06 revision engine;
- choose actions/goals/plans;
- treat desired state as evidence;
- treat predicted utility as permission.

## Contour Placement
`W01 -> W02 -> W03 -> W04 -> W05 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w05_predictive_prior_injection_checkpoint`

## Authority Boundaries
- W05 consumes W04 applicability decisions/permission boundaries.
- W05 preserves W04 prohibited uses and guarded boundaries.
- W05 cannot broaden W04 scope.
- W05 approval is not action authorization.

## Execution Seam
- Every `UpdateRoutingPacket` has `execution_prohibited=True`.
- Every downstream W05 packet has `must_not_execute_update=True`.
- `execution_authorization_granted` is always `False`.

## W05.1 Prior Gain Control
- Effective gain depends on prior strength, evidence precision, and source reliability.
- High-precision contradictory observation suppresses gain.
- Low-precision noise does not erase prior without uncertainty/revalidation routes.
- Permitted-channel blocks cap/suppress gain regardless of predicted strength.

## Hardening Addendum (Post-Audit)
- Channel-collapse detection is widened beyond duplicate IDs:
  - duplicate channel IDs,
  - slot channel-marker mismatch,
  - desired/observed semantic collapse suspicion,
  - predicted/permitted collapse suspicion,
  - observed/permitted collapse suspicion.
- `MismatchClassificationRecord.compared_channels` now reflects actual compared route rather than fixed predicted/observed.
- `PermittedChannelEnforcementRecord` is covered by exact owner assertions for permission markers and reason semantics.
- Per-channel provenance/authority/confidence/precision separation is covered by direct owner assertions.
- W05 remains routing-only; no W06 behavior, no learning execution, no mutation of memory/policy/schema/world/constitutional state.

## Compatibility Note
C05 compatibility must not be overstated when C05 test paths are absent; report as non-executable compatibility.
M03 compatibility must not be overstated when M03 test paths are absent; report as non-executable compatibility.

## Out Of Scope
- W06 revision-loop execution.
- M03 lifecycle mutation.
- Planner/action selector behavior.
- World-truth or ontology expansion.
