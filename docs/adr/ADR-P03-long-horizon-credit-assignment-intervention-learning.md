# ADR-P03: Long-horizon credit assignment / intervention learning (RT01-hosted narrow slice)

## Status
Accepted (frontier build slice)

## Date
2026-04-26

## Decision
- Introduce `P03` as an RT01-hosted narrow contour stage:
  - `... -> V03 -> C06 -> P02 -> P03 -> bounded_outcome_resolution -> ...`
  - checkpoint: `rt01.p03_credit_assignment_checkpoint`
- `P03` consumes typed `P02` episode records + typed delayed outcomes/windows + typed confounders + continuity refs.
- `P03` emits typed attribution artifacts (credit records, no-update records, recommendations) and does not mutate policy.
- `P03` remains bounded attribution authority only (no full causal truth claim, no map-wide rollout claim).

## Scope (narrow and explicit)
- RT01-hosted frontier slice only.
- Load-bearing outputs:
  - typed attribution class (`positive/negative/mixed/null/unresolved/confounded_association`)
  - typed contribution mode
  - typed window/evidence status
  - first-class no-update records
  - typed update recommendations as separate artifacts
- Downstream gate path includes:
  - `require_p03_credit_record_consumer`
  - `require_p03_no_update_consumer`
  - `require_p03_update_recommendation_consumer`
- Default detours (basis-gated):
  - `default_p03_confounded_association_detour`
  - `default_p03_outcome_window_open_detour`
  - `default_p03_negative_side_effect_detour`

## Non-goals / forbidden shortcuts
- No scalar reward accumulator.
- No hidden policy mutation inside P03.
- No raw approval/fluency/gratitude proxy learning shortcut.
- No full causal discovery claims.
- No expansion from local evidence to map-wide intervention-family certainty.

## Seam-honesty choices
- Direct narrow seam set kept to causally necessary inputs in this slice:
  - `P02` result (required)
  - `C06` result (required for residue/carryover confounder branch)
- `P01` is not a direct consumed seam in the P03 policy interface in this slice:
  - no deterministic tested branch in this implementation where direct `P01` object changes P03 attribution/recommendation.
  - avoids decorative direct dependency.

## Consequences
- Downstream no longer needs raw outcome impressions for this slice; it can consume typed attribution refs.
- `subject_tick` downstream decision now reads typed P03 semantics directly (counts/readiness/confounded/window/side-effect), not only checkpoint token.
- Disabling `disable_p03_enforcement` is explicitly material in integration behavior.

## Intentionally left open
- Full long-horizon learner/policy adaptation backbone.
- Cross-phase map-wide consumer ecology.
- Broad causal structure discovery beyond bounded attribution classes.
- Any retention-write authority changes (F01 persistence seam remains unchanged).

## Closure-note bounded limits
- P03 attribution remains bounded heuristic attribution, not SCM-level causal inference.
- Cross-episode misbinding adversarial coverage is intentionally narrower than full general-case causal disentanglement.
- `subject_tick` gate currently consumes only a subset of P03 counters/readiness surfaces for direct gate effects.
- These bounded limits do not block the narrow RT01-hosted closure claim for P03.
