# W03 Build Working Notes

## Phase
W03 // Schema consolidation / everyday prior formation.

## Contour Placement
`W01 -> W02 -> W03 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w03_schema_consolidation_checkpoint`

## Implemented Narrow Slice
- Added typed W03 owner package for bounded schema consolidation over W02 regularities.
- Added channel-separated schema candidate/prior states and contradiction consequence routes.
- Added stale/revalidation and version-record surfaces.
- Added machine-readable downstream schema permission packets with prohibited claims.
- Integrated W03 into subject_tick/runtime topology/runtime trace as a load-bearing checkpoint.

## Load-Bearing Integration
- `subject_tick/update.py` computes W03 after W02 and projects compact `w03_*` state.
- `subject_tick/policy.py` consumes typed `w03_*` fields and adds restrictions when stale/contested/no-clean/must-abstain states appear.
- `runtime_topology/policy.py` requires W03 checkpoint/surface and rejects `disable_w03_enforcement` in production route.
- `runtime_tap_trace.py` + trace tests allowlist compact W03 observability fields.

## Narrow Hardening (MH-01..MH-04)
- W03 permission emission now prevents clean bounded-prior leaks from deferred/stale/contested/scaffold-laundered states.
- W03 authority/provenance ablation is operational: permission/status changes, not just provenance string differences.
- W03 contradiction route coverage is explicit for distinct operational routes (`block_downstream_use` vs `split`).
- W02 same-envelope integration proof is strengthened with strong-vs-weak restriction-set divergence assertions under W03 mediation.

## Files Added
- `src/substrate/w03_schema_consolidation/__init__.py`
- `src/substrate/w03_schema_consolidation/models.py`
- `src/substrate/w03_schema_consolidation/policy.py`
- `src/substrate/w03_schema_consolidation/downstream_contract.py`
- `src/substrate/w03_schema_consolidation/telemetry.py`
- `tests/substrate/w03_schema_consolidation_testkit.py`
- `tests/substrate/test_w03_schema_consolidation_build/test_w03_schema_consolidation_build.py`
- `tests/substrate/test_subject_tick_build/test_w03_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_w03_runtime_topology_integration.py`
- `tools/w03_schema_consolidation_demo.py`
- `tests/tools/test_w03_schema_consolidation_demo.py`
- `docs/adr/ADR-W03-schema-consolidation-everyday-prior-formation.md`

## Files Changed
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Known Limitations
- No W04 applicability deployment logic (out of scope).
- No planner/action selection logic (out of scope).
- No memory lifecycle/M03 logic (out of scope).
- No ontology/common-sense truth engine (out of scope).
- C05 executable compatibility is reported only if C05 test paths exist.

## Known Unrelated Failure
- `tests/substrate/test_subject_tick_build/test_v03_subject_tick_integration.py::test_disabling_v03_enforcement_changes_outcome_class_under_protected_omission_leak` (if unchanged signature persists in informational full-pack run).

## Test Commands and Results
Required W03:
- `pytest -q tests/substrate/test_w03_schema_consolidation_build/test_w03_schema_consolidation_build.py` -> `33 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w03_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w03_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `27 passed`
- `pytest -q tests/tools/test_w03_schema_consolidation_demo.py` -> `1 passed`

Compatibility:
- `pytest -q tests/substrate/test_w02_regularity_extraction_build/test_w02_regularity_extraction_build.py` -> `27 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w02_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w02_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/tools/test_w02_regularity_extraction_demo.py` -> `1 passed`
- `pytest -q tests/substrate/test_w01_bounded_world_loop_build/test_w01_bounded_world_loop_build.py` -> `22 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w01_subject_tick_integration.py` -> `8 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w01_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/tools/test_w01_packet_world_demo.py` -> `1 passed`
- `pytest -q tests/substrate/test_m01_homeostatic_salience_imprint_build/test_m01_homeostatic_salience_imprint_build.py` -> `19 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_m01_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_m01_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/tools/test_m01_imprint_demo.py` -> `1 passed`
- `pytest -q tests/substrate/test_m02_predictive_relevance_build/test_m02_predictive_relevance_build.py` -> `19 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_m02_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_m02_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/tools/test_m02_predictive_relevance_demo.py` -> `1 passed`
- `pytest -q tests/substrate/test_n03_autobiographical_relevance_build/test_n03_autobiographical_relevance_build.py` -> `21 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_n03_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_n03_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/tools/test_n03_autobiographical_relevance_demo.py` -> `1 passed`

C05 path checks:
- `tests/substrate/test_c05_temporal_validity_selective_revalidation_build/test_c05_temporal_validity_selective_revalidation_build.py` -> absent
- `tests/substrate/test_subject_tick_build/test_c05_subject_tick_integration.py` -> absent
- `tests/substrate/test_runtime_topology_build/test_c05_runtime_topology_integration.py` -> absent

Informational:
- `pytest -q tests/substrate/test_subject_tick_build` -> `1 failed, 259 passed` (known unrelated V03 integration failure)
