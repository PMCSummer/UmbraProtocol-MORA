# W05 Build Working Notes

## Phase
W05 // Predictive prior injection into interpretation and policy.

## Contour Placement
`W01 -> W02 -> W03 -> W04 -> W05 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w05_predictive_prior_injection_checkpoint`

## Implemented Narrow Slice
- Added typed W05 owner package with four-channel signal stack (`desired`, `predicted`, `observed`, `permitted`).
- Added route-only mismatch classification and update routing records with execution prohibition seam.
- Added W05.1 gain control (prior strength + precision + source reliability interaction).
- Added constitutional/protected-target guards and downstream routing permission packets.
- Hardened channel-collapse detection beyond duplicate IDs:
  - channel marker mismatch,
  - desired/observed semantic collapse suspicion,
  - predicted/permitted and observed/permitted collapse suspicion.
- Hardened mismatch metadata: `compared_channels` now tracks actual compared route.
- Hardened owner proofs for `PermittedChannelEnforcementRecord` and per-channel provenance/authority/confidence/precision separation.

## Load-Bearing Integration
- `subject_tick/update.py` now computes W05 after W04 and before M01 and emits W05 checkpoint.
- `SubjectTickState` projects compact `w05_*` counters/markers.
- `subject_tick/policy.py` consumes typed `w05_*` and injects route-specific restrictions.
- `runtime_topology/policy.py` requires W05 checkpoint/surface and rejects `disable_w05_enforcement` in production.
- `runtime_tap_trace.py` allowlists compact W05 fields only.
- Tick observability order now requires `W01 -> W02 -> W03 -> W04 -> W05 -> M01`.

## Bounded Non-Claims
- No W06 revision execution.
- No planner/action selector.
- No action authorization.
- No memory/policy/schema mutation.
- No world-truth or ontology expansion.

## Files Added
- `src/substrate/w05_predictive_prior_injection/__init__.py`
- `src/substrate/w05_predictive_prior_injection/models.py`
- `src/substrate/w05_predictive_prior_injection/policy.py`
- `src/substrate/w05_predictive_prior_injection/downstream_contract.py`
- `src/substrate/w05_predictive_prior_injection/telemetry.py`
- `tests/substrate/w05_predictive_prior_injection_testkit.py`
- `tests/substrate/test_w05_predictive_prior_injection_build/test_w05_predictive_prior_injection_build.py`
- `tests/substrate/test_subject_tick_build/test_w05_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_w05_runtime_topology_integration.py`
- `tools/w05_predictive_prior_injection_demo.py`
- `tests/tools/test_w05_predictive_prior_injection_demo.py`
- `docs/adr/ADR-W05-predictive-prior-injection-interpretation-policy.md`

## Files Changed
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Limitations / Out Of Scope
- W06 remains out of scope (no revision execution).
- M03 remains out of scope (no lifecycle updates).
- C05 compatibility remains non-executable if paths are absent.
- S03 integration/runtime compatibility remains non-executable when only owner-build path exists.
