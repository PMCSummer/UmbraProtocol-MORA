from __future__ import annotations

from dataclasses import dataclass

from substrate.p04_interpersonal_counterfactual_policy_simulation import (
    P04BeliefStateAssumption,
    P04BeliefStateMode,
    P04CandidateRole,
    P04PolicyCandidate,
    P04PolicyCandidateSet,
    P04PolicyClass,
    P04SimulationInput,
    P04SimulationResult,
    build_p04_interpersonal_counterfactual_policy_simulation,
)
from tests.substrate.p03_long_horizon_credit_assignment_intervention_learning_testkit import (
    P03HarnessRun,
    build_p03_harness_case,
    harness_cases as p03_harness_cases,
)


def p04_candidate(
    *,
    candidate_id: str,
    policy_ref: str,
    policy_class: P04PolicyClass,
    action_class: str,
    sequencing_rule: str,
    escalation_stance: str,
    de_escalation_stance: str,
    clarification_strategy: str,
    boundary_posture: str,
    boundary_timing: str,
    stopping_conditions: tuple[str, ...],
    horizon_steps: int,
    candidate_role: P04CandidateRole = P04CandidateRole.SELECTABLE,
    licensed: bool = True,
    scope_overrun: bool = False,
    protective_conflict: bool = False,
) -> P04PolicyCandidate:
    return P04PolicyCandidate(
        candidate_id=candidate_id,
        policy_ref=policy_ref,
        policy_class=policy_class,
        action_class=action_class,
        sequencing_rule=sequencing_rule,
        escalation_stance=escalation_stance,
        de_escalation_stance=de_escalation_stance,
        clarification_strategy=clarification_strategy,
        boundary_posture=boundary_posture,
        boundary_timing=boundary_timing,
        stopping_conditions=stopping_conditions,
        horizon_steps=horizon_steps,
        candidate_role=candidate_role,
        licensed=licensed,
        scope_overrun=scope_overrun,
        protective_conflict=protective_conflict,
        provenance=f"tests.p04.candidate:{candidate_id}",
    )


def p04_candidate_set(
    *,
    set_id: str,
    candidates: tuple[P04PolicyCandidate, ...],
) -> P04PolicyCandidateSet:
    return P04PolicyCandidateSet(
        candidate_set_id=set_id,
        candidates=candidates,
        reason=f"tests.p04.candidate_set:{set_id}",
        provenance=f"tests.p04.candidate_set:{set_id}",
    )


def p04_assumption(
    *,
    assumption_id: str,
    mode: P04BeliefStateMode,
    shared_knowledge_confidence: float,
    incomplete_information_support: bool = False,
    false_belief_case_support: bool = False,
    misread_case_support: bool = False,
    knowledge_uncertainty_support: bool = False,
    summary: str = "",
) -> P04BeliefStateAssumption:
    return P04BeliefStateAssumption(
        assumption_id=assumption_id,
        mode=mode,
        other_agent_state_summary=summary or f"tests.p04.assumption:{assumption_id}",
        shared_knowledge_confidence=shared_knowledge_confidence,
        incomplete_information_support=incomplete_information_support,
        false_belief_case_support=false_belief_case_support,
        misread_case_support=misread_case_support,
        knowledge_uncertainty_support=knowledge_uncertainty_support,
        reason=f"tests.p04.assumption:{assumption_id}",
        provenance=f"tests.p04.assumption:{assumption_id}",
    )


def p04_simulation_input(
    *,
    input_id: str,
    candidate_set: P04PolicyCandidateSet,
    input_state_refs: tuple[str, ...] = (),
    p02_episode_refs: tuple[str, ...] = (),
    p03_credit_refs: tuple[str, ...] = (),
    current_rupture_risk: float = 0.5,
    current_trust_fragility: float = 0.5,
    current_dependency_pressure: float = 0.5,
    current_project_blockage: float = 0.5,
    current_protective_load: float = 0.5,
    current_commitment_strain: float = 0.5,
    horizon_steps: int = 3,
    assumptions: tuple[P04BeliefStateAssumption, ...] = (),
    missing_state_factors: tuple[str, ...] = (),
    assumption_perturbation_level: float = 0.0,
    use_p03_priors: bool = True,
) -> P04SimulationInput:
    return P04SimulationInput(
        input_id=input_id,
        candidate_set=candidate_set,
        input_state_refs=input_state_refs,
        p02_episode_refs=p02_episode_refs,
        p03_credit_refs=p03_credit_refs,
        current_rupture_risk=current_rupture_risk,
        current_trust_fragility=current_trust_fragility,
        current_dependency_pressure=current_dependency_pressure,
        current_project_blockage=current_project_blockage,
        current_protective_load=current_protective_load,
        current_commitment_strain=current_commitment_strain,
        horizon_steps=horizon_steps,
        assumptions=assumptions,
        missing_state_factors=missing_state_factors,
        assumption_perturbation_level=assumption_perturbation_level,
        use_p03_priors=use_p03_priors,
        provenance=f"tests.p04.input:{input_id}",
    )


@dataclass(frozen=True, slots=True)
class P04HarnessCase:
    case_id: str
    simulation_input: P04SimulationInput | None
    p03_case_key: str = "modest_immediate_later_durable_success"
    simulation_enabled: bool = True


@dataclass(frozen=True, slots=True)
class P04HarnessRun:
    p04_result: P04SimulationResult
    p03_run: P03HarnessRun


def build_p04_harness_case(case: P04HarnessCase) -> P04HarnessRun:
    p03_case = p03_harness_cases()[case.p03_case_key]
    p03_run = build_p03_harness_case(p03_case)
    p04_result = build_p04_interpersonal_counterfactual_policy_simulation(
        tick_id=f"tests.p04:{case.case_id}",
        tick_index=1,
        p02_result=p03_run.p02_result,
        p03_result=p03_run.p03_result,
        simulation_input=case.simulation_input,
        source_lineage=("tests.p04", case.case_id),
        simulation_enabled=case.simulation_enabled,
    )
    return P04HarnessRun(
        p04_result=p04_result,
        p03_run=p03_run,
    )
