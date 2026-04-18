# ADR-O04 Rupture / Hostility / Coercion Dynamics

## Status
Accepted (narrow RT01-hosted frontier slice)

## Context
After P01, RT01 had no typed structural surface for rupture/hostility/coercion dynamics.  
Routing could react to generic repair/revalidation pressure, but could not distinguish tone-only harshness from leverage-backed pressure, could not expose actor-target directionality as a first-class contract surface, and could not track bounded rupture risk from repeated withdrawal patterns.

## Decision
Introduce `o04_rupture_hostility_coercion` as a distinct RT01 segment placed after `P01` and before bounded outcome resolution.  
This first slice provides:
- explicit typed O04 dynamic state (`dynamic_type`, `directional_links`, leverage surface, legitimacy hint, rupture status, uncertainty flags);
- bounded structural classification from typed interaction events (not tone-only shortcuts);
- directionality/asymmetry-sensitive coercive-pressure gating under blocked-option/threat/dependency structure;
- legitimacy-sensitive differentiation for matched pressure structure (`legitimacy_supported` can downgrade to bounded enforcement/hard-bargaining branch when sanction structure is absent);
- narrow rupture tracking from repeated withdrawal / exclusion / commitment-break patterns with repair counterevidence handling;
- bounded prior-state rupture carry/revision for short RT01 chains (carry-forward under continued withdrawal, downgrade under repair evidence, non-sticky reset on thin single-step basis);
- explicit require-path and narrow default-path checkpoint detours.

## Inputs
O04 consumes only bounded typed inputs:
- RT01-hosted `O04InteractionEventInput` bundle (actor/target, blocked-option, leverage/dependency hints, legitimacy hints, repair/escalation markers);
- bounded O03 and P01 context surfaces as modulation only;
- source lineage and bounded history-depth tag.

No moral/legal authority is assumed. No hidden emotion/intent reading is performed.

## Outputs
O04 emits:
- `O04DynamicModel`;
- `O04DynamicGateDecision`;
- `O04ScopeMarker`;
- `O04Telemetry`;
- RT01 checkpoint `rt01.o04_rupture_hostility_coercion_checkpoint`.

## Narrow Downstream Effect Implemented Now
RT01 now has bounded O04 effects:
- explicit require-path enforcement:
  - `require_o04_dynamic_contract_consumer`
  - `require_o04_directionality_consumer`
  - `require_o04_protective_handoff_consumer`
- narrow default-path detours (only with real O04 event basis) for:
  - coercive structure candidate,
  - rupture-risk pattern,
  - legitimacy/directionality ambiguity-preserving handling;
- downstream gate restrictions consume typed O04 semantics (directionality/coercion/rupture fields), not only checkpoint token presence.
- one additional typed-semantic downstream branch differentiates legitimacy-absent/contested coercive pressure from legitimacy-supported pressure even when checkpoint status class matches.

## Authority Boundary
O04 does not claim:
- full coercion/abuse detection;
- legal legitimacy adjudication;
- moral verdicts;
- R05 protective policy control;
- response-verbalization planning (V-line).

## Non-Claims
This ADR does **not** claim:
- moderation or toxicity classification;
- full multi-agent world modeling;
- map-wide safety authority.

## Current Limitations / Open Falsifiers
- O04 remains RT01-local with a narrow consumer/gating surface.
- Input event bundle is frontier-hosted and intentionally compact.
- Rupture tracking is short-horizon and pattern-bounded, not long-horizon social memory.
- Legitimacy differentiation remains hint-based/coarse; unresolved legitimacy still defaults to ambiguity-preserving fallback.
