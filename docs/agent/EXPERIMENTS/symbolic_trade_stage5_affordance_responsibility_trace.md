# Symbolic Trade Stage 5 Affordance Responsibility Trace

## Stage 5 purpose
Stage 5 adds a harness-level responsibility trace over Stage 4 to make the affordance-use chain auditable:
- why an external transfer affordance is relevant;
- which surface produced that relevance;
- which preconditions/permissions are required;
- how candidate, selection, request, invocation, world execution, observed result, and verification differ.

## What Stage 5 proves
Stage 5 provides a typed, bounded responsibility ledger for symbolic exchange-start episodes:
- Stage 4 offer/readiness outputs are reused without core mutation;
- affordance selection is represented with precondition accounting;
- invocation request is separated from world actuator execution;
- world actuator execution is explicit-flag gated;
- observed result is separated from completion claim;
- failed/blocked paths preserve residue/revalidation boundaries.

## What Stage 5 does not prove
- no autonomous trade understanding;
- no negotiation competence;
- no natural-language competence;
- no economic agency;
- no theory-of-mind or social cognition claim;
- no subjective need-awareness claim;
- no subject motor-control claim;
- no learning/update execution claim.

## Responsibility boundaries
- W01: packet admission and claim/fact boundary only.
- W02/W03: bounded support only; no one-shot truth/schema inflation.
- W04: applicability/permission gate only; no action execution.
- W05: desired/predicted/observed/permitted separation only.
- W06: residue/revalidation and correction non-execution boundary.
- A02-compatible: missing/blocked/contested affordance gap markers.
- A04-compatible: external affordance binding metadata.
- P02-compatible: candidate/attempt/result/verification separation.
- V01/V02-compatible: communicative offer/request boundary.
- World actuator: harness/world-side execution surface only.

## No-exec vs exec modes
- No-exec (`--stage5-affordance-trace`):
  - world actuator not invoked;
  - invocation request may exist, but remains non-executing;
  - completion claim remains false.
- Exec (`--stage5-affordance-trace --stage5-execute-world-actuator`):
  - invocation only if selection/request/preconditions pass;
  - causal post-invocation packet refs appear only after invocation;
  - completion requires explicit episode verification boundary.

## Hardening addendum
- Completion claim now requires a typed completion basis chain:
  offer candidate, affordance selection, valid invocation request, explicit execution flag, actual world invocation, invocation/attempt linkage, causal refs, succeeded result, and verified episode.
- Passive scripted transfer packets and causal post-invocation packets are separated with explicit linkage fields and are validated by structural falsifiers.
- Blocked/contested affordance state structurally prevents valid invocation and prevents invocation from being accepted as a clean path.
- W06 correction boundary remains non-executing in the Stage 5 harness ledger; completion cannot be justified via correction execution.
- Phase evidence now carries source-run linkage to Stage 4 evidence snapshots instead of prefix-only checks.

## Separation checklist
- offer candidate != affordance selection;
- affordance selected != invocation request;
- invocation request != world actuator execution;
- transfer result != completion oracle;
- succeeded result != verified completion without typed verification fields.

## Representative scenario result
For `successful_scripted_exchange_cycle` in exec mode:
- selection is `selected_for_invocation_request`;
- request is world-sendable only under explicit flag;
- world actuator may invoke;
- succeeded transfer result is visible;
- completion claim is bounded and tied to typed verification fields.

## Known limitations
- still scripted-counterpart harness;
- world actuator is harness/world-side, not subject motor execution;
- no GUI path;
- no semi-scripted counterpart autonomy;
- no two-subject autonomous interaction.

## Honest claim wording
Stage 5 provides sufficient information for developer closure decision as a harness-only affordance responsibility trace; it does not establish autonomous trade competence.
