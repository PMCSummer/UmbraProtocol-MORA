# ADR-AB06: Self-World Causal Attribution Integration

## Why AB6 exists
P11 provides perturbation-battery evidence and AB5 provides support updates, but there was no dedicated integration seam that converts AP01/effect/frontier/update evidence into bounded self/world causal attribution frames.

## Relation to P11
- P11 remains an experiment-side battery.
- AB6 consumes P11-like evidence patterns but is a substrate attribution contract seam.

## Relation to S01-S05
- AB6 may consume ownership/efference markers and S-style evidence refs.
- AB6 does not replace S01-S05 and does not claim S-level global ownership truth.

## Relation to AB5
- AB6 can consume AB5 update refs.
- AB6 does not modify hypothesis support and is not a hypothesis-update owner.

## Why AB6 is not full self-model
- AB6 emits bounded attribution candidates and statuses only.
- AB6 does not claim complete self-world understanding or theory-of-mind closure.

## Why AB6 is not final causal truth
- AB6 always keeps `fact_claimed=False` and `cause_confirmed=False`.
- closure is operational (`open/blocked/provisionally_attributed`), not truth closure.

## Inputs
- frontier refs
- update refs
- AP01 request refs
- effect refs
- event digest refs
- candidate refs
- observation/timing refs
- optional external/other/mixed/delay/mismatch markers

## Outputs
- `CausalAttributionFrame` with:
  - attribution candidates (`self_action`, `world_process`, `other_actor`, `delayed_self_effect`, `mixed_cause`, `unknown_cause`, `sensor_or_projection_error`)
  - supported/blocked/unresolved kinds
  - missing evidence
  - bounded uncertainty
  - no action/request/execution authority

## Falsifiers
- world_change_claimed_as_self_action
- self_action_effect_without_AP01_ref
- other_agent_effect_claimed_as_self
- mixed_cause_collapsed
- unknown_forced_to_self
- delayed_effect_misattributed_immediate
- AP01_request_as_effect
- effect_without_correlation_claimed_self
- blocked_action_claimed_success
- hidden_truth_attribution
- scenario_label_attribution
- sensor_mismatch_claimed_world_fact
- ownership_confidence_without_evidence
- attribution_erases_missing_evidence
- AB6_updates_hypotheses
- AB6_selects_epistemic_action
- AB6_emits_action_request
- AB6_overclaims_self_model

## Ablations
- remove_AP01_ref
- remove_effect_correlation
- world_only_change
- delayed_effect
- remove_ownership_evidence
- remove_other_actor_marker
- remove_mixed_evidence
- hidden_eval_only
- remove_public_observation_refs

## World-specific boundary
AB6 remains generic: no GridWorld coordinates/rules, no recipe/station/Minecraft semantics, no scenario-label policy, no hidden/eval truth consumption.
