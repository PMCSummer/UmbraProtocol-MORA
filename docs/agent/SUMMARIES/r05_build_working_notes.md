# R05 Build Working Notes (no-rescan anchor)

Purpose: keep minimal implementation context for `R05 // Appraisal-sovereign protective regulation` so codegen can continue without broad repo rescan after context compression.

## Scope lock
- Mode: `BUILD`
- Target: narrow RT01-hosted shim only
- Placement required: `... -> O03 -> P01 -> O04 -> R05 -> bounded_outcome_resolution -> ...`
- New checkpoint required: `rt01.r05_protective_regulation_checkpoint`
- Do not implement: map-wide safety/controller/planner/memory/legal-moral layers

## Seam / contract references already read
- `docs/seams/R05.seam.md`
- `docs/seams/RT01.seam.md`
- `docs/agent/RT01_CONTOUR_MAP.md`
- `docs/agent/SUMMARIES/subject_tick_update.map.md`
- `docs/agent/SUMMARIES/runtime_topology_policy.map.md`

## Existing pattern to mirror
- O04 package as template:
  - `src/substrate/o04_rupture_hostility_coercion/models.py`
  - `src/substrate/o04_rupture_hostility_coercion/policy.py`
  - `src/substrate/o04_rupture_hostility_coercion/downstream_contract.py`
  - `src/substrate/o04_rupture_hostility_coercion/telemetry.py`
  - `src/substrate/o04_rupture_hostility_coercion/__init__.py`
- O04 integration pattern:
  - `src/substrate/subject_tick/update.py` (O04 block + checkpoint + taps + required/default detours)
  - `src/substrate/subject_tick/models.py` (context flags, restriction codes, state summary fields, result field)
  - `src/substrate/subject_tick/policy.py` (checkpoint + typed-semantic downstream restrictions)
  - `src/substrate/runtime_topology/policy.py` (order/nodes/edges/checkpoints/hooks/surfaces)
  - `src/substrate/runtime_tap_trace.py` (module allowlist fields)
- O04 tests as template:
  - `tests/substrate/o04_rupture_hostility_coercion_testkit.py`
  - `tests/substrate/test_o04_rupture_hostility_coercion_build/test_o04_rupture_hostility_coercion_build.py`
  - `tests/substrate/test_subject_tick_build/test_o04_subject_tick_integration.py`
  - `tests/substrate/test_runtime_topology_build/test_o04_runtime_topology_integration.py`

## Confirmed current anchor points (for direct edits)
- `src/substrate/subject_tick/update.py`
  - O04 block starts around lines `3550+`
  - O04 checkpoint write: `rt01.o04_rupture_hostility_coercion_checkpoint` around `3745+`
  - Bounded outcome block starts right after O04 checkpoint
  - State assembly includes O04 summary fields around `4440+`
  - `SubjectTickResult(...)` return includes `o04_result` around `4559`
  - attempted paths constant includes `"subject_tick.evaluate_o04_rupture_hostility_coercion"`
- `src/substrate/subject_tick/policy.py`
  - O04 downstream consumption block around `880-980`
- `src/substrate/subject_tick/models.py`
  - Restriction enum already has O04 entries
  - Context contains O04 flags and inputs:
    - `prior_o04_state`
    - `require_o04_*`
    - `disable_o04_enforcement`
    - `o04_interaction_events`
  - State has O04 summary defaults
  - Result includes `o04_result`
- `src/substrate/runtime_topology/policy.py`
  - Runtime order currently includes `... O03, P01, O04, RT01`
  - Node/checkpoint/surface lists include O04, no R05 yet
  - `_context_has_ablation_flags` includes `disable_o04_enforcement`, no `disable_r05_enforcement` yet
- `src/substrate/runtime_tap_trace.py`
  - module allowlist has O04 fields, no R05 yet
- Trace/runtime topology tests already assert ordering/allowlist with O04 as last hosted social segment before bounded outcome.

## Known gap relevant to R05 inputs
- No concrete G08 package/surface found in current `src/substrate` search.
- For this build pass, use narrow hosted typed appraisal hints in `SubjectTickContext` (explicitly bounded), plus O04/P01 basis.

## Files to add for R05
- `src/substrate/r05_appraisal_sovereign_protective_regulation/models.py`
- `src/substrate/r05_appraisal_sovereign_protective_regulation/policy.py`
- `src/substrate/r05_appraisal_sovereign_protective_regulation/downstream_contract.py`
- `src/substrate/r05_appraisal_sovereign_protective_regulation/telemetry.py`
- `src/substrate/r05_appraisal_sovereign_protective_regulation/__init__.py`
- `tests/substrate/r05_appraisal_sovereign_protective_regulation_testkit.py`
- `tests/substrate/test_r05_appraisal_sovereign_protective_regulation_build/test_r05_appraisal_sovereign_protective_regulation_build.py`
- `tests/substrate/test_subject_tick_build/test_r05_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_r05_runtime_topology_integration.py`
- `docs/adr/ADR-R05-appraisal-sovereign-protective-regulation.md`

## Existing files to edit (approved narrow surfaces)
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Required R05 require-path flags
- `require_r05_protective_state_consumer`
- `require_r05_surface_inhibition_consumer`
- `require_r05_release_contract_consumer`

## Required R05 behavior to encode
- threat-to-regulation transform (typed, inspectable modes)
- bounded sovereign override (surface-bounded, not global)
- surface-specific inhibition (not generic caution-only)
- release + hysteresis (non-sticky, deterministic downgrade/release path)
- weak/insufficient basis fallback (no jump to hard override)
- anti-shortcut: no tone-only shutdown

## R05 trace module contract (to add)
- module: `r05_appraisal_sovereign_protective_regulation`
- steps: `enter`, `decision`, `blocked`, `exit`
- allowlist fields target:
  - `protective_mode`
  - `authority_level`
  - `trigger_count`
  - `inhibited_surface_count`
  - `override_active`
  - `release_pending`
  - `regulation_conflict`
  - `insufficient_basis_for_override`
  - `downstream_consumer_ready`
  - `project_override_active`

## Minimal test matrix (must be deterministic)
- Core/build:
  - same wording + different structure => different mode
  - polite structural threat > rude low-basis case
  - weak basis => vigilance/candidate, no hard override
  - release/hysteresis prevents stickiness
- Subject tick integration:
  - R05 order/checkpoint after O04, before bounded outcome
  - require-path detour when consumer missing
  - default-path only with real protective basis
  - typed semantics affect downstream (not token-only)
  - no-trigger => no R05 default friction
  - release evidence => deterministic downgrade/release consequence
- Runtime topology + observability:
  - order/node/checkpoint/source-of-truth/hook include R05
  - tap allowlist and ordering include R05

## ADR convention observed (use same style)
- Recent ADRs follow:
  - `# ADR-<PHASE> <title>`
  - `## Status`
  - `## Context`
  - `## Decision`
  - `## Inputs`
  - `## Outputs`
  - `## Narrow Downstream Effect Implemented Now`
  - `## Authority Boundary`
  - `## Non-Claims`
  - `## Current Limitations / Open Falsifiers`
- Keep claim strictly frontier-level, no inflation.
