# A04 Build Working Notes (Narrow Frontier Slice)

## Insertion point
- A04 checkpoint inserted in RT01 sequence after `P04` and before bounded outcome resolution.
- Checkpoint id: `rt01.a04_external_affordance_binding_checkpoint`.

## Files touched
- `src/substrate/a04_external_affordance_binding/*` owner package
- `src/substrate/subject_tick/models.py`
- `src/substrate/subject_tick/update.py`
- `src/substrate/subject_tick/policy.py`
- `src/substrate/runtime_topology/policy.py`
- `src/substrate/runtime_tap_trace.py`
- A04 owner/integration/topology/trace tests

## Closed falsifiers in this pass
- authority-less or scaffold-absent external candidate promoted as admitted binding
- object scaffold intake promoted to mature object claim
- contradictory scaffold packets silently resolved
- revoked scaffold still treated as active
- checkpoint/telemetry-only A04 with no gate impact

## Why this is narrow and staged
- A04 remains staged scaffold only.
- Entity-centric admission is supported; object scaffolds remain explicitly non-mature.
- No planner replacement, no policy selection, no execution, no map-wide world claim.

## A04 load-bearing surfaces
- Typed ledger decisions: admitted/blocked/contested/revoked with explicit reasons.
- Gate restrictions and consumer readiness are consumed by subject-tick downstream gate.
- Runtime tap trace exposes compact A04 fields only.

## Known limits (intentional)
- no map-wide migration
- no mature object perception
- no global object identity resolution
- no W-line completion claim
