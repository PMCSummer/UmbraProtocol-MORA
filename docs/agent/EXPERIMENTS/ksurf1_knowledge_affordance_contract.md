# K-SURF1 Knowledge Affordance Contract

## Purpose
Demonstrate that multi-provider surfaces are normalized into source-bound hints/slots/conflicts and never upgraded to action authority, truth, value, or mature knowledge.

## Demo cases
- `jei_hint_not_recipe_truth`
- `encyclopedia_locked_slot`
- `encyclopedia_partial_unlock`
- `quest_objective_hint`
- `machine_status_hint`
- `scanner_candidate_hint`
- `manual_claim_hint`
- `provider_conflict`
- `hidden_provider_blocked`
- `stale_lossy_provider`
- `provider_truth_rejected`
- `provider_value_rejected`

## Accepted examples
- JEI/index entry becomes transformation hint candidates only.
- Encyclopedia slot can stay locked or become partial with explicit public unlock basis.
- Quest text becomes objective hint candidate, not goal authority.
- Machine UI state becomes status hint candidate, not diagnosis/fact.
- Scanner output becomes identity/property candidate, not identity truth.

## Blocked examples
- provider payload with hidden/eval/scenario markers
- truth-authority provider claim
- selected-action/policy payload in provider metadata
- value assignment payload in provider metadata
- unlock attempt without explicit public basis

## Locked/partial slot discipline
- Locked slot:
  - visible basis may exist
  - no action/recipe/value authority
- Partial slot:
  - known + unknown parts preserved
  - uncertainty/lossiness preserved
  - maturity remains false

## Provider conflict discipline
- Conflicting claims produce `ProviderConflictFrame`.
- Resolution remains `unresolved`.
- `chosen_winner` remains `null`.

## Why this is not K1/provider backend/action selection
- No provider backend execution.
- No progressive unlock semantics beyond source-bound hint/slot state.
- No action or goal selection.
- No AP01 request emission.
- No mature recipe/skill/automation claim.
