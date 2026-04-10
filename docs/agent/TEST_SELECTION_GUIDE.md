# Test Selection Guide (RT01/T01/T02/T03 contour)

Rule set:
1. Smallest owner subset first (`-k` where practical).
2. Then owner file.
3. Then direct contour file.
4. Stage contour only when persistence/traceability/dispatch contract is touched.

## Minimal ladders by touched surface

| Changed surface | Owner test first | Direct contour second | Stage contour when needed |
|---|---|---|---|
| `src/substrate/t01_semantic_field/*` | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k \"t01\"` | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py` | only if dispatch/persistence contracts touched |
| `src/substrate/t02_relation_binding/*` | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k \"t02\"` | `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k \"t02\"` | only if dispatch/persistence contracts touched |
| `src/substrate/t03_hypothesis_competition/*` | `pytest -q tests/substrate/test_t03_hypothesis_competition_build/test_t03_hypothesis_competition_build.py` | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k \"t03\"` then `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k \"t03\"` | only if dispatch/persistence contracts touched |
| `src/substrate/subject_tick/update.py` (checkpoint logic) | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k \"t01 or t02 or t03\"` | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py` then `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` | stage contour when traceability/F01/dispatch contracts changed |
| `src/substrate/runtime_topology/policy.py` / `dispatch.py` / contract/telemetry | `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k \"dispatch or topology or t01 or t02 or t03\"` | `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` | stage contour only when F01 persistence contract impacted |
| `src/substrate/subject_tick/downstream_contract.py` or `src/substrate/runtime_topology/downstream_contract.py` with S01 contract-view exposure | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k \"s01\"` | `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k \"s01\"` | only when dispatch persistence/traceability changed |
| `src/substrate/subject_tick/downstream_contract.py` or `src/substrate/runtime_topology/downstream_contract.py` with T04 require-flag exposure | `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k \"t04\"` | `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k \"t04\"` | only when dispatch persistence/traceability changed |

## Fast command set (smallest-first)
- `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k "t01 or t02 or t03"`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k "t01 or t02 or t03"`
- `pytest -q tests/substrate/test_t03_hypothesis_competition_build/test_t03_hypothesis_competition_build.py`
- `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k s01`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k s01`
- `pytest -q tests/substrate/test_subject_tick_build/test_subject_tick_build.py -k t04`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py -k t04`
- Optional stage contour:
  - `pytest -q tests/substrate/test_stage_contour/test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_c04_c05_subject_tick.py`

## Stop conditions
- If owner + direct contour tests pass and no persistence/traceability/dispatch-scope change was made, do not escalate to stage contour.
