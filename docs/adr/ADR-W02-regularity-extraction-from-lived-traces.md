# ADR-W02: Regularity Extraction From Lived Traces (Narrow Build Slice)

## Status
Accepted for narrow W02 build slice.

## Scope
W02 adds a typed regularity-extraction layer over W01-admitted lived traces.
It is not mature object truth, not object recognition, not scene understanding, and not planner logic.

## Decision
W02 emits typed regularity records with staged maturity and explicit gates:
- trace token -> recurrent scaffold -> persistent instance candidate/hypothesis
- kind/role/structure/affordance/lineage candidates stay separated
- contradiction ledger is first-class
- downgrade/revalidation is explicit and non-monotonic
- downstream permissions are typed and bounded

Core guardrails:
- single trace cannot promote to persistent instance hypothesis;
- scaffold-only/partial/contested/contradictory/revoked evidence constrains promotion;
- duplicate/provider-bias/text-artifact repetition does not count as clean recurrence;
- same kind does not imply same instance;
- role recurrence does not imply kind;
- structural signature recurrence does not imply same object;
- stable identity claim remains forbidden in W02 downstream permissions.
- scaffold-only/partial/contested recurrence is not treated as clean consumer-ready regularity.
- replacement lineage markers route through contradiction/revalidation handling and do not preserve clean same-instance continuity.

## Runtime Placement
Current contour placement includes W02 immediately after W01:

`rt01.w01_bounded_world_loop_checkpoint`
-> `rt01.w02_regularity_extraction_checkpoint`
-> `rt01.m01_homeostatic_salience_imprint_checkpoint`
-> `rt01.m02_predictive_relevance_checkpoint`
-> `rt01.n01_narrative_commitments_checkpoint`
-> `rt01.n02_identity_drift_reflection_checkpoint`
-> `rt01.n03_autobiographical_relevance_checkpoint`
-> `rt01.outcome_resolution_checkpoint`

## Downstream Contract
W02 exposes typed permission packets with explicit boundaries:
- scaffold / instance-hypothesis / kind-hint / role-hint / affordance-hint permissions;
- `may_claim_stable_identity` remains false;
- contradiction and abstain requirements are machine-readable.

## Non-Claims
W02 does not claim:
- mature object identity truth;
- W03 schema consolidation;
- full ontology or scene graph;
- planner decisions;
- memory retrieval/lifecycle behavior.

## Compatibility Limitation
Direct C05 compatibility is non-executable when C05 test paths are absent in this repository.

## Validation Snapshot
Required W02 pack:
- `pytest -q tests/substrate/test_w02_regularity_extraction_build/test_w02_regularity_extraction_build.py` -> `25 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w02_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w02_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `27 passed`
- `pytest -q tests/tools/test_w02_regularity_extraction_demo.py` -> `1 passed`

Compatibility snapshots:
- W01 pack -> `22/8/4/1 passed`
- M01 pack -> `19/7/4/1 passed`
- M02 pack -> `19/7/4/1 passed`
- N01 pack -> `22/8/4/1 passed`
- N02 pack -> `22/8/4/1 passed`
- N03 pack -> `21/7/4/1 passed`
- A01 pack -> `12/8/4 passed`
- A02 pack -> `13/7/3 passed`
- A03 pack -> `12/7/3 passed`
- S04 pack -> `27/6 passed`
- S05 pack -> `17/7 passed`
