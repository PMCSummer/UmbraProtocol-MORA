# ADR-P02 Intervention Episode Layer Licensed Action Trace

## Status
Accepted (frontier RT01-hosted slice)

## Decision
Introduce `P02` as a separate typed runtime segment that constructs explicit intervention episode records from licensed-action snapshots, execution events, outcome evidence, boundary decisions, and residue.

`P02` is wired in RT01 contour after `C06` and before bounded outcome resolution, with checkpoint:
- `rt01.p02_intervention_episode_checkpoint`

## Mechanistic Scope (Built)
- Typed episode artifacts:
  - episode boundary (`included/excluded` events + ambiguity)
  - license linkage and overrun detection
  - execution status vs outcome verification status
  - episode status (including `awaiting_verification`, `partial`, `blocked`, `overran_scope`)
  - residue and side-effect carryover
- Require-path enforcement:
  - `require_p02_episode_consumer`
  - `require_p02_boundary_consumer`
  - `require_p02_verification_consumer`
- Basis-gated default-path detours:
  - `default_p02_awaiting_verification_detour`
  - `default_p02_possible_overrun_detour`
  - `default_p02_residue_followup_detour`
- Typed downstream gate consumption in `subject_tick/policy.py` (not token-only).
- Seam-honesty decision:
  - direct `p01_result` / `r05_result` modulation is **not** claimed in current P02 slice;
  - direct inputs were removed from P02 policy entrypoint because they were not causally load-bearing for P02 verdicts;
  - any project/protective influence at this seam is mediated upstream (via V01/V02/V03/C06 artifacts), not via direct P02-side modulation.

## Explicit Non-Claims
- No action licensing authority (handled upstream by `V01`).
- No project formation authority (handled upstream by `P01`).
- No map-wide intervention lifecycle governance.
- No external success proof without explicit evidence.
- No retention/memory-write authority.
- No replacement of raw logging; this is a typed episode layer.

## Why Separate P02 Seam
Without P02, downstream must infer episode closure from local emission/output artifacts. P02 introduces explicit distinction between:
- attempted/emitted,
- executed,
- observed,
- verified,
and prevents completion inflation when verification is missing.

## Open Seams Left Intentionally
- Deeper external outcome attestation remains downstream.
- Map-wide cross-episode continuity policy remains downstream.
- Long-horizon retention/scheduling remains outside P02.
