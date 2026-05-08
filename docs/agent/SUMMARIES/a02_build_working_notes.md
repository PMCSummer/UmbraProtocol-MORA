# A02 Build Working Notes (frontier-hosted narrow slice)

## Lawful insertion point
- Inserted after A01 and before A-line:
  - `rt01.a01_affordance_ontology_cleanup_checkpoint`
  - `rt01.a02_capability_gap_detection_checkpoint`
  - `rt01.a_line_normalization_checkpoint`

## Falsifiers targeted
- planner-deadend-rebranded-as-gap-detection
- no-plan-found-substitutes-capability-gap
- low-confidence-substitutes-capability-gap
- wish-as-capability-demand
- missing-vs-blocked-capability-confusion
- composition-gap-blindness
- ownership-boundary-gap-ignored
- generic-cannot-do-label-substitutes-taxonomy
- hidden-affordance-invention
- downstream-ignores-gap-packets
- no-bypass in narrow slice

## Why A02 is not a planner proxy
- A02 consumes typed demand packets + A01 canonical affordances only.
- Planner deadend markers are allowed as metadata but not used as missing-capability proof.

## A01 dependency
- A02 consumes A01 canonical ontology snapshot.
- If A01 canonical surface is missing, A02 emits no-clean-coverage/insufficient-basis path instead of fabricating gaps.

## Load-bearing gap taxonomy
- Subject tick gate consumes typed counts:
  - missing / blocked / partial / composition / ownership-boundary / no-clean coverage.
- Basis-gated default detours are enforced only with explicit A02 demand basis.

## Composition and ownership handling
- Composition support exists in narrow form (covered-by-composition vs composition gap/unverified).
- Ownership-boundary gap is explicit and routed separately from missing internal capability.

## Strengthened typed-shape-over-token proof
- Added integration contrast with same checkpoint envelope and same required-action shell (`require_a02_gap_packet_consumer`) but different typed A02 shape (composition enabled vs disabled), producing different downstream acceptance.

## Narrow hardening pass closures
- Planner/low-confidence shortcut mediation is now explicit:
  - `planner_deadend_signal` and `low_confidence_signal` are threaded as non-authoritative evidence refs only.
  - Deterministic owner contrast proves those signals cannot convert covered demand into `missing_affordance`.
- Decorative taxonomy risk reduced:
  - `LOW_RELIABILITY_AFFORDANCE` branch now returns explicit non-missing gap for low-reliability controllability.
  - `RESOURCE_BLOCKED_GAP` branch now returns explicit non-missing gap for resource/mode-blocked availability.
  - `CONTESTED` status is now bound to real multi-candidate ambiguity (conflicting preconditions/channels), not blanket contested validity.
- Blocked-path owner assertions are strict enum checks (no permissive set-membership fallback).

## Anti-rescan anchors
- `src/substrate/a02_capability_gap_detection/*`
- `src/substrate/subject_tick/update.py` A02 checkpoint block
- `src/substrate/subject_tick/policy.py` A02 gate block
- `src/substrate/runtime_topology/policy.py` A02 graph/checkpoint/surface wiring
- `src/substrate/runtime_tap_trace.py` A02 allowlist fields

## Known narrow limits
- Map-wide A02 consumer migration not claimed.
- Full planner integration not claimed.
- Capability acquisition/discovery not claimed.
