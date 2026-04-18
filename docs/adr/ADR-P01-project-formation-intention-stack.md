# ADR-P01 Project Formation / Intention Stack

## Status
Accepted (narrow RT01-hosted frontier slice)

## Context
After O03, RT01 still had no typed project-formation seam. Directive-like signals could influence continuation, but there was no explicit intention stack with authority-sensitive admission, project identity/dedup, conflict arbitration, or bounded handoff readiness.

## Decision
Introduce `p01_project_formation` as a distinct RT01 segment placed after `O03` and before bounded outcome resolution.  
This first slice provides:
- explicit typed intention-stack state (`active/candidate/suspended/rejected`, arbitration records, authority and grounding flags);
- authority-sensitive candidate-to-project formation from typed signal inputs;
- identity/dedup handling for restated targets and bounded carryover from prior stack;
- explicit conflict arbitration records (`reject_weaker_source` / `no_safe_resolution`) instead of silent winner selection;
- stale/termination handling for completion/policy-disallow paths;
- narrow require-path and default-path RT01 consequences via `rt01.p01_project_formation_checkpoint`.

## Inputs
P01 consumes only bounded typed inputs:
- RT01-hosted typed project signals (`P01ProjectSignalInput`);
- optional bounded prior P01 stack (`prior_p01_state`);
- bounded O03 strategy pressure (`O03StrategyEvaluationResult`) as conservative modulation only;
- source lineage from current tick context.

No full planner substrate, no autonomous self-generated initiative engine, and no map-wide project memory are assumed.

## Outputs
P01 emits:
- `P01IntentionStackState`;
- `P01ProjectFormationGateDecision`;
- `P01ScopeMarker`;
- `P01Telemetry`;
- RT01 checkpoint `rt01.p01_project_formation_checkpoint`.

## Narrow Downstream Effect Implemented Now
RT01 now has bounded P01 effects:
- explicit require-path enforcement:
  - `require_p01_intention_stack_consumer`
  - `require_p01_authority_bound_consumer`
  - `require_p01_project_handoff_consumer`
- narrow default-path detours for:
  - blocked-by-missing-precondition project activation attempts;
  - conflicting-authority project sets requiring explicit arbitration;
- one typed-semantic downstream gate branch that consumes P01 state fields (not only checkpoint tokens) for prompt-local substitution guard, conflict arbitration requirement, stale-active guard, and handoff readiness constraints.

## Authority Boundary
P01 does not claim:
- full planning/execution orchestration;
- deep autonomous intention generation;
- map-wide project persistence governance;
- completion semantics from response emission alone.

## Non-Claims
This ADR does **not** claim:
- P02/P03/P04 capability;
- V-line commitment constitution;
- full long-horizon project agency.

## Current Limitations / Open Falsifiers
- P01 remains RT01-local with a narrow consumer/gating surface.
- Input signals are frontier-hosted and intentionally compact.
- Carryover is bounded and short-horizon; no broad persistence policy is introduced.
- Empty admissible intersections still resolve conservatively (candidate/blocked/no-safe) without rich relaxation planning.
