from __future__ import annotations

from dataclasses import dataclass

from substrate.t03_hypothesis_competition.models import (
    T03CompetitionResult,
    T03ConvergenceStatus,
)


@dataclass(frozen=True, slots=True)
class T03CompetitionContractView:
    competition_id: str
    source_t01_scene_id: str
    source_t02_constrained_scene_id: str
    convergence_status: str
    current_leader_hypothesis_id: str | None
    provisional_frontrunner_hypothesis_id: str | None
    tied_competitor_ids: tuple[str, ...]
    blocked_hypothesis_ids: tuple[str, ...]
    eliminated_hypothesis_ids: tuple[str, ...]
    reactivated_hypothesis_ids: tuple[str, ...]
    bounded_plurality: bool
    honest_nonconvergence: bool
    publication_current_leader: str | None
    publication_competitive_neighborhood: tuple[str, ...]
    publication_unresolved_conflicts: tuple[str, ...]
    publication_open_slots: tuple[str, ...]
    publication_authority_profile: tuple[str, ...]
    publication_stability_status: str
    convergence_consumer_ready: bool
    frontier_consumer_ready: bool
    nonconvergence_preserved: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_t03_first_slice_only: bool
    scope_t04_implemented: bool
    scope_o01_implemented: bool
    scope_o02_implemented: bool
    scope_o03_implemented: bool
    scope_full_silent_thought_line_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class T03PreverbalCompetitionConsumerView:
    competition_id: str
    convergence_status: str
    can_consume_convergence: bool
    frontier_consumer_ready: bool
    nonconvergence_preserved: bool
    bounded_plurality: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_t03_competition_contract_view(
    result: T03CompetitionResult,
) -> T03CompetitionContractView:
    if not isinstance(result, T03CompetitionResult):
        raise TypeError("derive_t03_competition_contract_view requires T03CompetitionResult")
    return T03CompetitionContractView(
        competition_id=result.state.competition_id,
        source_t01_scene_id=result.state.source_t01_scene_id,
        source_t02_constrained_scene_id=result.state.source_t02_constrained_scene_id,
        convergence_status=result.state.convergence_status.value,
        current_leader_hypothesis_id=result.state.current_leader_hypothesis_id,
        provisional_frontrunner_hypothesis_id=result.state.provisional_frontrunner_hypothesis_id,
        tied_competitor_ids=result.state.tied_competitor_ids,
        blocked_hypothesis_ids=result.state.blocked_hypothesis_ids,
        eliminated_hypothesis_ids=result.state.eliminated_hypothesis_ids,
        reactivated_hypothesis_ids=result.state.reactivated_hypothesis_ids,
        bounded_plurality=result.state.bounded_plurality,
        honest_nonconvergence=result.state.honest_nonconvergence,
        publication_current_leader=result.state.publication_frontier.current_leader,
        publication_competitive_neighborhood=(
            result.state.publication_frontier.competitive_neighborhood
        ),
        publication_unresolved_conflicts=result.state.publication_frontier.unresolved_conflicts,
        publication_open_slots=result.state.publication_frontier.open_slots,
        publication_authority_profile=result.state.publication_frontier.authority_profile,
        publication_stability_status=result.state.publication_frontier.stability_status,
        convergence_consumer_ready=result.gate.convergence_consumer_ready,
        frontier_consumer_ready=result.gate.frontier_consumer_ready,
        nonconvergence_preserved=result.gate.nonconvergence_preserved,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_t03_first_slice_only=result.scope_marker.t03_first_slice_only,
        scope_t04_implemented=result.scope_marker.t04_implemented,
        scope_o01_implemented=result.scope_marker.o01_implemented,
        scope_o02_implemented=result.scope_marker.o02_implemented,
        scope_o03_implemented=result.scope_marker.o03_implemented,
        scope_full_silent_thought_line_implemented=(
            result.scope_marker.full_silent_thought_line_implemented
        ),
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_t03_preverbal_competition_consumer_view(
    result_or_view: T03CompetitionResult | T03CompetitionContractView,
) -> T03PreverbalCompetitionConsumerView:
    view = (
        derive_t03_competition_contract_view(result_or_view)
        if isinstance(result_or_view, T03CompetitionResult)
        else result_or_view
    )
    if not isinstance(view, T03CompetitionContractView):
        raise TypeError(
            "derive_t03_preverbal_competition_consumer_view requires T03CompetitionResult/T03CompetitionContractView"
        )
    can_consume = bool(
        view.convergence_consumer_ready
        and view.convergence_status
        in {
            T03ConvergenceStatus.PROVISIONAL_CONVERGENCE.value,
            T03ConvergenceStatus.STABLE_LOCAL_CONVERGENCE.value,
        }
        and view.current_leader_hypothesis_id is not None
    )
    return T03PreverbalCompetitionConsumerView(
        competition_id=view.competition_id,
        convergence_status=view.convergence_status,
        can_consume_convergence=can_consume,
        frontier_consumer_ready=view.frontier_consumer_ready,
        nonconvergence_preserved=view.nonconvergence_preserved,
        bounded_plurality=view.bounded_plurality,
        restrictions=view.restrictions,
        reason="t03 pre-verbal competition consumer view derived from bounded hypothesis frontier",
    )


def require_t03_convergence_consumer_ready(
    result_or_view: T03CompetitionResult | T03CompetitionContractView,
) -> T03PreverbalCompetitionConsumerView:
    consumer_view = derive_t03_preverbal_competition_consumer_view(result_or_view)
    if not consumer_view.can_consume_convergence:
        raise PermissionError(
            "t03 convergence consumer requires lawful bounded convergence with explicit leader"
        )
    return consumer_view


def require_t03_frontier_consumer_ready(
    result_or_view: T03CompetitionResult | T03CompetitionContractView,
) -> T03PreverbalCompetitionConsumerView:
    consumer_view = derive_t03_preverbal_competition_consumer_view(result_or_view)
    if not consumer_view.frontier_consumer_ready:
        raise PermissionError(
            "t03 frontier consumer requires structured publication frontier snapshot"
        )
    return consumer_view


def derive_t03_competition_signature(
    result_or_view: T03CompetitionResult | T03CompetitionContractView,
) -> tuple[object, ...]:
    view = (
        derive_t03_competition_contract_view(result_or_view)
        if isinstance(result_or_view, T03CompetitionResult)
        else result_or_view
    )
    if not isinstance(view, T03CompetitionContractView):
        raise TypeError(
            "derive_t03_competition_signature requires T03CompetitionResult/T03CompetitionContractView"
        )
    return (
        view.convergence_status,
        view.current_leader_hypothesis_id,
        tuple(sorted(view.tied_competitor_ids)),
        tuple(sorted(view.publication_unresolved_conflicts)),
        tuple(sorted(view.publication_open_slots)),
        tuple(sorted(view.publication_competitive_neighborhood)),
    )
