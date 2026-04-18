from __future__ import annotations

from dataclasses import dataclass

from substrate.p01_project_formation.models import (
    P01IntentionStackState,
    P01ProjectFormationResult,
)


@dataclass(frozen=True, slots=True)
class P01IntentionStackContractView:
    stack_id: str
    active_project_ids: tuple[str, ...]
    candidate_project_ids: tuple[str, ...]
    suspended_project_ids: tuple[str, ...]
    rejected_project_ids: tuple[str, ...]
    arbitration_count: int
    no_safe_project_formation: bool
    grounded_context_underconstrained: bool
    prompt_local_capture_risk: bool
    conflicting_authority: bool
    blocked_pending_grounding: bool
    candidate_only_without_activation_basis: bool
    stale_active_project_detected: bool
    intention_stack_consumer_ready: bool
    authority_bound_consumer_ready: bool
    project_handoff_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_p01_first_slice_only: bool
    scope_p02_not_implemented: bool
    scope_p03_not_implemented: bool
    scope_p04_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class P01IntentionStackConsumerView:
    stack_id: str
    has_active_projects: bool
    has_candidate_projects: bool
    requires_conflict_arbitration: bool
    clarification_or_grounding_required: bool
    prompt_local_substitution_forbidden: bool
    stale_active_project_forbidden: bool
    intention_stack_consumer_ready: bool
    authority_bound_consumer_ready: bool
    project_handoff_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_p01_project_formation_contract_view(
    result: P01ProjectFormationResult,
) -> P01IntentionStackContractView:
    if not isinstance(result, P01ProjectFormationResult):
        raise TypeError(
            "derive_p01_project_formation_contract_view requires P01ProjectFormationResult"
        )
    state = result.state
    return P01IntentionStackContractView(
        stack_id=state.stack_id,
        active_project_ids=tuple(item.project_id for item in state.active_projects),
        candidate_project_ids=tuple(item.project_id for item in state.candidate_projects),
        suspended_project_ids=tuple(item.project_id for item in state.suspended_projects),
        rejected_project_ids=tuple(item.project_id for item in state.rejected_candidates),
        arbitration_count=len(state.arbitration_records),
        no_safe_project_formation=state.no_safe_project_formation,
        grounded_context_underconstrained=state.grounded_context_underconstrained,
        prompt_local_capture_risk=state.prompt_local_capture_risk,
        conflicting_authority=state.conflicting_authority,
        blocked_pending_grounding=state.blocked_pending_grounding,
        candidate_only_without_activation_basis=state.candidate_only_without_activation_basis,
        stale_active_project_detected=state.stale_active_project_detected,
        intention_stack_consumer_ready=result.gate.intention_stack_consumer_ready,
        authority_bound_consumer_ready=result.gate.authority_bound_consumer_ready,
        project_handoff_consumer_ready=result.gate.project_handoff_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_p01_first_slice_only=result.scope_marker.p01_first_slice_only,
        scope_p02_not_implemented=result.scope_marker.p02_not_implemented,
        scope_p03_not_implemented=result.scope_marker.p03_not_implemented,
        scope_p04_not_implemented=result.scope_marker.p04_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_p01_project_formation_consumer_view(
    result_or_view: P01ProjectFormationResult | P01IntentionStackContractView,
) -> P01IntentionStackConsumerView:
    view = (
        derive_p01_project_formation_contract_view(result_or_view)
        if isinstance(result_or_view, P01ProjectFormationResult)
        else result_or_view
    )
    if not isinstance(view, P01IntentionStackContractView):
        raise TypeError(
            "derive_p01_project_formation_consumer_view requires P01ProjectFormationResult/P01IntentionStackContractView"
        )

    has_active_projects = bool(view.active_project_ids)
    has_candidate_projects = bool(view.candidate_project_ids)
    requires_conflict_arbitration = bool(
        view.conflicting_authority or view.arbitration_count > 0
    )
    clarification_or_grounding_required = bool(
        view.blocked_pending_grounding
        or view.grounded_context_underconstrained
        or view.candidate_only_without_activation_basis
        or view.no_safe_project_formation
    )
    prompt_local_substitution_forbidden = bool(view.prompt_local_capture_risk)
    stale_active_project_forbidden = bool(view.stale_active_project_detected)

    return P01IntentionStackConsumerView(
        stack_id=view.stack_id,
        has_active_projects=has_active_projects,
        has_candidate_projects=has_candidate_projects,
        requires_conflict_arbitration=requires_conflict_arbitration,
        clarification_or_grounding_required=clarification_or_grounding_required,
        prompt_local_substitution_forbidden=prompt_local_substitution_forbidden,
        stale_active_project_forbidden=stale_active_project_forbidden,
        intention_stack_consumer_ready=view.intention_stack_consumer_ready,
        authority_bound_consumer_ready=view.authority_bound_consumer_ready,
        project_handoff_consumer_ready=view.project_handoff_consumer_ready,
        restrictions=view.restrictions,
        reason="p01 intention-stack consumer view",
    )


def require_p01_intention_stack_consumer_ready(
    result_or_view: P01ProjectFormationResult | P01IntentionStackContractView,
) -> P01IntentionStackConsumerView:
    view = derive_p01_project_formation_consumer_view(result_or_view)
    if not view.intention_stack_consumer_ready:
        raise PermissionError(
            "p01 intention-stack consumer requires non-empty bounded intention stack surface"
        )
    return view


def require_p01_authority_bound_consumer_ready(
    result_or_view: P01ProjectFormationResult | P01IntentionStackContractView,
) -> P01IntentionStackConsumerView:
    view = derive_p01_project_formation_consumer_view(result_or_view)
    if not view.authority_bound_consumer_ready:
        raise PermissionError(
            "p01 authority-bound consumer requires prompt-local capture and authority conflicts to be resolved"
        )
    return view


def require_p01_project_handoff_consumer_ready(
    result_or_view: P01ProjectFormationResult | P01IntentionStackContractView,
) -> P01IntentionStackConsumerView:
    view = derive_p01_project_formation_consumer_view(result_or_view)
    if not view.project_handoff_consumer_ready:
        raise PermissionError(
            "p01 project handoff consumer requires at least one active authority-bounded project"
        )
    return view

