# AB1 Event Digest Build Notes

## Inventory result
- Reused surfaces:
  - `src/substrate/w06_error_driven_revision/*`
  - `src/substrate/s01_efference_copy/*`
  - `src/substrate/s02_prediction_boundary/*`
  - `src/substrate/world_adapter/*`
  - `src/substrate/world_entry_contract/*`
  - `experiments/embodied_playground/body_action_proof.py`
  - `experiments/embodied_playground/causal_necessity*`
- Gap identified:
  - no dedicated typed AB1 event digest owner contract that emits bounded anomaly digest without causal closure.

## Files added
- `src/substrate/ab01_event_digest/__init__.py`
- `src/substrate/ab01_event_digest/models.py`
- `src/substrate/ab01_event_digest/policy.py`
- `src/substrate/ab01_event_digest/downstream_contract.py`
- `src/substrate/ab01_event_digest/telemetry.py`
- `tests/substrate/test_ab01_event_digest_build/test_ab01_event_digest_build.py`
- `experiments/embodied_playground/ab1_event_digest_probe.py`
- `tests/experiments/test_embodied_playground_ab1_event_digest_probe.py`
- `tools/ab1_event_digest_demo.py`
- `tests/tools/test_ab1_event_digest_demo.py`
- `docs/adr/ADR-AB01-event-digest-anomaly-compression.md`
- `docs/agent/EXPERIMENTS/embodied_playground_ab1_event_digest.md`

## Mechanism
- AB1 consumes public refs and compact mismatch/residue/effect markers.
- AB1 emits typed digest events only.
- AB1 enforces non-causal closure and no action/request authority.

## Tests
- substrate AB1 owner tests for mismatch/block/delay/ref-integrity/no-hidden/no-scenario/no-cause boundaries
- embodied probe tests over P10 blocked/pickup traces
- demo CLI tests for listed cases and claim-discipline output

## Known limitations
- AB1 is not AB2/AB3/AB4.
- AB1 does not generate hypotheses.
- AB1 does not score causes.
- AB1 does not select epistemic actions.

## Next relation (AB2)
- AB2 may consume AB1 digests to seed bounded hypothesis candidates.
- AB1 remains non-causal and signal-compression-only.
