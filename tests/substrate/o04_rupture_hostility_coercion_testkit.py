from __future__ import annotations

from dataclasses import dataclass

from substrate.o04_rupture_hostility_coercion import (
    O04InteractionEventInput,
    O04LegitimacyHintStatus,
    build_o04_rupture_hostility_coercion,
)
from tests.substrate.o03_strategy_class_evaluation_testkit import (
    build_o03_harness_case,
    harness_cases as o03_harness_cases,
)
from tests.substrate.p01_project_formation_testkit import (
    P01HarnessCase,
    build_p01_harness_case,
    p01_signal,
)
from substrate.p01_project_formation import P01AuthoritySourceKind


@dataclass(frozen=True, slots=True)
class O04HarnessCase:
    case_id: str
    tick_index: int
    interaction_events: tuple[O04InteractionEventInput, ...]
    history_depth_band: str = "single"
    o03_case_id: str = "cooperative_transparent"
    include_p01_context: bool = True
    modeling_enabled: bool = True


def o04_event(
    *,
    event_id: str,
    actor_ref: str | None = "agent_a",
    target_ref: str | None = "agent_b",
    speech_act_kind: str | None = None,
    blocked_option_present: bool = False,
    threatened_loss_present: bool = False,
    resource_control_present: bool = False,
    access_withdrawal_present: bool = False,
    dependency_surface_present: bool = False,
    sanction_power_present: bool = False,
    consent_marker: bool = False,
    refusal_marker: bool = False,
    commitment_break_marker: bool = False,
    exclusion_marker: bool = False,
    repair_attempt_marker: bool = False,
    escalation_shift_marker: bool = False,
    legitimacy_hint_status: O04LegitimacyHintStatus = O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
    project_link_ref: str | None = "project:tests-o04",
    history_depth_band: str = "single",
) -> O04InteractionEventInput:
    return O04InteractionEventInput(
        event_id=event_id,
        actor_ref=actor_ref,
        target_ref=target_ref,
        speech_act_kind=speech_act_kind,
        blocked_option_present=blocked_option_present,
        threatened_loss_present=threatened_loss_present,
        resource_control_present=resource_control_present,
        access_withdrawal_present=access_withdrawal_present,
        dependency_surface_present=dependency_surface_present,
        sanction_power_present=sanction_power_present,
        consent_marker=consent_marker,
        refusal_marker=refusal_marker,
        commitment_break_marker=commitment_break_marker,
        exclusion_marker=exclusion_marker,
        repair_attempt_marker=repair_attempt_marker,
        escalation_shift_marker=escalation_shift_marker,
        legitimacy_hint_status=legitimacy_hint_status,
        project_link_ref=project_link_ref,
        history_depth_band=history_depth_band,
        provenance=f"tests.o04.event:{event_id}",
    )


def build_o04_harness_case(case: O04HarnessCase):
    o03_result = build_o03_harness_case(o03_harness_cases()[case.o03_case_id])
    p01_result = (
        build_p01_harness_case(
            P01HarnessCase(
                case_id=f"o04-p01-{case.case_id}",
                tick_index=case.tick_index,
                signals=(
                    p01_signal(
                        signal_id=f"o04-p01-signal-{case.case_id}",
                        authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                        target="stabilize bounded runtime response path",
                    ),
                ),
            )
        )
        if case.include_p01_context
        else None
    )
    return build_o04_rupture_hostility_coercion(
        tick_id=f"o04:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        interaction_events=case.interaction_events,
        o03_result=o03_result,
        p01_result=p01_result,
        history_depth_band=case.history_depth_band,
        source_lineage=(f"tests.o04:{case.case_id}",),
        modeling_enabled=case.modeling_enabled,
    )


def harness_cases() -> dict[str, O04HarnessCase]:
    return {
        "rude_noncoercive": O04HarnessCase(
            case_id="rude_noncoercive",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="rude-1",
                    speech_act_kind="harsh_statement",
                ),
            ),
        ),
        "polite_coercive": O04HarnessCase(
            case_id="polite_coercive",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="pc-1",
                    speech_act_kind="neutral_statement",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                ),
            ),
        ),
        "same_words_low_leverage": O04HarnessCase(
            case_id="same_words_low_leverage",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="sw-low-1",
                    speech_act_kind="demand_request",
                ),
            ),
        ),
        "same_words_high_leverage": O04HarnessCase(
            case_id="same_words_high_leverage",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="sw-high-1",
                    speech_act_kind="demand_request",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                ),
            ),
        ),
        "legitimacy_supported_boundary": O04HarnessCase(
            case_id="legitimacy_supported_boundary",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="legit-1",
                    speech_act_kind="constraint_statement",
                    resource_control_present=True,
                    refusal_marker=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_SUPPORTED,
                ),
            ),
        ),
        "legitimacy_unknown_pressure": O04HarnessCase(
            case_id="legitimacy_unknown_pressure",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="legit-2",
                    speech_act_kind="constraint_statement",
                    resource_control_present=True,
                    refusal_marker=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
                ),
            ),
        ),
        "repeated_withdrawal_pattern": O04HarnessCase(
            case_id="repeated_withdrawal_pattern",
            tick_index=1,
            history_depth_band="deep",
            interaction_events=(
                o04_event(
                    event_id="rw-1",
                    access_withdrawal_present=True,
                    exclusion_marker=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    escalation_shift_marker=True,
                ),
                o04_event(
                    event_id="rw-2",
                    access_withdrawal_present=True,
                    commitment_break_marker=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
                o04_event(
                    event_id="rw-3",
                    exclusion_marker=True,
                    access_withdrawal_present=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
            ),
        ),
        "repair_attempt_after_withdrawal": O04HarnessCase(
            case_id="repair_attempt_after_withdrawal",
            tick_index=1,
            history_depth_band="deep",
            interaction_events=(
                o04_event(
                    event_id="rp-1",
                    access_withdrawal_present=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
                o04_event(
                    event_id="rp-2",
                    repair_attempt_marker=True,
                    consent_marker=True,
                ),
            ),
        ),
        "directionality_ambiguous_structure": O04HarnessCase(
            case_id="directionality_ambiguous_structure",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="da-1",
                    actor_ref=None,
                    target_ref="agent_b",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                ),
            ),
        ),
        "underconstrained_no_events": O04HarnessCase(
            case_id="underconstrained_no_events",
            tick_index=1,
            interaction_events=(),
        ),
        "disabled": O04HarnessCase(
            case_id="disabled",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="disabled-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
            ),
            modeling_enabled=False,
        ),
        "polite_coercive_vs_rude_noncoercive_pair": O04HarnessCase(
            case_id="polite_coercive_vs_rude_noncoercive_pair",
            tick_index=1,
            interaction_events=(
                o04_event(
                    event_id="pair-1",
                    speech_act_kind="neutral_statement",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                ),
                o04_event(
                    event_id="pair-2",
                    speech_act_kind="harsh_statement",
                ),
            ),
            history_depth_band="medium",
        ),
    }
