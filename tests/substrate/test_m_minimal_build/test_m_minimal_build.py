from __future__ import annotations

import pytest

from substrate.a_line_normalization import build_a_line_normalization
from substrate.m_minimal import (
    MemoryLifecycleStatus,
    build_m_minimal,
    derive_m_minimal_contract_view,
    m_minimal_snapshot,
)
from substrate.self_contour import build_s_minimal_contour
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    derive_subject_tick_contract_view,
    execute_subject_tick,
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
        source_ref="world.sensor.sprint8d",
        observed_at="2026-04-10T10:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _m_result(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str = "reuse_without_revalidation",
):
    tick_id = f"tick-{case_id}"
    if effect_action_id == "__MATCHED__":
        effect_action_id = f"world-action-{tick_id}"
    effect_packet = None
    if effect_action_id is not None:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=effect_action_id,
            observed_at="2026-04-10T10:00:01+00:00",
            source_ref="world.effect.sprint8d",
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
        source_lineage=("test.sprint8d.m-minimal",),
    )
    world_entry = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.sprint8d.m-minimal",),
    )
    s_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry,
        world_adapter_result=adapter_result,
        source_lineage=("test.sprint8d.m-minimal",),
    )
    a_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        source_lineage=("test.sprint8d.m-minimal",),
    )
    return build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        c05_validity_action=c05_action,
        source_lineage=("test.sprint8d.m-minimal",),
    )


def test_m_minimal_materializes_typed_lifecycle_and_scope() -> None:
    result = _m_result(
        "m-typed",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    view = derive_m_minimal_contract_view(result)
    snapshot = m_minimal_snapshot(result)
    assert result.state.memory_item_id.startswith("m-memory-item:")
    assert result.state.lifecycle_status == MemoryLifecycleStatus.BOUNDED_RETAINED
    assert result.gate.safe_memory_claim_allowed is True
    assert view.scope == "rt01_contour_only"
    assert view.scope_rt01_contour_only is True
    assert view.scope_m_minimal_only is True
    assert view.scope_readiness_gate_only is True
    assert view.scope_m01_implemented is False
    assert view.scope_m02_implemented is False
    assert view.scope_m03_implemented is False
    assert view.scope_full_memory_stack_implemented is False
    assert view.scope_repo_wide_adoption is False
    assert view.m01_structurally_present_but_not_ready in {True, False}
    assert view.m01_stale_risk_unacceptable in {True, False}
    assert view.m01_conflict_risk_unacceptable in {True, False}
    assert view.m01_reactivation_requires_review in {True, False}
    assert view.m01_temporary_carry_not_stable_enough in {True, False}
    assert view.m01_no_safe_memory_basis in {True, False}
    assert view.m01_provenance_insufficient in {True, False}
    assert view.m01_lifecycle_underconstrained in {True, False}
    assert snapshot["admission"]["m01_implemented"] is False
    assert snapshot["admission"]["m02_implemented"] is False
    assert snapshot["admission"]["m03_implemented"] is False
    assert snapshot["scope_marker"]["readiness_gate_only"] is True


def test_temporary_carry_vs_bounded_retained_contrast_is_typed() -> None:
    temporary = _m_result(
        "m-temporary",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
    )
    bounded = _m_result(
        "m-bounded",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert temporary.state.lifecycle_status in {
        MemoryLifecycleStatus.TEMPORARY_CARRY,
        MemoryLifecycleStatus.REVIEW_REQUIRED,
        MemoryLifecycleStatus.REACTIVATION_CANDIDATE,
    }
    assert bounded.state.lifecycle_status == MemoryLifecycleStatus.BOUNDED_RETAINED
    assert temporary.gate.safe_memory_claim_allowed is False
    assert bounded.gate.safe_memory_claim_allowed is True
    assert temporary.state.bounded_persistence_allowed is False
    assert bounded.state.bounded_persistence_allowed is True


def test_stale_and_conflict_shortcuts_are_machine_readable() -> None:
    stale = _m_result(
        "m-stale",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c05_action="suspend_until_revalidation_basis",
    )
    no_basis = _m_result(
        "m-no-basis",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert stale.state.stale_risk.value in {"medium", "high"}
    assert "stale_memory_reframed_as_current_truth" in stale.gate.forbidden_shortcuts
    assert no_basis.gate.no_safe_memory_claim is True
    assert "no_provenance_memory_claim" in no_basis.gate.forbidden_shortcuts
    assert "unreviewed_memory_reused_as_safe_basis" in no_basis.gate.forbidden_shortcuts


def test_m01_readiness_hard_blockers_are_falsifiable_on_borderline_lifecycle() -> None:
    borderline = _m_result(
        "m-borderline",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    admission = borderline.admission
    assert admission.admission_ready_for_m01 is False
    assert admission.structurally_present_but_not_ready is True
    assert admission.stale_risk_unacceptable is True
    assert admission.temporary_carry_not_stable_enough is True
    assert admission.lifecycle_underconstrained is True
    assert "stale_risk_unacceptable" in admission.blockers
    assert "temporary_carry_not_stable_enough" in admission.blockers
    assert "lifecycle_underconstrained" in admission.blockers


def test_weak_provenance_and_no_safe_basis_block_m01_admission() -> None:
    no_basis = _m_result(
        "m-no-safe-basis",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    admission = no_basis.admission
    assert admission.admission_ready_for_m01 is False
    assert admission.no_safe_memory_basis is True
    assert admission.provenance_insufficient is True
    assert "no_safe_memory_basis" in admission.blockers
    assert "provenance_insufficient" in admission.blockers


def test_m_lifecycle_adversarial_distinctions_are_not_collapsed() -> None:
    retained = _m_result(
        "m-retained",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    stale = _m_result(
        "m-stale-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c05_action="run_selective_revalidation",
    )
    no_safe = _m_result(
        "m-no-safe-contrast",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    reactivation = _m_result(
        "m-reactivation-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
    )
    assert retained.state.lifecycle_status == MemoryLifecycleStatus.BOUNDED_RETAINED
    assert stale.state.stale_risk.value in {"medium", "high"}
    assert stale.state.lifecycle_status in {
        MemoryLifecycleStatus.NO_SAFE_MEMORY_CLAIM,
        MemoryLifecycleStatus.REVIEW_REQUIRED,
        MemoryLifecycleStatus.REACTIVATION_CANDIDATE,
        MemoryLifecycleStatus.STALE_MEMORY_SURFACE,
        MemoryLifecycleStatus.PRUNING_CANDIDATE,
    }
    assert stale.gate.safe_memory_claim_allowed is False
    assert stale.state.bounded_persistence_allowed is False
    assert no_safe.state.lifecycle_status == MemoryLifecycleStatus.NO_SAFE_MEMORY_CLAIM
    assert no_safe.gate.no_safe_memory_claim is True
    assert no_safe.gate.safe_memory_claim_allowed is False
    assert reactivation.state.lifecycle_status in {
        MemoryLifecycleStatus.REACTIVATION_CANDIDATE,
        MemoryLifecycleStatus.REVIEW_REQUIRED,
    }
    assert reactivation.gate.safe_memory_claim_allowed is False
    assert reactivation.state.bounded_persistence_allowed is False


def test_rt01_memory_safe_claim_requirement_is_path_affecting() -> None:
    baseline = execute_subject_tick(_tick_input("m-rt01-baseline"))
    enforced = execute_subject_tick(
        _tick_input("m-rt01-enforced"),
        context=SubjectTickContext(require_memory_safe_claim=True),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.m_minimal_contour_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in enforced.state.execution_checkpoints
    )


def test_m_line_admission_surface_is_explicit_without_m01_m02_m03_build() -> None:
    result = _m_result(
        "m-admission",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert isinstance(result.admission.blockers, tuple)
    assert result.admission.m01_implemented is False
    assert result.admission.m02_implemented is False
    assert result.admission.m03_implemented is False
    assert result.scope_marker.m01_implemented is False
    assert result.scope_marker.m02_implemented is False
    assert result.scope_marker.m03_implemented is False


def test_subject_tick_public_surfaces_expose_m_scope_truth() -> None:
    tick = execute_subject_tick(_tick_input("m-public-scope"))
    view = derive_subject_tick_contract_view(tick)
    payload = subject_tick_result_to_payload(tick)
    assert view.m_scope == "rt01_contour_only"
    assert view.m_scope_rt01_contour_only is True
    assert view.m_scope_m_minimal_only is True
    assert view.m_scope_readiness_gate_only is True
    assert view.m_scope_m01_implemented is False
    assert view.m_scope_m02_implemented is False
    assert view.m_scope_m03_implemented is False
    assert view.m_scope_full_memory_stack_implemented is False
    assert view.m_scope_repo_wide_adoption is False
    assert payload["state"]["m_scope"] == "rt01_contour_only"
    assert payload["state"]["m_scope_readiness_gate_only"] is True
    assert payload["telemetry"]["m_scope_readiness_gate_only"] is True


@pytest.mark.parametrize(
    ("include_observation", "request_action", "effect_action_id", "expected"),
    (
        (True, True, "__MATCHED__", MemoryLifecycleStatus.BOUNDED_RETAINED),
        (True, True, None, MemoryLifecycleStatus.REACTIVATION_CANDIDATE),
        (False, False, None, MemoryLifecycleStatus.NO_SAFE_MEMORY_CLAIM),
    ),
)
def test_m_lifecycle_matrix_is_typed(
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    expected: MemoryLifecycleStatus,
) -> None:
    result = _m_result(
        f"m-matrix-{expected.value}",
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
    )
    assert result.state.lifecycle_status == expected
