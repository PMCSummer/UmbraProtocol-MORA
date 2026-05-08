# A01 Build Working Notes (frontier-hosted narrow slice)

## Lawful narrow insertion point
- Chosen insertion point: inside existing A-line frontier segment, between `S_MINIMAL` and `A_LINE_NORMALIZATION`.
- Checkpoint: `rt01.a01_affordance_ontology_cleanup_checkpoint`.
- Rationale: keeps scope narrow and seam-honest with current RT01 topology, avoids introducing map-wide phase migration.

## Exact targeted falsifiers
- `naming-cleanup-instead-of-ontology-cleanup`
- `pure-string-dedup-masquerades-as-canonicalization`
- `manual-whitelist-masquerades-as-cleanup`
- `same-label-different-precondition-confusion`
- `same-outcome-different-control-confusion`
- `mode-action-class-collapse`
- `false-control-promise-from-contaminated-affordance`
- `downstream-still-uses-legacy-local-labels`
- `silent-deletion-of-messy-affordances`
- `no-bypass in narrow slice`

## Why this is not string dedup
- Merge occurs only under strict typed equivalence (class/preconditions/effect/controllability/channel alignment).
- Same-label precondition/control/class conflicts are split or contested, not merged by label.

## Why this is not whitelist curation
- Messy/conflicted candidates are preserved as contested entries with explicit ledger records.
- Deprecated/unavailable/narrowed outputs are first-class and not silently dropped.

## Where class boundary separation became mechanistically real
- Canonical entries keep explicit `A01AffordanceClass` taxonomy.
- Same-label class conflict generates contested+split records instead of a generic action bucket.

## Where canonical IDs became downstream load-bearing
- `subject_tick` consumes A01 typed counters/readiness fields and enforces A01 require/default path restrictions.
- Legacy-label-only bypass triggers explicit A01 detour and can block continuation in narrow RT01 slice.
- Granularity parent-child relations can degrade downstream usability in bounded routing.

## Anti-rescan note
- For A01 follow-ups, reread only:
  - `src/substrate/a01_internal_affordance_ontology_cleanup/*`
  - `src/substrate/subject_tick/update.py` A01 checkpoint block
  - `src/substrate/subject_tick/policy.py` A01 gate block
  - `src/substrate/runtime_topology/policy.py` A01 checkpoint/surface wiring
  - `src/substrate/runtime_tap_trace.py` A01 allowlist entry

## Known limits after build
- Map-wide dual-ontology migration remains open.
- Full planner integration over canonical IDs remains open.
- Creative affordance discovery remains out of scope.

## Narrow hardening pass closures
- `source_lineage` is now threaded end-to-end in A01 typed outputs:
  - ledger + telemetry + contract view now publish `source_lineage_count` / `source_lineage_complete`.
  - explicit-basis + partial lineage now triggers bounded A01 detour instead of silent pass-through.
- Schema-façade drift removed:
  - dormant `parent_label_hint` and `contaminated_controllability` fields were removed from A01 candidate schema/testkit because they had no mechanistic role in this slice.
- Contested/deprecated downstream proofs strengthened:
  - subject_tick integration now has explicit default-detour tests for contested canonicalization and deprecated/context-invalid affordances.
- Typed-shape-over-token proof strengthened:
  - new integration test keeps A01 checkpoint token shell constant (`require_a01_canonical_affordance_consumer`) while varying canonical-id coverage shape, and observes different downstream gate outcome.
