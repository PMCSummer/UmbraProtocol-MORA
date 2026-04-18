from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.o04_rupture_hostility_coercion import (
    O04InteractionEventInput,
    O04LegitimacyHintStatus,
)
from substrate.p01_project_formation import P01AuthoritySourceKind, P01ProjectSignalInput
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickOutcome,
    SubjectTickRestrictionCode,
    SubjectTickUsabilityClass,
)
from tests.substrate.subject_tick_testkit import build_subject_tick


def _result(case_id: str, *, context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context=context,
    )


def _signal(
    *,
    signal_id: str,
    relation: str,
    claim: str,
    turn_index: int,
) -> O01EntitySignal:
    return O01EntitySignal(
        signal_id=signal_id,
        entity_id_hint=None,
        referent_label="user",
        source_authority="current_user_direct",
        relation_class=relation,
        claim_value=claim,
        confidence=0.81,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.o04.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="g3",
            relation="knowledge_boundary",
            claim="knows_cli_basics",
            turn_index=3,
        ),
    )


def _transparent_o03_candidate(case_id: str) -> O03CandidateStrategyInput:
    return O03CandidateStrategyInput(
        candidate_move_id=f"{case_id}:transparent",
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=True,
        material_uncertainty_omitted=False,
        selective_omission_risk_marker=False,
        reversibility_preserved=True,
        repairability_preserved=True,
    )


def _project_signal(case_id: str) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=f"{case_id}:project",
        signal_kind="directive",
        authority_source_kind=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
        target_summary="stabilize bounded runtime response path",
        grounded_basis_present=True,
        provenance=f"tests.o04.integration:{case_id}:project",
    )


def _event(
    *,
    event_id: str,
    actor_ref: str | None = "agent_a",
    target_ref: str | None = "agent_b",
    speech_act_kind: str | None = None,
    blocked_option_present: bool = False,
    threatened_loss_present: bool = False,
    dependency_surface_present: bool = False,
    sanction_power_present: bool = False,
    access_withdrawal_present: bool = False,
    consent_marker: bool = False,
    repair_attempt_marker: bool = False,
    commitment_break_marker: bool = False,
    exclusion_marker: bool = False,
    escalation_shift_marker: bool = False,
    legitimacy_hint_status: O04LegitimacyHintStatus = O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
) -> O04InteractionEventInput:
    return O04InteractionEventInput(
        event_id=event_id,
        actor_ref=actor_ref,
        target_ref=target_ref,
        speech_act_kind=speech_act_kind,
        blocked_option_present=blocked_option_present,
        threatened_loss_present=threatened_loss_present,
        dependency_surface_present=dependency_surface_present,
        sanction_power_present=sanction_power_present,
        access_withdrawal_present=access_withdrawal_present,
        consent_marker=consent_marker,
        repair_attempt_marker=repair_attempt_marker,
        commitment_break_marker=commitment_break_marker,
        exclusion_marker=exclusion_marker,
        escalation_shift_marker=escalation_shift_marker,
        legitimacy_hint_status=legitimacy_hint_status,
        provenance=f"tests.o04.integration:{event_id}",
    )


def test_subject_tick_emits_o04_checkpoint_in_runtime_order_after_p01() -> None:
    result = _result(
        "rt-o04-order",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-order"),
            p01_project_signals=(_project_signal("rt-o04-order"),),
            o04_interaction_events=(
                _event(
                    event_id="order-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.p01_project_formation_checkpoint" in ids
    assert "rt01.o04_rupture_hostility_coercion_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.p01_project_formation_checkpoint") < ids.index(
        "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert ids.index("rt01.o04_rupture_hostility_coercion_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_subject_tick_carries_typed_o04_result() -> None:
    result = _result(
        "rt-o04-typed",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-typed"),
            p01_project_signals=(_project_signal("rt-o04-typed"),),
            o04_interaction_events=(
                _event(
                    event_id="typed-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                ),
            ),
        ),
    )
    assert result.o04_result.state.interaction_model_id.startswith("o04-dynamic:")
    assert result.o04_result.state.directional_links
    assert result.o04_result.scope_marker.rt01_hosted_only is True
    assert result.o04_result.scope_marker.o04_first_slice_only is True


def test_default_path_coercive_structure_detour() -> None:
    baseline = _result(
        "rt-o04-default-baseline",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-default-baseline"),
            p01_project_signals=(_project_signal("rt-o04-default-baseline"),),
            o04_interaction_events=(
                _event(event_id="baseline-1", speech_act_kind="harsh_statement"),
            ),
        ),
    )
    risky = _result(
        "rt-o04-default-coercive",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-default-coercive"),
            p01_project_signals=(_project_signal("rt-o04-default-coercive"),),
            o04_interaction_events=(
                _event(
                    event_id="coercive-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                ),
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    risky_checkpoint = next(
        item
        for item in risky.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "enforced_detour"
    assert "default_o04_coercive_structure_detour" in risky_checkpoint.required_action
    assert risky.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_no_candidate_no_default_o04_detour() -> None:
    result = _result(
        "rt-o04-no-events-default",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-no-events-default"),
            p01_project_signals=(_project_signal("rt-o04-no-events-default"),),
            o04_interaction_events=(),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert "default_o04_coercive_structure_detour" not in checkpoint.required_action
    assert "default_o04_rupture_risk_detour" not in checkpoint.required_action
    assert "default_o04_legitimacy_ambiguity_detour" not in checkpoint.required_action


def test_explicit_require_consumer_path() -> None:
    result = _result(
        "rt-o04-required",
        context=SubjectTickContext(
            require_o04_dynamic_contract_consumer=True,
            require_o04_directionality_consumer=True,
            require_o04_protective_handoff_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-required"),
            p01_project_signals=(_project_signal("rt-o04-required"),),
            o04_interaction_events=(),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o04_dynamic_contract_consumer" in checkpoint.required_action
    assert "require_o04_directionality_consumer" in checkpoint.required_action
    assert "require_o04_protective_handoff_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_subject_tick_o04_positive_require_path_can_continue_lawfully() -> None:
    result = _result(
        "rt-o04-positive",
        context=SubjectTickContext(
            require_o04_dynamic_contract_consumer=True,
            require_o04_directionality_consumer=True,
            require_o04_protective_handoff_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-positive"),
            p01_project_signals=(_project_signal("rt-o04-positive"),),
            o04_interaction_events=(
                _event(
                    event_id="positive-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                ),
            ),
        ),
    )
    checkpoint = next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert result.o04_result.gate.dynamic_contract_consumer_ready is True
    assert result.o04_result.gate.directionality_consumer_ready is True
    assert result.o04_result.gate.protective_handoff_consumer_ready is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_typed_o04_semantics_not_only_checkpoint_token_drive_policy() -> None:
    baseline = _result(
        "rt-o04-semantic-baseline",
        context=SubjectTickContext(
            require_o04_dynamic_contract_consumer=True,
            require_o04_directionality_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-semantic-baseline"),
            p01_project_signals=(_project_signal("rt-o04-semantic-baseline"),),
            o04_interaction_events=(
                _event(
                    event_id="semantic-baseline-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                ),
            ),
        ),
    )
    rupture = _result(
        "rt-o04-semantic-rupture",
        context=SubjectTickContext(
            require_o04_dynamic_contract_consumer=True,
            require_o04_directionality_consumer=True,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-semantic-rupture"),
            p01_project_signals=(_project_signal("rt-o04-semantic-rupture"),),
            o04_interaction_events=(
                _event(
                    event_id="semantic-rupture-1",
                    access_withdrawal_present=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
                _event(
                    event_id="semantic-rupture-2",
                    access_withdrawal_present=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
            ),
        ),
    )
    baseline_checkpoint = next(
        item
        for item in baseline.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    rupture_checkpoint = next(
        item
        for item in rupture.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert rupture_checkpoint.status.value == "allowed"
    assert baseline_checkpoint.required_action != rupture_checkpoint.required_action
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert rupture.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    baseline_restrictions = set(baseline.downstream_gate.restrictions)
    rupture_restrictions = set(rupture.downstream_gate.restrictions)
    assert rupture.downstream_gate.usability_class == SubjectTickUsabilityClass.DEGRADED_BOUNDED
    assert (
        SubjectTickRestrictionCode.O04_RUPTURE_TRACKING_REQUIRED
        not in baseline_restrictions
    )
    assert (
        SubjectTickRestrictionCode.O04_RUPTURE_TRACKING_REQUIRED
        in rupture_restrictions
    )


def test_legitimacy_supported_vs_absent_changes_downstream_consequence() -> None:
    absent = _result(
        "rt-o04-legitimacy-absent",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-legitimacy-absent"),
            p01_project_signals=(_project_signal("rt-o04-legitimacy-absent"),),
            o04_interaction_events=(
                _event(
                    event_id="legit-absent-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=False,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                ),
            ),
        ),
    )
    supported = _result(
        "rt-o04-legitimacy-supported",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-legitimacy-supported"),
            p01_project_signals=(_project_signal("rt-o04-legitimacy-supported"),),
            o04_interaction_events=(
                _event(
                    event_id="legit-supported-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=False,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_SUPPORTED,
                ),
            ),
        ),
    )
    absent_checkpoint = next(
        item
        for item in absent.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    supported_checkpoint = next(
        item
        for item in supported.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert absent_checkpoint.status.value == "enforced_detour"
    assert supported_checkpoint.status.value == "allowed"
    assert "default_o04_coercive_structure_detour" in absent_checkpoint.required_action
    assert "default_o04_coercive_structure_detour" not in supported_checkpoint.required_action
    assert absent.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert supported.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_prior_o04_state_bounded_rupture_carry_and_revision() -> None:
    tick1 = _result(
        "rt-o04-prior-chain-1",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-prior-chain-1"),
            p01_project_signals=(_project_signal("rt-o04-prior-chain-1"),),
            o04_interaction_events=(
                _event(
                    event_id="chain-1a",
                    access_withdrawal_present=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                ),
                _event(
                    event_id="chain-1b",
                    access_withdrawal_present=True,
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    exclusion_marker=True,
                ),
            ),
        ),
    )
    tick2 = _result(
        "rt-o04-prior-chain-2",
        context=SubjectTickContext(
            prior_o04_state=tick1.o04_result.state,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-prior-chain-2"),
            p01_project_signals=(_project_signal("rt-o04-prior-chain-2"),),
            o04_interaction_events=(
                _event(
                    event_id="chain-2a",
                    access_withdrawal_present=True,
                    blocked_option_present=False,
                    threatened_loss_present=False,
                    dependency_surface_present=False,
                ),
            ),
        ),
    )
    tick3 = _result(
        "rt-o04-prior-chain-3",
        context=SubjectTickContext(
            prior_o04_state=tick2.o04_result.state,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-prior-chain-3"),
            p01_project_signals=(_project_signal("rt-o04-prior-chain-3"),),
            o04_interaction_events=(
                _event(
                    event_id="chain-3a",
                    repair_attempt_marker=True,
                    consent_marker=True,
                ),
            ),
        ),
    )
    tick4 = _result(
        "rt-o04-prior-chain-4",
        context=SubjectTickContext(
            prior_o04_state=tick3.o04_result.state,
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-prior-chain-4"),
            p01_project_signals=(_project_signal("rt-o04-prior-chain-4"),),
            o04_interaction_events=(
                _event(event_id="chain-4a"),
            ),
        ),
    )
    assert tick1.o04_result.state.rupture_status.value == "rupture_risk_only"
    assert tick2.o04_result.state.rupture_status.value == "rupture_risk_only"
    assert "prior_rupture_carry_forward" in tick2.o04_result.state.uncertainty_markers
    assert tick3.o04_result.state.rupture_status.value == "deescalated_but_not_closed"
    assert "prior_rupture_repair_downgrade" in tick3.o04_result.state.uncertainty_markers
    assert tick4.o04_result.state.rupture_status.value == "no_rupture_basis"
    assert "prior_rupture_not_sticky" in tick4.o04_result.state.uncertainty_markers


def test_same_checkpoint_status_different_typed_o04_shape_changes_restriction() -> None:
    absent = _result(
        "rt-o04-shape-absent",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-shape-absent"),
            p01_project_signals=(_project_signal("rt-o04-shape-absent"),),
            o04_interaction_events=(
                _event(
                    event_id="shape-absent-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                ),
            ),
        ),
    )
    supported = _result(
        "rt-o04-shape-supported",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-shape-supported"),
            p01_project_signals=(_project_signal("rt-o04-shape-supported"),),
            o04_interaction_events=(
                _event(
                    event_id="shape-supported-1",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                    legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_SUPPORTED,
                ),
            ),
        ),
    )
    absent_checkpoint = next(
        item
        for item in absent.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    supported_checkpoint = next(
        item
        for item in supported.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    absent_restrictions = set(absent.downstream_gate.restrictions)
    supported_restrictions = set(supported.downstream_gate.restrictions)
    assert absent_checkpoint.status.value == "enforced_detour"
    assert supported_checkpoint.status.value == "enforced_detour"
    assert (
        SubjectTickRestrictionCode.O04_PROTECTIVE_HANDOFF_CONSUMER_REQUIRED
        in absent_restrictions
    )
    assert (
        SubjectTickRestrictionCode.O04_PROTECTIVE_HANDOFF_CONSUMER_REQUIRED
        not in supported_restrictions
    )
    assert (
        SubjectTickRestrictionCode.O04_DYNAMIC_CONTRACT_CONSUMER_REQUIRED
        in supported_restrictions
    )


def test_mutual_harshness_with_one_sided_leverage_preserves_asymmetry() -> None:
    result = _result(
        "rt-o04-asymmetry-preserved",
        context=SubjectTickContext(
            o01_entity_signals=_grounded_user_signals(),
            o03_candidate_strategy=_transparent_o03_candidate("rt-o04-asymmetry-preserved"),
            p01_project_signals=(_project_signal("rt-o04-asymmetry-preserved"),),
            o04_interaction_events=(
                _event(
                    event_id="asym-1",
                    actor_ref="agent_a",
                    target_ref="agent_b",
                    speech_act_kind="harsh_statement",
                    blocked_option_present=True,
                    threatened_loss_present=True,
                    dependency_surface_present=True,
                    sanction_power_present=True,
                ),
                _event(
                    event_id="asym-2",
                    actor_ref="agent_b",
                    target_ref="agent_a",
                    speech_act_kind="harsh_statement",
                ),
            ),
        ),
    )
    assert result.o04_result.telemetry.directionality_kind.value in {
        "mutual",
        "asymmetric_mutual",
    }
    assert len(result.o04_result.state.coercion_candidates) > 0
