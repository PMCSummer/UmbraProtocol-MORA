# W06 Build Working Notes

## Phase
W06 // Error-driven revision / regularity humility.

## Contour Placement
`W01 -> W02 -> W03 -> W04 -> W05 -> W06 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w06_error_driven_revision_checkpoint`

## Implemented Narrow Slice
- Added typed W06 owner package for revision-consequence routing (no correction execution).
- Added consequence matrix over mismatch/contradiction/protection/authority routes.
- Added W06.1 revision ledger with confidence-drop policy and downstream permission effects.
- Added residual uncertainty record retained across contested/downgrade/revalidate routes.
- Added anti-paralysis route for repeated revalidation without progress.
- Added identity routing (`split/duplicate/replacement/unknown_lineage`) and continuity claim blocking.
- Added claim-block propagation and downstream revision permission packet.
- Added correction candidate seam with:
  - `execution_prohibited=True`
  - required evidence
  - future seam ref.
- Narrow hardening pass:
  - enforced `allowed_revision_scopes` against selected `revision_scope` with explicit fail-closed reason codes;
  - tightened ambiguous-route semantics: contested/no-clean markers, competing candidates preservation, confidence cap for suspected correction candidate;
  - strengthened blocked-claim consumer obedience: blocked claim plus retained residue required, fail-closed quarantine/revalidation when residue markers are missing.

## Integration
- `subject_tick/update.py`:
  - W06 executed after W05 and before M01.
  - emits `rt01.w06_error_driven_revision_checkpoint`
  - projects compact `w06_*` fields into `SubjectTickState`.
- `subject_tick/policy.py`:
  - consumes typed `w06_*` fields
  - emits route-specific restrictions for claim block/revalidate/residue/identity/anti-paralysis/quarantine.
- `runtime_topology/policy.py`:
  - W06 checkpoint and source-of-truth surface required in production contour
  - `disable_w06_enforcement` rejected via production ablation guard.
- `runtime_tap_trace.py` + trace tests:
  - allowlist only compact W06 fields
  - order includes `W05 -> W06 -> M01`
  - no raw W06 owner object leakage.

## Files Added
- `src/substrate/w06_error_driven_revision/__init__.py`
- `src/substrate/w06_error_driven_revision/models.py`
- `src/substrate/w06_error_driven_revision/policy.py`
- `src/substrate/w06_error_driven_revision/downstream_contract.py`
- `src/substrate/w06_error_driven_revision/telemetry.py`
- `tests/substrate/w06_error_driven_revision_testkit.py`
- `tests/substrate/test_w06_error_driven_revision_build/test_w06_error_driven_revision_build.py`
- `tests/substrate/test_subject_tick_build/test_w06_subject_tick_integration.py`
- `tests/substrate/test_runtime_topology_build/test_w06_runtime_topology_integration.py`
- `tools/w06_error_driven_revision_demo.py`
- `tests/tools/test_w06_error_driven_revision_demo.py`
- `docs/adr/ADR-W06-error-driven-revision-regularity-humility.md`

## Files Changed
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- `tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py`
- `tests/tools/test_tick_observability_trace.py`

## Limitations / Out of Scope
- No W06 correction execution.
- No learner/update writer.
- No memory/policy/schema/prior mutation.
- No planner/action selector.
- S03/M03/C05 executable compatibility depends on path availability; report honestly.
- No correction execution/update execution was added in hardening.
