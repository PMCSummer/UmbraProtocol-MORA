from __future__ import annotations

from substrate.p04_interpersonal_counterfactual_policy_simulation import (
    P04BeliefStateMode,
    P04CandidateRole,
    P04ComparisonReadiness,
    P04DominanceState,
    P04ExclusionReason,
    P04PolicyClass,
    P04UncertaintyStatus,
)
from tests.substrate.p04_interpersonal_counterfactual_policy_simulation_testkit import (
    P04HarnessCase,
    build_p04_harness_case,
    p04_assumption,
    p04_candidate,
    p04_candidate_set,
    p04_simulation_input,
)


def _run(case: P04HarnessCase):
    return build_p04_harness_case(case).p04_result


def _baseline_candidates() -> tuple:
    return (
        p04_candidate(
            candidate_id="cand:fast-risky",
            policy_ref="policy.fast_risky",
            policy_class=P04PolicyClass.ESCALATORY_ENFORCEMENT,
            action_class="authority_command",
            sequencing_rule="boundary_before_clarify",
            escalation_stance="hard_assertive",
            de_escalation_stance="none",
            clarification_strategy="minimal",
            boundary_posture="rigid",
            boundary_timing="late",
            stopping_conditions=("exit_on_rupture",),
            horizon_steps=2,
        ),
        p04_candidate(
            candidate_id="cand:slow-safe",
            policy_ref="policy.slow_safe",
            policy_class=P04PolicyClass.COLLABORATIVE_CLARIFICATION,
            action_class="authority_command",
            sequencing_rule="clarify_before_boundary",
            escalation_stance="calibrated",
            de_escalation_stance="repair_first",
            clarification_strategy="explicit",
            boundary_posture="guarded",
            boundary_timing="phased",
            stopping_conditions=("verification", "exit_on_rupture"),
            horizon_steps=2,
        ),
    )


def test_p04_output_is_typed_simulation_set_not_option_prose() -> None:
    result = _run(
        P04HarnessCase(
            case_id="typed-simulation-set",
            simulation_input=p04_simulation_input(
                input_id="input:typed",
                candidate_set=p04_candidate_set(
                    set_id="set:typed",
                    candidates=_baseline_candidates(),
                ),
                assumptions=(
                    p04_assumption(
                        assumption_id="as:shared",
                        mode=P04BeliefStateMode.SHARED_KNOWLEDGE,
                        shared_knowledge_confidence=0.9,
                    ),
                ),
            ),
        )
    )
    assert result.simulation_set.branch_records
    assert result.simulation_set.comparison_matrix.contrasts
    assert result.simulation_set.branch_records[0].assumption_records
    assert result.simulation_set.branch_records[0].uncertainty_envelope.status in {
        P04UncertaintyStatus.STABLE,
        P04UncertaintyStatus.GUARDED,
    }
    assert result.scope_marker.simulation_not_selector is True
    assert result.scope_marker.no_policy_mutation_authority is True


def test_same_policies_with_different_relational_state_change_branch_forecast() -> None:
    candidates = _baseline_candidates()
    low_risk = _run(
        P04HarnessCase(
            case_id="same-policies-low-risk",
            simulation_input=p04_simulation_input(
                input_id="input:low",
                candidate_set=p04_candidate_set(set_id="set:low", candidates=candidates),
                current_rupture_risk=0.2,
                current_trust_fragility=0.2,
                current_dependency_pressure=0.2,
            ),
        )
    )
    high_risk = _run(
        P04HarnessCase(
            case_id="same-policies-high-risk",
            simulation_input=p04_simulation_input(
                input_id="input:high",
                candidate_set=p04_candidate_set(set_id="set:high", candidates=candidates),
                current_rupture_risk=0.8,
                current_trust_fragility=0.8,
                current_dependency_pressure=0.8,
            ),
        )
    )
    low_branch = low_risk.simulation_set.branch_records[0]
    high_branch = high_risk.simulation_set.branch_records[0]
    assert high_branch.risk_vector.rupture_risk > low_branch.risk_vector.rupture_risk
    assert high_branch.risk_vector.coercion_risk > low_branch.risk_vector.coercion_risk
    assert high_branch.ranking_score_hint < low_branch.ranking_score_hint


def test_same_state_different_sequencing_changes_trajectory_structurally() -> None:
    shared = dict(
        policy_ref="policy.seq",
        policy_class=P04PolicyClass.COLLABORATIVE_CLARIFICATION,
        action_class="structured_dialogue",
        escalation_stance="calibrated",
        de_escalation_stance="repair_first",
        clarification_strategy="explicit",
        boundary_posture="guarded",
        boundary_timing="phased",
        stopping_conditions=("verification",),
        horizon_steps=2,
    )
    candidates = (
        p04_candidate(
            candidate_id="cand:seq:clarify-first",
            sequencing_rule="clarify_before_boundary",
            **shared,
        ),
        p04_candidate(
            candidate_id="cand:seq:boundary-first",
            sequencing_rule="boundary_before_clarify",
            **shared,
        ),
    )
    result = _run(
        P04HarnessCase(
            case_id="sequencing-contrast",
            simulation_input=p04_simulation_input(
                input_id="input:sequencing",
                candidate_set=p04_candidate_set(set_id="set:sequencing", candidates=candidates),
            ),
        )
    )
    first = result.simulation_set.branch_records[0]
    second = result.simulation_set.branch_records[1]
    assert first.benefit_vector.clarity_gain > second.benefit_vector.clarity_gain
    assert first.risk_vector.rupture_risk < second.risk_vector.rupture_risk
    assert first.risk_vector.delay_cost > second.risk_vector.delay_cost


def test_stereotype_resistance_uses_typed_state_not_role_label_shortcut() -> None:
    candidates = _baseline_candidates()
    result = _run(
        P04HarnessCase(
            case_id="stereotype-resistance",
            simulation_input=p04_simulation_input(
                input_id="input:stereotype",
                candidate_set=p04_candidate_set(set_id="set:stereotype", candidates=candidates),
                assumptions=(
                    p04_assumption(
                        assumption_id="as:false-belief",
                        mode=P04BeliefStateMode.FALSE_BELIEF,
                        shared_knowledge_confidence=0.3,
                        false_belief_case_support=True,
                    ),
                ),
                current_rupture_risk=0.75,
                current_trust_fragility=0.7,
            ),
        )
    )
    by_ref = {item.policy_ref: item for item in result.simulation_set.branch_records}
    assert by_ref["policy.fast_risky"].ranking_score_hint < by_ref["policy.slow_safe"].ranking_score_hint
    assert by_ref["policy.fast_risky"].risk_vector.rupture_risk > by_ref["policy.slow_safe"].risk_vector.rupture_risk


def test_horizon_tradeoff_exposes_fast_risky_vs_slow_safe_contrast() -> None:
    result = _run(
        P04HarnessCase(
            case_id="horizon-tradeoff",
            simulation_input=p04_simulation_input(
                input_id="input:horizon-tradeoff",
                candidate_set=p04_candidate_set(
                    set_id="set:horizon-tradeoff",
                    candidates=_baseline_candidates(),
                ),
            ),
        )
    )
    by_ref = {item.policy_ref: item for item in result.simulation_set.branch_records}
    fast = by_ref["policy.fast_risky"]
    slow = by_ref["policy.slow_safe"]
    assert fast.benefit_vector.project_progress > slow.benefit_vector.project_progress
    assert fast.risk_vector.rupture_risk > slow.risk_vector.rupture_risk
    assert fast.risk_vector.coercion_risk > slow.risk_vector.coercion_risk
    assert any(
        contrast.faster_but_riskier
        for contrast in result.simulation_set.comparison_matrix.contrasts
    )


def test_guardrail_inheritance_excludes_unlicensed_or_overrun_candidates() -> None:
    candidates = (
        p04_candidate(
            candidate_id="cand:licensed",
            policy_ref="policy.licensed",
            policy_class=P04PolicyClass.HOLD_AND_VERIFY,
            action_class="check",
            sequencing_rule="clarify_before_boundary",
            escalation_stance="defer",
            de_escalation_stance="repair_first",
            clarification_strategy="explicit",
            boundary_posture="guarded",
            boundary_timing="early",
            stopping_conditions=("verification",),
            horizon_steps=2,
        ),
        p04_candidate(
            candidate_id="cand:unlicensed",
            policy_ref="policy.unlicensed",
            policy_class=P04PolicyClass.ESCALATORY_ENFORCEMENT,
            action_class="force",
            sequencing_rule="escalate_early",
            escalation_stance="hard_assertive",
            de_escalation_stance="none",
            clarification_strategy="minimal",
            boundary_posture="rigid",
            boundary_timing="late",
            stopping_conditions=(),
            horizon_steps=2,
            licensed=False,
        ),
        p04_candidate(
            candidate_id="cand:overrun",
            policy_ref="policy.overrun",
            policy_class=P04PolicyClass.ASSERTIVE_BOUNDARY,
            action_class="boundary_push",
            sequencing_rule="boundary_before_clarify",
            escalation_stance="hard_assertive",
            de_escalation_stance="none",
            clarification_strategy="minimal",
            boundary_posture="rigid",
            boundary_timing="late",
            stopping_conditions=(),
            horizon_steps=2,
            scope_overrun=True,
        ),
    )
    result = _run(
        P04HarnessCase(
            case_id="guardrail-exclusions",
            simulation_input=p04_simulation_input(
                input_id="input:guardrail",
                candidate_set=p04_candidate_set(set_id="set:guardrail", candidates=candidates),
            ),
        )
    )
    selectable_refs = {item.policy_ref for item in result.simulation_set.branch_records}
    excluded = {item.policy_ref: item.reason_code for item in result.simulation_set.excluded_policies}
    assert "policy.licensed" in selectable_refs
    assert "policy.unlicensed" not in selectable_refs
    assert "policy.overrun" not in selectable_refs
    assert excluded["policy.unlicensed"] is P04ExclusionReason.UNLICENSED_POLICY
    assert excluded["policy.overrun"] is P04ExclusionReason.SCOPE_OVERRUN


def test_uncertainty_stress_yields_unstable_region_and_no_clear_dominance() -> None:
    result = _run(
        P04HarnessCase(
            case_id="uncertainty-stress",
            simulation_input=p04_simulation_input(
                input_id="input:uncertainty",
                candidate_set=p04_candidate_set(set_id="set:uncertainty", candidates=_baseline_candidates()),
                assumptions=(
                    p04_assumption(
                        assumption_id="as:ku",
                        mode=P04BeliefStateMode.KNOWLEDGE_UNCERTAINTY,
                        shared_knowledge_confidence=0.2,
                        knowledge_uncertainty_support=True,
                    ),
                ),
                missing_state_factors=("missing_relational_history", "missing_external_change"),
                assumption_perturbation_level=0.8,
            ),
        )
    )
    assert result.telemetry.unstable_region_count == 1
    assert result.simulation_set.comparison_matrix.dominance_state is P04DominanceState.UNSTABLE_REGION
    assert result.simulation_set.comparison_matrix.no_clear_dominance is True
    assert result.simulation_set.comparison_matrix.comparison_readiness is P04ComparisonReadiness.COMPARISON_ONLY


def test_belief_conditioned_rollout_changes_forecast_across_modes() -> None:
    base_candidate_set = p04_candidate_set(
        set_id="set:belief-modes",
        candidates=(
            p04_candidate(
                candidate_id="cand:belief",
                policy_ref="policy.belief",
                policy_class=P04PolicyClass.COLLABORATIVE_CLARIFICATION,
                action_class="dialogue",
                sequencing_rule="clarify_before_boundary",
                escalation_stance="calibrated",
                de_escalation_stance="repair_first",
                clarification_strategy="explicit",
                boundary_posture="guarded",
                boundary_timing="phased",
                stopping_conditions=("verification",),
                horizon_steps=2,
            ),
        ),
    )
    incomplete = _run(
        P04HarnessCase(
            case_id="belief-incomplete",
            simulation_input=p04_simulation_input(
                input_id="input:belief-incomplete",
                candidate_set=base_candidate_set,
                assumptions=(
                    p04_assumption(
                        assumption_id="as:inc",
                        mode=P04BeliefStateMode.INCOMPLETE_INFORMATION,
                        shared_knowledge_confidence=0.4,
                        incomplete_information_support=True,
                    ),
                ),
            ),
        )
    )
    false_belief = _run(
        P04HarnessCase(
            case_id="belief-false",
            simulation_input=p04_simulation_input(
                input_id="input:belief-false",
                candidate_set=base_candidate_set,
                assumptions=(
                    p04_assumption(
                        assumption_id="as:false",
                        mode=P04BeliefStateMode.FALSE_BELIEF,
                        shared_knowledge_confidence=0.3,
                        false_belief_case_support=True,
                    ),
                ),
            ),
        )
    )
    misread = _run(
        P04HarnessCase(
            case_id="belief-misread",
            simulation_input=p04_simulation_input(
                input_id="input:belief-misread",
                candidate_set=base_candidate_set,
                assumptions=(
                    p04_assumption(
                        assumption_id="as:misread",
                        mode=P04BeliefStateMode.MISREAD,
                        shared_knowledge_confidence=0.35,
                        misread_case_support=True,
                    ),
                ),
            ),
        )
    )
    knowledge_uncertainty = _run(
        P04HarnessCase(
            case_id="belief-knowledge-uncertainty",
            simulation_input=p04_simulation_input(
                input_id="input:belief-ku",
                candidate_set=base_candidate_set,
                assumptions=(
                    p04_assumption(
                        assumption_id="as:ku",
                        mode=P04BeliefStateMode.KNOWLEDGE_UNCERTAINTY,
                        shared_knowledge_confidence=0.2,
                        knowledge_uncertainty_support=True,
                    ),
                ),
            ),
        )
    )
    b_inc = incomplete.simulation_set.branch_records[0]
    b_false = false_belief.simulation_set.branch_records[0]
    b_misread = misread.simulation_set.branch_records[0]
    b_ku = knowledge_uncertainty.simulation_set.branch_records[0]
    assert b_false.risk_vector.rupture_risk > b_inc.risk_vector.rupture_risk
    assert b_misread.risk_vector.coercion_risk > b_inc.risk_vector.coercion_risk
    assert b_ku.uncertainty_envelope.status in {
        P04UncertaintyStatus.GUARDED,
        P04UncertaintyStatus.UNSTABLE,
    }
    assert knowledge_uncertainty.telemetry.knowledge_uncertainty_support is True
    assert false_belief.telemetry.false_belief_case_support is True
    assert misread.telemetry.misread_case_support is True
    assert incomplete.telemetry.incomplete_information_support is True


def test_ablation_of_p03_priors_changes_branch_scores_but_keeps_typed_simulation() -> None:
    candidates = _baseline_candidates()
    with_priors = _run(
        P04HarnessCase(
            case_id="ablation-priors-on",
            p03_case_key="immediate_positive_later_degraded",
            simulation_input=p04_simulation_input(
                input_id="input:priors:on",
                candidate_set=p04_candidate_set(set_id="set:priors:on", candidates=candidates),
                use_p03_priors=True,
            ),
        )
    )
    without_priors = _run(
        P04HarnessCase(
            case_id="ablation-priors-off",
            p03_case_key="immediate_positive_later_degraded",
            simulation_input=p04_simulation_input(
                input_id="input:priors:off",
                candidate_set=p04_candidate_set(set_id="set:priors:off", candidates=candidates),
                use_p03_priors=False,
            ),
        )
    )
    with_score = with_priors.simulation_set.branch_records[0].ranking_score_hint
    without_score = without_priors.simulation_set.branch_records[0].ranking_score_hint
    assert with_score != without_score
    assert with_priors.simulation_set.branch_records
    assert without_priors.simulation_set.branch_records
    assert with_priors.simulation_set.comparison_matrix.comparison_readiness is not P04ComparisonReadiness.BLOCKED
    assert without_priors.simulation_set.comparison_matrix.comparison_readiness is not P04ComparisonReadiness.BLOCKED


def test_anti_narrative_masquerade_requires_typed_branches_assumptions_uncertainty_and_contrasts() -> None:
    result = _run(
        P04HarnessCase(
            case_id="anti-narrative",
            simulation_input=p04_simulation_input(
                input_id="input:anti-narrative",
                candidate_set=p04_candidate_set(
                    set_id="set:anti-narrative",
                    candidates=(
                        *_baseline_candidates(),
                        p04_candidate(
                            candidate_id="cand:hazard",
                            policy_ref="policy.hazard",
                            policy_class=P04PolicyClass.ESCALATORY_ENFORCEMENT,
                            action_class="force",
                            sequencing_rule="escalate_early",
                            escalation_stance="hard_assertive",
                            de_escalation_stance="none",
                            clarification_strategy="minimal",
                            boundary_posture="rigid",
                            boundary_timing="late",
                            stopping_conditions=(),
                            horizon_steps=2,
                            candidate_role=P04CandidateRole.HAZARD_ONLY,
                        ),
                    ),
                ),
                assumptions=(
                    p04_assumption(
                        assumption_id="as:shared",
                        mode=P04BeliefStateMode.SHARED_KNOWLEDGE,
                        shared_knowledge_confidence=0.8,
                    ),
                ),
            ),
        )
    )
    assert len(result.simulation_set.branch_records) == 3
    assert result.simulation_set.branch_records[0].assumption_records
    assert result.simulation_set.branch_records[0].uncertainty_envelope.unstable_factors == ()
    assert result.simulation_set.comparison_matrix.contrasts
    assert any(item.outcome_status.value == "hazard_only" for item in result.simulation_set.branch_records)
