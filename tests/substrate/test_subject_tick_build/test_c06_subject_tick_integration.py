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
from substrate.c06_surfacing_candidates import C06SurfacingInput
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
        provenance=f"tests.c06.integration:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="c06-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="c06-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="c06-g3",
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
        provenance=f"tests.c06.integration:{case_id}:project",
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
        proposition_ref="prop:c06-integration",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        commitment_target_ref="target:c06" if act_type is V01ActType.PROMISE else None,
        provenance=f"tests.c06.integration:{act_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_user_signals(),
        o03_candidate_strategy=_transparent_o03_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def _c06_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.c06_surfacing_candidates_checkpoint"
    )


def test_subject_tick_emits_c06_checkpoint_after_v03_and_before_outcome() -> None:
    result = _result(
        "rt-c06-order",
        context=replace(
            _base_context("rt-c06-order"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-order",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.v03_constrained_realization_checkpoint" in ids
    assert "rt01.c06_surfacing_candidates_checkpoint" in ids
    assert "rt01.outcome_resolution_checkpoint" in ids
    assert ids.index("rt01.v03_constrained_realization_checkpoint") < ids.index(
        "rt01.c06_surfacing_candidates_checkpoint"
    )
    assert ids.index("rt01.c06_surfacing_candidates_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_explicit_c06_require_paths_are_deterministic() -> None:
    result = _result(
        "rt-c06-require",
        context=replace(
            _base_context("rt-c06-require"),
            require_c06_candidate_set_consumer=True,
            require_c06_suppression_report_consumer=True,
            require_c06_identity_merge_consumer=True,
            v01_act_candidates=(),
        ),
    )
    checkpoint = _c06_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_c06_candidate_set_consumer" in checkpoint.required_action
    assert "require_c06_suppression_report_consumer" in checkpoint.required_action
    assert "require_c06_identity_merge_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_c06_no_basis_path_has_no_default_friction() -> None:
    result = _result(
        "rt-c06-no-basis",
        context=replace(
            _base_context("rt-c06-no-basis"),
            v01_act_candidates=(),
            c06_surfacing_input=None,
        ),
    )
    checkpoint = _c06_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "c06_optional"
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_c06_default_ambiguity_detour_is_basis_gated_and_load_bearing() -> None:
    result = _result(
        "rt-c06-default-ambiguity",
        context=replace(
            _base_context("rt-c06-default-ambiguity"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-ambiguity",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-ambiguity",
                prior_unresolved_question_present=True,
                unresolved_ambiguity_tokens=("ambiguity:1",),
            ),
        ),
    )
    checkpoint = _c06_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_c06_candidate_ambiguity_detour" in checkpoint.required_action
    assert result.state.c06_ambiguous_candidate_count > 0


def test_same_checkpoint_envelope_but_different_typed_c06_shape_changes_downstream_restrictions() -> None:
    baseline = _result(
        "rt-c06-shape-baseline",
        context=replace(
            _base_context("rt-c06-shape-baseline"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-shape-baseline",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-shape-baseline",
                closure_resolved=True,
            ),
        ),
    )
    carry = _result(
        "rt-c06-shape-carry",
        context=replace(
            _base_context("rt-c06-shape-carry"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-shape-carry",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-shape-carry",
                closure_resolved=True,
                confidence_residue_tokens=("residue:1",),
            ),
        ),
    )
    baseline_checkpoint = _c06_checkpoint(baseline)
    carry_checkpoint = _c06_checkpoint(carry)
    assert baseline_checkpoint.status.value == "allowed"
    assert carry_checkpoint.status.value == "allowed"
    assert baseline_checkpoint.required_action == "c06_optional"
    assert carry_checkpoint.required_action == "c06_optional"

    baseline_restrictions = set(baseline.downstream_gate.restrictions)
    carry_restrictions = set(carry.downstream_gate.restrictions)
    assert (
        SubjectTickRestrictionCode.C06_CONFIDENCE_RESIDUE_PRESERVATION_REQUIRED
        not in baseline_restrictions
    )
    assert (
        SubjectTickRestrictionCode.C06_CONFIDENCE_RESIDUE_PRESERVATION_REQUIRED
        in carry_restrictions
    )
    assert baseline_restrictions != carry_restrictions


def test_same_checkpoint_envelope_but_different_typed_c06_shape_changes_outcome_class() -> None:
    published = _result(
        "rt-c06-shape-published",
        context=replace(
            _base_context("rt-c06-shape-published"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-shape-published",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-shape-published",
                workspace_item_ids=("workspace:item:published",),
                published_frontier_item_ids=("workspace:item:published",),
            ),
        ),
    )
    unpublished = _result(
        "rt-c06-shape-unpublished",
        context=replace(
            _base_context("rt-c06-shape-unpublished"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-shape-unpublished",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-shape-unpublished",
                workspace_item_ids=("workspace:item:published",),
                published_frontier_item_ids=(),
            ),
        ),
    )
    published_checkpoint = _c06_checkpoint(published)
    unpublished_checkpoint = _c06_checkpoint(unpublished)
    assert published_checkpoint.status.value == "allowed"
    assert unpublished_checkpoint.status.value == "allowed"
    assert published_checkpoint.required_action == "c06_optional"
    assert unpublished_checkpoint.required_action == "c06_optional"
    assert published.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert unpublished.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert published.downstream_gate.accepted is True
    assert unpublished.downstream_gate.accepted is False
    assert published.downstream_gate.usability_class != unpublished.downstream_gate.usability_class


def test_disabling_c06_enforcement_changes_downstream_outcome_under_same_basis() -> None:
    enabled = _result(
        "rt-c06-enabled",
        context=replace(
            _base_context("rt-c06-enabled"),
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-enabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-enabled",
                prior_unresolved_question_present=True,
                unresolved_ambiguity_tokens=("ambiguity:1",),
            ),
        ),
    )
    disabled = _result(
        "rt-c06-disabled",
        context=replace(
            _base_context("rt-c06-disabled"),
            disable_c06_enforcement=True,
            v01_act_candidates=(
                _candidate(
                    act_id="assertion-c06-disabled",
                    act_type=V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
            ),
            c06_surfacing_input=C06SurfacingInput(
                input_id="c06-disabled",
                prior_unresolved_question_present=True,
                unresolved_ambiguity_tokens=("ambiguity:1",),
            ),
        ),
    )
    enabled_checkpoint = _c06_checkpoint(enabled)
    disabled_checkpoint = _c06_checkpoint(disabled)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert disabled_checkpoint.status.value == "allowed"
    assert "default_c06_candidate_ambiguity_detour" in enabled_checkpoint.required_action
    assert disabled_checkpoint.required_action == "c06_optional"
    assert enabled.state.final_execution_outcome != disabled.state.final_execution_outcome
    assert enabled.state.active_execution_mode != disabled.state.active_execution_mode
