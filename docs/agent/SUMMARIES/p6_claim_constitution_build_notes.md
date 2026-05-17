# P6 Claim Constitution Build Notes

## Files Added
- `tools/claim_constitution_checker.py`
- `tests/tools/test_claim_constitution_checker.py`
- `docs/agent/GOVERNANCE/mora_claim_constitution.md`
- `docs/agent/GOVERNANCE/mora_claim_levels.md`

## Checker Behavior
- Scans roadmap/docs/experiments surfaces (configurable flags).
- Produces hard findings, missing evidence findings, advisory findings.
- Emits positive authorization and blocked claim lists.
- Supports JSON output and non-zero exit on `--fail-on-overclaim`.

## Test Coverage
- Consciousness/AGI overclaim blocking.
- Cautious language allowance.
- L8 artifact gate.
- Closed-with-blockers/TODO claim gate.
- AP01/ACP01 stage overclaim gates.
- JSON schema sections.
- CLI failure behavior for hard violations.
- Near-defensible calibration presence.

## Known Limitations
- Static/heuristic checker; stronger schema integration can reduce false positives.
- External reviewer artifact bundle is not built by this stage.
- Baseline artifacts are validated by presence markers, not semantic quality.

## Future Integration Points
- Optional direct parsing of tracker model schema.
- CI policy gate for release branches.
- Reviewer-pack artifact verifier for L8-L10 claims.
