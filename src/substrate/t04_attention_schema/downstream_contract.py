from __future__ import annotations

from dataclasses import dataclass

from substrate.t04_attention_schema.models import T04AttentionSchemaResult, T04ReportabilityStatus


@dataclass(frozen=True, slots=True)
class T04AttentionSchemaContractView:
    schema_id: str
    source_t03_competition_id: str
    focus_targets: tuple[tuple[str, str | None, float, str], ...]
    peripheral_targets: tuple[tuple[str, str | None, float, str], ...]
    attention_owner: str
    focus_mode: str
    control_estimate: float
    stability_estimate: float
    redirect_cost: float
    reportability_status: str
    focus_ownership_consumer_ready: bool
    reportable_focus_consumer_ready: bool
    peripheral_preservation_ready: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_t04_first_slice_only: bool
    scope_o01_implemented: bool
    scope_o02_implemented: bool
    scope_o03_implemented: bool
    scope_full_attention_line_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class T04PreverbalFocusConsumerView:
    schema_id: str
    can_consume_focus_ownership: bool
    can_consume_reportable_focus: bool
    peripheral_preservation_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_t04_attention_schema_contract_view(
    result: T04AttentionSchemaResult,
) -> T04AttentionSchemaContractView:
    if not isinstance(result, T04AttentionSchemaResult):
        raise TypeError("derive_t04_attention_schema_contract_view requires T04AttentionSchemaResult")
    return T04AttentionSchemaContractView(
        schema_id=result.state.schema_id,
        source_t03_competition_id=result.state.source_t03_competition_id,
        focus_targets=tuple(
            (
                item.target_id,
                item.source_hypothesis_id,
                item.prominence_score,
                item.status.value,
            )
            for item in result.state.focus_targets
        ),
        peripheral_targets=tuple(
            (
                item.target_id,
                item.source_hypothesis_id,
                item.prominence_score,
                item.status.value,
            )
            for item in result.state.peripheral_targets
        ),
        attention_owner=result.state.attention_owner.value,
        focus_mode=result.state.focus_mode.value,
        control_estimate=result.state.control_estimate,
        stability_estimate=result.state.stability_estimate,
        redirect_cost=result.state.redirect_cost,
        reportability_status=result.state.reportability_status.value,
        focus_ownership_consumer_ready=result.gate.focus_ownership_consumer_ready,
        reportable_focus_consumer_ready=result.gate.reportable_focus_consumer_ready,
        peripheral_preservation_ready=result.gate.peripheral_preservation_ready,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_t04_first_slice_only=result.scope_marker.t04_first_slice_only,
        scope_o01_implemented=result.scope_marker.o01_implemented,
        scope_o02_implemented=result.scope_marker.o02_implemented,
        scope_o03_implemented=result.scope_marker.o03_implemented,
        scope_full_attention_line_implemented=result.scope_marker.full_attention_line_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_t04_preverbal_focus_consumer_view(
    result_or_view: T04AttentionSchemaResult | T04AttentionSchemaContractView,
) -> T04PreverbalFocusConsumerView:
    view = (
        derive_t04_attention_schema_contract_view(result_or_view)
        if isinstance(result_or_view, T04AttentionSchemaResult)
        else result_or_view
    )
    if not isinstance(view, T04AttentionSchemaContractView):
        raise TypeError(
            "derive_t04_preverbal_focus_consumer_view requires T04AttentionSchemaResult/T04AttentionSchemaContractView"
        )
    can_consume_reportable_focus = bool(
        view.reportable_focus_consumer_ready
        and view.reportability_status
        in {
            T04ReportabilityStatus.REPORTABLE_STABLE.value,
            T04ReportabilityStatus.REPORTABLE_PROVISIONAL.value,
        }
    )
    return T04PreverbalFocusConsumerView(
        schema_id=view.schema_id,
        can_consume_focus_ownership=view.focus_ownership_consumer_ready,
        can_consume_reportable_focus=can_consume_reportable_focus,
        peripheral_preservation_ready=view.peripheral_preservation_ready,
        restrictions=view.restrictions,
        reason="t04 pre-verbal focus consumer view derived from bounded attention schema",
    )


def require_t04_focus_ownership_consumer_ready(
    result_or_view: T04AttentionSchemaResult | T04AttentionSchemaContractView,
) -> T04PreverbalFocusConsumerView:
    view = derive_t04_preverbal_focus_consumer_view(result_or_view)
    if not view.can_consume_focus_ownership:
        raise PermissionError(
            "t04 focus ownership consumer requires explicit lawful attention owner and control basis"
        )
    return view


def require_t04_reportable_focus_consumer_ready(
    result_or_view: T04AttentionSchemaResult | T04AttentionSchemaContractView,
) -> T04PreverbalFocusConsumerView:
    view = derive_t04_preverbal_focus_consumer_view(result_or_view)
    if not view.can_consume_reportable_focus:
        raise PermissionError(
            "t04 reportable focus consumer requires reportability status consistent with stability/control"
        )
    return view


def require_t04_peripheral_preservation_ready(
    result_or_view: T04AttentionSchemaResult | T04AttentionSchemaContractView,
) -> T04PreverbalFocusConsumerView:
    view = derive_t04_preverbal_focus_consumer_view(result_or_view)
    if not view.peripheral_preservation_ready:
        raise PermissionError(
            "t04 peripheral preservation consumer requires unresolved competitive targets to remain visible"
        )
    return view
