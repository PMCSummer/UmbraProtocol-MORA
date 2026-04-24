from __future__ import annotations

from dataclasses import dataclass

from substrate.r05_appraisal_sovereign_protective_regulation import (
    R05ProtectiveResult,
    R05ProtectiveTriggerInput,
    build_r05_appraisal_sovereign_protective_regulation,
)
from substrate.p01_project_formation import (
    P01AuthoritySourceKind,
    P01ProjectFormationResult,
    P01ProjectSignalInput,
    build_p01_project_formation,
)
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommunicativeActCandidate,
    V01LicenseResult,
    build_v01_normative_permission_commitment_licensing,
)
from substrate.v02_communicative_intent_utterance_plan_bridge import (
    V02UtterancePlanInput,
    V02UtterancePlanResult,
    V02UtterancePlanState,
    build_v02_communicative_intent_utterance_plan_bridge,
)


@dataclass(frozen=True, slots=True)
class V02HarnessCase:
    case_id: str
    tick_index: int
    act_candidates: tuple[V01CommunicativeActCandidate, ...]
    plan_input: V02UtterancePlanInput | None = None
    r05_result: R05ProtectiveResult | None = None
    p01_result: P01ProjectFormationResult | None = None
    prior_state: V02UtterancePlanState | None = None
    planning_enabled: bool = True


def v01_candidate(
    *,
    act_id: str,
    act_type: V01ActType,
    proposition_ref: str,
    evidence_strength: float = 0.0,
    authority_basis_present: bool = False,
    explicit_uncertainty_present: bool = False,
    helpfulness_pressure: float = 0.0,
    protective_sensitivity: bool = False,
    commitment_target_ref: str | None = None,
) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=act_type,
        proposition_ref=proposition_ref,
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        explicit_uncertainty_present=explicit_uncertainty_present,
        helpfulness_pressure=helpfulness_pressure,
        protective_sensitivity=protective_sensitivity,
        commitment_target_ref=commitment_target_ref,
        provenance=f"tests.v02.candidate:{act_id}",
    )


def v02_plan_input(
    *,
    input_id: str,
    prior_unresolved_question: bool = False,
    prior_refusal_present: bool = False,
    prior_commitment_carry_present: bool = False,
    prior_repair_required: bool = False,
    discourse_pressure_hint: float = 0.0,
) -> V02UtterancePlanInput:
    return V02UtterancePlanInput(
        input_id=input_id,
        prior_unresolved_question=prior_unresolved_question,
        prior_refusal_present=prior_refusal_present,
        prior_commitment_carry_present=prior_commitment_carry_present,
        prior_repair_required=prior_repair_required,
        discourse_pressure_hint=discourse_pressure_hint,
        provenance=f"tests.v02.input:{input_id}",
    )


def build_r05_protective_basis(case_id: str) -> R05ProtectiveResult:
    return build_r05_appraisal_sovereign_protective_regulation(
        tick_id=f"r05-for-v02:{case_id}",
        tick_index=1,
        protective_triggers=(
            R05ProtectiveTriggerInput(
                trigger_id=f"{case_id}:r05-trigger",
                trigger_kind="coercive_structure_basis",
                threat_structure_score=0.88,
                load_pressure_score=0.72,
                o04_coercive_structure_present=True,
                o04_rupture_risk_present=True,
                p01_project_continuation_active=True,
                communication_surface_exposed=True,
                project_continuation_requested=True,
                permission_hardening_available=True,
                provenance=f"tests.v02.r05:{case_id}",
            ),
        ),
        o04_result=None,
        p01_result=None,
        source_lineage=(f"tests.v02.r05:{case_id}",),
    )


def build_p01_blocked_basis(case_id: str) -> P01ProjectFormationResult:
    return build_p01_project_formation(
        tick_id=f"p01-for-v02:{case_id}",
        tick_index=1,
        signals=(
            P01ProjectSignalInput(
                signal_id=f"{case_id}:p01-signal",
                signal_kind="directive",
                authority_source_kind=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                target_summary="deliver constrained execution handoff",
                grounded_basis_present=True,
                missing_precondition_marker=True,
                provenance=f"tests.v02.p01:{case_id}",
            ),
        ),
        o03_result=None,
        source_lineage=(f"tests.v02.p01:{case_id}",),
    )


def build_v02_harness_case(case: V02HarnessCase) -> V02UtterancePlanResult:
    v01_result: V01LicenseResult = build_v01_normative_permission_commitment_licensing(
        tick_id=f"v01-for-v02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        act_candidates=case.act_candidates,
        r05_result=case.r05_result,
        source_lineage=(f"tests.v02.v01:{case.case_id}",),
    )
    return build_v02_communicative_intent_utterance_plan_bridge(
        tick_id=f"v02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        v01_result=v01_result,
        r05_result=case.r05_result,
        o04_result=None,
        p01_result=case.p01_result,
        plan_input=case.plan_input,
        source_lineage=(f"tests.v02:{case.case_id}",),
        prior_state=case.prior_state,
        planning_enabled=case.planning_enabled,
    )


def harness_cases() -> dict[str, V02HarnessCase]:
    proposition = "prop:v02-plan-bridge"
    return {
        "assertion_base": V02HarnessCase(
            case_id="assertion_base",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-base-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
        ),
        "assertion_with_unresolved_history": V02HarnessCase(
            case_id="assertion_with_unresolved_history",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-history-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
            plan_input=v02_plan_input(
                input_id="history:clarification-first",
                prior_unresolved_question=True,
            ),
        ),
        "weak_assertion_qualifier_binding": V02HarnessCase(
            case_id="weak_assertion_qualifier_binding",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-weak-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.52,
                    authority_basis_present=True,
                ),
            ),
        ),
        "branch_ambiguity": V02HarnessCase(
            case_id="branch_ambiguity",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-branch-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.92,
                    authority_basis_present=True,
                ),
            ),
            plan_input=v02_plan_input(
                input_id="history:branch-ambiguity",
                prior_unresolved_question=True,
                prior_refusal_present=True,
            ),
        ),
        "protective_structure": V02HarnessCase(
            case_id="protective_structure",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="advice-protective-1",
                    act_type=V01ActType.ADVICE,
                    proposition_ref=proposition,
                    evidence_strength=0.84,
                    authority_basis_present=True,
                    protective_sensitivity=True,
                ),
            ),
            r05_result=build_r05_protective_basis("protective_structure"),
        ),
        "p01_blocked_handoff": V02HarnessCase(
            case_id="p01_blocked_handoff",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-p01-blocked-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
            p01_result=build_p01_blocked_basis("p01_blocked_handoff"),
        ),
        "commitment_split": V02HarnessCase(
            case_id="commitment_split",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-for-split-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.92,
                    authority_basis_present=True,
                ),
                v01_candidate(
                    act_id="promise-for-split-1",
                    act_type=V01ActType.PROMISE,
                    proposition_ref=proposition,
                    evidence_strength=0.62,
                    authority_basis_present=True,
                    commitment_target_ref="target:v02",
                ),
            ),
        ),
        "no_basis": V02HarnessCase(
            case_id="no_basis",
            tick_index=1,
            act_candidates=(),
            plan_input=None,
        ),
        "disabled": V02HarnessCase(
            case_id="disabled",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="disabled-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
            planning_enabled=False,
        ),
    }
