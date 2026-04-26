from substrate.p02_intervention_episode_layer_licensed_action_trace import (
    P02InterventionEpisodeResult,
)
from substrate.p03_long_horizon_credit_assignment_intervention_learning import (
    P03CreditAssignmentResult,
)
from substrate.p04_interpersonal_counterfactual_policy_simulation.models import (
    P04BeliefStateAssumption,
    P04BeliefStateMode,
    P04BranchAssumptionRecord,
    P04BranchBenefitVector,
    P04BranchOutcomeStatus,
    P04BranchRecord,
    P04BranchRiskVector,
    P04BranchUncertaintyEnvelope,
    P04CandidateRole,
    P04CommitmentEffect,
    P04ComparisonMatrix,
    P04ComparisonReadiness,
    P04ContrastiveDifference,
    P04CounterfactualPolicySimulationSet,
    P04DominanceState,
    P04ExcludedPolicyRecord,
    P04ExclusionReason,
    P04PolicyCandidate,
    P04ProtectiveLoadEffect,
    P04RelationalTransition,
    P04ScopeMarker,
    P04SimulationGateDecision,
    P04SimulationInput,
    P04SimulationMetadata,
    P04SimulationResult,
    P04Telemetry,
    P04TransitionType,
    P04UncertaintyStatus,
    P04UnstableRegion,
)


def build_p04_interpersonal_counterfactual_policy_simulation(
    *,
    tick_id: str,
    tick_index: int,
    p02_result: P02InterventionEpisodeResult,
    p03_result: P03CreditAssignmentResult,
    simulation_input: P04SimulationInput | None,
    source_lineage: tuple[str, ...],
    simulation_enabled: bool = True,
) -> P04SimulationResult:
    if not simulation_enabled:
        return _build_minimal_result(
            reason="p04 simulation disabled in ablation context",
            restrictions=("p04_disabled", "simulation_not_evaluated"),
            source_lineage=source_lineage,
        )
    if not isinstance(p02_result, P02InterventionEpisodeResult):
        raise TypeError("p04 requires P02InterventionEpisodeResult")
    if not isinstance(p03_result, P03CreditAssignmentResult):
        raise TypeError("p04 requires P03CreditAssignmentResult")

    explicit_input = simulation_input if isinstance(simulation_input, P04SimulationInput) else None
    if explicit_input is None:
        return _build_minimal_result(
            reason=(
                "p04 frontier slice requires explicit typed simulation input; "
                "narrative option reconstruction is intentionally forbidden"
            ),
            restrictions=("insufficient_p04_basis", "no_narrative_option_list_shortcut"),
            source_lineage=source_lineage,
        )

    candidates = explicit_input.candidate_set.candidates
    if not candidates:
        return _build_minimal_result(
            reason="p04 received no policy candidates and produced no branch rollout",
            restrictions=("no_policy_candidates", "simulation_not_evaluated"),
            source_lineage=source_lineage,
        )

    prior_positive = (
        p03_result.telemetry.positive_credit_count if explicit_input.use_p03_priors else 0
    )
    prior_negative = (
        p03_result.telemetry.negative_credit_count + p03_result.telemetry.side_effect_dominant_count
        if explicit_input.use_p03_priors
        else 0
    )
    prior_uncertain = (
        p03_result.telemetry.confounded_credit_count + p03_result.telemetry.unresolved_credit_count
        if explicit_input.use_p03_priors
        else 0
    )
    prior_open_window = (
        p03_result.telemetry.outcome_window_open_count if explicit_input.use_p03_priors else 0
    )

    branches: list[P04BranchRecord] = []
    excluded: list[P04ExcludedPolicyRecord] = []
    for ordinal, candidate in enumerate(candidates, start=1):
        exclusion = _resolve_exclusion_reason(candidate)
        if exclusion is not None:
            excluded.append(
                P04ExcludedPolicyRecord(
                    excluded_id=f"p04:{tick_id}:{tick_index}:{ordinal}:excluded",
                    policy_ref=candidate.policy_ref,
                    reason_code=exclusion,
                    hazard_only=True,
                    selectable_candidate=False,
                    reason="candidate violated policy guardrail and cannot be selected",
                    provenance="p04.policy.guardrail_exclusion",
                )
            )
            continue
        branches.append(
            _simulate_branch(
                tick_id=tick_id,
                tick_index=tick_index,
                ordinal=ordinal,
                candidate=candidate,
                simulation_input=explicit_input,
                prior_positive=prior_positive,
                prior_negative=prior_negative,
                prior_uncertain=prior_uncertain,
                prior_open_window=prior_open_window,
            )
        )

    unstable_regions = _build_unstable_regions(
        tick_id=tick_id,
        tick_index=tick_index,
        branches=tuple(branches),
        simulation_input=explicit_input,
    )
    comparison = _build_comparison_matrix(
        tick_id=tick_id,
        tick_index=tick_index,
        branches=tuple(branches),
        unstable_regions=unstable_regions,
    )

    (
        belief_conditioned_rollout,
        incomplete_information_support,
        false_belief_case_support,
        misread_case_support,
        knowledge_uncertainty_support,
    ) = _belief_support(explicit_input.assumptions)

    metadata = P04SimulationMetadata(
        simulation_id=f"p04:{tick_id}:metadata",
        evaluated_candidate_count=len(candidates),
        selectable_candidate_count=sum(
            int(item.outcome_status is P04BranchOutcomeStatus.SELECTABLE) for item in branches
        ),
        excluded_policy_count=len(excluded),
        belief_conditioned_rollout=belief_conditioned_rollout,
        incomplete_information_support=incomplete_information_support,
        false_belief_case_support=false_belief_case_support,
        misread_case_support=misread_case_support,
        knowledge_uncertainty_support=knowledge_uncertainty_support,
        source_lineage=source_lineage,
        reason=(
            "p04 metadata records branch coverage and belief-conditioned support without selecting final policy"
        ),
    )
    simulation_set = P04CounterfactualPolicySimulationSet(
        simulation_id=f"p04:{tick_id}:counterfactual_simulation",
        branch_records=tuple(branches),
        excluded_policies=tuple(excluded),
        unstable_regions=unstable_regions,
        comparison_matrix=comparison,
        metadata=metadata,
        reason=(
            "p04 generated explicit branch records, exclusions, unstable regions and contrastive comparison matrix"
        ),
    )
    gate = _build_gate(simulation_set=simulation_set)
    telemetry = _build_telemetry(simulation_set=simulation_set, gate=gate)
    scope = P04ScopeMarker(
        scope="rt01_hosted_p04_frontier_slice",
        rt01_hosted_only=True,
        p04_frontier_slice_only=True,
        simulation_not_selector=True,
        no_hidden_policy_selection_authority=True,
        no_policy_mutation_authority=True,
        no_map_wide_prediction_claim=True,
        no_full_social_world_prediction_claim=True,
        reason=(
            "p04 emits bounded counterfactual comparison artifacts only and never selects/mutates policy"
        ),
    )
    return P04SimulationResult(
        simulation_set=simulation_set,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=(
            "p04 produced typed counterfactual simulation artifacts for downstream consumers in RT01 hosted narrow slice"
        ),
    )


def _resolve_exclusion_reason(candidate: P04PolicyCandidate) -> P04ExclusionReason | None:
    if not candidate.licensed:
        return P04ExclusionReason.UNLICENSED_POLICY
    if candidate.scope_overrun:
        return P04ExclusionReason.SCOPE_OVERRUN
    if candidate.protective_conflict:
        return P04ExclusionReason.PROTECTIVE_CONFLICT
    return None


def _simulate_branch(
    *,
    tick_id: str,
    tick_index: int,
    ordinal: int,
    candidate: P04PolicyCandidate,
    simulation_input: P04SimulationInput,
    prior_positive: int,
    prior_negative: int,
    prior_uncertain: int,
    prior_open_window: int,
) -> P04BranchRecord:
    rupture = _clamp(simulation_input.current_rupture_risk)
    trust_fragility = _clamp(simulation_input.current_trust_fragility)
    coercion = _clamp(0.2 + simulation_input.current_dependency_pressure * 0.45)
    repair_debt = _clamp(simulation_input.current_commitment_strain * 0.45)
    delay_cost = _clamp(simulation_input.current_project_blockage * 0.4)

    project_progress = _clamp(0.35 + (1.0 - simulation_input.current_project_blockage) * 0.35)
    clarity_gain = 0.3
    trust_repair = _clamp(0.25 + (1.0 - trust_fragility) * 0.2)
    boundary_preservation = 0.35
    protective_load = _clamp(simulation_input.current_protective_load)
    commitment_stability = _clamp(0.3 + (1.0 - simulation_input.current_commitment_strain) * 0.35)
    sensitivity = _clamp(simulation_input.assumption_perturbation_level)
    unstable_factors: list[str] = list(simulation_input.missing_state_factors)

    sequencing = candidate.sequencing_rule.lower()
    if "clarify_before_boundary" in sequencing:
        clarity_gain += 0.24
        rupture -= 0.09
        delay_cost += 0.12
        trust_fragility -= 0.04
    elif "boundary_before_clarify" in sequencing:
        boundary_preservation += 0.22
        clarity_gain -= 0.12
        rupture += 0.07
        delay_cost -= 0.03
    elif "escalate_early" in sequencing:
        project_progress += 0.18
        coercion += 0.22
        rupture += 0.16
    else:
        project_progress += 0.05
        clarity_gain += 0.06

    timing = candidate.boundary_timing.lower()
    if "early" in timing:
        rupture -= 0.06
        boundary_preservation += 0.08
        delay_cost += 0.05
    elif "late" in timing:
        rupture += 0.09
        trust_fragility += 0.07
        project_progress += 0.08
    elif "phased" in timing:
        trust_repair += 0.06
        delay_cost += 0.04

    escalation = candidate.escalation_stance.lower()
    if "hard" in escalation or "assertive" in escalation:
        coercion += 0.18
        rupture += 0.1
        project_progress += 0.09
    elif "defer" in escalation or "none" in escalation:
        project_progress -= 0.05
        delay_cost += 0.07
        rupture -= 0.03
    elif "calibrated" in escalation:
        project_progress += 0.05
        rupture += 0.02

    deescalation = candidate.de_escalation_stance.lower()
    if "repair" in deescalation:
        trust_repair += 0.18
        rupture -= 0.08
        delay_cost += 0.06
    elif "none" in deescalation:
        trust_repair -= 0.05
        rupture += 0.04

    clarification = candidate.clarification_strategy.lower()
    if "explicit" in clarification:
        clarity_gain += 0.2
    elif "minimal" in clarification:
        clarity_gain -= 0.14
        trust_fragility += 0.06
    elif "probing" in clarification:
        clarity_gain += 0.1
        delay_cost += 0.05

    posture = candidate.boundary_posture.lower()
    if "rigid" in posture:
        boundary_preservation += 0.16
        protective_load += 0.18
        trust_fragility += 0.08
    elif "flexible" in posture:
        boundary_preservation -= 0.05
        trust_repair += 0.08
        rupture -= 0.03
    elif "guarded" in posture:
        boundary_preservation += 0.08
        protective_load += 0.09

    if not candidate.stopping_conditions:
        commitment_stability -= 0.08
        unstable_factors.append("missing_stopping_condition")
    if any("verification" in item.lower() for item in candidate.stopping_conditions):
        coercion -= 0.05
        clarity_gain += 0.05
    if any("exit_on_rupture" in item.lower() for item in candidate.stopping_conditions):
        rupture -= 0.05
        project_progress -= 0.04

    assumption_records = _assumption_records(simulation_input.assumptions)
    for assumption in simulation_input.assumptions:
        confidence = _clamp(assumption.shared_knowledge_confidence)
        if assumption.mode is P04BeliefStateMode.INCOMPLETE_INFORMATION:
            delay_cost += 0.08
            clarity_gain -= 0.07
            sensitivity += 0.2
            unstable_factors.append("incomplete_information")
        elif assumption.mode is P04BeliefStateMode.FALSE_BELIEF:
            rupture += 0.18
            trust_fragility += 0.14
            project_progress -= 0.12
            sensitivity += 0.26
            unstable_factors.append("false_belief")
        elif assumption.mode is P04BeliefStateMode.MISREAD:
            rupture += 0.12
            coercion += 0.1
            trust_repair -= 0.08
            sensitivity += 0.2
            unstable_factors.append("misread")
        elif assumption.mode is P04BeliefStateMode.KNOWLEDGE_UNCERTAINTY:
            delay_cost += 0.07
            clarity_gain -= 0.08
            sensitivity += 0.3
            unstable_factors.append("knowledge_uncertainty")
        else:
            sensitivity -= 0.08 * confidence

    if simulation_input.use_p03_priors:
        project_progress += 0.04 * min(prior_positive, 3)
        trust_repair += 0.03 * min(prior_positive, 3)
        rupture += 0.05 * min(prior_negative, 3)
        coercion += 0.03 * min(prior_negative + prior_uncertain, 4)
        trust_repair -= 0.04 * min(prior_negative, 3)
        sensitivity += 0.05 * min(prior_uncertain, 3)
        sensitivity += 0.06 * min(prior_open_window, 3)

    sensitivity += 0.12 * len(simulation_input.missing_state_factors)

    out_of_horizon = candidate.horizon_steps > simulation_input.horizon_steps
    if out_of_horizon:
        unstable_factors.append("out_of_horizon")

    rupture = _clamp(rupture)
    trust_fragility = _clamp(trust_fragility)
    coercion = _clamp(coercion)
    repair_debt = _clamp(repair_debt + max(0.0, rupture - trust_repair) * 0.2)
    delay_cost = _clamp(delay_cost)
    project_progress = _clamp(project_progress)
    clarity_gain = _clamp(clarity_gain)
    trust_repair = _clamp(trust_repair)
    boundary_preservation = _clamp(boundary_preservation)
    protective_load = _clamp(protective_load)
    commitment_stability = _clamp(commitment_stability)
    sensitivity = _clamp(sensitivity)
    uncertainty_status = _resolve_uncertainty_status(
        sensitivity=sensitivity,
        out_of_horizon=out_of_horizon,
    )
    uncertainty = P04BranchUncertaintyEnvelope(
        status=uncertainty_status,
        unstable_factors=tuple(dict.fromkeys(unstable_factors)),
        sensitivity=sensitivity,
        out_of_horizon=out_of_horizon,
        reason="p04 uncertainty envelope is explicit and guards selection claims when unstable",
    )

    transition_deltas = _transition_deltas(
        rupture=rupture - simulation_input.current_rupture_risk,
        trust=trust_repair - simulation_input.current_trust_fragility,
        coercion=coercion - simulation_input.current_dependency_pressure,
        progress=project_progress - simulation_input.current_project_blockage,
        commitment=commitment_stability - simulation_input.current_commitment_strain,
    )
    transitions = tuple(
        P04RelationalTransition(
            transition_id=f"p04:{tick_id}:{tick_index}:{ordinal}:transition:{index + 1}",
            transition_type=transition_type,
            delta=delta,
            reason=reason,
            provenance="p04.policy.branch_rollout",
        )
        for index, (transition_type, delta, reason) in enumerate(transition_deltas)
    )

    protective_load_effect = P04ProtectiveLoadEffect(
        load_delta=protective_load - simulation_input.current_protective_load,
        burden_class=_burden_class(protective_load - simulation_input.current_protective_load),
        reason="p04 preserves protective load movement as first-class branch effect",
    )
    commitment_effect = P04CommitmentEffect(
        commitment_delta=project_progress - delay_cost - 0.5,
        commitment_stability_delta=commitment_stability - 0.5,
        reason="p04 keeps commitment effects explicit instead of collapsing to scalar success",
    )
    risk_vector = P04BranchRiskVector(
        rupture_risk=rupture,
        trust_fragility=trust_fragility,
        coercion_risk=coercion,
        repair_debt=repair_debt,
        delay_cost=delay_cost,
    )
    benefit_vector = P04BranchBenefitVector(
        project_progress=project_progress,
        clarity_gain=clarity_gain,
        trust_repair=trust_repair,
        boundary_preservation=boundary_preservation,
    )
    ranking_score_hint = (
        project_progress
        + clarity_gain
        + trust_repair
        + boundary_preservation
        - rupture
        - coercion
        - (0.5 * delay_cost)
        - (0.4 * trust_fragility)
        - (0.3 * max(0.0, protective_load_effect.load_delta))
    )
    if candidate.candidate_role is P04CandidateRole.HAZARD_ONLY:
        ranking_score_hint -= 0.35
    return P04BranchRecord(
        branch_id=f"p04:{tick_id}:{tick_index}:{ordinal}:branch",
        policy_ref=candidate.policy_ref,
        outcome_status=(
            P04BranchOutcomeStatus.HAZARD_ONLY
            if candidate.candidate_role is P04CandidateRole.HAZARD_ONLY
            else P04BranchOutcomeStatus.SELECTABLE
        ),
        hazard_only=candidate.candidate_role is P04CandidateRole.HAZARD_ONLY,
        input_state_refs=simulation_input.input_state_refs,
        assumption_records=assumption_records,
        relational_transitions=transitions,
        risk_vector=risk_vector,
        benefit_vector=benefit_vector,
        protective_load_effect=protective_load_effect,
        commitment_effect=commitment_effect,
        uncertainty_envelope=uncertainty,
        out_of_horizon_marked=out_of_horizon,
        ranking_score_hint=ranking_score_hint,
        reason="p04 branch rollout evaluated typed policy candidate under explicit assumptions",
        provenance="p04.policy.branch_rollout",
    )


def _assumption_records(
    assumptions: tuple[P04BeliefStateAssumption, ...],
) -> tuple[P04BranchAssumptionRecord, ...]:
    return tuple(
        P04BranchAssumptionRecord(
            assumption_id=item.assumption_id,
            mode=item.mode,
            applied=True,
            confidence=_clamp(item.shared_knowledge_confidence),
            reason=item.reason or "belief-state assumption applied to branch rollout",
        )
        for item in assumptions
    )


def _resolve_uncertainty_status(
    *,
    sensitivity: float,
    out_of_horizon: bool,
) -> P04UncertaintyStatus:
    if out_of_horizon:
        return P04UncertaintyStatus.OUT_OF_HORIZON
    if sensitivity >= 0.7:
        return P04UncertaintyStatus.UNSTABLE
    if sensitivity >= 0.3:
        return P04UncertaintyStatus.GUARDED
    return P04UncertaintyStatus.STABLE


def _transition_deltas(
    *,
    rupture: float,
    trust: float,
    coercion: float,
    progress: float,
    commitment: float,
) -> tuple[tuple[P04TransitionType, float, str], ...]:
    transitions: list[tuple[P04TransitionType, float, str]] = []
    if rupture >= 0.02:
        transitions.append((P04TransitionType.RUPTURE_RISK_INCREASE, rupture, "rupture risk increased"))
    if rupture <= -0.02:
        transitions.append((P04TransitionType.RUPTURE_RISK_DECREASE, rupture, "rupture risk decreased"))
    if trust >= 0.02:
        transitions.append((P04TransitionType.TRUST_INCREASE, trust, "trust repair increased"))
    if trust <= -0.02:
        transitions.append((P04TransitionType.TRUST_DECREASE, trust, "trust repair decreased"))
    if coercion >= 0.02:
        transitions.append((P04TransitionType.COERCION_RISK_INCREASE, coercion, "coercion risk increased"))
    if coercion <= -0.02:
        transitions.append((P04TransitionType.COERCION_RISK_DECREASE, coercion, "coercion risk decreased"))
    if progress >= 0.02:
        transitions.append((P04TransitionType.PROJECT_PROGRESS_INCREASE, progress, "project progress increased"))
    if progress <= -0.02:
        transitions.append((P04TransitionType.PROJECT_PROGRESS_DECREASE, progress, "project progress decreased"))
    if commitment >= 0.02:
        transitions.append(
            (
                P04TransitionType.COMMITMENT_STABILITY_INCREASE,
                commitment,
                "commitment stability increased",
            )
        )
    if commitment <= -0.02:
        transitions.append(
            (
                P04TransitionType.COMMITMENT_STABILITY_DECREASE,
                commitment,
                "commitment stability decreased",
            )
        )
    if not transitions:
        transitions.append((P04TransitionType.REPAIR_CAPACITY_DECREASE, 0.0, "no material transition"))
    return tuple(transitions)


def _build_unstable_regions(
    *,
    tick_id: str,
    tick_index: int,
    branches: tuple[P04BranchRecord, ...],
    simulation_input: P04SimulationInput,
) -> tuple[P04UnstableRegion, ...]:
    selectable = tuple(
        item for item in branches if item.outcome_status is P04BranchOutcomeStatus.SELECTABLE
    )
    unstable = tuple(
        item
        for item in selectable
        if item.uncertainty_envelope.status in {P04UncertaintyStatus.UNSTABLE, P04UncertaintyStatus.OUT_OF_HORIZON}
    )
    if not selectable:
        return (
            P04UnstableRegion(
                region_id=f"p04:{tick_id}:{tick_index}:unstable:no_selectable",
                policy_refs=(),
                trigger_factors=("no_selectable_branches",),
                no_clear_dominance=True,
                comparison_only=True,
                simulation_blocked=True,
                reason="no selectable branches remain after guardrail exclusions",
                provenance="p04.policy.unstable_region",
            ),
        )
    missing_state_heavy = len(simulation_input.missing_state_factors) >= 2
    high_perturbation = simulation_input.assumption_perturbation_level >= 0.7
    if not unstable and not missing_state_heavy and not high_perturbation:
        return ()
    trigger_factors = list(simulation_input.missing_state_factors)
    if high_perturbation:
        trigger_factors.append("assumption_perturbation_high")
    if unstable:
        trigger_factors.extend(
            f"uncertainty:{item.policy_ref}:{item.uncertainty_envelope.status.value}" for item in unstable
        )
    return (
        P04UnstableRegion(
            region_id=f"p04:{tick_id}:{tick_index}:unstable:1",
            policy_refs=tuple(item.policy_ref for item in selectable),
            trigger_factors=tuple(dict.fromkeys(trigger_factors)),
            no_clear_dominance=True,
            comparison_only=True,
            simulation_blocked=bool(unstable),
            reason=(
                "branch ranking is sensitivity-heavy; p04 returns comparison-only unstable region instead of sharp selection"
            ),
            provenance="p04.policy.unstable_region",
        ),
    )


def _build_comparison_matrix(
    *,
    tick_id: str,
    tick_index: int,
    branches: tuple[P04BranchRecord, ...],
    unstable_regions: tuple[P04UnstableRegion, ...],
) -> P04ComparisonMatrix:
    selectable = tuple(
        item for item in branches if item.outcome_status is P04BranchOutcomeStatus.SELECTABLE
    )
    contrasts: list[P04ContrastiveDifference] = []
    for index, lhs in enumerate(selectable):
        for rhs in selectable[index + 1 :]:
            lhs_risk = lhs.risk_vector.rupture_risk + lhs.risk_vector.coercion_risk
            rhs_risk = rhs.risk_vector.rupture_risk + rhs.risk_vector.coercion_risk
            lhs_delay = lhs.risk_vector.delay_cost
            rhs_delay = rhs.risk_vector.delay_cost
            lhs_boundary = lhs.benefit_vector.boundary_preservation
            rhs_boundary = rhs.benefit_vector.boundary_preservation
            lhs_clarity = lhs.benefit_vector.clarity_gain
            rhs_clarity = rhs.benefit_vector.clarity_gain

            faster_but_riskier = lhs_delay + 0.07 < rhs_delay and lhs_risk > rhs_risk + 0.08
            slower_but_safer = lhs_delay > rhs_delay + 0.07 and lhs_risk + 0.08 < rhs_risk
            preserves_boundary_leaves_ambiguity = (
                lhs_boundary > rhs_boundary + 0.08 and lhs_clarity + 0.08 < rhs_clarity
            )
            lowers_rupture_increases_delay = (
                lhs.risk_vector.rupture_risk + 0.08 < rhs.risk_vector.rupture_risk
                and lhs_delay > rhs_delay + 0.07
            )
            summary_codes = []
            if faster_but_riskier:
                summary_codes.append("faster_but_riskier")
            if slower_but_safer:
                summary_codes.append("slower_but_safer")
            if preserves_boundary_leaves_ambiguity:
                summary_codes.append("preserves_boundary_leaves_ambiguity")
            if lowers_rupture_increases_delay:
                summary_codes.append("lowers_rupture_increases_delay")
            if not summary_codes:
                summary_codes.append("net_tradeoff_present")
            contrasts.append(
                P04ContrastiveDifference(
                    contrast_id=f"p04:{tick_id}:{tick_index}:contrast:{len(contrasts) + 1}",
                    lhs_policy_ref=lhs.policy_ref,
                    rhs_policy_ref=rhs.policy_ref,
                    faster_but_riskier=faster_but_riskier,
                    slower_but_safer=slower_but_safer,
                    preserves_boundary_leaves_ambiguity=preserves_boundary_leaves_ambiguity,
                    lowers_rupture_increases_delay=lowers_rupture_increases_delay,
                    summary_codes=tuple(summary_codes),
                    reason="p04 emits explicit branch-to-branch tradeoff contrast",
                    provenance="p04.policy.comparison",
                )
            )

    if not selectable:
        return P04ComparisonMatrix(
            matrix_id=f"p04:{tick_id}:{tick_index}:comparison",
            contrasts=tuple(contrasts),
            dominance_state=P04DominanceState.NO_CLEAR_DOMINANCE,
            comparison_readiness=P04ComparisonReadiness.BLOCKED,
            no_clear_dominance=True,
            reason="no selectable branch exists; comparison is blocked",
        )

    if unstable_regions:
        return P04ComparisonMatrix(
            matrix_id=f"p04:{tick_id}:{tick_index}:comparison",
            contrasts=tuple(contrasts),
            dominance_state=P04DominanceState.UNSTABLE_REGION,
            comparison_readiness=P04ComparisonReadiness.COMPARISON_ONLY,
            no_clear_dominance=True,
            reason="unstable region detected; p04 allows comparison-only and blocks dominance claim",
        )

    if len(selectable) == 1:
        return P04ComparisonMatrix(
            matrix_id=f"p04:{tick_id}:{tick_index}:comparison",
            contrasts=tuple(contrasts),
            dominance_state=P04DominanceState.CLEAR_DOMINANCE,
            comparison_readiness=P04ComparisonReadiness.SELECTION_READY,
            no_clear_dominance=False,
            reason="single selectable branch remains after exclusions",
        )

    ordered = sorted(selectable, key=lambda item: item.ranking_score_hint, reverse=True)
    lead_margin = ordered[0].ranking_score_hint - ordered[1].ranking_score_hint
    if lead_margin >= 0.25:
        return P04ComparisonMatrix(
            matrix_id=f"p04:{tick_id}:{tick_index}:comparison",
            contrasts=tuple(contrasts),
            dominance_state=P04DominanceState.CLEAR_DOMINANCE,
            comparison_readiness=P04ComparisonReadiness.SELECTION_READY,
            no_clear_dominance=False,
            reason="bounded comparison found a clear dominance margin",
        )
    return P04ComparisonMatrix(
        matrix_id=f"p04:{tick_id}:{tick_index}:comparison",
        contrasts=tuple(contrasts),
        dominance_state=P04DominanceState.NO_CLEAR_DOMINANCE,
        comparison_readiness=P04ComparisonReadiness.COMPARISON_ONLY,
        no_clear_dominance=True,
        reason="bounded comparison found no clear dominance margin",
    )


def _belief_support(
    assumptions: tuple[P04BeliefStateAssumption, ...],
) -> tuple[bool, bool, bool, bool, bool]:
    if not assumptions:
        return False, False, False, False, False
    modes = {item.mode for item in assumptions}
    return (
        True,
        P04BeliefStateMode.INCOMPLETE_INFORMATION in modes
        or any(item.incomplete_information_support for item in assumptions),
        P04BeliefStateMode.FALSE_BELIEF in modes
        or any(item.false_belief_case_support for item in assumptions),
        P04BeliefStateMode.MISREAD in modes
        or any(item.misread_case_support for item in assumptions),
        P04BeliefStateMode.KNOWLEDGE_UNCERTAINTY in modes
        or any(item.knowledge_uncertainty_support for item in assumptions),
    )


def _build_gate(
    *,
    simulation_set: P04CounterfactualPolicySimulationSet,
) -> P04SimulationGateDecision:
    branch_ready = bool(simulation_set.branch_records)
    comparison_ready = (
        bool(simulation_set.branch_records)
        and simulation_set.comparison_matrix.comparison_readiness is not P04ComparisonReadiness.BLOCKED
    )
    excluded_ready = bool(simulation_set.excluded_policies)
    restrictions: list[str] = []
    if not branch_ready:
        restrictions.append("branch_record_consumer_not_ready")
    if not comparison_ready:
        restrictions.append("comparison_consumer_not_ready")
    if not excluded_ready:
        restrictions.append("excluded_policy_consumer_not_ready")
    return P04SimulationGateDecision(
        branch_record_consumer_ready=branch_ready,
        comparison_consumer_ready=comparison_ready,
        excluded_policy_consumer_ready=excluded_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "p04 gate exposes branch/comparison/exclusion consumer readiness without selecting final policy"
        ),
    )


def _build_telemetry(
    *,
    simulation_set: P04CounterfactualPolicySimulationSet,
    gate: P04SimulationGateDecision,
) -> P04Telemetry:
    metadata = simulation_set.metadata
    return P04Telemetry(
        branch_count=len(simulation_set.branch_records),
        selectable_branch_count=sum(
            int(item.outcome_status is P04BranchOutcomeStatus.SELECTABLE)
            for item in simulation_set.branch_records
        ),
        excluded_policy_count=len(simulation_set.excluded_policies),
        unstable_region_count=len(simulation_set.unstable_regions),
        no_clear_dominance_count=int(simulation_set.comparison_matrix.no_clear_dominance),
        belief_conditioned_rollout=metadata.belief_conditioned_rollout,
        incomplete_information_support=metadata.incomplete_information_support,
        false_belief_case_support=metadata.false_belief_case_support,
        misread_case_support=metadata.misread_case_support,
        knowledge_uncertainty_support=metadata.knowledge_uncertainty_support,
        guardrail_exclusion_count=sum(
            int(
                item.reason_code
                in {
                    P04ExclusionReason.UNLICENSED_POLICY,
                    P04ExclusionReason.SCOPE_OVERRUN,
                    P04ExclusionReason.PROTECTIVE_CONFLICT,
                }
            )
            for item in simulation_set.excluded_policies
        ),
        downstream_consumer_ready=(
            gate.branch_record_consumer_ready and gate.comparison_consumer_ready
        ),
    )


def _build_minimal_result(
    *,
    reason: str,
    restrictions: tuple[str, ...],
    source_lineage: tuple[str, ...],
) -> P04SimulationResult:
    metadata = P04SimulationMetadata(
        simulation_id="p04:minimal:metadata",
        evaluated_candidate_count=0,
        selectable_candidate_count=0,
        excluded_policy_count=0,
        belief_conditioned_rollout=False,
        incomplete_information_support=False,
        false_belief_case_support=False,
        misread_case_support=False,
        knowledge_uncertainty_support=False,
        source_lineage=source_lineage,
        reason=reason,
    )
    comparison = P04ComparisonMatrix(
        matrix_id="p04:minimal:comparison",
        contrasts=(),
        dominance_state=P04DominanceState.NO_CLEAR_DOMINANCE,
        comparison_readiness=P04ComparisonReadiness.BLOCKED,
        no_clear_dominance=False,
        reason=reason,
    )
    simulation_set = P04CounterfactualPolicySimulationSet(
        simulation_id="p04:minimal",
        branch_records=(),
        excluded_policies=(),
        unstable_regions=(),
        comparison_matrix=comparison,
        metadata=metadata,
        reason=reason,
    )
    gate = P04SimulationGateDecision(
        branch_record_consumer_ready=False,
        comparison_consumer_ready=False,
        excluded_policy_consumer_ready=False,
        restrictions=restrictions,
        reason=reason,
    )
    telemetry = P04Telemetry(
        branch_count=0,
        selectable_branch_count=0,
        excluded_policy_count=0,
        unstable_region_count=0,
        no_clear_dominance_count=0,
        belief_conditioned_rollout=False,
        incomplete_information_support=False,
        false_belief_case_support=False,
        misread_case_support=False,
        knowledge_uncertainty_support=False,
        guardrail_exclusion_count=0,
        downstream_consumer_ready=False,
    )
    scope = P04ScopeMarker(
        scope="rt01_hosted_p04_frontier_slice",
        rt01_hosted_only=True,
        p04_frontier_slice_only=True,
        simulation_not_selector=True,
        no_hidden_policy_selection_authority=True,
        no_policy_mutation_authority=True,
        no_map_wide_prediction_claim=True,
        no_full_social_world_prediction_claim=True,
        reason="p04 minimal fallback scope",
    )
    return P04SimulationResult(
        simulation_set=simulation_set,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _burden_class(delta: float) -> str:
    if delta > 0.05:
        return "increased"
    if delta < -0.05:
        return "decreased"
    return "stable"
