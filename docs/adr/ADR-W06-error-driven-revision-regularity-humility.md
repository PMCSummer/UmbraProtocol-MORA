# ADR-W06: Error-Driven Revision / Regularity Humility

## Status
Accepted for narrow BUILD slice.

## Decision
W06 is a revision-consequence routing seam.  
It consumes typed mismatch/contradiction intake and emits typed operational consequences, ledger, uncertainty residue, and downstream permissions. It does not execute corrections.

## Scope
- In scope:
  - consequence routing (`invalidate`, `downgrade`, `revalidate`, `split_identity`, `block_claim`, `quarantine`, `retain_unresolved`, `narrow_continuation`, `escalate_review`)
  - W06.1 ledger fields as load-bearing output
  - residual uncertainty retention as downstream-visible artifact
  - anti-paralysis route for repeated revalidation loops
  - identity routing and claim block propagation
  - correction-candidate seam with execution prohibition
- Out of scope:
  - learning/update execution
  - memory/policy/schema/prior mutation
  - planner/action selector behavior
  - W07+ update executor

## Core Invariants
- `W06CausalCorrectionCandidate.execution_prohibited` is always `True`.
- `W06DownstreamRevisionPermissionPacket.must_not_execute_correction` is always `True`.
- W06 does not mutate W01/W02/W03/W04/W05 records.
- Contradictions/mismatches are operationally consequential, not telemetry-only.
- Residual uncertainty remains visible after downgrade/narrow/revalidate routes.
- Local/global revision scope is explicit and bounded by criteria.
- Anti-paralysis prevents endless plain revalidate loops without progress.
- Selected revision scope must be inside `allowed_revision_scopes`; disallowed scope is fail-closed to bounded/revalidate/blocked routes with explicit reason markers.
- Ambiguous mismatch cannot present as a clean confident correction path; confidence is capped, competing candidates are preserved, and route remains contested/revalidate-oriented.
- Blocked-claim continuation requires preserved residual uncertainty markers; missing residue under blocked-claim routes fails closed.

## Runtime Contour Placement
`W01 -> W02 -> W03 -> W04 -> W05 -> W06 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w06_error_driven_revision_checkpoint`

## Downstream Contract
W06 emits:
- revision decision
- ledger entry
- claim block packet
- correction candidate (route-only, not executed)
- downstream revision permission packet

Downstream must obey:
- blocked claims
- revalidation/escalation requirements
- preserved uncertainty markers
- correction execution prohibition

## Non-Claims
- W06 is not a learner.
- W06 is not a correction executor.
- W06 does not authorize action.
- W06 does not declare global world truth.
