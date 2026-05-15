# W04 Build Working Notes

## Phase
W04 // Applicability gating / perspective-safe deployment.

## Contour Placement
`W01 -> W02 -> W03 -> W04 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w04_applicability_gating_checkpoint`

## Implemented Narrow Slice
- Added typed W04 owner package for applicability gating over W03 intake.
- Added desired-state, context, perspective, constraint-profile, intersection, decision, relaxation, revalidation and blocked-record typed surfaces.
- Added machine-readable downstream applicability permission packets with strict non-claims (`action_authorization_granted=False`).
- Added subject_tick/runtime topology/runtime trace integration for compact load-bearing W04 state.

## Load-Bearing Integration
- `subject_tick/update.py` computes W04 after W03 before M01 and projects compact `w04_*` state.
- `subject_tick/policy.py` consumes typed `w04_*` and applies restrictions for hard/unknown/revalidate/abstain/malformed/perspective/authority/stale/relaxation paths.
- `runtime_topology/policy.py` requires W04 checkpoint+surface and rejects `disable_w04_enforcement` in production route.
- `runtime_tap_trace.py` allowlists compact W04 observability fields only.

## Bounded Non-Claims
- No planner/action selector.
- No W05 predictive prior injection.
- No W06 revision engine.
- No world-model/ontology/truth layer expansion.
- No upstream W03 schema mutation.

## Narrow Hardening Notes
- W03 `prohibited_claims` are now preserved into W04 downstream `prohibited_uses` and preserved markers.
- Missing desired-state provenance/source authority now routes to malformed/block semantics and cannot clean-deploy.
- Overbroad desired-state relaxation requests are rejected for clean deployment and cannot silently relax hard/authority/perspective scopes.
- W04 integration coverage now asserts exact malformed-route restriction token (`w04_malformed_desired_state_restriction`) and typed counter delta, not only coarse counters.

## Files Added
- `src/substrate/w04_applicability_gating/__init__.py`
- `src/substrate/w04_applicability_gating/models.py`
- `src/substrate/w04_applicability_gating/policy.py`
- `src/substrate/w04_applicability_gating/downstream_contract.py`
- `src/substrate/w04_applicability_gating/telemetry.py`
- `tests/substrate/w04_applicability_gating_testkit.py`
- `tests/substrate/test_w04_applicability_gating_build/test_w04_applicability_gating_build.py`
- `tests/substrate/test_subject_tick_build/test_w04_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_w04_runtime_topology_integration.py`
- `tools/w04_applicability_gating_demo.py`
- `tests/tools/test_w04_applicability_gating_demo.py`
- `docs/adr/ADR-W04-applicability-gating-perspective-safe-deployment.md`

## Files Changed
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Tests Run and Results
Required W04:
- `pytest -q tests/substrate/test_w04_applicability_gating_build/test_w04_applicability_gating_build.py` -> `38 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w04_subject_tick_integration.py` -> `8 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w04_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `28 passed`
- `pytest -q tests/tools/test_w04_applicability_gating_demo.py` -> `1 passed`

Compatibility:
- W03: `pytest -q tests/substrate/test_w03_schema_consolidation_build/test_w03_schema_consolidation_build.py` -> `33 passed`
- W03: `pytest -q tests/substrate/test_subject_tick_build/test_w03_subject_tick_integration.py` -> `7 passed`
- W03: `pytest -q tests/substrate/test_runtime_topology_build/test_w03_runtime_topology_integration.py` -> `5 passed`
- W03: `pytest -q tests/tools/test_w03_schema_consolidation_demo.py` -> `1 passed`
- W02: `pytest -q tests/substrate/test_w02_regularity_extraction_build/test_w02_regularity_extraction_build.py` -> `27 passed`
- W02: `pytest -q tests/substrate/test_subject_tick_build/test_w02_subject_tick_integration.py` -> `7 passed`
- W02: `pytest -q tests/substrate/test_runtime_topology_build/test_w02_runtime_topology_integration.py` -> `4 passed`
- W02: `pytest -q tests/tools/test_w02_regularity_extraction_demo.py` -> `1 passed`
- W01: `pytest -q tests/substrate/test_w01_bounded_world_loop_build/test_w01_bounded_world_loop_build.py` -> `22 passed`
- W01: `pytest -q tests/substrate/test_subject_tick_build/test_w01_subject_tick_integration.py` -> `8 passed`
- W01: `pytest -q tests/substrate/test_runtime_topology_build/test_w01_runtime_topology_integration.py` -> `4 passed`
- W01: `pytest -q tests/tools/test_w01_packet_world_demo.py` -> `1 passed`
- M01: `pytest -q tests/substrate/test_m01_homeostatic_salience_imprint_build/test_m01_homeostatic_salience_imprint_build.py` -> `19 passed`
- M01: `pytest -q tests/substrate/test_subject_tick_build/test_m01_subject_tick_integration.py` -> `7 passed`
- M01: `pytest -q tests/substrate/test_runtime_topology_build/test_m01_runtime_topology_integration.py` -> `4 passed`
- M01: `pytest -q tests/tools/test_m01_imprint_demo.py` -> `1 passed`
- M02: `pytest -q tests/substrate/test_m02_predictive_relevance_build/test_m02_predictive_relevance_build.py` -> `19 passed`
- M02: `pytest -q tests/substrate/test_subject_tick_build/test_m02_subject_tick_integration.py` -> `7 passed`
- M02: `pytest -q tests/substrate/test_runtime_topology_build/test_m02_runtime_topology_integration.py` -> `4 passed`
- M02: `pytest -q tests/tools/test_m02_predictive_relevance_demo.py` -> `1 passed`
- N03: `pytest -q tests/substrate/test_n03_autobiographical_relevance_build/test_n03_autobiographical_relevance_build.py` -> `22 passed`
- N03: `pytest -q tests/substrate/test_subject_tick_build/test_n03_subject_tick_integration.py` -> `7 passed`
- N03: `pytest -q tests/substrate/test_runtime_topology_build/test_n03_runtime_topology_integration.py` -> `4 passed`
- N03: `pytest -q tests/tools/test_n03_autobiographical_relevance_demo.py` -> `1 passed`

## Known Unrelated Failures
- `pytest -q tests/substrate/test_subject_tick_build` -> `1 failed, 267 passed`
- failing test: `tests/substrate/test_subject_tick_build/test_v03_subject_tick_integration.py::test_disabling_v03_enforcement_changes_outcome_class_under_protected_omission_leak`
- signature preserved: expected `repair_runtime_path`, got `revalidate_scope` on enabled branch.

## C05 Compatibility
- C05 paths absent:
  - `tests/substrate/test_c05_temporal_validity_selective_revalidation_build/test_c05_temporal_validity_selective_revalidation_build.py`
  - `tests/substrate/test_subject_tick_build/test_c05_subject_tick_integration.py`
  - `tests/substrate/test_runtime_topology_build/test_c05_runtime_topology_integration.py`
- status: non-executable compatibility (no green claim).
