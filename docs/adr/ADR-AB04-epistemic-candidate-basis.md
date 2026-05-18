# ADR-AB04: Evidence-Seeking Candidate Basis

## Why AB4 exists
AB3 keeps competing explanations open but does not produce ACP01-consumable epistemic basis.
AB4 converts unresolved frontier state into bounded evidence-seeking basis without selecting facts or actions.

## What AB3 provides
- open/provisionally-ranked frontier
- competing hypotheses
- unresolved conflicts
- missing evidence
- discriminating tests

## Relation to ACP01/AP01
- AB4 emits only basis artifacts.
- ACP01 remains candidate production authority.
- AP01 remains publication authority.
- AB4 has no direct publication or execution authority.

## Why AB4 is not an active inference engine
- AB4 uses bounded qualitative EIG levels tied to explicit frontier uncertainty/test refs.
- AB4 does not optimize global policy.
- AB4 does not execute tests or select final actions.

## Why AB4 is not action selection
- AB4 output has `forbidden_execution=True`.
- `action_request_emitted=False`, `ap01_request_ref=None`.
- no world submission authority.

## Authority boundaries
- no fact/cause closure
- no hypothesis update
- no ACP01/AP01 bypass
- no world execution

## Inputs
- AB3 ExplanationFrontier
- source/observation/residue/effect refs
- uncertainty and discriminating-test refs

## Outputs
- bounded `EpistemicCandidateBasis` records
- candidate kinds like inspect/wait/reobserve/check_consistency
- expected-information-gain levels with explicit policy/refs

## EIG policy
- default qualitative levels: `none|low|medium|high`
- numeric EIG disabled by default
- numeric EIG only allowed when scoring refs are explicit
- no precision without evidence refs

## Falsifiers
- ACP01/AP01 bypass
- EIG without frontier/uncertainty/discriminating hypotheses
- hidden/eval/scenario-based selection
- basis emitted from fact-claiming frontier
- basis treated as action candidate/request/execution
- fake precision EIG
- AB4 overclaiming active inference/scientific reasoning/consciousness

## Ablations
- no frontier
- no uncertainty
- no discriminating tests
- hidden_eval_only
- scenario_label_only
- fact_claiming_frontier
- remove_public_basis_refs
- no ACP01 / no AP01 route checks (if routed)

## World-specific boundary
AB4 substrate remains generic.
No GridWorld coordinates, no recipe/station semantics, no Minecraft IDs, no scenario labels, no hidden/eval truth.
