# ADR-AB01: Event Digest & Anomaly Compression

## Why AB1 exists
AB1 introduces a bounded, non-causal event digest seam that compresses public anomaly/effect/residue signals into typed digest records.

AB1 allows claims of the form:
- "an anomaly happened"
- "an effect mismatch is present"

AB1 forbids claims of the form:
- "cause is confirmed"
- "this is the final explanation"

## Reused existing mechanisms (non-duplication)
- `W06`: residue/revalidation/blocked-claim discipline remains owner of revision routing.
- `S01`: intended-vs-observed/efference comparisons remain owner of comparison and contamination gating.
- `S02`: self/world prediction boundary remains owner of boundary status.
- `world_adapter` and `world_entry_contract`: effect correlation/admission constraints remain owner of world-success admissibility.
- `P9` strict-mode traces: provide runtime evidence for basis-flow and no hidden substitution.

AB1 does not replace any of the above. It only projects bounded event digests.

## Authority boundaries
- AB1 emits event digests only.
- AB1 has no hypothesis authority.
- AB1 has no action-candidate authority.
- AB1 has no AP01 request authority.
- AB1 has no execution authority.

## Inputs
- public observation refs
- public effect refs
- residue refs (if present)
- expected/observed refs (if present)
- optional prediction-error/efference signals as numeric/contextual input only

## Outputs
- typed digest event with:
  - event kind
  - refs
  - magnitude/confidence/uncertainty
  - compression method and lossiness
  - explicit non-causal closure flags

## No causal closure
AB1 always enforces:
- `explicit_non_causal_closure=True`
- `cause_claimed=False`
- no final cause field or hypothesis ranking.

## Falsifiers and ablations
AB1 tests cover:
- hidden/eval leakage rejection
- scenario-label leakage rejection
- no source/basis ref rejection
- lossiness marker requirements
- no action/request emission
- confidence degradation when raw window refs are absent
- low-noise/low-magnitude anomaly confidence control

## World-specific boundary
AB1 substrate policy is generic and portable.
World-specific interpretation (coordinates, recipe/station semantics, Minecraft IDs, scenario answer labels) remains outside AB1.
