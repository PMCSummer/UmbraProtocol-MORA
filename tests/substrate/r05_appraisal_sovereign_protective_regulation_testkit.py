from __future__ import annotations

from dataclasses import dataclass

from substrate.r05_appraisal_sovereign_protective_regulation import (
    R05ProtectiveRegulationState,
    R05ProtectiveResult,
    R05ProtectiveTriggerInput,
    build_r05_appraisal_sovereign_protective_regulation,
)


@dataclass(frozen=True, slots=True)
class R05HarnessCase:
    case_id: str
    tick_index: int
    protective_triggers: tuple[R05ProtectiveTriggerInput, ...]
    regulation_enabled: bool = True
    prior_state: R05ProtectiveRegulationState | None = None


def r05_trigger(
    *,
    trigger_id: str,
    threat_structure_score: float = 0.0,
    load_pressure_score: float = 0.0,
    o04_coercive_structure_present: bool = False,
    o04_rupture_risk_present: bool = False,
    p01_project_continuation_active: bool = True,
    p01_blocked_or_conflicted: bool = False,
    communication_surface_exposed: bool = True,
    project_continuation_requested: bool = True,
    permission_hardening_available: bool = True,
    escalation_route_available: bool = False,
    tone_only_discomfort: bool = False,
    counterevidence_present: bool = False,
    release_signal_present: bool = False,
) -> R05ProtectiveTriggerInput:
    return R05ProtectiveTriggerInput(
        trigger_id=trigger_id,
        threat_structure_score=threat_structure_score,
        load_pressure_score=load_pressure_score,
        o04_coercive_structure_present=o04_coercive_structure_present,
        o04_rupture_risk_present=o04_rupture_risk_present,
        p01_project_continuation_active=p01_project_continuation_active,
        p01_blocked_or_conflicted=p01_blocked_or_conflicted,
        communication_surface_exposed=communication_surface_exposed,
        project_continuation_requested=project_continuation_requested,
        permission_hardening_available=permission_hardening_available,
        escalation_route_available=escalation_route_available,
        tone_only_discomfort=tone_only_discomfort,
        counterevidence_present=counterevidence_present,
        release_signal_present=release_signal_present,
        provenance=f"tests.r05.trigger:{trigger_id}",
    )


def build_r05_harness_case(case: R05HarnessCase) -> R05ProtectiveResult:
    return build_r05_appraisal_sovereign_protective_regulation(
        tick_id=f"r05:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        protective_triggers=case.protective_triggers,
        o04_result=None,
        p01_result=None,
        source_lineage=(f"tests.r05:{case.case_id}",),
        prior_state=case.prior_state,
        regulation_enabled=case.regulation_enabled,
    )


def harness_cases() -> dict[str, R05HarnessCase]:
    return {
        "no_signal": R05HarnessCase(
            case_id="no_signal",
            tick_index=1,
            protective_triggers=(),
        ),
        "rude_low_basis_tone_only": R05HarnessCase(
            case_id="rude_low_basis_tone_only",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="rude-1",
                    threat_structure_score=0.12,
                    tone_only_discomfort=True,
                ),
            ),
        ),
        "polite_structural_threat": R05HarnessCase(
            case_id="polite_structural_threat",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="polite-1",
                    threat_structure_score=0.78,
                    o04_coercive_structure_present=True,
                    tone_only_discomfort=False,
                ),
            ),
        ),
        "same_words_low_structure": R05HarnessCase(
            case_id="same_words_low_structure",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="same-low-1",
                    threat_structure_score=0.24,
                    tone_only_discomfort=False,
                ),
            ),
        ),
        "same_words_high_structure": R05HarnessCase(
            case_id="same_words_high_structure",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="same-high-1",
                    threat_structure_score=0.78,
                    o04_coercive_structure_present=True,
                    tone_only_discomfort=False,
                ),
            ),
        ),
        "surface_exposure_wide": R05HarnessCase(
            case_id="surface_exposure_wide",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="surface-wide-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                    communication_surface_exposed=True,
                    project_continuation_requested=True,
                    permission_hardening_available=True,
                    escalation_route_available=True,
                ),
            ),
        ),
        "surface_exposure_narrow": R05HarnessCase(
            case_id="surface_exposure_narrow",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="surface-narrow-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                    communication_surface_exposed=False,
                    project_continuation_requested=False,
                    permission_hardening_available=False,
                    escalation_route_available=False,
                ),
            ),
        ),
        "weak_basis_candidate": R05HarnessCase(
            case_id="weak_basis_candidate",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="weak-candidate-1",
                    threat_structure_score=0.38,
                    project_continuation_requested=True,
                    p01_project_continuation_active=False,
                ),
            ),
        ),
        "insufficient_basis_for_override": R05HarnessCase(
            case_id="insufficient_basis_for_override",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="insufficient-1",
                    threat_structure_score=0.12,
                    project_continuation_requested=False,
                    p01_project_continuation_active=False,
                ),
            ),
        ),
        "regulation_conflict": R05HarnessCase(
            case_id="regulation_conflict",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="conflict-1",
                    threat_structure_score=0.62,
                    p01_blocked_or_conflicted=True,
                    project_continuation_requested=True,
                    release_signal_present=True,
                ),
            ),
        ),
        "release_candidate_high": R05HarnessCase(
            case_id="release_candidate_high",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="release-high-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                ),
            ),
        ),
        "disabled": R05HarnessCase(
            case_id="disabled",
            tick_index=1,
            protective_triggers=(
                r05_trigger(
                    trigger_id="disabled-1",
                    threat_structure_score=0.8,
                    o04_coercive_structure_present=True,
                ),
            ),
            regulation_enabled=False,
        ),
    }
