# ACP01 Build Working Notes

## Scope
P4 adds ACP01 as a narrow internal candidate producer seam and wires it into `subject_tick` and the embodied bridge internal mode.

## Mechanistic Path
- Bridge public observation -> ACP01 typed input projection (optional internal mode).
- `execute_subject_tick` runs ACP01 (when enabled/input present).
- ACP01 may emit AP01 candidate set.
- AP01 decides publication (unchanged authority).
- Bridge extracts AP01 request and may submit to world backend.

## Boundaries Preserved
- ACP01 has no publication authority.
- ACP01 has no execution authority.
- ACP01 has no world submission authority.
- No direct bridge runtime call to ACP01/AP01 publication policy.
- No W/A/P/S surface edits.

## P4 Candidate Gating
- Pickup requires drive + visible object + pickup surface + proximity basis + capacity basis.
- Inspect may be proposed for uncertainty/probe when pickup is not safely supported.
- Blocked/insufficient/revalidation decisions remain first-class.

## Known Limits
- No autonomous planner.
- No pathfinding/movement strategy synthesis.
- No recipe/automation/station production logic.
