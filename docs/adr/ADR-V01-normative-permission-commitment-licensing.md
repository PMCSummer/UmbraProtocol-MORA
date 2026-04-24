# ADR-V01 Normative Permission / Commitment Licensing

## Status
Accepted (frontier RT01-hosted first slice)

## Context
Before V01, RT01 had no explicit typed seam that licensed communicative act candidates and separated:
- act-level license vs deny vs conditional license;
- commitment creation vs commitment denial;
- mandatory qualifier binding vs optional wording hints.

As a result, promise-like leakage and qualifier-loss risks could survive downstream as token-only handling.

## Decision
Introduce `v01_normative_permission_commitment_licensing` as a distinct RT01 segment after `R05` and before bounded outcome resolution.

This first slice provides:
- typed act candidates and typed license state;
- act-type-sensitive licensing for `assertion/advice/promise/...`;
- explicit denied-act surface with reason codes and narrowed alternatives;
- explicit commitment delta surface (`create_commitment` vs `commitment_denied`);
- mandatory qualifier binding as a downstream-consumable contract surface;
- bounded protective narrowing from R05 without blanket silence;
- explicit require-path and narrow default-path checkpoint consequences.

## Scope Boundary (What This Slice Does Not Claim)
This ADR does **not** claim:
- map-wide V-line maturity;
- V02/V03 realization guarantees;
- legal/moral adjudication engine;
- full downstream ecosystem rollout.

V01 remains a narrow RT01-hosted licensing shim.

## Mechanistically Real in Code
- Typed surfaces: `V01CommunicativeActCandidate`, `V01LicensedActEntry`, `V01DeniedActEntry`,
  `V01CommitmentDelta`, `V01CommunicativeLicenseState`, `V01LicenseGateDecision`,
  `V01ScopeMarker`, `V01Telemetry`, `V01LicenseResult`.
- Checkpoint: `rt01.v01_normative_permission_commitment_licensing_checkpoint`.
- Require path:
  - `require_v01_license_consumer`
  - `require_v01_commitment_delta_consumer`
  - `require_v01_qualifier_binding_consumer`
- Default path:
  - `default_v01_unlicensed_act_detour`
  - `default_v01_qualification_required_detour`
  - `default_v01_commitment_denied_detour`
- Downstream policy reads typed V01 fields (counts + promise-denied + qualifier IDs), not only checkpoint token strings.

## Why V01 Is Separate From Wording
V01 emits licensing/commitment/qualifier contracts and deny surface before wording realization.
It does not pick final phrasing and does not replace V02/V03.

## Open Seams Intentionally Left Open
- Broad consumer rollout beyond RT01 gate remains open.
- Rich qualifier semantics across all downstream layers remains open.
- Multi-phase episode policy integration (P02/P04) remains open.
