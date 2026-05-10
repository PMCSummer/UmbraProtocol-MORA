# ADR-N03: Autobiographical Relevance (Narrow Transfer Discipline Slice)

## Status
Accepted for narrow frontier build slice.

## Scope
N03 adds a typed autobiographical relevance layer between historical self-line traces and current regulation/planning demands.
It is not retrieval, not a planner, and not memory lifecycle execution.

## Decision
N03 emits typed relevance entries that bind:
- `source_trace_id`
- `current_target_id`
- `relevance_kind`
- `transfer_decision`
- `transfer_scope`
- structural support dimensions
- anti-generalization limits
- limiting reasons

Core guardrails:
- semantic similarity alone is blocked;
- recency alone is blocked;
- vividness alone is capped/blocked;
- single-episode broad transfer is blocked;
- drift markers can downweight or block transfer;
- capability/affordance shifts can demote historical templates to caution paths;
- conflicting trace sets stay explicit and are not flattened.

## Runtime Placement
Current contour placement:

`rt01.w01_bounded_world_loop_checkpoint`
-> `rt01.m01_homeostatic_salience_imprint_checkpoint`
-> `rt01.m02_predictive_relevance_checkpoint`
-> `rt01.n01_narrative_commitments_checkpoint`
-> `rt01.n02_identity_drift_reflection_checkpoint`
-> `rt01.n03_autobiographical_relevance_checkpoint`
-> `rt01.outcome_resolution_checkpoint`

## Downstream Contract
N03 exposes typed consumer packets and contract views with explicit routing/caution signals.
Consumers are constrained to bounded transfer use and cannot treat N03 as a truth oracle, global rule generator, retrieval subsystem, or planner command.

## Non-Claims
N03 does not claim:
- full autobiographical self;
- memory retrieval/replay/consolidation lifecycle (M03);
- identity drift generation (N02 owns this);
- narrative commitment generation (N01 owns this);
- user/other entity modeling (O01+);
- world-body implementations (W-line expansions).

## Compatibility Limitation
Direct C05 compatibility remains a non-executable limitation when C05 test paths are absent in the repository.

## Validation Snapshot
Required N03 pack:
- `pytest -q tests/substrate/test_n03_autobiographical_relevance_build/test_n03_autobiographical_relevance_build.py` -> `20 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_n03_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_n03_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `27 passed`
- `pytest -q tests/tools/test_n03_autobiographical_relevance_demo.py` -> `1 passed`

Compatibility snapshots:
- N02 pack -> `22/8/4/1 passed`
- N01 pack -> `22/8/4/1 passed`
- M02 pack -> `19/7/4/1 passed`
- M01 pack -> `19/7/4/1 passed`
- W01 pack -> `22/8/4/1 passed`
- A01 pack -> `12/8/4 passed`
- A02 pack -> `13/7/3 passed`
- A03 pack -> `12/7/3 passed`
- S04 pack -> `27/6 passed`
- S05 pack -> `17/7 passed`
