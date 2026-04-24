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
    evaluate_subject_tick_downstream_gate,
)
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommunicativeActCandidate,
)
from substrate.v02_communicative_intent_utterance_plan_bridge import V02UtterancePlanInput
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
        provenance=f"tests.v02.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="v02-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="v02-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="v02-g3",
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
        provenance=f"tests.v02.integration:{case_id}:project",
    )


def _candidate(
    *,
    act_id: str,
    act_type: V01ActType,
    evidence_strength: float,
    authority_basis_present: bool = True,
    explicit_uncertainty_present: bool = False,
    commitment_target_ref: str | None = None,
) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=act_type,
        proposition_ref="prop:v02-integration",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        explicit_uncertainty_present=explicit_uncertainty_present,
        commitment_target_ref=commitment_target_ref,
        provenance=f"tests.v02.integration:{act_id}",
    )


def _plan_input(
    *,
    input_id: str,
    prior_unresolved_question: bool = False,
    prior_refusal_present: bool = False,
    prior_commitment_carry_present: bool = False,
) -> V02UtterancePlanInput:
    return V02UtterancePlanInput(
        input_id=input_id,
        prior_unresolved_question=prior_unresolved_question,
        prior_refusal_present=prior_refusal_present,
        prior_commitment_carry_present=prior_commitment_carry_present,
        provenance=f"tests.v02.integration:{input_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_user_signals(),
        o03_candidate_strategy=_transparent_o03_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def _v02_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v02_utterance_plan_checkpoint"
    )


def test_subject_tick_emits_v02_checkpoint_after_v01_and_before_outcome() -> None:
    result = _result("rt-v02-order", context=_base_context("rt-v02-order"))
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.v01_normative_permission_commitment_licensing_checkpoint" in ids
    assert "rt01.v02_utterance_plan_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.v01_normative_permission_commitment_licensing_checkpoint") < ids.index(
        "rt01.v02_utterance_plan_checkpoint"
    )
    assert ids.index("rt01.v02_utterance_plan_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_explicit_v02_require_paths_are_deterministic() -> None:
    result = _result(
        "rt-v02-require",
        context=replace(
            _base_context("rt-v02-require"),
            require_v02_plan_consumer=True,
            require_v02_ordering_consumer=True,
            require_v02_realization_contract_consumer=True,
            v01_act_candidates=(),
        ),
    )
    checkpoint = _v02_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_v02_plan_consumer" in checkpoint.required_action
    assert "require_v02_ordering_consumer" in checkpoint.required_action
    assert "require_v02_realization_contract_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_v02_no_basis_path_has_no_default_friction() -> None:
    result = _result(
        "rt-v02-no-basis",
        context=replace(
            _base_context("rt-v02-no-basis"),
            v01_act_candidates=(),
            v02_plan_input=None,
        ),
    )
    checkpoint = _v02_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "v02_optional"
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_v02_clarification_first_default_detour_is_load_bearing() -> None:
    baseline = _result(
        "rt-v02-clarification-baseline",
        context=replace(
            _base_context("rt-v02-clarification-baseline"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-baseline",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    clarification = _result(
        "rt-v02-clarification-required",
        context=replace(
            _base_context("rt-v02-clarification-required"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-clarify",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
            v02_plan_input=_plan_input(
                input_id="clarification-required",
                prior_unresolved_question=True,
            ),
        ),
    )
    baseline_checkpoint = _v02_checkpoint(baseline)
    clarification_checkpoint = _v02_checkpoint(clarification)
    assert baseline_checkpoint.status.value == "allowed"
    assert "default_v02_clarification_first_detour" not in baseline_checkpoint.required_action
    assert clarification_checkpoint.status.value == "enforced_detour"
    assert "default_v02_clarification_first_detour" in clarification_checkpoint.required_action
    assert clarification.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_same_checkpoint_envelope_but_typed_v02_shape_changes_restrictions() -> None:
    strong = _result(
        "rt-v02-semantic-strong",
        context=replace(
            _base_context("rt-v02-semantic-strong"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-strong",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    weak = _result(
        "rt-v02-semantic-weak",
        context=replace(
            _base_context("rt-v02-semantic-weak"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-weak",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.52,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    strong_checkpoint = _v02_checkpoint(strong)
    weak_checkpoint = _v02_checkpoint(weak)
    assert strong_checkpoint.status.value == "allowed"
    assert weak_checkpoint.status.value == "allowed"
    assert strong_checkpoint.required_action == "v02_optional"
    assert weak_checkpoint.required_action == "v02_optional"
    strong_restrictions = set(strong.downstream_gate.restrictions)
    weak_restrictions = set(weak.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED not in strong_restrictions
    assert SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED in weak_restrictions
    assert strong_restrictions != weak_restrictions


def test_same_checkpoint_and_same_required_action_but_exact_qualifier_ids_change_outcome() -> None:
    weak = _result(
        "rt-v02-qualifier-identity-base",
        context=replace(
            _base_context("rt-v02-qualifier-identity-base"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-weak-identity",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.52,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    checkpoint = _v02_checkpoint(weak)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "v02_optional"

    baseline_gate = evaluate_subject_tick_downstream_gate(weak.state)
    assert (
        SubjectTickRestrictionCode.V02_QUALIFIER_IDENTITY_BINDING_REQUIRED
        not in baseline_gate.restrictions
    )

    assert weak.state.v01_mandatory_qualifier_count == 2
    assert weak.state.v02_mandatory_qualifier_attachment_count >= 2
    assert len(weak.state.v02_mandatory_qualifier_ids) == 2
    tampered_state = replace(
        weak.state,
        v02_mandatory_qualifier_ids=(
            "advice_basis_disclosure_required",
            "preserve_explicit_uncertainty",
        ),
        v02_mandatory_qualifier_attachment_count=weak.state.v02_mandatory_qualifier_attachment_count,
        final_execution_outcome=SubjectTickOutcome.CONTINUE,
    )
    tampered_gate = evaluate_subject_tick_downstream_gate(tampered_state)
    assert (
        SubjectTickRestrictionCode.V02_QUALIFIER_IDENTITY_BINDING_REQUIRED
        in tampered_gate.restrictions
    )
    assert tampered_gate.accepted is False
    assert baseline_gate.accepted is not tampered_gate.accepted


def test_v02_ordering_tamper_is_detectable_downstream() -> None:
    weak = _result(
        "rt-v02-ordering-tamper",
        context=replace(
            _base_context("rt-v02-ordering-tamper"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-weak-ordering",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.52,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    tampered_state = replace(
        weak.state,
        v02_ordering_edge_count=0,
        v02_partial_plan_only=False,
        final_execution_outcome=SubjectTickOutcome.CONTINUE,
    )
    tampered_gate = evaluate_subject_tick_downstream_gate(tampered_state)
    assert SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED in tampered_gate.restrictions
    assert tampered_gate.accepted is False


def test_v02_disable_enforcement_changes_route_in_no_bypass_contrast() -> None:
    with_v02 = _result(
        "rt-v02-enabled",
        context=replace(
            _base_context("rt-v02-enabled"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-enabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
            v02_plan_input=_plan_input(
                input_id="enabled-clarification",
                prior_unresolved_question=True,
            ),
        ),
    )
    ablated_v02 = _result(
        "rt-v02-disabled",
        context=replace(
            _base_context("rt-v02-disabled"),
            disable_v02_enforcement=True,
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-disabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
            v02_plan_input=_plan_input(
                input_id="disabled-clarification",
                prior_unresolved_question=True,
            ),
        ),
    )
    enabled_checkpoint = _v02_checkpoint(with_v02)
    disabled_checkpoint = _v02_checkpoint(ablated_v02)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_v02_clarification_first_detour" in enabled_checkpoint.required_action
    assert with_v02.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert disabled_checkpoint.status.value == "allowed"
    assert "default_v02_clarification_first_detour" not in disabled_checkpoint.required_action
    assert ablated_v02.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
