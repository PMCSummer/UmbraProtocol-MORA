# Runtime Topology Alignment (P7)

## Purpose
P7 adds an executable alignment check between:
- formal runtime topology / role artifacts;
- actually executed subject/world seams in the current runtime contour.

It strengthens governance by making topology claims auditable against real execution surfaces.

## Why alignment matters
- Prevents decorative topology maps that diverge from executable architecture.
- Forces explicit authority boundaries (`candidate`, `request`, `execution`, `effect`).
- Makes consumer obligations inspectable.

## Current executed contour (bounded)
- public world observation projection
- `execute_subject_tick`
- `ACP01` candidate production (when enabled)
- `AP01` publication decision
- envelope wrapping outside subject authority
- world backend submission/execution outside subject authority
- effect feedback into next observation

## Required seam registry
The checker uses an explicit seam registry with:
- seam id/name
- expected owner + authority
- expected inputs/outputs (via evidence patterns)
- ordering expectations
- forbidden authority patterns
- consumer obligations

Primary falsifier:
- `executed_seam_missing_from_topology`

## Ordering contract
- observation projection before subject tick
- `ACP01 -> AP01` ordering inside `subject_tick` when internal candidate path is enabled
- envelope wrapping only from AP01-published request
- world execution only after envelope submission
- effect feedback carried into next observation

## Authority boundary contract
- `ACP01`: candidate production only
- `AP01`: publication authority only
- bridge: wrapping/orchestration only
- world backend: execution/mutation authority
- effect frame: feedback (not completion oracle)

## Consumer obligations
- candidate != request
- request != execution
- effect != completion
- public subject-visible payload != eval/private truth
- provenance refs should be preserved

## Representation statuses
- represented: executed seam has explicit topology/role evidence
- partial: only subset evidence is found
- missing: executed seam is not represented

## Checker usage
```bash
python tools/runtime_topology_alignment_checker.py
python tools/runtime_topology_alignment_checker.py --json
python tools/runtime_topology_alignment_checker.py --include-advisory
python tools/runtime_topology_alignment_checker.py --fail-on-missing
```

## Relationship to roadmap/governance
P7 does not rewrite roadmap or mutate claim statuses.
It provides an auditable alignment layer that feeds governance and claim-discipline reviews.

## Known limitations
- static registry/pattern checker, not full semantic verifier
- evidence can be partial until runtime topology docs/policy are fully synchronized
- topology alignment does not prove cognition, agency, or consciousness by itself
