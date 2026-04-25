from __future__ import annotations

from dataclasses import replace

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.p01_project_formation import P01AuthoritySourceKind, P01ProjectSignalInput
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickOutcome,
    SubjectTickRestrictionCode,
)
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommunicativeActCandidate,
)
from tests.substrate.p02_intervention_episode_layer_licensed_action_trace_testkit import (
    p02_episode_input,
    p02_execution_event,
    p02_license_snapshot,
    p02_outcome_evidence,
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
        confidence=0.82,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.p02.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="p02-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="p02-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="p02-g3",
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
        provenance=f"tests.p02.integration:{case_id}:project",
    )


def _candidate(
    *,
    act_id: str,
    act_type: V01ActType,
    evidence_strength: float,
    authority_basis_present: bool = True,
) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=act_type,
        proposition_ref="prop:p02-integration",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        commitment_target_ref="target:p02" if act_type is V01ActType.PROMISE else None,
        provenance=f"tests.p02.integration:{act_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_user_signals(),
        o03_candidate_strategy=_transparent_o03_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def _p02_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p02_intervention_episode_checkpoint"
    )


def test_subject_tick_emits_p02_checkpoint_after_c06_and_before_outcome() -> None:
    result = _result(
        "rt-p02-order",
        context=replace(
            _base_context("rt-p02-order"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-p02-order",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.c06_surfacing_candidates_checkpoint" in ids
    assert "rt01.p02_intervention_episode_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.c06_surfacing_candidates_checkpoint") < ids.index(
        "rt01.p02_intervention_episode_checkpoint"
    )
    assert ids.index("rt01.p02_intervention_episode_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_explicit_require_paths_are_deterministic_for_p02() -> None:
    result = _result(
        "rt-p02-require",
        context=replace(
            _base_context("rt-p02-require"),
            require_p02_episode_consumer=True,
            require_p02_boundary_consumer=True,
            require_p02_verification_consumer=True,
            v01_act_candidates=(),
        ),
    )
    checkpoint = _p02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_p02_episode_consumer" in checkpoint.required_action
    assert "require_p02_boundary_consumer" in checkpoint.required_action
    assert "require_p02_verification_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_default_path_awaiting_verification_detour_is_load_bearing() -> None:
    licensed = p02_license_snapshot(
        action_id="act:p02-await",
        source_license_ref="v01:licensed:act:p02-await",
        license_scope_ref="assertion",
    )
    result = _result(
        "rt-p02-default-awaiting",
        context=replace(
            _base_context("rt-p02-default-awaiting"),
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-await",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-awaiting",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-await",
                        action_ref="act:p02-await",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
    )
    checkpoint = _p02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_p02_awaiting_verification_detour" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_same_checkpoint_envelope_but_different_typed_p02_shape_changes_downstream() -> None:
    licensed = p02_license_snapshot(
        action_id="act:p02-shape",
        source_license_ref="v01:licensed:act:p02-shape",
        license_scope_ref="assertion",
    )
    completed = _result(
        "rt-p02-shape-completed",
        context=replace(
            _base_context("rt-p02-shape-completed"),
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-shape",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-shape-completed",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-completed",
                        action_ref="act:p02-shape",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
                outcome_evidence=(
                    p02_outcome_evidence(
                        evidence_id="e:p02-verified",
                        action_ref="act:p02-shape",
                        evidence_kind="verified_success",
                        verified=True,
                    ),
                ),
            ),
        ),
    )
    partial = _result(
        "rt-p02-shape-partial",
        context=replace(
            _base_context("rt-p02-shape-partial"),
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-shape",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-shape-partial",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-partial",
                        action_ref="act:p02-shape",
                        event_kind="partial",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
    )
    completed_checkpoint = _p02_checkpoint(completed)
    partial_checkpoint = _p02_checkpoint(partial)
    assert completed_checkpoint.status.value == "allowed"
    assert partial_checkpoint.status.value == "allowed"
    assert completed_checkpoint.required_action == "p02_optional"
    assert partial_checkpoint.required_action == "p02_optional"
    assert completed.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert partial.state.final_execution_outcome == SubjectTickOutcome.CONTINUE

    completed_restrictions = set(completed.downstream_gate.restrictions)
    partial_restrictions = set(partial.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.P02_EPISODE_CONSUMER_REQUIRED not in completed_restrictions
    assert SubjectTickRestrictionCode.P02_EPISODE_CONSUMER_REQUIRED in partial_restrictions
    assert completed_restrictions != partial_restrictions


def test_same_checkpoint_envelope_same_required_action_but_typed_shape_changes_outcome_class() -> None:
    licensed = p02_license_snapshot(
        action_id="act:p02-envelope",
        source_license_ref="v01:licensed:act:p02-envelope",
        license_scope_ref="assertion",
    )
    safe = _result(
        "rt-p02-envelope-safe",
        context=replace(
            _base_context("rt-p02-envelope-safe"),
            require_p02_episode_consumer=True,
            require_p02_boundary_consumer=True,
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-envelope",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-envelope-safe",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-envelope-safe",
                        action_ref="act:p02-envelope",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
                outcome_evidence=(
                    p02_outcome_evidence(
                        evidence_id="e:p02-envelope-safe-verified",
                        action_ref="act:p02-envelope",
                        evidence_kind="verified_success",
                        verified=True,
                    ),
                ),
            ),
        ),
    )
    risky = _result(
        "rt-p02-envelope-risky",
        context=replace(
            _base_context("rt-p02-envelope-risky"),
            require_p02_episode_consumer=True,
            require_p02_boundary_consumer=True,
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-envelope",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-envelope-risky",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-envelope-risky",
                        action_ref="act:p02-outside-license",
                        event_kind="executed",
                        order_index=1,
                    ),
                ),
            ),
        ),
    )
    safe_checkpoint = _p02_checkpoint(safe)
    risky_checkpoint = _p02_checkpoint(risky)
    assert safe_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "allowed"
    assert safe_checkpoint.required_action == "require_p02_episode_consumer;require_p02_boundary_consumer"
    assert risky_checkpoint.required_action == "require_p02_episode_consumer;require_p02_boundary_consumer"
    assert safe.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert risky.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert safe.downstream_gate.accepted is True
    assert risky.downstream_gate.accepted is False
    assert safe.downstream_gate.usability_class.value in {"usable_bounded", "degraded_bounded"}
    assert risky.downstream_gate.usability_class.value == "blocked"


def test_disable_p02_enforcement_changes_outcome_in_no_bypass_contrast() -> None:
    licensed = p02_license_snapshot(
        action_id="act:p02-bypass",
        source_license_ref="v01:licensed:act:p02-bypass",
        license_scope_ref="assertion",
    )
    enabled = _result(
        "rt-p02-enabled",
        context=replace(
            _base_context("rt-p02-enabled"),
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-bypass",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-enabled",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-enabled",
                        action_ref="act:p02-bypass",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
    )
    disabled = _result(
        "rt-p02-disabled",
        context=replace(
            _base_context("rt-p02-disabled"),
            disable_p02_enforcement=True,
            v01_act_candidates=(
                _candidate(
                    act_id="act:p02-bypass",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            p02_episode_input=p02_episode_input(
                input_id="p02-disabled",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:p02-disabled",
                        action_ref="act:p02-bypass",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
    )
    enabled_checkpoint = _p02_checkpoint(enabled)
    disabled_checkpoint = _p02_checkpoint(disabled)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_p02_awaiting_verification_detour" in enabled_checkpoint.required_action
    assert disabled_checkpoint.status.value == "allowed"
    assert disabled_checkpoint.required_action == "p02_optional"
    assert enabled.state.final_execution_outcome != disabled.state.final_execution_outcome
