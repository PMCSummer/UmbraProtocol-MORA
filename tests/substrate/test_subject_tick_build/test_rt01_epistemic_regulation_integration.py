from __future__ import annotations

from dataclasses import replace

from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    derive_subject_tick_contract_view,
    execute_subject_tick,
)


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
    )


def test_epistemics_enters_rt01_before_regulation_and_exposes_allowance() -> None:
    result = execute_subject_tick(_tick_input("rt01-epistemic-order"))
    attempted_paths = result.telemetry.attempted_paths
    assert "subject_tick.evaluate_epistemic_admission" in attempted_paths
    assert "subject_tick.run_regulation_stack" in attempted_paths
    assert attempted_paths.index("subject_tick.evaluate_epistemic_admission") < attempted_paths.index(
        "subject_tick.run_regulation_stack"
    )

    checkpoint = next(
        checkpoint
        for checkpoint in result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.epistemic_admission_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert result.state.epistemic_claim_strength == result.epistemic_result.allowance.claim_strength
    assert (
        result.state.epistemic_allowance_restrictions
        == result.epistemic_result.allowance.restrictions
    )


def test_epistemic_unknown_or_abstain_marks_restrictions_and_outcome_honestly() -> None:
    result = execute_subject_tick(
        SubjectTickInput(
            case_id="rt01-epistemic-abstain",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            epistemic_source_class="unknown",
            epistemic_modality="unspecified",
        ),
        context=SubjectTickContext(require_epistemic_observation=True),
    )
    assert result.state.epistemic_should_abstain is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE

    checkpoint = next(
        checkpoint
        for checkpoint in result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.epistemic_admission_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"

    r_step = next(step for step in result.state.downstream_step_results if step.phase_id == "R")
    assert "epistemic_should_abstain" in r_step.restrictions
    assert result.state.epistemic_claim_strength != "grounded_observation"


def test_regulation_contractization_remains_coherent_with_shared_runtime_precedence() -> None:
    prior_runtime_state = create_empty_state()
    prior_runtime_state = replace(
        prior_runtime_state,
        domains=replace(
            prior_runtime_state.domains,
            validity=replace(
                prior_runtime_state.domains.validity,
                legality_reuse_allowed=False,
                revalidation_required=True,
                no_safe_reuse=False,
            ),
        ),
    )

    result = execute_subject_tick(
        _tick_input("rt01-regulation-contractization"),
        context=SubjectTickContext(prior_runtime_state=prior_runtime_state),
    )
    shared_checkpoint = next(
        checkpoint
        for checkpoint in result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.shared_runtime_domain_checkpoint"
    )
    assert shared_checkpoint.status.value == "enforced_detour"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE

    view = derive_subject_tick_contract_view(result)
    assert view.regulation_pressure_level == result.state.regulation_pressure_level
    assert view.regulation_escalation_stage == result.state.regulation_escalation_stage
    assert view.regulation_override_scope == result.state.regulation_override_scope
    assert view.regulation_no_strong_override_claim == result.state.regulation_no_strong_override_claim
    assert view.regulation_gate_accepted == result.state.regulation_gate_accepted
    assert view.regulation_source_state_ref == result.state.regulation_source_state_ref
    assert any(
        checkpoint.checkpoint_id == "rt01.downstream_obedience_checkpoint"
        for checkpoint in result.state.execution_checkpoints
    )
