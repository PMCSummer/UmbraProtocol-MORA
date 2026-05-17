# AP01 Build Working Notes

## Build Intent
Add a narrow owner seam for subject-owned external action request publication without introducing planning or execution authority.

## Implemented Surfaces
- `src/substrate/ap01_subject_action_publication/models.py`
- `src/substrate/ap01_subject_action_publication/policy.py`
- `src/substrate/ap01_subject_action_publication/downstream_contract.py`
- `src/substrate/ap01_subject_action_publication/telemetry.py`
- `src/substrate/ap01_subject_action_publication/__init__.py`

## Subject Tick Integration
- `SubjectTickContext` now accepts optional AP01 candidate set input.
- `SubjectTickResult` now carries `ap01_result`.
- `SubjectTickState` now carries AP01 compact counters/flags.
- No AP01-driven world execution wiring added.

## Boundaries Preserved
- no W01-W06 owner behavior edits;
- no A01-A04 owner behavior edits;
- no P01-P04 owner behavior edits;
- no S01-S05 owner behavior edits;
- no world mutation from AP01.

## Remaining Gap
AP01 publishes bounded request packets only; downstream world bridge must execute or refuse and return effect evidence.
