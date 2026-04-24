from __future__ import annotations

from dataclasses import dataclass

from substrate.r05_appraisal_sovereign_protective_regulation import (
    R05ProtectiveResult,
    R05ProtectiveTriggerInput,
    build_r05_appraisal_sovereign_protective_regulation,
)
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommunicativeActCandidate,
    V01CommunicativeLicenseState,
    V01LicenseResult,
    build_v01_normative_permission_commitment_licensing,
)


@dataclass(frozen=True, slots=True)
class V01HarnessCase:
    case_id: str
    tick_index: int
    act_candidates: tuple[V01CommunicativeActCandidate, ...]
    r05_result: R05ProtectiveResult | None = None
    prior_state: V01CommunicativeLicenseState | None = None
    licensing_enabled: bool = True


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
        provenance=f"tests.v01.candidate:{act_id}",
    )


def build_v01_harness_case(case: V01HarnessCase) -> V01LicenseResult:
    return build_v01_normative_permission_commitment_licensing(
        tick_id=f"v01:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        act_candidates=case.act_candidates,
        r05_result=case.r05_result,
        source_lineage=(f"tests.v01:{case.case_id}",),
        prior_state=case.prior_state,
        licensing_enabled=case.licensing_enabled,
    )


def build_r05_active_override_basis(case_id: str) -> R05ProtectiveResult:
    return build_r05_appraisal_sovereign_protective_regulation(
        tick_id=f"r05-for-v01:{case_id}",
        tick_index=1,
        protective_triggers=(
            R05ProtectiveTriggerInput(
                trigger_id=f"{case_id}:r05-trigger",
                threat_structure_score=0.86,
                o04_coercive_structure_present=True,
                p01_project_continuation_active=True,
                project_continuation_requested=True,
                communication_surface_exposed=True,
                provenance=f"tests.v01.r05:{case_id}",
            ),
        ),
        o04_result=None,
        p01_result=None,
        source_lineage=(f"tests.v01.r05:{case_id}",),
    )


def harness_cases() -> dict[str, V01HarnessCase]:
    proposition = "prop:bounded-runtime-guidance"
    return {
        "assertion_strong": V01HarnessCase(
            case_id="assertion_strong",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-strong-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
        ),
        "assertion_weak": V01HarnessCase(
            case_id="assertion_weak",
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
        "assertion_missing": V01HarnessCase(
            case_id="assertion_missing",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-missing-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.12,
                    authority_basis_present=False,
                ),
            ),
        ),
        "advice_helpfulness_shortcut": V01HarnessCase(
            case_id="advice_helpfulness_shortcut",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="advice-helpfulness-1",
                    act_type=V01ActType.ADVICE,
                    proposition_ref=proposition,
                    evidence_strength=0.8,
                    authority_basis_present=False,
                    helpfulness_pressure=0.95,
                ),
            ),
        ),
        "promise_strong": V01HarnessCase(
            case_id="promise_strong",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="promise-strong-1",
                    act_type=V01ActType.PROMISE,
                    proposition_ref=proposition,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                    commitment_target_ref="target:deliverable",
                ),
            ),
        ),
        "promise_weakened_by_assertion_split": V01HarnessCase(
            case_id="promise_weakened_by_assertion_split",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-for-promise-split-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.86,
                    authority_basis_present=True,
                ),
                v01_candidate(
                    act_id="promise-split-1",
                    act_type=V01ActType.PROMISE,
                    proposition_ref=proposition,
                    evidence_strength=0.62,
                    authority_basis_present=True,
                    commitment_target_ref="target:deliverable",
                ),
            ),
        ),
        "protective_defer_advice": V01HarnessCase(
            case_id="protective_defer_advice",
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
            r05_result=build_r05_active_override_basis("protective_defer_advice"),
        ),
        "disabled": V01HarnessCase(
            case_id="disabled",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="disabled-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.9,
                    authority_basis_present=True,
                ),
            ),
            licensing_enabled=False,
        ),
    }
