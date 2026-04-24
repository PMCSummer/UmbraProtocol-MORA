# V01 Build / Hardening Working Notes

## Contour Placement
- RT01 hosted order (current): `... -> O04 -> R05 -> V01 -> RT01 outcome resolution`
- Checkpoint: `rt01.v01_normative_permission_commitment_licensing_checkpoint`

## Typed Surfaces
- Package: `src/substrate/v01_normative_permission_commitment_licensing/`
- Core typed state:
  - `V01CommunicativeActCandidate`
  - `V01LicensedActEntry`
  - `V01DeniedActEntry`
  - `V01CommitmentDelta`
  - `V01CommunicativeLicenseState`
  - `V01LicenseGateDecision`
  - `V01ScopeMarker`
  - `V01Telemetry`
  - `V01LicenseResult`

## Require / Default Paths (RT01)
- Require:
  - `require_v01_license_consumer`
  - `require_v01_commitment_delta_consumer`
  - `require_v01_qualifier_binding_consumer`
- Default:
  - `default_v01_unlicensed_act_detour`
  - `default_v01_qualification_required_detour`
  - `default_v01_commitment_denied_detour`
- Basis-gated by explicit V01 candidates; no-candidate path stays `v01_optional`.

## Hardening Notes (Current Pass)
- Protective defer seam fixed to use bounded R05 surface pressure, not only override/release flags.
- Assertion evidence gradient tightened to a clearer `full -> qualified -> deny`.
- Added downstream identity surface in `SubjectTickState`:
  - `v01_mandatory_qualifier_ids`
- Added downstream qualifier identity guard in `subject_tick/policy.py`.
- Added typed-semantic branch where commitment-creating V01 shape changes downstream restriction under same checkpoint token (`v01_optional`) contrast.

## Current Shortcut Closures
- Act-type contrast (`assertion` vs `advice` vs `promise`) is load-bearing in V01 policy.
- Promise does not silently collapse from assertion.
- Denied acts remain explicit state with reasons + alternatives.
- Qualifier identity mismatch/substitution can be detected downstream.

## Open Limitations (Narrow)
- V01 remains RT01-local first slice, not map-wide V-line maturity.
- No V02/V03 realization guarantees.
- Consumer ecosystem beyond RT01 gate remains narrow.

## Test Commands Used (This Pass)
- `pytest -q tests/substrate/test_v01_normative_permission_commitment_licensing_build/test_v01_normative_permission_commitment_licensing_build.py`
- `pytest -q tests/substrate/test_subject_tick_build/test_v01_subject_tick_integration.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_v01_runtime_topology_integration.py`
- `pytest -q tests/tools/test_tick_observability_trace.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `pytest -q tests/substrate/test_subject_tick_build`
