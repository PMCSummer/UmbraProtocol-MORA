# ADR-O03 Cooperation vs Manipulation as Low-Entropy Strategy

## Status
Accepted (narrow RT01-hosted frontier slice)

## Context
After O02, RT01 still lacked a typed strategy-class seam that could distinguish cooperative coordination from concealment-dependent, high-entropy candidate moves. Existing contour gating could detour on repair/clarification, but it had no dedicated low-entropy strategy contract surface and no explicit hidden-divergence/dependency lens.

## Decision
Introduce `o03_strategy_class_evaluation` as a distinct RT01 segment placed after `O02` and before bounded outcome resolution.  
This first slice provides:
- explicit typed strategy state (`strategy_class`, hidden-divergence/asymmetry/dependency bands, reversibility/repairability, transparency, uncertainty flags);
- bounded strategy-class evaluation from typed candidate inputs plus O01/O02/S05 context;
- conservative underclassification fallback (`strategy_class_underconstrained` / `no_safe_classification`) when evidence is thin;
- narrow RT01 gating consequences for transparency increase, cooperative default preference, and exploitative-candidate blocking;
- explicit require-path checkpoints plus one narrow default-path detour.

## Inputs
O03 consumes only bounded typed inputs:
- O01 other-model state/uncertainty markers;
- O02 regulation posture/constraints;
- S05 factorization context (bounded modulation only);
- RT01-hosted candidate strategy packet (`O03CandidateStrategyInput`);
- bounded self-side pressure and C05 revalidation signal.

No hidden motive/emotion reading or broad social ontology is used.

## Outputs
O03 emits:
- `O03StrategyEvaluationState`;
- `O03StrategyEvaluationGateDecision`;
- `O03ScopeMarker`;
- `O03Telemetry`;
- RT01 checkpoint `rt01.o03_strategy_class_evaluation_checkpoint`.

## Narrow Downstream Effect Implemented Now
RT01 now has bounded O03 effects:
- explicit require-path enforcement:
  - `require_o03_strategy_contract_consumer`
  - `require_o03_cooperative_selection_consumer`
  - `require_o03_transparency_preserving_consumer`
- narrow default-path detours for concealment/high-entropy strategy shapes;
- one typed-semantic downstream gate branch that reads O03 state fields (not only checkpoint tokens) and applies cooperative/transparency/exploitative restrictions.

## Authority Boundary
O03 does not claim:
- global ethics/legal verdicts;
- O04 coercion/rupture dynamics;
- full planner governance;
- broad anti-influence policy;
- tone-based manipulation diagnosis.

## Non-Claims
This ADR does **not** claim:
- rich manipulation ontology;
- full autonomy psychology;
- repo-wide O03 consumer rollout.

## Current Limitations / Open Falsifiers
- O03 remains RT01-local with a single narrow consumer surface.
- Candidate strategy input is frontier-hosted and intentionally compact (not planner-wide).
- Long-horizon accumulation of dependency risk remains an open seam for future hardening.
