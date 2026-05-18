# ADR-AB03: Hypothesis Frontier & Competition

## Why AB3 exists
AB2 emits bounded explanatory seeds but does not maintain a frontier.  
AB3 introduces a local, evidence-bounded explanation frontier over AB2 seeds.

AB3 allows:
- keep multiple competing hypotheses alive;
- rank provisionally without fact closure;
- preserve unresolved conflicts and missing evidence.

AB3 forbids:
- cause confirmation;
- fact selection;
- action candidate/request emission;
- epistemic action selection.

## What AB2 provides
- `HypothesisSeedSet` with provisional hypotheses, expected observations, possible tests, missing evidence.
- no fact closure and no action authority.

## Why AB3 is not duplicate T03/P04/W06/S/AB2
- `AB2`: seed generation owner only.
- `T03`: global silent-convergence competition across broader contour; not replaced.
- `P04`: counterfactual policy simulation owner; AB3 does not simulate.
- `W06`: residue/revision owner; AB3 does not revise.
- `S01-S05`: efference/prediction/attribution owners; AB3 consumes public refs only.

AB3 is a local abductive frontier layer over AB2 outputs.

## Authority boundaries
- no fact closure (`fact_claimed=False`, `selected_fact_hypothesis_id=None`, `cause_confirmed=False`)
- no AP01/ACP01/world action authority
- no active inference or epistemic action selection

## Inputs
- AB2 seed set
- public event/residue/effect/observation refs
- optional public disconfirming evidence refs

## Outputs
- `ExplanationFrontier` with:
  - competing hypotheses
  - optional provisional leader
  - unresolved conflicts
  - missing evidence
  - discriminating tests
  - confidence distribution

## Confidence policy
- evidence-bounded only (`confidence_policy="evidence_bounded"`)
- no precision without evidence refs
- missing evidence degrades support and closure status

## Falsifiers and ablations
AB3 tests include:
- leader-as-fact rejection
- ambiguous evidence stays open
- competing-hypothesis requirement
- evidence-required confidence
- hidden/eval and scenario-label rejection
- cause-claiming seed rejection
- no action/request emission
- world-specific token leakage rejection

## World-specific boundary
AB3 substrate uses generic hypothesis taxonomy only.
No GridWorld coordinate policy, no station/recipe/Minecraft semantics, no hidden/eval truth.
