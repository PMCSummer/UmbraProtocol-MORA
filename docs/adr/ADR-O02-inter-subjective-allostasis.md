# ADR-O02 Inter-subjective Allostasis

## Status
Accepted (narrow RT01-hosted frontier slice)

## Context
After O01, RT01 still lacked a typed interaction-regulation layer that could combine other-model quality, self-side caution, and recent repair pressure without drifting into emotion-reading or generic politeness behavior. This left ambiguity between lawful clarification/repair posture and style-only adaptation.

## Decision
Introduce `o02_intersubjective_allostasis` as a distinct RT01 segment placed after `O01` and before bounded outcome resolution.  
This first slice provides:
- explicit typed regulation state (`interaction_mode`, load bands, repair pressure, budgets, lever preferences, boundary status, reliance status);
- bounded forecasting of interactional repair/clarification pressure from typed diagnostics;
- conservative fallback when other-model basis is underconstrained;
- explicit guard against politeness-only collapse when uncertainty/boundary signals require explicit caution.

## Inputs
O02 consumes only bounded typed inputs:
- O01 other-entity model result (including uncertainty/individuation markers);
- S05 factorization result as contextual modulation signal;
- C04 selected mode and C05 revalidation pressure;
- narrow interaction diagnostics packet (`O02InteractionDiagnosticsInput`);
- self-side caution signal and regulation pressure scalar from RT01-hosted surfaces.

No hidden emotion/personality inference is used.

## Outputs
O02 emits:
- `O02IntersubjectiveAllostasisState`;
- `O02IntersubjectiveAllostasisGateDecision`;
- `O02ScopeMarker`;
- `O02Telemetry`;
- RT01 checkpoint `rt01.o02_intersubjective_allostasis_checkpoint`.

## Narrow Downstream Effect Implemented Now
RT01 now has two bounded O02 effects:
- explicit require-path enforcement:
  - `require_o02_repair_sensitive_consumer`
  - `require_o02_boundary_preserving_consumer`
- narrow default-path detours when O02 shape indicates unresolved repair pressure or underconstrained other-model basis.

Checkpoint `required_action` carries O02 shape markers used by downstream gate restrictions.

## Authority Boundary
O02 does not claim:
- full dialogue policy;
- emotion detection/empathy inference;
- deep personalization or theory-of-mind;
- O03 cooperation/manipulation evaluation;
- broad memory-policy ownership.

## Non-Claims
This ADR does **not** claim:
- rich social strategy ecosystem rollout;
- stable cross-session interpersonal modeling;
- full downstream consumer stack beyond RT01-local gate behavior.

## Current Limitations / Open Falsifiers
- O02.1 belief/ignorance coupling remains narrow and RT01-local.
- Default-path consequences are intentionally selective; most clean cases remain pass-through.
- Wider downstream consumer ecosystem and long-horizon adaptation remain open seams.
