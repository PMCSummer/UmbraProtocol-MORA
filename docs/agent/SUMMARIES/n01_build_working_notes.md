# N01 Build Working Notes (Narrow Registry Slice)

## Contour Placement
- Added checkpoint: `rt01.n01_narrative_commitments_checkpoint`
- Placement: after `rt01.m02_predictive_relevance_checkpoint`, before `rt01.outcome_resolution_checkpoint`

## Files Added
- `src/substrate/n01_narrative_commitments/__init__.py`
- `src/substrate/n01_narrative_commitments/models.py`
- `src/substrate/n01_narrative_commitments/policy.py`
- `src/substrate/n01_narrative_commitments/downstream_contract.py`
- `src/substrate/n01_narrative_commitments/telemetry.py`
- `tests/substrate/n01_narrative_commitments_testkit.py`
- `tests/substrate/test_n01_narrative_commitments_build/test_n01_narrative_commitments_build.py`
- `tests/substrate/test_subject_tick_build/test_n01_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_n01_runtime_topology_integration.py`
- `tools/n01_narrative_commitment_demo.py`
- `tests/tools/test_n01_narrative_commitment_demo.py`
- `docs/adr/ADR-N01-narrative-commitments.md`

## Files Updated
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Mechanistic Notes
- N01 is a typed claim-to-commitment registry, not a prose generator.
- Support basis, scope caps, conflict status, and revision action are load-bearing fields.
- Capability and limitation claim kinds use separate support requirements.
- Existing commitment references are preserved on revision/retirement paths.
- `revised_commitment` is now exercised as a distinct emitted decision with explicit prior-decision provenance.
- Conflict-marked candidates without explicit `existing_commitment_refs` are routed to contested/no-clean states and cannot silently become clean commitments.
- Downstream obligations are machine-readable and scope-aware.

## Known Limits
- No N02 identity drift reflection.
- No N03 autobiographical relevance channel.
- No M03 retention/replay/retrieval lifecycle execution.
- No identity drift reflection or user/other modeling claims.
- No map-wide narrative migration claim.
