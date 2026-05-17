# P7 Runtime Topology Alignment Build Notes

## Files added
- `tools/runtime_topology_alignment_checker.py`
- `tests/tools/test_runtime_topology_alignment_checker.py`
- `docs/agent/GOVERNANCE/runtime_topology_alignment.md`

## Checker behavior
- detects executed seams from `subject_tick` and embodied bridge surfaces
- checks representation evidence in runtime topology + docs
- reports represented / partial / missing seams
- checks `ACP01 -> AP01` ordering
- checks authority conflation patterns
- checks presence of core consumer obligations
- supports JSON and fail-on-missing mode

## Tests
- validates required JSON sections
- validates ordering detection
- validates missing seam detection
- validates conflation detection
- validates fail-on-missing exit code
- validates no-mutation behavior on scanned repos
- validates ACP01/AP01 are not hard-missing in current repo
- validates claim calibration wording

## Known limitations
- static pattern/registry checker, not complete semantic static analysis
- representation can be partial when topology policy/docs are intentionally lagging
- checker enforces architecture alignment only; it does not prove cognition/agency

## Next steps
- optionally promote advisory partial seams into stricter formal policy representation
- keep seam registry synchronized with future runtime contour changes
