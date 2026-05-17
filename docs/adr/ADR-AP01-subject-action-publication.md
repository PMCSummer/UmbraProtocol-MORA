# ADR-AP01: Subject-Owned Action Publication / External Request Seam

## Status
Accepted (frontier-hosted narrow slice).

## Context
P0 inventory found no subject-owned, bounded external action request packet in core.  
Existing `world_adapter` action packet is scaffold-level and unsafe as direct external execution intent.

## Decision
Introduce `ap01_subject_action_publication` as a dedicated publication seam:
- input: typed action-publication candidates with explicit permission/evidence/affordance/episode boundaries;
- policy: publish / block / revalidate / abstain / malformed / unsafe_basis;
- output: `AP01SubjectActionRequestPacket` marked `external_world_only` and `not_executed_by_subject`;
- downstream contract: request is not world change, not success, not completion.

## Guardrails
- AP01 is not planner, not selector, not executor.
- AP01 cannot mutate world and cannot call `world.step`.
- AP01 rejects scenario/eval/hidden-truth laundering.
- AP01 rejects trade-specific magic action kinds.
- AP01 preserves residue/revalidation boundaries.

## Integration Scope
Narrow `subject_tick` integration:
- optional AP01 candidate input in context;
- AP01 result attached to `SubjectTickResult`;
- compact AP01 counters added to `SubjectTickState`;
- no wiring to world execution surfaces.

## Consequences
Positive:
- explicit owner seam for bounded external request publication;
- falsifier-oriented rejection of unsafe/malformed basis.

Limitations:
- AP01 does not solve planning or action selection;
- AP01 relies on externally provided candidate basis until future internal producer seam is added;
- world execution/effect loop remains downstream responsibility.
