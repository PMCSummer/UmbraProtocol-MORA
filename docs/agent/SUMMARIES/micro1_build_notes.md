# MICRO1 Build Notes

## Scope
Strict BUILD pass for MICRO1 owner seam only. No subject_tick/AP01/ACP01/AB/UMWELT/K-SURF1 semantic mutation.

## Files added/changed
- `src/substrate/micro1_micro_operation_frame/__init__.py`
- `src/substrate/micro1_micro_operation_frame/models.py`
- `src/substrate/micro1_micro_operation_frame/policy.py`
- `src/substrate/micro1_micro_operation_frame/telemetry.py`
- `src/substrate/micro1_micro_operation_frame/downstream_contract.py`
- `src/substrate/micro1_micro_operation_frame/fixtures.py`
- `tests/substrate/test_micro1_micro_operation_frame_build/test_micro1_micro_operation_frame_build.py`
- `tools/micro1_micro_operation_demo.py`
- `docs/adr/ADR-MICRO1-micro-operation-frame.md`
- `docs/agent/EXPERIMENTS/micro1_micro_operation_contract.md`

## Inspected surfaces
- UMWELT0 contact/action/effect/source models.
- CONTACT-PROJECTION-GATE basis/channel outputs.
- UMWELT-S action-surface/ref/channel declarations.
- K-SURF1 hint/slot/provider outputs and non-authoritative boundaries.
- ACP01 candidate basis models.
- AP01 request publication packet models.
- AB-INT input/output envelope surfaces.
- A01/A02/A03/A04 affordance/capability model surfaces.

## Model/policy summary
- Added typed `MicroOperationFrame`, `MicroOperationBasis`, `MicroOperationConstraintSet`, `MicroOperationExpectedEffectSet`, `MicroOperationLineage`, `MicroOperationResidueFrame`.
- Added `MicroOperationGraph` with bounded dependency edges and unverified intermediate blocking.
- Added status lattice and validation result model with counters.
- Enforced hard-false authority flags for action/publication/execution/fact/cause/value/maturity/automation/goal/hidden-inference.
- Enforced:
  - public basis requirement;
  - expected-effect requirement;
  - AP01 reference-only lineage;
  - no direct AP01/world emission;
  - macro-action decomposition requirement;
  - residue preservation on failure/block.

## Fixtures
- `inspect_unknown_resource_fixture`
- `move_toward_resource_fixture`
- `use_station_candidate_fixture`
- `store_resource_fixture`
- `repair_check_fixture`
- `provider_hint_basis_fixture`
- `quest_objective_blocked_fixture`
- `macro_factory_action_blocked_fixture`
- `ap01_lineage_reference_fixture`
- `failed_operation_residue_fixture`
- `effect_without_request_unresolved_fixture`
- `bounded_graph_fixture`
- `hidden_precondition_rejected_fixture`

## Tests
- Added dedicated MICRO1 build test suite covering required operation, lineage, residue, macro-decomposition, multichannel basis, and bounded graph falsifiers/ablations.

## Limitations
- No operation selection policy.
- No AP01 publication behavior in MICRO1.
- No WORLD0 runtime loop.
- No COST1 comparison integration.
- No ACTLEARN1/OPTION1 maturity progression.
- No durable runtime memory integration.

## Next recommended phase
Prefer `COST1` before `WORLD0` smoke pass. If strategic memory policy is prioritized, perform memory-boundary design discussion first.
