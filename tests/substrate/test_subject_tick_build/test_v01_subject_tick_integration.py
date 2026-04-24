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
        provenance=f"tests.v01.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="v01-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="v01-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="v01-g3",
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
        provenance=f"tests.v01.integration:{case_id}:project",
    )


def _candidate(
    *,
    act_id: str,
    act_type: V01ActType,
    evidence_strength: float,
    authority_basis_present: bool = True,
    helpfulness_pressure: float = 0.0,
    protective_sensitivity: bool = False,
    commitment_target_ref: str | None = None,
    explicit_uncertainty_present: bool = False,
) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=act_type,
        proposition_ref="prop:v01-integration",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        explicit_uncertainty_present=explicit_uncertainty_present,
        helpfulness_pressure=helpfulness_pressure,
        protective_sensitivity=protective_sensitivity,
        commitment_target_ref=commitment_target_ref,
        provenance=f"tests.v01.integration:{act_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_user_signals(),
        o03_candidate_strategy=_transparent_o03_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def _v01_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v01_normative_permission_commitment_licensing_checkpoint"
    )


def test_subject_tick_emits_v01_checkpoint_after_r05_and_before_outcome() -> None:
    result = _result("rt-v01-order", context=_base_context("rt-v01-order"))
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.r05_protective_regulation_checkpoint" in ids
    assert "rt01.v01_normative_permission_commitment_licensing_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.r05_protective_regulation_checkpoint") < ids.index(
        "rt01.v01_normative_permission_commitment_licensing_checkpoint"
    )
    assert ids.index("rt01.v01_normative_permission_commitment_licensing_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_explicit_require_paths_are_deterministic_for_v01() -> None:
    result = _result(
        "rt-v01-require",
        context=replace(
            _base_context("rt-v01-require"),
            require_v01_license_consumer=True,
            require_v01_commitment_delta_consumer=True,
            require_v01_qualifier_binding_consumer=True,
            v01_act_candidates=(),
        ),
    )
    checkpoint = _v01_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_v01_license_consumer" in checkpoint.required_action
    assert "require_v01_commitment_delta_consumer" in checkpoint.required_action
    assert "require_v01_qualifier_binding_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_default_path_commitment_denied_detour_is_load_bearing() -> None:
    baseline = _result(
        "rt-v01-baseline-assertion",
        context=replace(
            _base_context("rt-v01-baseline-assertion"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-strong-baseline",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    denied_commitment = _result(
        "rt-v01-commitment-denied",
        context=replace(
            _base_context("rt-v01-commitment-denied"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-for-split",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
                _candidate(
                    act_id="promise-for-split",
                    act_type=V01ActType.PROMISE,
                    evidence_strength=0.62,
                    authority_basis_present=True,
                    commitment_target_ref="target:bounded",
                ),
            ),
        ),
    )
    baseline_checkpoint = _v01_checkpoint(baseline)
    denied_checkpoint = _v01_checkpoint(denied_commitment)
    assert baseline_checkpoint.status.value == "allowed"
    assert "default_v01_commitment_denied_detour" not in baseline_checkpoint.required_action
    assert denied_checkpoint.status.value == "enforced_detour"
    assert "default_v01_commitment_denied_detour" in denied_checkpoint.required_action
    assert denied_commitment.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_same_checkpoint_token_envelope_but_typed_v01_shape_changes_downstream() -> None:
    assertion = _result(
        "rt-v01-semantic-assertion",
        context=replace(
            _base_context("rt-v01-semantic-assertion"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-semantic",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    promise = _result(
        "rt-v01-semantic-promise",
        context=replace(
            _base_context("rt-v01-semantic-promise"),
            v01_act_candidates=(
                _candidate(
                    act_id="promise-semantic",
                    act_type=V01ActType.PROMISE,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                    explicit_uncertainty_present=True,
                    commitment_target_ref="target:semantic",
                ),
            ),
        ),
    )
    assertion_checkpoint = _v01_checkpoint(assertion)
    promise_checkpoint = _v01_checkpoint(promise)
    assert assertion_checkpoint.status.value == "allowed"
    assert promise_checkpoint.status.value == "allowed"
    assert assertion_checkpoint.required_action == "v01_optional"
    assert promise_checkpoint.required_action == "v01_optional"
    assert "default_v01_qualification_required_detour" not in assertion_checkpoint.required_action
    assert "default_v01_qualification_required_detour" not in promise_checkpoint.required_action

    assertion_restrictions = set(assertion.downstream_gate.restrictions)
    promise_restrictions = set(promise.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.V01_COMMITMENT_DELTA_CONSUMER_REQUIRED not in assertion_restrictions
    assert SubjectTickRestrictionCode.V01_COMMITMENT_DELTA_CONSUMER_REQUIRED in promise_restrictions
    assert assertion_restrictions != promise_restrictions


def test_qualifier_identity_tampering_is_detectable_downstream() -> None:
    weak_assertion = _result(
        "rt-v01-qualifier-identity",
        context=replace(
            _base_context("rt-v01-qualifier-identity"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-weak-qualifier",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.52,
                    authority_basis_present=True,
                ),
            ),
        ),
    )
    assert "qualified_assertion_required" in weak_assertion.state.v01_mandatory_qualifier_ids
    tampered_state = replace(
        weak_assertion.state,
        v01_mandatory_qualifier_ids=("tampered_qualifier",),
        v01_mandatory_qualifier_count=1,
        final_execution_outcome=SubjectTickOutcome.CONTINUE,
    )
    tampered_gate = evaluate_subject_tick_downstream_gate(tampered_state)
    assert SubjectTickRestrictionCode.V01_QUALIFIER_BINDING_CONSUMER_REQUIRED in tampered_gate.restrictions
    assert tampered_gate.accepted is False


def test_v01_disable_enforcement_changes_route_in_no_bypass_contrast() -> None:
    with_v01 = _result(
        "rt-v01-enabled",
        context=replace(
            _base_context("rt-v01-enabled"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-for-enabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
                _candidate(
                    act_id="promise-for-enabled",
                    act_type=V01ActType.PROMISE,
                    evidence_strength=0.62,
                    authority_basis_present=True,
                    commitment_target_ref="target:enabled",
                ),
            ),
        ),
    )
    ablated_v01 = _result(
        "rt-v01-disabled",
        context=replace(
            _base_context("rt-v01-disabled"),
            disable_v01_enforcement=True,
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-for-disabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                    authority_basis_present=True,
                ),
                _candidate(
                    act_id="promise-for-disabled",
                    act_type=V01ActType.PROMISE,
                    evidence_strength=0.62,
                    authority_basis_present=True,
                    commitment_target_ref="target:disabled",
                ),
            ),
        ),
    )
    enabled_checkpoint = _v01_checkpoint(with_v01)
    disabled_checkpoint = _v01_checkpoint(ablated_v01)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_v01_commitment_denied_detour" in enabled_checkpoint.required_action
    assert with_v01.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert disabled_checkpoint.status.value == "allowed"
    assert "insufficient_license_basis" in disabled_checkpoint.required_action
    assert "default_v01_commitment_denied_detour" not in disabled_checkpoint.required_action
    assert ablated_v01.state.final_execution_outcome != with_v01.state.final_execution_outcome
