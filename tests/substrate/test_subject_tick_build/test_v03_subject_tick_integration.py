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
from substrate.v03_surface_verbalization_causality_constrained_realization import V03RealizationInput
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
        provenance=f"tests.v03.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="v03-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="v03-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="v03-g3",
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
        provenance=f"tests.v03.integration:{case_id}:project",
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
        proposition_ref="prop:v03-integration",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        commitment_target_ref="target:v03" if act_type is V01ActType.PROMISE else None,
        provenance=f"tests.v03.integration:{act_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_user_signals(),
        o03_candidate_strategy=_transparent_o03_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def _v03_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v03_constrained_realization_checkpoint"
    )


def test_subject_tick_emits_v03_checkpoint_after_v02_and_before_outcome() -> None:
    result = _result(
        "rt-v03-order",
        context=replace(
            _base_context("rt-v03-order"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-order",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.v02_utterance_plan_checkpoint" in ids
    assert "rt01.v03_constrained_realization_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.v02_utterance_plan_checkpoint") < ids.index(
        "rt01.v03_constrained_realization_checkpoint"
    )
    assert ids.index("rt01.v03_constrained_realization_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_explicit_v03_require_paths_are_deterministic() -> None:
    result = _result(
        "rt-v03-require",
        context=replace(
            _base_context("rt-v03-require"),
            require_v03_realization_consumer=True,
            require_v03_alignment_consumer=True,
            require_v03_constraint_report_consumer=True,
            v01_act_candidates=(),
        ),
    )
    checkpoint = _v03_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_v03_realization_consumer" in checkpoint.required_action
    assert "require_v03_alignment_consumer" in checkpoint.required_action
    assert "require_v03_constraint_report_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_v03_no_basis_path_has_no_default_friction() -> None:
    result = _result(
        "rt-v03-no-basis",
        context=replace(
            _base_context("rt-v03-no-basis"),
            v01_act_candidates=(),
            v03_realization_input=None,
        ),
    )
    checkpoint = _v03_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "v03_optional"
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_v03_default_failure_detour_is_load_bearing_when_alignment_breaks() -> None:
    result = _result(
        "rt-v03-default-failure",
        context=replace(
            _base_context("rt-v03-default-failure"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-weak-v03",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.52,
                ),
            ),
            v03_realization_input=V03RealizationInput(
                input_id="v03-qualifier-tamper",
                tamper_qualifier_locality_segment_id="seg:1:qualification",
            ),
        ),
    )
    checkpoint = _v03_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_v03_realization_failure_detour" in checkpoint.required_action
    assert result.state.v03_qualifier_locality_failures > 0


def test_same_checkpoint_and_required_action_but_typed_v03_shape_changes_restrictions() -> None:
    strong = _result(
        "rt-v03-shape-strong",
        context=replace(
            _base_context("rt-v03-shape-strong"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-strong-v03",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
        ),
    )
    weak = _result(
        "rt-v03-shape-weak",
        context=replace(
            _base_context("rt-v03-shape-weak"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-weak-v03-shape",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.52,
                ),
            ),
        ),
    )
    strong_checkpoint = _v03_checkpoint(strong)
    weak_checkpoint = _v03_checkpoint(weak)
    assert strong_checkpoint.status.value == "allowed"
    assert weak_checkpoint.status.value == "allowed"
    assert strong_checkpoint.required_action == "v03_optional"
    assert weak_checkpoint.required_action == "v03_optional"

    strong_restrictions = set(strong.downstream_gate.restrictions)
    weak_restrictions = set(weak.downstream_gate.restrictions)
    assert SubjectTickRestrictionCode.V03_ALIGNMENT_CONSUMER_REQUIRED not in strong_restrictions
    assert SubjectTickRestrictionCode.V03_ALIGNMENT_CONSUMER_REQUIRED in weak_restrictions
    assert strong_restrictions != weak_restrictions


def test_disabling_v03_enforcement_changes_outcome_class_under_protected_omission_leak() -> None:
    enabled = _result(
        "rt-v03-enabled",
        context=replace(
            _base_context("rt-v03-enabled"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-v03-enabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
                _candidate(
                    act_id="promise-v03-enabled",
                    act_type=V01ActType.PROMISE,
                    evidence_strength=0.62,
                ),
            ),
            v03_realization_input=V03RealizationInput(
                input_id="v03-protected-omission-leak-enabled",
                inject_protected_omission_token="omit:promise-v03-enabled",
            ),
        ),
    )
    disabled = _result(
        "rt-v03-disabled",
        context=replace(
            _base_context("rt-v03-disabled"),
            disable_v03_enforcement=True,
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-v03-disabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
                _candidate(
                    act_id="promise-v03-disabled",
                    act_type=V01ActType.PROMISE,
                    evidence_strength=0.62,
                ),
            ),
            v03_realization_input=V03RealizationInput(
                input_id="v03-protected-omission-leak-disabled",
                inject_protected_omission_token="omit:promise-v03-disabled",
            ),
        ),
    )
    enabled_checkpoint = _v03_checkpoint(enabled)
    disabled_checkpoint = _v03_checkpoint(disabled)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert disabled_checkpoint.status.value == "allowed"
    assert "default_v03_realization_failure_detour" in enabled_checkpoint.required_action
    assert disabled_checkpoint.required_action == "v03_optional"
    assert enabled.state.final_execution_outcome != SubjectTickOutcome.CONTINUE
    assert disabled.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert enabled.state.active_execution_mode == "repair_runtime_path"
    assert disabled.state.active_execution_mode == "revalidate_scope"
    assert enabled.state.active_execution_mode != disabled.state.active_execution_mode
    assert (
        SubjectTickRestrictionCode.V03_REALIZATION_FAILURE_DETOUR_REQUIRED
        in set(enabled.downstream_gate.restrictions)
    )
    assert (
        SubjectTickRestrictionCode.V03_REALIZATION_FAILURE_DETOUR_REQUIRED
        not in set(disabled.downstream_gate.restrictions)
    )
