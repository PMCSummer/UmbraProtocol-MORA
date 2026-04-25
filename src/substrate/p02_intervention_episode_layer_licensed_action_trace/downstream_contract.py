from __future__ import annotations

from dataclasses import dataclass

from substrate.p02_intervention_episode_layer_licensed_action_trace.models import (
    P02InterventionEpisodeResult,
)


@dataclass(frozen=True, slots=True)
class P02InterventionEpisodeContractView:
    episode_count: int
    completed_as_licensed_count: int
    partial_episode_count: int
    blocked_episode_count: int
    awaiting_verification_count: int
    completion_verified_count: int
    overrun_detected_count: int
    boundary_ambiguous_count: int
    license_link_missing_count: int
    residue_count: int
    side_effect_count: int
    episode_consumer_ready: bool
    boundary_consumer_ready: bool
    verification_consumer_ready: bool
    restrictions: tuple[str, ...]
    episode_statuses: tuple[str, ...]
    execution_statuses: tuple[str, ...]
    verification_statuses: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_p02_first_slice_only: bool
    scope_no_project_formation_authority: bool
    scope_no_action_licensing_authority: bool
    scope_no_external_success_claim_without_evidence: bool
    scope_no_memory_retention_authority: bool
    scope_no_map_wide_rollout_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class P02InterventionEpisodeConsumerView:
    episode_count: int
    completed_as_licensed_count: int
    partial_episode_count: int
    blocked_episode_count: int
    awaiting_verification_count: int
    completion_verified_count: int
    overrun_detected_count: int
    boundary_ambiguous_count: int
    license_link_missing_count: int
    residue_count: int
    side_effect_count: int
    episode_consumer_ready: bool
    boundary_consumer_ready: bool
    verification_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_p02_intervention_episode_contract_view(
    result: P02InterventionEpisodeResult,
) -> P02InterventionEpisodeContractView:
    if not isinstance(result, P02InterventionEpisodeResult):
        raise TypeError("derive_p02_intervention_episode_contract_view requires P02InterventionEpisodeResult")
    metadata = result.metadata
    return P02InterventionEpisodeContractView(
        episode_count=metadata.episode_count,
        completed_as_licensed_count=metadata.completed_as_licensed_count,
        partial_episode_count=metadata.partial_episode_count,
        blocked_episode_count=metadata.blocked_episode_count,
        awaiting_verification_count=metadata.awaiting_verification_count,
        completion_verified_count=metadata.completion_verified_count,
        overrun_detected_count=metadata.overrun_detected_count,
        boundary_ambiguous_count=metadata.boundary_ambiguous_count,
        license_link_missing_count=metadata.license_link_missing_count,
        residue_count=metadata.residue_count,
        side_effect_count=metadata.side_effect_count,
        episode_consumer_ready=result.gate.episode_consumer_ready,
        boundary_consumer_ready=result.gate.boundary_consumer_ready,
        verification_consumer_ready=result.gate.verification_consumer_ready,
        restrictions=result.gate.restrictions,
        episode_statuses=tuple(item.status.value for item in result.episodes),
        execution_statuses=tuple(item.execution_status.value for item in result.episodes),
        verification_statuses=tuple(item.outcome_verification_status.value for item in result.episodes),
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_p02_first_slice_only=result.scope_marker.p02_first_slice_only,
        scope_no_project_formation_authority=result.scope_marker.no_project_formation_authority,
        scope_no_action_licensing_authority=result.scope_marker.no_action_licensing_authority,
        scope_no_external_success_claim_without_evidence=(
            result.scope_marker.no_external_success_claim_without_evidence
        ),
        scope_no_memory_retention_authority=result.scope_marker.no_memory_retention_authority,
        scope_no_map_wide_rollout_claim=result.scope_marker.no_map_wide_rollout_claim,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_p02_intervention_episode_consumer_view(
    result_or_view: P02InterventionEpisodeResult | P02InterventionEpisodeContractView,
) -> P02InterventionEpisodeConsumerView:
    view = (
        derive_p02_intervention_episode_contract_view(result_or_view)
        if isinstance(result_or_view, P02InterventionEpisodeResult)
        else result_or_view
    )
    if not isinstance(view, P02InterventionEpisodeContractView):
        raise TypeError(
            "derive_p02_intervention_episode_consumer_view requires P02InterventionEpisodeResult/P02InterventionEpisodeContractView"
        )
    return P02InterventionEpisodeConsumerView(
        episode_count=view.episode_count,
        completed_as_licensed_count=view.completed_as_licensed_count,
        partial_episode_count=view.partial_episode_count,
        blocked_episode_count=view.blocked_episode_count,
        awaiting_verification_count=view.awaiting_verification_count,
        completion_verified_count=view.completion_verified_count,
        overrun_detected_count=view.overrun_detected_count,
        boundary_ambiguous_count=view.boundary_ambiguous_count,
        license_link_missing_count=view.license_link_missing_count,
        residue_count=view.residue_count,
        side_effect_count=view.side_effect_count,
        episode_consumer_ready=view.episode_consumer_ready,
        boundary_consumer_ready=view.boundary_consumer_ready,
        verification_consumer_ready=view.verification_consumer_ready,
        restrictions=view.restrictions,
        reason="p02 intervention episode consumer view",
    )


def require_p02_episode_consumer_ready(
    result_or_view: P02InterventionEpisodeResult | P02InterventionEpisodeContractView,
) -> P02InterventionEpisodeConsumerView:
    view = derive_p02_intervention_episode_consumer_view(result_or_view)
    if not view.episode_consumer_ready:
        raise PermissionError("p02 episode consumer requires explicit intervention episode record readiness")
    return view


def require_p02_boundary_consumer_ready(
    result_or_view: P02InterventionEpisodeResult | P02InterventionEpisodeContractView,
) -> P02InterventionEpisodeConsumerView:
    view = derive_p02_intervention_episode_consumer_view(result_or_view)
    if not view.boundary_consumer_ready:
        raise PermissionError("p02 boundary consumer requires non-ambiguous episode boundary")
    return view


def require_p02_verification_consumer_ready(
    result_or_view: P02InterventionEpisodeResult | P02InterventionEpisodeContractView,
) -> P02InterventionEpisodeConsumerView:
    view = derive_p02_intervention_episode_consumer_view(result_or_view)
    if not view.verification_consumer_ready:
        raise PermissionError("p02 verification consumer requires explicit verification-ready episode state")
    return view
