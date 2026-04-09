from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.a_line_normalization import build_a_line_normalization
from substrate.m_minimal import build_m_minimal
from substrate.n_minimal import (
    NarrativeCommitmentStatus,
    build_n_minimal,
    derive_n_minimal_contract_view,
    n_minimal_snapshot,
    require_bounded_n_minimal_scope,
    require_strong_narrative_commitment_for_consumer,
)
from substrate.self_contour import build_s_minimal_contour
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    derive_subject_tick_contract_view,
    execute_subject_tick,
    require_subject_tick_bounded_n_scope,
    require_subject_tick_strong_narrative_commitment,
    subject_tick_result_to_payload,
)
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_effect_packet,
    build_world_observation_packet,
    run_world_adapter_cycle,
)
from substrate.world_entry_contract import build_world_entry_contract


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _observation(case_id: str):
    return build_world_observation_packet(
        observation_id=f"obs-{case_id}",
        source_ref="world.sensor.sprint8e",
        observed_at="2026-04-10T12:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _n_result(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str = "reuse_without_revalidation",
    claim_pressure: bool = False,
    require_self_side_claim: bool = False,
    require_world_side_claim: bool = False,
    require_self_controlled_transition_claim: bool = False,
):
    tick_id = f"tick-{case_id}"
    if effect_action_id == "__MATCHED__":
        effect_action_id = f"world-action-{tick_id}"
    effect_packet = None
    if effect_action_id is not None:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=effect_action_id,
            observed_at="2026-04-10T12:00:01+00:00",
            source_ref="world.effect.sprint8e",
            success=True,
        )
    adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=include_observation,
            adapter_available=include_observation,
            observation_packet=_observation(case_id) if include_observation else None,
            effect_packet=effect_packet,
        ),
        request_action_candidate=request_action,
        source_lineage=("test.sprint8e.n-minimal",),
    )
    world_entry = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.sprint8e.n-minimal",),
    )
    s_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry,
        world_adapter_result=adapter_result,
        require_self_side_claim=require_self_side_claim,
        require_world_side_claim=require_world_side_claim,
        require_self_controlled_transition_claim=require_self_controlled_transition_claim,
        source_lineage=("test.sprint8e.n-minimal",),
    )
    a_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        source_lineage=("test.sprint8e.n-minimal",),
    )
    m_result = build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        c05_validity_action=c05_action,
        source_lineage=("test.sprint8e.n-minimal",),
    )
    return build_n_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        claim_pressure=claim_pressure,
        source_lineage=("test.sprint8e.n-minimal",),
    )


def test_n_minimal_materializes_typed_commitment_surface_and_scope() -> None:
    result = _n_result(
        "n-typed",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    view = derive_n_minimal_contract_view(result)
    snapshot = n_minimal_snapshot(result)
    assert result.state.narrative_commitment_id.startswith("n-commitment:")
    assert result.state.commitment_status in {
        NarrativeCommitmentStatus.BOUNDED_NARRATIVE_COMMITMENT,
        NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM,
    }
    assert view.scope == "rt01_contour_only"
    assert view.scope_rt01_contour_only is True
    assert view.scope_n_minimal_only is True
    assert view.scope_readiness_gate_only is True
    assert view.scope_n01_implemented is False
    assert view.scope_n02_implemented is False
    assert view.scope_n03_implemented is False
    assert view.scope_n04_implemented is False
    assert view.scope_full_narrative_line_implemented is False
    assert view.scope_repo_wide_adoption is False
    assert snapshot["admission"]["n01_implemented"] is False
    assert snapshot["admission"]["n02_implemented"] is False
    assert snapshot["admission"]["n03_implemented"] is False
    assert snapshot["admission"]["n04_implemented"] is False


def test_narrative_basis_absence_forces_no_safe_claim() -> None:
    no_basis = _n_result(
        "n-no-basis",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert no_basis.gate.no_safe_narrative_claim is True
    assert no_basis.gate.safe_narrative_commitment_allowed is False
    assert no_basis.state.commitment_status == NarrativeCommitmentStatus.NO_SAFE_NARRATIVE_CLAIM
    assert "prose_without_commitment_basis" in no_basis.gate.forbidden_shortcuts


def test_ambiguity_and_underconstrained_narrative_are_not_upgraded_to_bounded_commitment() -> None:
    ambiguous = _n_result(
        "n-ambiguous",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    assert ambiguous.state.ambiguity_residue is True
    assert ambiguous.state.underconstrained is True
    assert ambiguous.gate.bounded_commitment_allowed is False
    assert ambiguous.state.commitment_status in {
        NarrativeCommitmentStatus.AMBIGUITY_PRESERVING_NARRATIVE,
        NarrativeCommitmentStatus.UNDERCONSTRAINED_NARRATIVE_SURFACE,
        NarrativeCommitmentStatus.CONTRADICTION_MARKED_NARRATIVE,
    }


def test_lawful_vs_underconstrained_contrast_is_sharper_under_claim_pressure() -> None:
    lawful = _n_result(
        "n-lawful-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        claim_pressure=True,
    )
    underconstrained = _n_result(
        "n-underconstrained-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
        claim_pressure=True,
    )
    assert lawful.gate.safe_narrative_commitment_allowed is True
    assert lawful.gate.no_safe_narrative_claim is False
    assert lawful.state.commitment_status in {
        NarrativeCommitmentStatus.BOUNDED_NARRATIVE_COMMITMENT,
        NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM,
    }
    assert underconstrained.gate.safe_narrative_commitment_allowed is False
    assert underconstrained.state.commitment_status in {
        NarrativeCommitmentStatus.AMBIGUITY_PRESERVING_NARRATIVE,
        NarrativeCommitmentStatus.UNDERCONSTRAINED_NARRATIVE_SURFACE,
        NarrativeCommitmentStatus.CONTRADICTION_MARKED_NARRATIVE,
        NarrativeCommitmentStatus.NO_SAFE_NARRATIVE_CLAIM,
    }


def test_shortcut_markers_are_falsifiable_under_claim_pressure() -> None:
    ambiguity_pressure = _n_result(
        "n-shortcut-ambiguity-pressure",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
        claim_pressure=True,
    )
    contradiction_pressure = _n_result(
        "n-shortcut-contradiction-pressure",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        claim_pressure=True,
    )
    assert (
        "ambiguity_erased_from_narrative_claim"
        in ambiguity_pressure.gate.forbidden_shortcuts
    )
    assert (
        "ambiguity_hiding_attempt_under_claim_pressure"
        in ambiguity_pressure.gate.restrictions
    )
    assert (
        "contradiction_hidden_by_fluent_wording"
        in contradiction_pressure.gate.forbidden_shortcuts
    )
    assert (
        "contradiction_hiding_attempt_under_claim_pressure"
        in contradiction_pressure.gate.restrictions
    )


def test_n_forbidden_shortcuts_are_machine_readable() -> None:
    result = _n_result(
        "n-shortcuts",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert "narrative_reframed_as_self_truth_without_basis" in result.gate.forbidden_shortcuts
    assert "narrative_reframed_as_world_truth_without_basis" in result.gate.forbidden_shortcuts
    assert "narrative_reframed_as_memory_truth_without_basis" in result.gate.forbidden_shortcuts
    assert "narrative_reframed_as_capability_truth_without_basis" in result.gate.forbidden_shortcuts


def test_rt01_require_narrative_safe_claim_is_path_affecting() -> None:
    baseline = execute_subject_tick(_tick_input("n-rt01-baseline"))
    enforced = execute_subject_tick(
        _tick_input("n-rt01-enforced"),
        context=SubjectTickContext(require_narrative_safe_claim=True),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.n_minimal_contour_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in enforced.state.execution_checkpoints
    )


def test_n_ablation_contrast_restores_old_permissive_profile() -> None:
    enforced = execute_subject_tick(
        _tick_input("n-ablation-enforced"),
        context=SubjectTickContext(require_narrative_safe_claim=True),
    )
    ablated = execute_subject_tick(
        _tick_input("n-ablation-disabled"),
        context=SubjectTickContext(
            require_narrative_safe_claim=True,
            disable_n_minimal_enforcement=True,
            disable_gate_application=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_n_line_admission_surface_is_explicit_without_n01_n04_build() -> None:
    result = _n_result(
        "n-admission",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert isinstance(result.admission.blockers, tuple)
    assert result.admission.n01_implemented is False
    assert result.admission.n02_implemented is False
    assert result.admission.n03_implemented is False
    assert result.admission.n04_implemented is False
    assert result.scope_marker.n01_implemented is False
    assert result.scope_marker.n02_implemented is False
    assert result.scope_marker.n03_implemented is False
    assert result.scope_marker.n04_implemented is False


def test_subject_tick_public_surfaces_expose_n_scope_truth() -> None:
    tick = execute_subject_tick(_tick_input("n-public-scope"))
    view = derive_subject_tick_contract_view(tick)
    payload = subject_tick_result_to_payload(tick)
    assert view.n_scope == "rt01_contour_only"
    assert view.n_scope_rt01_contour_only is True
    assert view.n_scope_n_minimal_only is True
    assert view.n_scope_readiness_gate_only is True
    assert view.n_scope_n01_implemented is False
    assert view.n_scope_n02_implemented is False
    assert view.n_scope_n03_implemented is False
    assert view.n_scope_n04_implemented is False
    assert view.n_scope_full_narrative_line_implemented is False
    assert view.n_scope_repo_wide_adoption is False
    assert payload["state"]["n_scope"] == "rt01_contour_only"
    assert payload["state"]["n_scope_readiness_gate_only"] is True
    assert payload["telemetry"]["n_scope_readiness_gate_only"] is True
    assert require_subject_tick_bounded_n_scope(view) is view


def test_n_minimal_and_subject_tick_consumer_scope_validators_block_overclaim() -> None:
    result = _n_result(
        "n-consumer-scope",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    view = derive_n_minimal_contract_view(result)
    assert require_bounded_n_minimal_scope(view) is view
    tampered_n_view = replace(view, scope_repo_wide_adoption=True)
    with pytest.raises(PermissionError):
        require_bounded_n_minimal_scope(tampered_n_view)
    with pytest.raises(PermissionError):
        require_strong_narrative_commitment_for_consumer(tampered_n_view)

    tick = execute_subject_tick(_tick_input("n-consumer-scope-tick"))
    tick_view = derive_subject_tick_contract_view(tick)
    assert require_subject_tick_bounded_n_scope(tick_view) is tick_view
    tampered_tick_view = replace(tick_view, n_scope_rt01_contour_only=False)
    with pytest.raises(PermissionError):
        require_subject_tick_bounded_n_scope(tampered_tick_view)
    with pytest.raises(PermissionError):
        require_subject_tick_strong_narrative_commitment(tampered_tick_view)


@pytest.mark.parametrize(
    ("include_observation", "request_action", "effect_action_id", "expected_statuses"),
    (
        (
            True,
            True,
            "__MATCHED__",
            {
                NarrativeCommitmentStatus.BOUNDED_NARRATIVE_COMMITMENT,
                NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM,
            },
        ),
        (
            True,
            True,
            None,
            {
                NarrativeCommitmentStatus.AMBIGUITY_PRESERVING_NARRATIVE,
                NarrativeCommitmentStatus.UNDERCONSTRAINED_NARRATIVE_SURFACE,
                NarrativeCommitmentStatus.CONTRADICTION_MARKED_NARRATIVE,
            },
        ),
        (
            False,
            False,
            None,
            {NarrativeCommitmentStatus.NO_SAFE_NARRATIVE_CLAIM},
        ),
    ),
)
def test_n_status_matrix_is_typed(
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    expected_statuses: set[NarrativeCommitmentStatus],
) -> None:
    result = _n_result(
        f"n-matrix-{effect_action_id}",
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
    )
    assert result.state.commitment_status in expected_statuses
