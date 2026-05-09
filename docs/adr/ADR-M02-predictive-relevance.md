# ADR-M02: Predictive Relevance / Useful-But-Boring Channel

## Status
Accepted for narrow frontier slice build.

## Phase Boundary
M02 adds a typed predictive-relevance channel for memory economics.
It does not implement full prediction systems, full memory lifecycle, M03 pruning/archival, planner policy, or generic importance scoring.

## Narrow Claim
M02 may only claim that a trace has bounded predictive usefulness for explicit target types, context scope, and horizon.
M02 outputs typed packets that downstream memory systems may use for retention/retrieval/replay/indexing bias under explicit restrictions.

## Contour Placement
RT01 checkpoint order in this slice:

- `rt01.w01_bounded_world_loop_checkpoint`
- `rt01.m01_homeostatic_salience_imprint_checkpoint`
- `rt01.m02_predictive_relevance_checkpoint`
- `rt01.outcome_resolution_checkpoint`

## Owner Surface
Package: `src/substrate/m02_predictive_relevance/`

- typed traces, targets, feedback, predictive marks, lifecycle adjustments
- typed gate decision and scope marker
- typed downstream contract view and consumer packets
- compact telemetry snapshot for seam observability

## Core Mechanism
- target-linked predictive utility is required
- repetition without gain does not produce strong predictive marks
- vividness/novelty/recency/homeostatic strength are non-authoritative for M02
- context-locked predictors keep bounded transfer limits
- spurious-pattern risk suppresses promotion
- failed transfer narrows/decays predictive influence

## Downstream Contract Discipline
Consumer packets must preserve:

- predicted target types
- context scope and horizon
- anti-spurious limits
- must-preserve-context and must-not-generalize flags
- must-not-treat-as-generic-importance flag

## Explicit Non-Claims
- no full prediction model
- no full retrieval/replay/consolidation engine
- no M03 pruning/compaction/archive implementation
- no planner or policy-selection authority
- no causal truth guarantee

