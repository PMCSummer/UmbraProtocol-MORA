# ADR-S01: Bounded Efference Copy Comparator (Intended vs Observed Change)

## Status
Accepted for first bounded BUILD increment in RT01-local contour.

## Why This Layer Exists
- RT01 already executes bounded runtime contour with C04/C05 authority consumption, but lacked a typed pre-observation intended-vs-observed comparator surface.
- This increment materializes S01 as a real comparator layer between registered expected change and later observed change, without broad self/nonself rollout.

## Canonical Seams
- Owner build seam:
  - `build_s01_efference_copy(...) -> S01EfferenceCopyResult`
- Owner downstream contract seam:
  - `derive_s01_contract_view(...) -> S01ContractView`
  - `derive_s01_comparison_consumer_view(...) -> S01ComparisonConsumerView`
  - `require_s01_comparison_consumer_ready(...)`
  - `require_s01_prediction_validity_ready(...)`
- RT01 local checkpoint seam:
  - `rt01.s01_efference_copy_checkpoint`

## Bounded Mechanism Added
- Typed pre-observation registry:
  - forward-model packet (`intended_change`, `expected_consequence`, `action_context`, `timing_window`, `mismatch_hooks`)
  - pending predictions with expiry and contamination sensitivity
- Typed observed comparison window on commensurable axes:
  - mode token
  - world effect feedback
  - world confidence delta
- Typed comparison statuses:
  - `matched_as_expected`
  - `partial_match`
  - `magnitude_mismatch`
  - `direction_mismatch`
  - `latency_mismatch`
  - `expected_but_unobserved`
  - `unexpected_change_detected`
  - `comparison_blocked_by_contamination`
- Contamination and stale handling:
  - mixed-cause contamination blocks strong comparison path
  - stale/expired predictions are marked and cannot be reused as valid
- Attribution gate discipline:
  - predicted-compatible outcomes remain `predicted_compatible_only`
  - no strong self-attribution is granted in this slice
  - no post-hoc prediction fabrication is allowed

## RT01 Integration Scope
- S01 is inserted as RT01-local comparator checkpoint after C05 legality and before downstream S/T contour surfaces.
- RT01 consumes S01 through bounded path-affecting requirements only:
  - `require_s01_comparison_consumer`
  - `require_s01_unexpected_change_consumer`
  - `require_s01_prediction_validity_consumer`
- If required S01 consumer conditions are not met, RT01 enforces detour (`repair`/`revalidate`) rather than silently continuing.

## Authority Boundary
- S01 in this increment is comparator-only.
- S01 does not:
  - solve full self/nonself attribution,
  - perform global causal inference,
  - replace C04 arbitration semantics,
  - replace C05 legality semantics,
  - act as planner/executor/perception/world model layer.

## What Is Claimed
- A separate typed S01 package now exists.
- Pre-observation expectation registration is real and consumed before comparison.
- Intended-vs-observed comparison is typed and mismatch-graded.
- Contamination, latency, and stale prediction handling are load-bearing.
- RT01 has a real S01 checkpoint with path-affecting consumer requirements.

## What Is Not Claimed
- No S02/S03/S04/S05 rollout.
- No full selfhood or global attribution correctness claim.
- No repo-wide observation channel coverage claim.
- No learning/factorization/generalized anomaly engine claim.
