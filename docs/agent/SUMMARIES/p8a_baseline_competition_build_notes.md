# P8A Build Notes

## Files added
- `experiments/embodied_playground/baselines.py`
- `experiments/embodied_playground/baseline_runner.py`
- `experiments/embodied_playground/baseline_metrics.py`
- `experiments/embodied_playground/baseline_falsifiers.py`
- `tools/embodied_baseline_competition_demo.py`
- `tests/experiments/test_embodied_playground_baselines.py`
- `tests/experiments/test_embodied_playground_baseline_runner.py`
- `tests/experiments/test_embodied_playground_baseline_metrics.py`
- `tests/experiments/test_embodied_playground_baseline_falsifiers.py`
- `tests/tools/test_embodied_baseline_competition_demo.py`
- `docs/agent/EXPERIMENTS/embodied_playground_p8a_baseline_competition_harness.md`

## Baselines
- random public baseline
- action-space greedy baseline
- visible-object heuristic baseline
- drive-only baseline
- hidden oracle (diagnostic unfair)
- direct bridge bypass (boundary-violation baseline)

## Metrics
Harness computes success/invalid/abstention/shortcut/provenance/boundary/recovery/effect-feedback/overclaim/matched-information/differentiator metrics.

## Validation
P8A tests cover baseline protocol behavior, competition runner behavior, metric computation, falsifiers, and demo CLI output.

## Known limitations
- Baselines are intentionally narrow and heuristic.
- No LLM/RL baseline in this stage.
- GridWorld-bounded comparison only.
- Diagnostic direct-bridge path is not subject evidence.

## Next steps
- Add stronger ablation matrix over seams in later stage.
- Add broader cross-backend baseline comparison after new backends exist.
