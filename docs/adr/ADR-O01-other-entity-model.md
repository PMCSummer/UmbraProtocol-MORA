# ADR-O01 User / Other Entity Model

## Status
Accepted (narrow RT01-hosted frontier slice)

## Context
RT01 had no explicit typed other-entity layer: current user, referenced other, and quoted third-party evidence could only be handled indirectly. This created risk of summary-style shortcuts, third-party contamination, and unstable temporary-to-stable promotion without a bounded revision contract.

## Decision
Introduce `o01_other_entity_model` as a distinct RT01 segment after `T04` and before bounded outcome resolution.  
This slice provides explicit typed entity state with:
- entity individuation classes (`current_user_model`, `referenced_other_model`, `third_party_stub`, `minimal_other_stub`);
- stable vs temporary separation;
- O01.1 belief/ignorance overlay with uncertainty;
- revision ledger (`reinforce`, `revise`, `invalidate`, `contradiction_preserved`, `entity_split_required`, `no_safe_state_claim`);
- explicit projection guard and fallback states.

## Inputs
O01 consumes only typed, provenance-bound interaction signals (`O01EntitySignal`) provided through RT01 context:
- speaker-attributed grounded statements,
- referenced/quoted markers,
- correction/contradiction evidence,
- bounded turn-local confidence and provenance.

It does not treat style-only priors or demographic/personality guesses as strong evidence.

## Outputs
O01 emits:
- `O01OtherEntityModelState`;
- `O01OtherEntityModelGateDecision`;
- `O01ScopeMarker`;
- `O01Telemetry`;
- RT01 checkpoint `rt01.o01_other_entity_model_checkpoint`.

## Narrow Downstream Effect Implemented Now
RT01 checkpoint gating now has explicit O01 consumer requirements:
- `require_o01_entity_individuation_consumer`;
- `require_o01_clarification_ready_consumer`.

When requested and unmet, RT01 applies detour/revalidation instead of silently continuing.

## Authority Boundary
O01 does not claim:
- full theory-of-mind;
- personality/demographic inference;
- emotion/motive reading as fact;
- O02/O03 behavior;
- broad personalization policy.

## Non-Claims
This ADR does **not** claim:
- rich long-horizon user modeling;
- memory-policy redesign;
- cross-line social reasoning rollout.

## Current Limitations / Open Falsifiers
- Consumer effect is narrow and RT01-local; no broad downstream ecosystem yet.
- Default path keeps bounded O01 checkpoint optional unless explicit consumer requirements are requested.
- Signal authority model is intentionally compact and local to O01 first slice.
