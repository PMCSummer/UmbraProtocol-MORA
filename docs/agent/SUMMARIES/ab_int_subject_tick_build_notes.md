# AB-INT Build Notes

## Inventory result
- Inspected seams/maps: `docs/seams/RT01.seam.md`, `docs/agent/SUMMARIES/subject_tick_update.map.md`, `docs/agent/SUMMARIES/runtime_topology_policy.map.md`.
- Inspected AB owners: AB1..AB7 packages and APIs.
- Inspected subject tick integration point: `src/substrate/subject_tick/update.py`, `src/substrate/subject_tick/models.py`.
- AB-INT is implemented as live cognitive contour, not action authority.

## Files added/changed
### Added
- `src/substrate/ab_subject_tick_integration/__init__.py`
- `src/substrate/ab_subject_tick_integration/models.py`
- `src/substrate/ab_subject_tick_integration/policy.py`
- `src/substrate/ab_subject_tick_integration/downstream_contract.py`
- `src/substrate/ab_subject_tick_integration/telemetry.py`
- `tests/substrate/test_ab_subject_tick_integration_build/test_ab_subject_tick_integration_build.py`
- `tests/substrate/test_subject_tick_build/test_ab_live_subject_tick_integration.py`
- `tools/ab_live_subject_tick_demo.py`
- `tests/tools/test_ab_live_subject_tick_demo.py`
- `docs/adr/ADR-AB-INT-subject-tick-integration.md`
- `docs/agent/EXPERIMENTS/subject_tick_ab_live_contour.md`

### Changed
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`

## Scheduling order implemented
AB1 -> AB2 -> AB3 -> AB5 -> AB6 -> AB7 -> AB4 (basis-only handoff before ACP01 consumption).

## Tests
- Added AB-INT owner tests (policy-level).
- Added subject_tick integration tests for enabled/disabled behavior, ACP01 handoff basis, ordering and drift bounds.
- Added demo CLI tests for required cases and bounded-claim output.

## Topology updates
- Topology checker update: no.
- Rationale: AB-INT currently exposes refs/counters in tick result/state and does not yet add a dedicated runtime tap segment.

## Known limitations
- Live AB contour only.
- No open-world runner.
- No factory executor.
- No UMWELT/contact membrane.
- No external encyclopedia affordance.
- No cross-backend portability proof.
- No public reviewer pack.

## Next relation
- WORLD0: runtime bridge expansion candidate.
- P17B/P18/P19: downstream embodiment and multi-step runtime hardening with preserved AB authority boundaries.
