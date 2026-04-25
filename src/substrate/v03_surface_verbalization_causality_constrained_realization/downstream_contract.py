from __future__ import annotations

from dataclasses import dataclass

from substrate.v03_surface_verbalization_causality_constrained_realization.models import (
    V03ConstrainedRealizationResult,
)


@dataclass(frozen=True, slots=True)
class V03RealizationContractView:
    realization_status: str
    realization_id: str
    segment_count: int
    aligned_segment_count: int
    hard_constraint_violation_count: int
    qualifier_locality_failures: int
    blocked_expansion_leak_detected: bool
    protected_omission_violation_detected: bool
    boundary_before_explanation_required: bool
    boundary_before_explanation_satisfied: bool
    partial_realization_only: bool
    replan_required: bool
    selected_branch_id: str
    mandatory_qualifier_ids: tuple[str, ...]
    blocked_expansion_ids: tuple[str, ...]
    protected_omission_ids: tuple[str, ...]
    realization_consumer_ready: bool
    alignment_consumer_ready: bool
    constraint_report_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_v03_first_slice_only: bool
    scope_v_line_not_map_wide_ready: bool
    scope_p02_not_implemented: bool
    scope_map_wide_realization_enforcement: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class V03RealizationConsumerView:
    realization_status: str
    hard_constraint_violation_count: int
    qualifier_locality_failures: int
    blocked_expansion_leak_detected: bool
    boundary_before_explanation_required: bool
    boundary_before_explanation_satisfied: bool
    partial_realization_only: bool
    replan_required: bool
    realization_consumer_ready: bool
    alignment_consumer_ready: bool
    constraint_report_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_v03_realization_contract_view(
    result: V03ConstrainedRealizationResult,
) -> V03RealizationContractView:
    if not isinstance(result, V03ConstrainedRealizationResult):
        raise TypeError("derive_v03_realization_contract_view requires V03ConstrainedRealizationResult")
    return V03RealizationContractView(
        realization_status=result.realization_status.value,
        realization_id=result.artifact.realization_id,
        segment_count=len(result.artifact.realized_segment_ids),
        aligned_segment_count=result.alignment_map.aligned_segment_count,
        hard_constraint_violation_count=result.constraint_report.hard_constraint_violation_count,
        qualifier_locality_failures=result.constraint_report.qualifier_locality_failures,
        blocked_expansion_leak_detected=result.constraint_report.blocked_expansion_leak_detected,
        protected_omission_violation_detected=result.constraint_report.protected_omission_violation_detected,
        boundary_before_explanation_required=result.constraint_report.boundary_before_explanation_required,
        boundary_before_explanation_satisfied=result.constraint_report.boundary_before_explanation_satisfied,
        partial_realization_only=result.failure_state.partial_realization_only,
        replan_required=result.failure_state.replan_required,
        selected_branch_id=result.artifact.selected_branch_id,
        mandatory_qualifier_ids=tuple(
            dict.fromkeys(
                qualifier_id
                for alignment in result.alignment_map.alignments
                for qualifier_id in _extract_alignment_qualifier_ids(alignment.realized_text)
            )
        ),
        blocked_expansion_ids=result.artifact.blocked_expansion_ids,
        protected_omission_ids=result.artifact.protected_omission_ids,
        realization_consumer_ready=result.gate.realization_consumer_ready,
        alignment_consumer_ready=result.gate.alignment_consumer_ready,
        constraint_report_consumer_ready=result.gate.constraint_report_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_v03_first_slice_only=result.scope_marker.v03_first_slice_only,
        scope_v_line_not_map_wide_ready=result.scope_marker.v_line_not_map_wide_ready,
        scope_p02_not_implemented=result.scope_marker.p02_not_implemented,
        scope_map_wide_realization_enforcement=result.scope_marker.map_wide_realization_enforcement,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_v03_realization_consumer_view(
    result_or_view: V03ConstrainedRealizationResult | V03RealizationContractView,
) -> V03RealizationConsumerView:
    view = (
        derive_v03_realization_contract_view(result_or_view)
        if isinstance(result_or_view, V03ConstrainedRealizationResult)
        else result_or_view
    )
    if not isinstance(view, V03RealizationContractView):
        raise TypeError(
            "derive_v03_realization_consumer_view requires "
            "V03ConstrainedRealizationResult/V03RealizationContractView"
        )
    return V03RealizationConsumerView(
        realization_status=view.realization_status,
        hard_constraint_violation_count=view.hard_constraint_violation_count,
        qualifier_locality_failures=view.qualifier_locality_failures,
        blocked_expansion_leak_detected=view.blocked_expansion_leak_detected,
        boundary_before_explanation_required=view.boundary_before_explanation_required,
        boundary_before_explanation_satisfied=view.boundary_before_explanation_satisfied,
        partial_realization_only=view.partial_realization_only,
        replan_required=view.replan_required,
        realization_consumer_ready=view.realization_consumer_ready,
        alignment_consumer_ready=view.alignment_consumer_ready,
        constraint_report_consumer_ready=view.constraint_report_consumer_ready,
        restrictions=view.restrictions,
        reason="v03 constrained-realization consumer view",
    )


def require_v03_realization_consumer_ready(
    result_or_view: V03ConstrainedRealizationResult | V03RealizationContractView,
) -> V03RealizationConsumerView:
    view = derive_v03_realization_consumer_view(result_or_view)
    if not view.realization_consumer_ready:
        raise PermissionError("v03 realization consumer requires constrained realization artifact readiness")
    return view


def require_v03_alignment_consumer_ready(
    result_or_view: V03ConstrainedRealizationResult | V03RealizationContractView,
) -> V03RealizationConsumerView:
    view = derive_v03_realization_consumer_view(result_or_view)
    if not view.alignment_consumer_ready:
        raise PermissionError("v03 alignment consumer requires span-level alignment pass")
    return view


def require_v03_constraint_report_consumer_ready(
    result_or_view: V03ConstrainedRealizationResult | V03RealizationContractView,
) -> V03RealizationConsumerView:
    view = derive_v03_realization_consumer_view(result_or_view)
    if not view.constraint_report_consumer_ready:
        raise PermissionError("v03 constrained-realization consumer requires hard-constraint pass")
    return view


def _extract_alignment_qualifier_ids(realized_text: str) -> tuple[str, ...]:
    if "qualifier_ids:[" not in realized_text:
        return ()
    start = realized_text.find("qualifier_ids:[")
    if start < 0:
        return ()
    payload = realized_text[start + len("qualifier_ids:[") :]
    end = payload.find("]")
    if end < 0:
        return ()
    raw = payload[:end]
    if not raw.strip():
        return ()
    return tuple(item.strip() for item in raw.split(",") if item.strip())

