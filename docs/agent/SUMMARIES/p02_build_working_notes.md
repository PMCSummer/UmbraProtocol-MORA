# P02 Build Working Notes (Frontier RT01 Slice)

## Contour Placement
- Runtime order insertion: `... -> V03 -> C06 -> P02 -> RT01 bounded_outcome_resolution`
- Checkpoint: `rt01.p02_intervention_episode_checkpoint`

## Owner Surfaces
- `src/substrate/p02_intervention_episode_layer_licensed_action_trace/models.py`
- `src/substrate/p02_intervention_episode_layer_licensed_action_trace/policy.py`
- `src/substrate/p02_intervention_episode_layer_licensed_action_trace/downstream_contract.py`
- `src/substrate/p02_intervention_episode_layer_licensed_action_trace/telemetry.py`
- `src/substrate/p02_intervention_episode_layer_licensed_action_trace/__init__.py`

## Hard Constraints Implemented
- Separate execution vs verification semantics.
- Boundary construction includes explicit excluded-event rationale.
- License-link missing and possible/actual overrun are explicit typed fields.
- Residue persists (pending verification, side-effects, follow-up obligations).
- Completion is not inferred from emission alone.

## Require / Default Paths
- Require:
  - `require_p02_episode_consumer`
  - `require_p02_boundary_consumer`
  - `require_p02_verification_consumer`
- Default (basis-gated):
  - `default_p02_awaiting_verification_detour`
  - `default_p02_possible_overrun_detour`
  - `default_p02_residue_followup_detour`

## Typed Downstream Consumption
- `subject_tick/policy.py` reads P02 typed fields:
  - `p02_awaiting_verification`
  - `p02_overrun_detected`
  - `p02_residue_count`
  - `p02_partial_episode_count`
  - `p02_boundary_ambiguous`
  - `p02_license_link_missing`
- Includes same-envelope typed-shape divergence branch.

## Seam-Honesty Decision (Hardening)
- Direct `p01_result` and `r05_result` inputs were removed from P02 policy interface.
- Causal criterion used: no deterministic branch where direct `p01_result`/`r05_result` changed P02 boundary/status/residue or RT01 outcome class in the current narrow slice.
- Direct topology implications `P01 -> P02` and `R05 -> P02` were removed.
- Upstream modulation remains mediated through consumed typed artifacts (`V01`, `V02`, `V03`, `C06`) only.

## Intentional Non-Claims
- No map-wide episode ecosystem.
- No external success attestation beyond provided evidence.
- No retention/write semantics.
- No project formation or action licensing authority.

## Test Commands Used
- `pytest -q tests/substrate/test_p02_intervention_episode_layer_licensed_action_trace_build/test_p02_intervention_episode_layer_licensed_action_trace_build.py`
- `pytest -q tests/substrate/test_subject_tick_build/test_p02_subject_tick_integration.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_p02_runtime_topology_integration.py`
- `pytest -q tests/tools/test_tick_observability_trace.py`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `pytest -q tests/substrate/test_subject_tick_build`
