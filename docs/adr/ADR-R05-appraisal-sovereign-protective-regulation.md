# ADR-R05 Appraisal-sovereign Protective Regulation

## Status
Accepted (narrow RT01-hosted frontier slice)

## Context
After O04, RT01 had no typed protective-regulation seam that could transform structural threat/appraisal/project pressure into bounded protective continuation control.  
Routing could react to generic repair/revalidation outcomes, but there was no first-class protective state with explicit inhibited surfaces, bounded override scope, and release/hysteresis discipline.

## Decision
Introduce `r05_appraisal_sovereign_protective_regulation` as a distinct RT01 segment placed after `O04` and before bounded outcome resolution.  
This first slice provides:
- typed threat-to-regulation transformation from bounded trigger inputs into `protective_mode`, `authority_level`, inhibited surfaces, and override scope;
- bounded sovereignty semantics (temporary project-continuation override only when structural basis is strong);
- surface-specific inhibition (communication exposure, interaction intensity, project continuation, permission hardening, escalation routing);
- release/hysteresis contract with explicit release conditions and non-sticky downgrade path;
- weak-basis fallbacks (`vigilance_without_override` / `insufficient_basis_for_override`) and regulation-conflict exposure;
- require-path and narrow default-path detours via `rt01.r05_protective_regulation_checkpoint`.

## Inputs
R05 consumes bounded typed inputs only:
- RT01-hosted `R05ProtectiveTriggerInput` bundle;
- narrow modulation from O04 dynamic result (coercive/rupture structure and ambiguity hints);
- narrow modulation from P01 project-continuation context;
- optional G08 appraisal-significance hint field when available in context.

No moral/legal adjudication and no sentiment/tone classifier authority is assumed.

## Outputs
R05 emits:
- `R05ProtectiveRegulationState`;
- `R05ProtectiveGateDecision`;
- `R05ScopeMarker`;
- `R05Telemetry`;
- `R05ProtectiveResult`;
- RT01 checkpoint `rt01.r05_protective_regulation_checkpoint`.

## Narrow Downstream Effect Implemented Now
RT01 now has bounded R05 effects:
- explicit require-path enforcement:
  - `require_r05_protective_state_consumer`
  - `require_r05_surface_inhibition_consumer`
  - `require_r05_release_contract_consumer`
- narrow default-path detours (only when real protective trigger basis exists):
  - `default_r05_protective_override_detour`
  - `default_r05_surface_throttle_detour`
  - `default_r05_release_recheck_detour`
- downstream gate reads typed R05 semantics (mode + inhibited-surface profile + release status), not only checkpoint token presence.

## Authority Boundary
R05 does not claim:
- full safety controller or map-wide protective governance;
- legal/moral threat adjudication;
- response-policy control (V-line substitution);
- planner/execution substrate authority;
- long-horizon memory-based protective identity.

## Non-Claims
This ADR does **not** claim:
- full homeostatic controller;
- full moderation or toxicity classification;
- full R05/R-line ecosystem completion.

## Current Limitations / Open Falsifiers
- Input trigger bundle remains frontier-hosted and compact.
- O04/P01/G08 modulation is narrow and bounded by current RT01 seam availability.
- Protective semantics are RT01-local; downstream consumer ecosystem beyond checkpoint/gate remains intentionally open.
- Hysteresis is short-horizon and does not implement long-memory protective dynamics.
