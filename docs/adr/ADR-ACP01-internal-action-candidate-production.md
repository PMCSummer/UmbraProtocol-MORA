# ADR-ACP01: Internal Action Candidate Production

## Status
Accepted (P4 scope)

## Decision
Introduce `ACP01` as a subject-owned internal candidate production seam that emits bounded AP01-ready candidate input from subject-visible basis only.

`ACP01` is integrated in `subject_tick` before AP01 publication:

1. ACP01 consumes typed public observation/drive/surface/capability/effect basis.
2. ACP01 emits candidate-production decisions and at most one AP01 candidate set in narrow P4 scope.
3. AP01 remains the only publication authority.
4. Bridge/world execution remains outside ACP01.

## Boundaries
- ACP01 produces candidates only.
- ACP01 does not publish requests.
- ACP01 does not create `PublishedActionEnvelope`.
- ACP01 does not submit to world backend.
- ACP01 does not execute actions.
- ACP01 does not call W/A/P/S/AP01 policy modules directly from bridge runtime.

## Forbidden Basis
- `scenario_id` / expected outcome labels
- eval-only/private world truth
- hidden map/private object basis
- action-space alone
- drive alone
- visible object alone
- previous effect as success oracle

## P4 Narrow Action Scope
- Candidate actions: `pickup`, `inspect` (plus no-candidate/blocked/revalidation decisions)
- No planning/pathfinding.
- No recipe/automation/station production.

## Rationale
P3 proved transport plumbing with manual candidates. P4 replaces manual candidate dependency with a bounded internal producer while preserving AP01 publication and world execution boundaries.
