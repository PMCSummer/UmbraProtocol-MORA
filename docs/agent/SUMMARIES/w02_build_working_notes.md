# W02 Build Working Notes

## Phase
W02 // Regularity extraction from lived traces.

## Narrow Role
Provide typed staged regularity extraction over W01-admitted traces:
- keep maturity staged (no direct mature object claim);
- preserve contradiction and lineage alternatives;
- support downgrade/revalidation when new negative evidence appears;
- emit bounded downstream permission packets.

## Contour Placement
`W01 -> W02 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
- `rt01.w02_regularity_extraction_checkpoint`

## Files Added
- `src/substrate/w02_regularity_extraction/__init__.py`
- `src/substrate/w02_regularity_extraction/models.py`
- `src/substrate/w02_regularity_extraction/policy.py`
- `src/substrate/w02_regularity_extraction/downstream_contract.py`
- `src/substrate/w02_regularity_extraction/telemetry.py`
- `tests/substrate/w02_regularity_extraction_testkit.py`
- `tests/substrate/test_w02_regularity_extraction_build/test_w02_regularity_extraction_build.py`
- `tests/substrate/test_subject_tick_build/test_w02_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_w02_runtime_topology_integration.py`
- `tools/w02_regularity_extraction_demo.py`
- `tests/tools/test_w02_regularity_extraction_demo.py`
- `docs/adr/ADR-W02-regularity-extraction-from-lived-traces.md`

## Integration Surfaces Updated
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Load-Bearing Outcome
W02 typed state is projected into `subject_tick` (`w02_*`) and consumed by gate policy:
- contradiction/no-clean/must-abstain/consumer-readiness are causal;
- same envelope can diverge via different typed W02 shape.

## Narrow Hardening Notes
- Strengthened permission-granularity owner assertions to remove tautological boolean checks.
- Scaffold-only traces remain low-maturity but are now treated as no-clean regularity for consumer readiness.
- Replacement lineage markers now produce explicit contradiction/revalidation pressure and block clean same-instance continuity.

## Known Limitations / Bounded Non-Claims
- No W03 schema consolidation.
- No mature object identity claim.
- No planner logic.
- No memory lifecycle implementation.
- C05 compatibility remains non-executable when C05 paths are absent.

## Known Unrelated Failure
- `tests/substrate/test_subject_tick_build/test_v03_subject_tick_integration.py::test_disabling_v03_enforcement_changes_outcome_class_under_protected_omission_leak`

## Test Commands And Results
Required W02:
- `pytest -q tests/substrate/test_w02_regularity_extraction_build/test_w02_regularity_extraction_build.py` -> `27 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w02_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w02_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `27 passed`
- `pytest -q tests/tools/test_w02_regularity_extraction_demo.py` -> `1 passed`

Compatibility:
- W01: `22/8/4/1 passed`
- M01: `19/7/4/1 passed`
- M02: `19/7/4/1 passed`
- N01: `22/8/4/1 passed`
- N02: `22/8/4/1 passed`
- N03: `21/7/4/1 passed`
- A01: `12/8/4 passed`
- A02: `13/7/3 passed`
- A03: `12/7/3 passed`
- S04: `27/6 passed`
- S05: `17/7 passed`

Informational:
- `pytest -q tests/substrate/test_subject_tick_build` -> `1 failed, 252 passed` (known unrelated V03 failure above)

C05 paths:
- `tests/substrate/test_c05_temporal_validity_selective_revalidation_build/test_c05_temporal_validity_selective_revalidation_build.py` -> absent
- `tests/substrate/test_subject_tick_build/test_c05_subject_tick_integration.py` -> absent
- `tests/substrate/test_runtime_topology_build/test_c05_runtime_topology_integration.py` -> absent
