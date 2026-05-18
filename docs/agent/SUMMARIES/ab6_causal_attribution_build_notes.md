# AB6 Causal Attribution Build Notes

## Inventory results
- Inspected S05 seam/ADR and ownership perturbation (P11) implementation.
- Inspected AB1-AB5 owners and probes.
- Result: no dedicated AB6 integration seam existed; P11 was battery-only and S05 is broader multi-cause factorization in RT01 contour.

## Files added/changed
- Added:
  - `src/substrate/ab06_causal_attribution/__init__.py`
  - `src/substrate/ab06_causal_attribution/models.py`
  - `src/substrate/ab06_causal_attribution/policy.py`
  - `src/substrate/ab06_causal_attribution/downstream_contract.py`
  - `src/substrate/ab06_causal_attribution/telemetry.py`
  - `experiments/embodied_playground/ab6_causal_attribution_probe.py`
  - `tests/substrate/test_ab06_causal_attribution_build/test_ab06_causal_attribution_build.py`
  - `tests/experiments/test_embodied_playground_ab6_causal_attribution_probe.py`
  - `tools/ab6_causal_attribution_demo.py`
  - `tests/tools/test_ab6_causal_attribution_demo.py`
  - `docs/adr/ADR-AB06-self-world-causal-attribution.md`
  - `docs/agent/EXPERIMENTS/embodied_playground_ab6_causal_attribution.md`

## Mechanism
- AB6 consumes AP01/effect/frontier/update/event evidence refs and emits bounded attribution frame.
- Supports attribution kinds:
  - self_action
  - world_process
  - other_actor
  - delayed_self_effect
  - mixed_cause
  - unknown_cause
  - sensor_or_projection_error
- Preserves mixed/unknown under uncertainty and blocks overclaims.

## Tests
- substrate owner tests for falsifier boundaries and ablations.
- probe tests using P11 scenario evidence and AB5 relation.
- demo tests for required CLI coverage and claim discipline.

## Known limitations
- AB6 is bounded attribution, not final cause proof.
- AB6 does not update hypotheses (AB5 role).
- AB6 does not select epistemic actions (AB4 role).
- AB6 does not perform full self-model/theory-of-mind inference.

## Next relation (AB7/P12)
- AB7 may consume AB6 frames plus AB5 update trajectories for longer-horizon attribution stability checks.
- P12 may extend embodied perturbation integration over wider action/interaction regimes.
