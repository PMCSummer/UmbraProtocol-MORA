# P03 Build Working Notes (RT01-hosted frontier slice)

## Contour placement
- Runtime order insertion: `... -> V03 -> C06 -> P02 -> P03 -> bounded_outcome_resolution`
- Checkpoint: `rt01.p03_credit_assignment_checkpoint`

## Owner surface
- `src/substrate/p03_long_horizon_credit_assignment_intervention_learning/models.py`
- `src/substrate/p03_long_horizon_credit_assignment_intervention_learning/policy.py`
- `src/substrate/p03_long_horizon_credit_assignment_intervention_learning/downstream_contract.py`
- `src/substrate/p03_long_horizon_credit_assignment_intervention_learning/telemetry.py`
- `src/substrate/p03_long_horizon_credit_assignment_intervention_learning/__init__.py`

## Seam-honesty notes
- Narrow direct seam set kept:
  - `P02` typed result (required)
  - `C06` typed result (required)
- Direct `P01` dependency intentionally not consumed in P03 policy for this slice:
  - no deterministic tested branch in this pass where direct `P01` object changes bounded P03 attribution outcome.

## Exact tested falsifiers
- Same immediate signal, different long-horizon outcome.
- Same later outcome, different confounder structure.
- Recency-bias adversarial contrast (earlier enabling vs later salient).
- Side-effect retention (primary gain + protective degradation).
- Verification ablation downgrade.
- Horizon within-window vs out-of-window contrast.
- No-update honesty (open window).
- Raw approval-only shortcut rejection.
- Same checkpoint envelope/required action with typed-shape downstream divergence.
- No-bypass contrast via `disable_p03_enforcement`.

## Closed
- `tests/substrate/p03_long_horizon_credit_assignment_intervention_learning_testkit.py` syntax repair:
  - closed unbalanced `cases` dict in `harness_cases()`.
- Conflict classification precision in `p03` policy:
  - `_build_conflict` now marks conflict only when:
    - explicit `conflicted=True`, or
    - verified `improved` and `degraded` coexist within the same `target_dimension`.
  - avoids false `UNRESOLVED` in side-effect retention branch where mixed attribution is lawful.
- Dedicated P03 build falsifiers all green.
- Subject-tick P03 integration falsifiers all green.
- Runtime-topology P03 integration falsifiers all green.
- Runtime topology baseline and observability trace baselines updated for P03 and green.

### Exact test commands/results
- `pytest -q tests\substrate\test_p03_long_horizon_credit_assignment_intervention_learning_build\test_p03_long_horizon_credit_assignment_intervention_learning_build.py`
  - result: `9 passed in 0.40s`
- `pytest -q tests\substrate\test_subject_tick_build\test_p03_subject_tick_integration.py`
  - result: `4 passed in 1.24s`
- `pytest -q tests\substrate\test_runtime_topology_build\test_p03_runtime_topology_integration.py`
  - result: `4 passed in 1.22s`
- `pytest -q tests\substrate\test_runtime_topology_build\test_runtime_topology_build.py`
  - result: `47 passed in 2.21s`
- `pytest -q tests\tools\test_tick_observability_trace.py`
  - result: `27 passed in 2.31s`

## Partial / open
- No map-wide claims made.
- No policy mutation path introduced in P03.
- Full cross-phase consumer ecology and broad causal discovery remain intentionally open by seam.
- ADR closure-note sync applied:
  - added explicit bounded-limits section in `ADR-P03-long-horizon-credit-assignment-intervention-learning.md`
  - no new strong claim introduced.

## Anti-rescan notes
- Reuse this file + `docs/agent/SUMMARIES/subject_tick_update.map.md` and `docs/agent/SUMMARIES/runtime_topology_policy.map.md` before rereading full owner files.
- For P03-only follow-ups, focus on:
  - `subject_tick/update.py` P02->P03->bounded block
  - `subject_tick/policy.py` P03 typed gate block
  - `runtime_topology/policy.py` P03 order/node/edge/checkpoint/surface
  - `runtime_tap_trace.py` P03 allowlist
