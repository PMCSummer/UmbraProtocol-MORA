# ADR-W03: Schema Consolidation / Everyday Prior Formation

## Status
Accepted for narrow BUILD slice.

## Decision
Introduce `W03` as a bounded schema-consolidation gate that consumes only typed `W02` regularity artifacts and emits typed schema candidates / everyday priors with explicit permission boundaries.

## Scope
W03 does:
- consolidate W02-supported regularities into bounded schema channels;
- keep support sets, negative evidence refs, authority scope, context scope, and temporal span;
- apply contradiction consequences operationally (invalidate/downgrade/revalidate/split/quarantine/block);
- emit stale/revalidation state and schema version records;
- emit machine-readable downstream permission packets with prohibited claims.

W03 does not:
- assert mature world truth;
- assert stable object identity beyond W02 evidence;
- implement common-sense/world ontology;
- implement planner/action selection;
- implement M03 memory lifecycle;
- implement W04 applicability deployment;
- inject language priors as world support.

## Contour Placement
`W01 -> W02 -> W03 -> M01 -> M02 -> N01 -> N02 -> N03 -> outcome_resolution`

Checkpoint:
`rt01.w03_schema_consolidation_checkpoint`

## Authority Boundaries
- W03 consumes W02 regularities + W02 permission/contradiction signals only.
- W03 cannot launder contested/scaffold-only/low-maturity W02 into clean priors.
- Live W01/W02 evidence overrides W03 prior in downstream contract.

## Channel Separation
W03 keeps independent channels:
- instance_prior
- kind_prior
- scene_role_prior
- structural_signature_prior
- affordance_prior

No silent instance/kind/role/affordance collapse.

## Operational Contradiction and Staleness
- Contradictions change status and permissions (not metadata-only).
- Stale/context/authority drift requires revalidation and may block downstream use.
- Updates emit version records with trigger and accepted/rejected evidence refs.

## Downstream Contract
W03 consumer packets expose explicit boundaries:
- `may_use_as_bounded_prior`
- `may_use_as_schema_hint`
- `may_use_as_operational_default`
- `must_revalidate_before_use`
- `must_preserve_contradiction`
- `must_abstain`
- `prohibited_claims`

Hardening note (post-audit):
- deferred / stale / contested / blocked / scaffold-laundered paths cannot emit clean `may_use_as_bounded_prior`;
- authority/provenance ablation now changes operational permission status, not only metadata strings;
- contradiction consequence routing is covered with distinct operational outcomes (`block_downstream_use` vs `split`) and permission deltas;
- W02 same-envelope integration proof is strengthened to assert strong-vs-weak restriction-set divergence under W03 mediation.

## Compatibility Note
C05 compatibility must not be overstated when C05 test paths are absent; report as non-executable compatibility.

## Build Validation Snapshot
Required W03 pack:
- `pytest -q tests/substrate/test_w03_schema_consolidation_build/test_w03_schema_consolidation_build.py` -> `33 passed`
- `pytest -q tests/substrate/test_subject_tick_build/test_w03_subject_tick_integration.py` -> `7 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_w03_runtime_topology_integration.py` -> `4 passed`
- `pytest -q tests/substrate/test_runtime_topology_build/test_runtime_topology_build.py` -> `47 passed`
- `pytest -q tests/tools/test_tick_observability_trace.py` -> `27 passed`
- `pytest -q tests/tools/test_w03_schema_consolidation_demo.py` -> `1 passed`

Compatibility pack summary:
- W02: `27/7/4/1 passed`
- W01: `22/8/4/1 passed`
- M01: `19/7/4/1 passed`
- M02: `19/7/4/1 passed`
- N03: `21/7/4/1 passed`
