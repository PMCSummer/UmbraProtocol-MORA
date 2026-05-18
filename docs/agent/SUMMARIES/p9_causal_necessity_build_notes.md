# P9 Build Notes

## Files added
- `experiments/embodied_playground/causal_necessity.py`
- `experiments/embodied_playground/ablation_runner.py`
- `experiments/embodied_playground/strict_mode_runner.py`
- `experiments/embodied_playground/causal_necessity_falsifiers.py`
- `tests/experiments/test_embodied_playground_causal_necessity.py`
- `tests/experiments/test_embodied_playground_ablation_runner.py`
- `tests/experiments/test_embodied_playground_strict_mode_runner.py`
- `tests/experiments/test_embodied_playground_causal_necessity_falsifiers.py`
- `tools/embodied_causal_necessity_demo.py`
- `tests/tools/test_embodied_causal_necessity_demo.py`
- `docs/agent/EXPERIMENTS/embodied_playground_p9_strict_no_auto_builder_causal_necessity.md`

## Ablations implemented
- ACP01/AP01 suppression
- drive/public-object/action-surface/proximity/capacity basis removals
- effect-feedback and residue-feedback suppression overlays
- hidden/eval substitution attempt
- permission and prediction/permission separation checks

## Strict mode behavior
- compares upstream basis flow vs downstream candidate/request/effect continuation
- flags fabricated basis, hidden/eval substitution, and unexpected success under ablation

## Tests
- causal-necessity models/metrics/verdicts
- ablation behavior checks
- strict mode checks
- falsifier negative controls
- demo CLI checks

## Known limitations
- strict enforcement is experiment-side runtime validation, not a full static proof.
- checks for W04/W05/W06-like gates are proxy-level through exposed embodied basis.
- evaluation remains GridWorld-bounded.

## Next steps
- extend ablation matrix across additional backends when available
- integrate stronger cross-run statistical summaries once broader scenario families exist
