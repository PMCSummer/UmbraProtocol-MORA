# ADR-A03: Internal Tool Affordances (Narrow Frontier Slice)

## Status
Accepted for narrow frontier build slice.

## Scope
- Frontier-hosted only (`RT01` narrow slice).
- Placement: `A01 -> A02 -> A03 -> A_LINE`.
- No map-wide planner/tool runtime migration claim.

## Decision
A03 defines a typed ontology seam for internal tool affordances.

A03 does:
- normalize typed internal operation candidates into canonical internal tool affordances;
- keep tool-vs-mode/helper/plumbing/stored-content boundaries explicit;
- expose invocation-contract completeness and availability/degradation/blocked status;
- link A02 gap packets to internal-tool insufficiency only when typed basis supports it;
- expose downstream contract/consumer views and compact telemetry for RT01 checkpoint gating.

A03 does not:
- execute tools;
- choose the runtime tool to invoke;
- invent tools from nothing;
- claim truth/correctness from tool presence;
- replace A01 ontology cleanup or A02 capability-gap detection.

## Authority Boundaries
- A01 remains source of canonical affordance IDs/classes/validity.
- A02 remains source of capability-gap packets/taxonomy.
- A03 only localizes internal-tool affordance structure and readiness over that upstream basis.

## Mechanistic Notes
- Overbroad generic operations are rejected as non-canonical unless decomposed into typed bounded operations.
- Narrative slogans without typed contracts are rejected.
- Legacy direct-call path detection is first-class in contract/gate surfaces.
- Contract incomplete, degraded, and blocked states are distinct and load-bearing in narrow downstream gating.

## Downstream Narrow Migration
- Checkpoint: `rt01.a03_internal_tool_affordances_checkpoint`.
- Require-path flags and default detours are basis-gated.
- Typed A03 shape can change downstream acceptance even under the same checkpoint required-action envelope.

## Observability
A03 exposes compact runtime tap fields only:
- `canonical_tool_count`
- `rejected_operation_count`
- `contested_tool_count`
- `contract_incomplete_count`
- `degraded_tool_count`
- `blocked_tool_count`
- `missing_internal_tool_gap_count`
- `blocked_internal_tool_gap_count`
- `overbroad_generic_operation_rejected`
- `legacy_direct_call_detected`
- `canonical_tool_id_coverage_complete`
- `downstream_consumer_ready`

## Falsifiers Closed in this Slice
- subroutine/module-name wrapper rebranded as tool ontology
- overbroad generic operation promoted as canonical tool
- contractless internal operation treated as fully available tool
- capability-gap mislocalized from world-action gap to internal-tool gap
- typed shape ignored under same envelope (narrow deterministic contrast added)

## Known Limits (Intentional)
- no map-wide planner integration claim
- no full tool runtime/orchestration claim
- no tool discovery/invention claim
- no correctness/truth guarantee claim
