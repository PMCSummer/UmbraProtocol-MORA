# N03 Build Working Notes

## Phase
N03 // Autobiographical relevance in regulation and planning.

## Narrow Role
Provide typed, bounded autobiographical transfer discipline:
- map typed self-line historical traces to current typed demand targets;
- emit scoped transfer decisions with anti-generalization limits;
- block semantic-only / recency-only / vividness-only shortcuts;
- preserve conflict and drift-aware transfer caveats.

## Contour Placement
`W01 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

## Files Added
- `src/substrate/n03_autobiographical_relevance/__init__.py`
- `src/substrate/n03_autobiographical_relevance/models.py`
- `src/substrate/n03_autobiographical_relevance/policy.py`
- `src/substrate/n03_autobiographical_relevance/downstream_contract.py`
- `src/substrate/n03_autobiographical_relevance/telemetry.py`
- `tests/substrate/n03_autobiographical_relevance_testkit.py`
- `tests/substrate/test_n03_autobiographical_relevance_build/test_n03_autobiographical_relevance_build.py`
- `tests/substrate/test_subject_tick_build/test_n03_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_n03_runtime_topology_integration.py`
- `tools/n03_autobiographical_relevance_demo.py`
- `tests/tools/test_n03_autobiographical_relevance_demo.py`
- `docs/adr/ADR-N03-autobiographical-relevance.md`

## Integration Surfaces Updated
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Load-Bearing Outcome
N03 typed state (`n03_*`) is projected into `subject_tick` and consumed by the downstream gate.
Same checkpoint envelope can diverge under different typed N03 shapes.

## Known Limitations
- No retrieval/replay/consolidation implementation (M03 out of scope).
- No identity generation (N02 remains upstream).
- No planner implementation (N03 emits constraints/signals only).
- C05 compatibility is non-executable when C05 test paths are absent.

## Known Unrelated Failure
- `tests/substrate/test_subject_tick_build/test_v03_subject_tick_integration.py::test_disabling_v03_enforcement_changes_outcome_class_under_protected_omission_leak`

## Test Commands And Results
Required N03:
- `pytest -q tests/substrate/test_n03_autobiographical_relevance_build/test_n03_autobiographical_relevance_build.py` -> `20 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_n03_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_n03_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `27 passed`
- `pytest -q tests/tools/test_n03_autobiographical_relevance_demo.py` -> `1 passed`

Compatibility:
- N02: `22/8/4/1 passed`
- N01: `22/8/4/1 passed`
- M02: `19/7/4/1 passed`
- M01: `19/7/4/1 passed`
- W01: `22/8/4/1 passed`
- A01: `12/8/4 passed`
- A02: `13/7/3 passed`
- A03: `12/7/3 passed`
- S04: `27/6 passed`
- S05: `17/7 passed`

C05 compatibility:
- path checks -> absent (`tests/substrate/test_c05_temporal_validity_selective_revalidation_build/test_c05_temporal_validity_selective_revalidation_build.py`, `tests/substrate/test_subject_tick_build/test_c05_subject_tick_integration.py`, `tests/substrate/test_runtime_topology_build/test_c05_runtime_topology_integration.py`)

Informational:
- `pytest -q tests/substrate/test_subject_tick_build` -> `1 failed, 245 passed` (known unrelated V03 failure above)
