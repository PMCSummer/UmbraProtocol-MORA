# COST1 Action Cost Contract

## Purpose
Demonstrate bounded multidimensional cost comparison artifacts without selection/publication/execution/value authority.

## Demo cases
- `material_vs_energy_tradeoff`
- `provider_declared_cost`
- `observed_cost`
- `unknown_dimension`
- `scalar_hiding_blocked`
- `risk_vs_material`
- `setup_time_tradeoff`
- `tool_wear`
- `station_occupation`
- `throughput_single_run`
- `throughput_repeated`
- `declared_observed_mismatch`
- `cost_comparison_no_action`
- `hidden_backend_cost_blocked`
- `cost_hint_permission_blocked`
- `value_assignment_blocked`

## Valid examples
- Separate material/energy/time vectors with explicit evidence kind.
- Provider-declared time/energy remains declared, not observed.
- Observed dimensions require effect/observation refs.
- Throughput marked provisional for single trace, stronger only with repetition.

## Blocked examples
- Scalar-only score attempting to hide dimension breakdown.
- Hidden/backend/scenario cost payload.
- Cost artifact trying to authorize action/goal.
- Value assignment attempt from cheap/efficient labels.

## Declared-vs-observed examples
- Delta artifacts preserve declared ref + observed ref + mismatch residue.
- Declared cost is not overwritten by observed cost.

## Throughput examples
- `single_observation_only` for one trace.
- `supported_repeated` only after repeated traces.

## Why COST1 is not planner/optimizer/action selector/value module
- COST1 only computes bounded comparison artifacts.
- It cannot select a candidate, emit AP01, submit world action, assign intrinsic value, or claim final efficiency truth.
