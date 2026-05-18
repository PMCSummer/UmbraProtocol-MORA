# ADR-AB02: Hypothesis Seed from Residue-Anomaly

## Why AB2 exists
AB2 introduces a bounded hypothesis-seed seam that consumes AB1 public event digests and emits multiple provisional explanatory seeds.

AB2 allows:
- "several plausible explanations remain open"

AB2 forbids:
- "cause is confirmed"
- "single best seed is fact"
- "seed is an action request"

## Inventory and reuse
- Reused `AB1` as event/anomaly owner (`src/substrate/ab01_event_digest/*`).
- Reused `W06` as residue/revision owner (`src/substrate/w06_error_driven_revision/*`).
- Reused `T03` as hypothesis competition/frontier owner (`src/substrate/t03_hypothesis_competition/*`).
- Reused `P04` as counterfactual simulation owner (`src/substrate/p04_interpersonal_counterfactual_policy_simulation/*`).
- Reused `S01/S02/S05` for efference/prediction/attribution context ownership.

AB2 is not duplicate:
- not W06 revision router,
- not T03 competitor/frontier selector,
- not P04 simulator,
- not S-layer attribution closure.

## Authority boundaries
- AB2 emits seed records only.
- AB2 has no fact selection authority.
- AB2 has no frontier competition authority.
- AB2 has no ACP01 action authority.
- AB2 has no AP01 request authority.
- AB2 has no world execution authority.

## Inputs
- AB1 event digest(s)
- public observation/effect/residue refs
- optional public prediction-error/efference mismatch context

## Outputs
- `AB2HypothesisSeedSet` with:
  - multiple bounded seeds
  - expected observations
  - possible tests
  - missing evidence
  - provisional confidence
  - open closure status

## Non-closure policy
AB2 enforces:
- `fact_claimed=False`
- `selected_fact_hypothesis_id=None`
- `cause_confirmed=False` for every seed
- rejection of AB1 digests that already claim cause

## Falsifiers and ablations
AB2 tests include:
- hidden/eval and scenario-label rejection
- event-digest-cause laundering rejection
- no-basis / no-source rejection
- competing hypotheses requirement for ambiguous events
- expected-observations and possible-tests requirements
- world-specific token leakage rejection
- no action/request emission

## World-specific boundary
AB2 substrate taxonomy is generic/portable and does not encode:
- GridWorld coordinates/rules
- station/recipe/automation semantics
- Minecraft identifiers
- scenario IDs
- hidden/eval truth.
