# ADR-AB07: Recipe-Automation Abductive Integration

## Why AB7 exists
P15 introduces provisional recipe/precursor candidates from lived traces, but those candidates require explicit attachment to AB1-AB6 explanatory constraints to avoid implicit promotion into mature executable knowledge.

## Relation to P13/P14/P15
- P13 remains owner of delayed-credit/confounder/disconfirmation gating.
- P14 remains owner of station affordance and AP01-gated station effect boundaries.
- P15 remains owner of provisional recipe/precursor candidate generation.
- AB7 is the integration seam that constrains P15 candidates with abductive/frontier/update/attribution evidence.

## Relation to AB1-AB6
- AB1 refs provide event digest provenance around station/effect traces.
- AB2/AB3 refs preserve competing explanation context.
- AB5 refs can strengthen/weakening context but do not become recipe truth.
- AB6 refs can support attribution context but do not become recipe truth.
- AB7 does not replace any AB owner and does not mutate AB1-AB6 behavior.

## Why recipe candidates are explanatory objects, not executable skills
- AB7 outputs a `RecipeAutomationAbductiveFrame` with constraints/bindings/readiness only.
- `mature_recipe_claimed=False`, `automation_claimed=False`, `action_request_emitted=False`, `world_submission_emitted=False`.
- `AutomationReadinessAssessment` is explicitly non-executable in AB7.

## Why automation readiness remains blocked/provisional
- P13-style gates are enforced: repeated traces, confounder resolution, disconfirmation checks.
- Missing P14 affordance refs blocks station-based integration.
- Missing AB frontier refs blocks explanatory integration.
- AB7 policy includes explicit `blocks_maturity` and `blocks_automation` constraints.

## Inputs
- P15 recipe/precursor candidate records
- P15 lived trace refs
- P13 credit/confounder refs
- P14 station affordance refs
- AB1 digest refs, AB2 seed refs, AB3 frontier refs, AB5 update refs, AB6 attribution refs
- public effect/input/missing/disconfirming refs

## Outputs
- `RecipeAutomationAbductiveFrame`
- `RecipeLearningConstraint` set
- `RecipeHypothesisBinding` set
- `AutomationReadinessAssessment` set
- explicit blocked reasons and maturity gate statuses

## Constraints
- requires repeated traces
- requires public effect refs
- requires public input refs
- requires station affordance refs
- requires AB frontier support
- requires P13 gate refs
- blocks maturity under disconfirmation/confounder/missing evidence
- blocks automation in AB7

## Falsifiers
- recipe_candidate_bypasses_ab_frontier
- automation_from_recipe_candidate
- mature_recipe_from_ab7
- p13_gate_bypassed
- p14_affordance_bypassed
- ab5_support_as_recipe_oracle
- ab6_attribution_as_recipe_oracle
- one_trace_to_automation
- active_confounder_ignored
- disconfirming_trace_ignored
- hidden_eval_rule_used
- scenario_label_recipe_integration
- recipe_without_public_trace_refs
- recipe_without_effect_refs
- recipe_without_input_refs
- unresolved_frontier_erased
- missing_evidence_erased
- recipe_integration_emits_action_request
- recipe_integration_executes_world
- AB7_overclaims_automation

## Ablations
- remove AB frontier refs
- remove P13 gate refs
- remove P14 affordance refs
- remove effect refs
- remove input refs
- remove repeated traces
- activate confounder
- add disconfirming trace
- protected evaluator-only rule only
- one trace only
- ambiguous frontier

## World-specific boundary
AB7 substrate integration remains generic and portable. It does not use Minecraft-specific/crafting-table rules, protected evaluator-only transformation data, scenario labels, or direct world-specific transformation truth.
