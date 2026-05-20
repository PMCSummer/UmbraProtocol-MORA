# COST1 Build Notes

## Scope
Strict COST1 build only. No mutation of subject_tick/AP01/ACP01/AB-INT/UMWELT0/CONTACT-PROJECTION-GATE/UMWELT-S/K-SURF1/MICRO1.

## Files added/changed
- `src/substrate/cost1_action_cost_efficiency/__init__.py`
- `src/substrate/cost1_action_cost_efficiency/models.py`
- `src/substrate/cost1_action_cost_efficiency/policy.py`
- `src/substrate/cost1_action_cost_efficiency/telemetry.py`
- `src/substrate/cost1_action_cost_efficiency/downstream_contract.py`
- `src/substrate/cost1_action_cost_efficiency/fixtures.py`
- `tests/substrate/test_cost1_action_cost_efficiency_build/test_cost1_action_cost_efficiency_build.py`
- `tools/cost1_action_cost_demo.py`
- `docs/adr/ADR-COST1-action-cost-efficiency.md`
- `docs/agent/EXPERIMENTS/cost1_action_cost_contract.md`

## Inspected surfaces
- MICRO1 operation/status/lineage/residue models.
- K-SURF1 provider hint/source/conflict contracts.
- UMWELT0 source/effect/uncertainty/lossiness and authority boundaries.
- CONTACT-PROJECTION-GATE channel/basis passthrough contracts.
- UMWELT-S channel/ref/provider declaration constraints.
- AB7/P15/P16/P17 evidence and no-automation boundaries.

## Model/policy summary
- Added multidimensional `ActionCostDimension` and `ActionCostVector`.
- Added evidence class discipline (`observed`, `estimated`, `provider_declared`, `inferred`, `unknown`).
- Added `DeclaredObservedCostDelta` and mismatch residue preservation.
- Added `ThroughputSupportFrame` with repetition-gated support statuses.
- Added `CostComparisonFrame` with per-dimension lower/higher/unknown breakdown.
- Enforced no selection/AP01/world/value/maturity authority flags.
- Blocked hidden/scenario/backend cost payloads, scalar-only hiding, and unknown-as-zero coercion.

## Fixtures
- material vs energy tradeoff
- provider-declared cost
- observed cost
- unknown dimension
- scalar hiding blocked
- risk vs material
- setup time
- tool wear
- station occupation
- throughput single/repeated
- declared-observed mismatch
- comparison no action
- hidden backend blocked
- cost hint permission blocked
- value assignment blocked

## Tests
Added dedicated COST1 suite with required and hardening cases for evidence class integrity, mismatch residue, throughput repetition, no permission lift, and no authority leakage.

## Limitations
- No action selection.
- No AP01 publication.
- No WORLD0 runtime loop.
- No P17B execution.
- No ACTLEARN1/OPTION1 learning/maturity.
- No live throughput measurement loop.
- No durable runtime memory policy here.

## Next recommended phase
WORLD0 smoke integration or P17B, depending integration priority.
