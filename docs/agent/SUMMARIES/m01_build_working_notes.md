# M01 Build Working Notes (Narrow Frontier Slice)

## Contour Placement
- Inserted checkpoint: `rt01.m01_homeostatic_salience_imprint_checkpoint`
- Placement: after `rt01.w01_bounded_world_loop_checkpoint`, before `rt01.outcome_resolution_checkpoint`

## Files Added
- `src/substrate/m01_homeostatic_salience_imprint/__init__.py`
- `src/substrate/m01_homeostatic_salience_imprint/models.py`
- `src/substrate/m01_homeostatic_salience_imprint/policy.py`
- `src/substrate/m01_homeostatic_salience_imprint/downstream_contract.py`
- `src/substrate/m01_homeostatic_salience_imprint/telemetry.py`
- `tests/substrate/m01_homeostatic_salience_imprint_testkit.py`
- `tests/substrate/test_m01_homeostatic_salience_imprint_build/test_m01_homeostatic_salience_imprint_build.py`
- `tests/substrate/test_subject_tick_build/test_m01_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_m01_runtime_topology_integration.py`
- `tools/m01_imprint_demo.py`
- `tests/tools/test_m01_imprint_demo.py`
- `docs/adr/ADR-M01-homeostatic-salience-imprint.md`

## Files Updated (Narrow Integration)
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Mechanistic Notes
- M01 is a typed regulatory-memory-economics bias seam, not full memory.
- Strong imprint requires typed regulatory delta + temporal coupling + attribution basis.
- Novelty/recency/outcome hints alone do not promote strong imprint.
- Recovery/relief paths are first-class and produce positive bounded bias.
- Contested timing cannot promote strong imprint and is explicitly capped to bounded/weak paths.
- Transfer limits are emitted on all imprint packets to prevent overgeneralization.
- Lifecycle adjustment path is typed (`reinforce`, `decay`, `keep_narrow_scope_only`, `downgrade_due_to_attribution_change`).
- Reinforcement is bounded by structural overlap (affected axes + sign); non-overlapping priors do not trigger reinforcement.
- Downstream consumer view now carries typed `affected_axes` and `transfer_limits`.

## Falsifier-Oriented Checks Implemented
- Same semantic trace, different regulatory delta -> different imprint class.
- Temporal/attribution downgrades block shortcut promotion.
- Mixed multi-axis effects stay structured and do not collapse to one generic importance scalar.
- Same checkpoint envelope with different typed M01 state changes downstream gate usability.
- No explicit M01 basis creates no default M01 detour pressure.
- Contested timing cap prevents strong imprint promotion even under strong regulatory deltas.
- Non-overlapping prior imprint negative-control blocks reinforcement escalation.

## Intentionally Out of Scope
- M02 predictive relevance channel.
- M03 pruning/compaction/reactivation lifecycle system.
- Full memory retrieval/replay orchestration.
- Map-wide memory migration.
