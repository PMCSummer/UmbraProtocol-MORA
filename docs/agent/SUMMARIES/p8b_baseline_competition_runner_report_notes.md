# P8B Build Notes

## Scope
P8B upgrades P8A comparison core into structured reporting artifacts.

## Files changed
- `experiments/embodied_playground/baseline_runner.py`
- `experiments/embodied_playground/baseline_metrics.py`
- `experiments/embodied_playground/baseline_falsifiers.py`
- `experiments/embodied_playground/__init__.py`
- `tests/experiments/test_embodied_playground_baseline_runner.py`
- `tests/experiments/test_embodied_playground_baseline_metrics.py`
- `tests/experiments/test_embodied_playground_baseline_falsifiers.py`
- `tests/tools/test_embodied_baseline_competition_demo.py`
- `tools/embodied_baseline_competition_demo.py`

## Runner/report additions
- Added `BaselineCompetitionRun` structured artifact fields:
  - `mora_trace`, `baseline_traces`, `metric_summary`, `boundary_violation_summary`,
    `fairness_report`, `differentiator_summary`, `claim_safe_verdict`, `claim_boundary`.
- Added matrix mode via `run_baseline_competition_matrix`.
- Added claim-safe verdict enum with bounded non-overclaim outcomes.

## CLI/report additions
- `--report` for structured human-readable scenario report.
- `--matrix` for required scenario matrix execution.
- `--matrix --json` and `--matrix --report` supported.

## Falsifiers
- Added P8B report-level falsifiers for missing sections, unfair-accounting errors, overclaim language,
  missing matrix scenarios, and missing matched-information metric.

## Known limitations
- GridWorld-bound comparison only.
- No FSM/LLM/RL baselines in this stage.
- Report artifacts strengthen evidence accounting but do not imply consciousness/general autonomy.
