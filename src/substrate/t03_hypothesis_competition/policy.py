from __future__ import annotations

from dataclasses import replace

from substrate.a_line_normalization import ALineNormalizationResult
from substrate.m_minimal import MMinimalResult
from substrate.n_minimal import NMinimalResult
from substrate.self_contour import SMinimalContourResult
from substrate.t01_semantic_field import T01ActiveFieldResult
from substrate.t02_relation_binding import T02BindingStatus, T02ConstrainedSceneResult
from substrate.t03_hypothesis_competition.models import (
    ForbiddenT03Shortcut,
    T03CompetitionMode,
    T03CompetitionOperation,
    T03CompetitionResult,
    T03CompetitionState,
    T03ConvergenceStatus,
    T03GateDecision,
    T03HypothesisCandidate,
    T03HypothesisStatus,
    T03PublicationFrontierSnapshot,
    T03ScopeMarker,
    T03StabilityState,
    T03Telemetry,
)
from substrate.world_entry_contract import WorldEntryContractResult

_REVALIDATE_ACTIONS = {
    "run_selective_revalidation",
    "run_bounded_revalidation",
    "suspend_until_revalidation_basis",
    "halt_reuse_and_rebuild_scope",
}


def build_t03_hypothesis_competition(
    *,
    tick_id: str,
    t01_result: T01ActiveFieldResult,
    t02_result: T02ConstrainedSceneResult,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    c05_validity_action: str,
    prior_state: T03CompetitionState | None = None,
    competition_mode: T03CompetitionMode = T03CompetitionMode.BOUNDED_COMPETITION,
    preserve_plurality: bool = True,
    allow_revival: bool = True,
    source_lineage: tuple[str, ...] = (),
) -> T03CompetitionResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(t01_result, T01ActiveFieldResult):
        raise TypeError("t01_result must be T01ActiveFieldResult")
    if not isinstance(t02_result, T02ConstrainedSceneResult):
        raise TypeError("t02_result must be T02ConstrainedSceneResult")
    if not isinstance(world_entry_result, WorldEntryContractResult):
        raise TypeError("world_entry_result must be WorldEntryContractResult")
    if not isinstance(s_minimal_result, SMinimalContourResult):
        raise TypeError("s_minimal_result must be SMinimalContourResult")
    if not isinstance(a_line_result, ALineNormalizationResult):
        raise TypeError("a_line_result must be ALineNormalizationResult")
    if not isinstance(m_minimal_result, MMinimalResult):
        raise TypeError("m_minimal_result must be MMinimalResult")
    if not isinstance(n_minimal_result, NMinimalResult):
        raise TypeError("n_minimal_result must be NMinimalResult")

    authority_weight = _authority_weight(
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        competition_mode=competition_mode,
    )
    candidates = _build_initial_candidates(
        t01_result=t01_result,
        t02_result=t02_result,
        authority_weight=authority_weight,
        c05_validity_action=c05_validity_action,
        competition_mode=competition_mode,
    )
    forbidden = _forbidden_shortcuts_from_mode(competition_mode)
    candidates, mode_forbidden = _apply_mode_biases(
        candidates=candidates,
        t01_result=t01_result,
        competition_mode=competition_mode,
        authority_weight=authority_weight,
    )
    forbidden.extend(mode_forbidden)
    ranked = tuple(sorted(candidates, key=lambda item: item.competition_score, reverse=True))

    convergence_status, leader_id, provisional_id, tied_ids, eliminated_ids, forced_single = (
        _derive_convergence_frontier(
            ranked=ranked,
            preserve_plurality=preserve_plurality,
            competition_mode=competition_mode,
        )
    )
    if forced_single:
        forbidden.append(ForbiddenT03Shortcut.FORCED_SINGLE_WINNER_UNDER_AMBIGUITY.value)

    reactivated_ids, revival_forbidden = _derive_reactivation(
        ranked=ranked,
        prior_state=prior_state,
        allow_revival=allow_revival,
        competition_mode=competition_mode,
    )
    forbidden.extend(revival_forbidden)
    blocked_ids = tuple(
        item.hypothesis_id for item in ranked if item.status is T03HypothesisStatus.BLOCKED
    )
    status_applied = _apply_candidate_statuses(
        ranked=ranked,
        leader_id=leader_id,
        provisional_id=provisional_id,
        tied_ids=tied_ids,
        blocked_ids=blocked_ids,
        eliminated_ids=eliminated_ids,
        reactivated_ids=reactivated_ids,
    )
    publication_frontier = _build_publication_frontier(
        ranked=status_applied,
        leader_id=leader_id,
        tied_ids=tied_ids,
        t01_result=t01_result,
        t02_result=t02_result,
        authority_weight=authority_weight,
        convergence_status=convergence_status,
    )
    honest_nonconvergence = convergence_status is T03ConvergenceStatus.HONEST_NONCONVERGENCE
    bounded_plurality = bool(tied_ids) and preserve_plurality
    operations = [
        T03CompetitionOperation.REGISTER_CANDIDATES.value,
        T03CompetitionOperation.WEIGHT_AUTHORITY_SUPPORT.value,
        T03CompetitionOperation.APPLY_CONSTRAINT_LOAD.value,
        T03CompetitionOperation.APPLY_UNRESOLVED_BURDEN.value,
        T03CompetitionOperation.RESOLVE_FRONTIER.value,
    ]
    if honest_nonconvergence:
        operations.append(T03CompetitionOperation.PRESERVE_NONCONVERGENCE.value)
    if reactivated_ids:
        operations.append(T03CompetitionOperation.REACTIVATE_HYPOTHESIS.value)

    state = T03CompetitionState(
        competition_id=f"t03-competition:{tick_id}",
        source_t01_scene_id=t01_result.state.scene_id,
        source_t02_constrained_scene_id=t02_result.state.constrained_scene_id,
        candidates=status_applied,
        convergence_status=convergence_status,
        current_leader_hypothesis_id=leader_id,
        provisional_frontrunner_hypothesis_id=provisional_id,
        tied_competitor_ids=tied_ids,
        blocked_hypothesis_ids=blocked_ids,
        eliminated_hypothesis_ids=eliminated_ids,
        reactivated_hypothesis_ids=reactivated_ids,
        honest_nonconvergence=honest_nonconvergence,
        bounded_plurality=bounded_plurality,
        publication_frontier=publication_frontier,
        operations_applied=tuple(dict.fromkeys(operations)),
        source_authority_tags=tuple(
            dict.fromkeys(
                (
                    *t01_result.state.source_authority_tags,
                    *t02_result.state.source_authority_tags,
                    f"T03:authority_weight={authority_weight:.3f}",
                    f"C05:validity_action={c05_validity_action}",
                )
            )
        ),
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *t01_result.state.source_lineage,
                    *t02_result.state.source_lineage,
                    *world_entry_result.episode.source_lineage,
                    *s_minimal_result.state.source_lineage,
                    *a_line_result.state.source_lineage,
                    *m_minimal_result.state.source_lineage,
                    *n_minimal_result.state.source_lineage,
                )
            )
        ),
        provenance="t03.hypothesis_competition.silent_convergence",
    )
    gate = _build_gate(
        state=state,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        preserve_plurality=preserve_plurality,
    )
    scope_marker = _build_scope_marker()
    telemetry = T03Telemetry(
        competition_id=state.competition_id,
        source_t01_scene_id=state.source_t01_scene_id,
        source_t02_constrained_scene_id=state.source_t02_constrained_scene_id,
        convergence_status=state.convergence_status,
        candidates_count=len(state.candidates),
        blocked_hypothesis_count=len(state.blocked_hypothesis_ids),
        eliminated_hypothesis_count=len(state.eliminated_hypothesis_ids),
        reactivated_hypothesis_count=len(state.reactivated_hypothesis_ids),
        tied_competitor_count=len(state.tied_competitor_ids),
        bounded_plurality=state.bounded_plurality,
        honest_nonconvergence=state.honest_nonconvergence,
        convergence_consumer_ready=gate.convergence_consumer_ready,
        frontier_consumer_ready=gate.frontier_consumer_ready,
        nonconvergence_preserved=gate.nonconvergence_preserved,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return T03CompetitionResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="t03.first_bounded_hypothesis_competition_slice",
    )


def _authority_weight(
    *,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    competition_mode: T03CompetitionMode,
) -> float:
    if competition_mode is T03CompetitionMode.AUTHORITY_WEIGHT_DISABLE_ABLATION:
        return 1.0
    return min(
        world_entry_result.episode.confidence,
        s_minimal_result.state.attribution_confidence,
        a_line_result.state.confidence,
        m_minimal_result.state.confidence,
        n_minimal_result.state.confidence,
    )


def _build_initial_candidates(
    *,
    t01_result: T01ActiveFieldResult,
    t02_result: T02ConstrainedSceneResult,
    authority_weight: float,
    c05_validity_action: str,
    competition_mode: T03CompetitionMode,
) -> tuple[T03HypothesisCandidate, ...]:
    confirmed = tuple(
        item.binding_id
        for item in t02_result.state.relation_bindings
        if item.status is T02BindingStatus.CONFIRMED
    )
    provisional = tuple(
        item.binding_id
        for item in t02_result.state.relation_bindings
        if item.status is T02BindingStatus.PROVISIONAL
    )
    blocked = tuple(
        item.binding_id
        for item in t02_result.state.relation_bindings
        if item.status is T02BindingStatus.BLOCKED
    )
    conflicted = tuple(
        item.binding_id
        for item in t02_result.state.relation_bindings
        if item.status in {T02BindingStatus.CONFLICTED, T02BindingStatus.INCOMPATIBLE}
    )
    unresolved_load = float(len(t01_result.state.unresolved_slots)) + (
        0.5 if t02_result.gate.no_clean_binding_commit else 0.0
    )
    c05_pressure = 0.2 if c05_validity_action in _REVALIDATE_ACTIONS else 0.0

    candidates: list[T03HypothesisCandidate] = []

    grounded_support = confirmed or provisional[:1]
    grounded_violations = tuple(
        item.constraint_id
        for item in t02_result.state.constraint_objects
        if item.propagation_status.value in {"stopped", "blocked"}
    )[:2]
    grounded_score = _score_candidate(
        support_count=len(grounded_support),
        satisfied_count=len(confirmed),
        violated_count=len(grounded_violations),
        unresolved_load=max(0.0, unresolved_load - 0.5),
        conflict_load=len(conflicted),
        authority_weight=authority_weight,
        practical_pressure=-c05_pressure,
    )
    candidates.append(
        T03HypothesisCandidate(
            hypothesis_id="t03-hypothesis:grounded-scene",
            scene_variant_id=f"{t02_result.state.constrained_scene_id}:grounded",
            support_sources=grounded_support,
            violated_constraints=grounded_violations,
            satisfied_constraints=confirmed,
            unresolved_load=round(max(0.0, unresolved_load - 0.5), 3),
            authority_profile=(
                f"authority_weight={authority_weight:.3f}",
                "supports:confirmed_bindings",
            ),
            competition_score=round(grounded_score, 3),
            stability_state=(
                T03StabilityState.STABLE
                if grounded_score >= 0.45 and not conflicted
                else T03StabilityState.PROVISIONAL
            ),
            divergence_signature=_divergence_signature(grounded_support, grounded_violations),
            status=T03HypothesisStatus.CANDIDATE,
            provenance="t03.hypothesis.from_t02_confirmed_bindings",
        )
    )

    ambiguity_support = tuple(dict.fromkeys((*provisional, *confirmed[:1], *blocked[:1])))
    ambiguity_violations = tuple(dict.fromkeys((*blocked[:2], *conflicted[:1])))
    ambiguity_score = _score_candidate(
        support_count=len(ambiguity_support),
        satisfied_count=len(provisional),
        violated_count=len(ambiguity_violations),
        unresolved_load=unresolved_load + 0.35,
        conflict_load=max(1, len(conflicted)),
        authority_weight=authority_weight,
        practical_pressure=0.05,
    )
    candidates.append(
        T03HypothesisCandidate(
            hypothesis_id="t03-hypothesis:ambiguity-preserving",
            scene_variant_id=f"{t02_result.state.constrained_scene_id}:ambiguity",
            support_sources=ambiguity_support,
            violated_constraints=ambiguity_violations,
            satisfied_constraints=provisional,
            unresolved_load=round(unresolved_load + 0.35, 3),
            authority_profile=(
                f"authority_weight={authority_weight:.3f}",
                "supports:provisional_bindings",
            ),
            competition_score=round(ambiguity_score, 3),
            stability_state=T03StabilityState.CONTESTED,
            divergence_signature=_divergence_signature(ambiguity_support, ambiguity_violations),
            status=T03HypothesisStatus.CANDIDATE,
            provenance="t03.hypothesis.from_t02_provisional_bindings",
        )
    )

    if conflicted:
        conflict_score = _score_candidate(
            support_count=len(conflicted),
            satisfied_count=0,
            violated_count=len(conflicted),
            unresolved_load=unresolved_load + 0.65,
            conflict_load=len(conflicted),
            authority_weight=authority_weight,
            practical_pressure=0.0,
        )
        candidates.append(
            T03HypothesisCandidate(
                hypothesis_id="t03-hypothesis:conflict-preserving",
                scene_variant_id=f"{t02_result.state.constrained_scene_id}:conflict",
                support_sources=conflicted,
                violated_constraints=conflicted,
                satisfied_constraints=(),
                unresolved_load=round(unresolved_load + 0.65, 3),
                authority_profile=(
                    f"authority_weight={authority_weight:.3f}",
                    "supports:conflict_preservation",
                ),
                competition_score=round(conflict_score, 3),
                stability_state=T03StabilityState.CONTESTED,
                divergence_signature=_divergence_signature(conflicted, conflicted),
                status=T03HypothesisStatus.CANDIDATE,
                provenance="t03.hypothesis.from_t02_conflict_records",
            )
        )

    if blocked:
        blocked_score = _score_candidate(
            support_count=0,
            satisfied_count=0,
            violated_count=len(blocked),
            unresolved_load=unresolved_load + 0.5,
            conflict_load=max(1, len(conflicted)),
            authority_weight=authority_weight,
            practical_pressure=0.0,
        )
        candidates.append(
            T03HypothesisCandidate(
                hypothesis_id="t03-hypothesis:blocked-path",
                scene_variant_id=f"{t02_result.state.constrained_scene_id}:blocked",
                support_sources=(),
                violated_constraints=blocked,
                satisfied_constraints=(),
                unresolved_load=round(unresolved_load + 0.5, 3),
                authority_profile=(
                    f"authority_weight={authority_weight:.3f}",
                    "supports:blocked_bindings",
                ),
                competition_score=round(blocked_score, 3),
                stability_state=T03StabilityState.BLOCKED,
                divergence_signature=_divergence_signature((), blocked),
                status=T03HypothesisStatus.BLOCKED,
                provenance="t03.hypothesis.from_t02_blocked_bindings",
            )
        )

    if competition_mode is T03CompetitionMode.HIDDEN_TEXT_RERANKING_ABLATION and candidates:
        wording = str(t01_result.state.wording_surface_ref or "").strip().lower()
        biased = sorted(
            candidates,
            key=lambda item: (
                0 if ("ambiguity" in wording and "ambiguity" in item.hypothesis_id) else 1,
                item.hypothesis_id,
            ),
        )
        first = biased[0]
        boosted = replace(first, competition_score=round(first.competition_score + 0.65, 3))
        candidates = [boosted, *(item for item in candidates if item.hypothesis_id != first.hypothesis_id)]

    return tuple(candidates)


def _score_candidate(
    *,
    support_count: int,
    satisfied_count: int,
    violated_count: int,
    unresolved_load: float,
    conflict_load: int,
    authority_weight: float,
    practical_pressure: float,
) -> float:
    return (
        ((support_count * 0.7) + (satisfied_count * 0.3)) * authority_weight
        - (violated_count * 0.55)
        - (unresolved_load * 0.35)
        - (conflict_load * 0.3)
        + practical_pressure
    )


def _divergence_signature(
    support_sources: tuple[str, ...] | tuple[()],
    violated_constraints: tuple[str, ...] | tuple[()],
) -> str:
    support = "|".join(sorted(support_sources)) if support_sources else "none"
    violated = "|".join(sorted(violated_constraints)) if violated_constraints else "none"
    return f"support={support};violated={violated}"


def _forbidden_shortcuts_from_mode(mode: T03CompetitionMode) -> list[str]:
    forbidden: list[str] = []
    if mode is T03CompetitionMode.GREEDY_ARGMAX_ABLATION:
        forbidden.append(ForbiddenT03Shortcut.GREEDY_WINNER_TAKE_ALL_ARGMAX.value)
    if mode is T03CompetitionMode.HIDDEN_TEXT_RERANKING_ABLATION:
        forbidden.append(ForbiddenT03Shortcut.HIDDEN_TEXT_RERANKING.value)
    if mode is T03CompetitionMode.CONVENIENCE_BIAS_ABLATION:
        forbidden.append(ForbiddenT03Shortcut.CONVENIENCE_BIASED_CANDIDATE_SELECTION.value)
    if mode is T03CompetitionMode.AUTHORITY_WEIGHT_DISABLE_ABLATION:
        forbidden.append(ForbiddenT03Shortcut.AUTHORITY_WEIGHT_DISABLED.value)
    return forbidden


def _apply_mode_biases(
    *,
    candidates: tuple[T03HypothesisCandidate, ...],
    t01_result: T01ActiveFieldResult,
    competition_mode: T03CompetitionMode,
    authority_weight: float,
) -> tuple[tuple[T03HypothesisCandidate, ...], tuple[str, ...]]:
    if competition_mode is not T03CompetitionMode.CONVENIENCE_BIAS_ABLATION:
        if (
            authority_weight < 0.5
            and candidates
            and max(item.competition_score for item in candidates) > 0.55
        ):
            return candidates, (ForbiddenT03Shortcut.LOW_AUTHORITY_SMOOTH_DOMINATION.value,)
        return candidates, ()
    forbidden: list[str] = []
    wording = str(t01_result.state.wording_surface_ref or "").strip().lower()
    adjusted: list[T03HypothesisCandidate] = []
    for item in candidates:
        boost = 0.0
        if "ambiguity" in item.hypothesis_id:
            boost += 0.25
        if wording and "clean" in wording and "grounded" in item.hypothesis_id:
            boost -= 0.1
        adjusted.append(replace(item, competition_score=round(item.competition_score + boost, 3)))
    if authority_weight < 0.55:
        forbidden.append(ForbiddenT03Shortcut.LOW_AUTHORITY_SMOOTH_DOMINATION.value)
    return tuple(adjusted), tuple(forbidden)


def _derive_convergence_frontier(
    *,
    ranked: tuple[T03HypothesisCandidate, ...],
    preserve_plurality: bool,
    competition_mode: T03CompetitionMode,
) -> tuple[T03ConvergenceStatus, str | None, str | None, tuple[str, ...], tuple[str, ...], bool]:
    active = tuple(item for item in ranked if item.status is not T03HypothesisStatus.BLOCKED)
    if not active:
        return (
            T03ConvergenceStatus.HONEST_NONCONVERGENCE,
            None,
            None,
            (),
            tuple(item.hypothesis_id for item in ranked),
            False,
        )
    leader = active[0]
    second_score = active[1].competition_score if len(active) > 1 else -99.0
    margin = leader.competition_score - second_score
    tie_margin = 0.08
    if leader.unresolved_load >= 1.0 or leader.stability_state in {
        T03StabilityState.PROVISIONAL,
        T03StabilityState.CONTESTED,
    }:
        tie_margin = 0.2
    if any(
        item.stability_state is T03StabilityState.CONTESTED
        for item in active[:2]
    ):
        tie_margin = max(tie_margin, 0.18)
    tied_ids = tuple(
        item.hypothesis_id
        for item in active
        if abs(item.competition_score - leader.competition_score) <= tie_margin
    )
    if (
        preserve_plurality
        and len(tied_ids) < 2
        and len(active) > 1
        and leader.unresolved_load >= 1.2
        and leader.stability_state in {T03StabilityState.PROVISIONAL, T03StabilityState.CONTESTED}
    ):
        tied_ids = (leader.hypothesis_id, active[1].hypothesis_id)
    forced_single = False
    if competition_mode is T03CompetitionMode.FORCED_SINGLE_WINNER_ABLATION and len(tied_ids) > 1:
        forced_single = True
        tied_ids = ()
    if competition_mode is T03CompetitionMode.GREEDY_ARGMAX_ABLATION:
        eliminated = tuple(item.hypothesis_id for item in active[1:])
        return (
            T03ConvergenceStatus.STABLE_LOCAL_CONVERGENCE,
            leader.hypothesis_id,
            None,
            (),
            eliminated,
            forced_single,
        )
    if len(tied_ids) > 1 and preserve_plurality:
        return (
            T03ConvergenceStatus.HONEST_NONCONVERGENCE,
            None,
            leader.hypothesis_id,
            tied_ids,
            tuple(
                item.hypothesis_id
                for item in active
                if item.hypothesis_id not in tied_ids
            ),
            forced_single,
        )
    if margin >= 0.35 and leader.competition_score >= 0.45 and leader.unresolved_load < 1.25:
        return (
            T03ConvergenceStatus.STABLE_LOCAL_CONVERGENCE,
            leader.hypothesis_id,
            None,
            (),
            tuple(item.hypothesis_id for item in active[1:] if item.competition_score < -0.1),
            forced_single,
        )
    if leader.competition_score >= 0.1:
        return (
            T03ConvergenceStatus.PROVISIONAL_CONVERGENCE,
            None,
            leader.hypothesis_id,
            (),
            tuple(item.hypothesis_id for item in active[1:] if item.competition_score < -0.2),
            forced_single,
        )
    return (
        T03ConvergenceStatus.CONTINUE_COMPETING,
        None,
        leader.hypothesis_id,
        (),
        tuple(item.hypothesis_id for item in active[1:] if item.competition_score < -0.2),
        forced_single,
    )


def _derive_reactivation(
    *,
    ranked: tuple[T03HypothesisCandidate, ...],
    prior_state: T03CompetitionState | None,
    allow_revival: bool,
    competition_mode: T03CompetitionMode,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if prior_state is None:
        return (), ()
    prior_by_id = {item.hypothesis_id: item for item in prior_state.candidates}
    revival_candidates = []
    for item in ranked:
        prior = prior_by_id.get(item.hypothesis_id)
        if prior is None:
            continue
        prior_support = len(prior.support_sources)
        current_support = len(item.support_sources)
        support_gained = current_support > prior_support
        score_improved = item.competition_score > prior.competition_score + 0.12
        prior_was_weakened = prior.status in {
            T03HypothesisStatus.ELIMINATED,
            T03HypothesisStatus.BLOCKED,
            T03HypothesisStatus.CANDIDATE,
        } or prior.competition_score < 0.1
        if (
            score_improved
            and support_gained
            and prior_was_weakened
        ):
            revival_candidates.append(item.hypothesis_id)
    forbidden: list[str] = []
    if not allow_revival or competition_mode is T03CompetitionMode.NO_REVIVAL_ABLATION:
        if revival_candidates:
            forbidden.append(ForbiddenT03Shortcut.NO_REVIVAL_COMPETITION.value)
        return (), tuple(forbidden)
    return tuple(dict.fromkeys(revival_candidates)), ()


def _apply_candidate_statuses(
    *,
    ranked: tuple[T03HypothesisCandidate, ...],
    leader_id: str | None,
    provisional_id: str | None,
    tied_ids: tuple[str, ...],
    blocked_ids: tuple[str, ...],
    eliminated_ids: tuple[str, ...],
    reactivated_ids: tuple[str, ...],
) -> tuple[T03HypothesisCandidate, ...]:
    updated: list[T03HypothesisCandidate] = []
    for item in ranked:
        status = item.status
        if item.hypothesis_id in blocked_ids:
            status = T03HypothesisStatus.BLOCKED
        elif item.hypothesis_id in reactivated_ids:
            status = T03HypothesisStatus.REACTIVATED
        elif item.hypothesis_id == leader_id:
            status = T03HypothesisStatus.LEADING
        elif item.hypothesis_id == provisional_id:
            status = T03HypothesisStatus.PROVISIONAL_FRONTRUNNER
        elif item.hypothesis_id in tied_ids:
            status = T03HypothesisStatus.TIED_COMPETITOR
        elif item.hypothesis_id in eliminated_ids:
            status = T03HypothesisStatus.ELIMINATED
        else:
            status = T03HypothesisStatus.CANDIDATE
        updated.append(replace(item, status=status))
    return tuple(updated)


def _build_publication_frontier(
    *,
    ranked: tuple[T03HypothesisCandidate, ...],
    leader_id: str | None,
    tied_ids: tuple[str, ...],
    t01_result: T01ActiveFieldResult,
    t02_result: T02ConstrainedSceneResult,
    authority_weight: float,
    convergence_status: T03ConvergenceStatus,
) -> T03PublicationFrontierSnapshot:
    neighborhood = tuple(item.hypothesis_id for item in ranked[:3])
    return T03PublicationFrontierSnapshot(
        current_leader=leader_id,
        competitive_neighborhood=neighborhood if neighborhood else tied_ids,
        unresolved_conflicts=tuple(
            dict.fromkeys(
                (
                    *(item.conflict_id for item in t02_result.state.conflict_records),
                    *(item.edge_id for item in t01_result.state.relation_edges if item.contested),
                )
            )
        ),
        open_slots=tuple(item.slot_id for item in t01_result.state.unresolved_slots),
        authority_profile=(
            f"authority_weight={authority_weight:.3f}",
            f"source_tags={len(t02_result.state.source_authority_tags)}",
        ),
        stability_status=convergence_status.value,
        provenance="t03.1.publication_frontier_snapshot",
    )


def _build_gate(
    *,
    state: T03CompetitionState,
    forbidden_shortcuts: tuple[str, ...],
    preserve_plurality: bool,
) -> T03GateDecision:
    frontier_shortcut_markers = {
        ForbiddenT03Shortcut.GREEDY_WINNER_TAKE_ALL_ARGMAX.value,
        ForbiddenT03Shortcut.HIDDEN_TEXT_RERANKING.value,
        ForbiddenT03Shortcut.CONVENIENCE_BIASED_CANDIDATE_SELECTION.value,
        ForbiddenT03Shortcut.FORCED_SINGLE_WINNER_UNDER_AMBIGUITY.value,
        ForbiddenT03Shortcut.AUTHORITY_WEIGHT_DISABLED.value,
    }
    frontier_shortcut_detected = any(
        marker in forbidden_shortcuts for marker in frontier_shortcut_markers
    )
    convergence_consumer_ready = state.convergence_status in {
        T03ConvergenceStatus.PROVISIONAL_CONVERGENCE,
        T03ConvergenceStatus.STABLE_LOCAL_CONVERGENCE,
    } and state.publication_frontier.current_leader is not None
    frontier_consumer_ready = bool(
        state.publication_frontier.competitive_neighborhood
        and state.publication_frontier.authority_profile
    ) and not frontier_shortcut_detected
    nonconvergence_preserved = bool(
        state.convergence_status is T03ConvergenceStatus.HONEST_NONCONVERGENCE
        and preserve_plurality
        and (
            state.tied_competitor_ids
            or state.publication_frontier.unresolved_conflicts
            or state.publication_frontier.open_slots
        )
    )
    restrictions: list[str] = [
        "t03_hypothesis_competition_contract_must_be_read",
        "t03_authority_weighted_support_must_be_read",
        "t03_constraint_structure_must_be_read",
        "t03_convergence_state_must_be_read",
        "t03_publication_frontier_must_be_read",
    ]
    if not convergence_consumer_ready:
        restrictions.append("t03_convergence_consumer_not_ready")
    if not frontier_consumer_ready:
        restrictions.append("t03_frontier_consumer_not_ready")
    if frontier_shortcut_detected:
        restrictions.append("t03_frontier_shortcut_detected")
    if (
        state.convergence_status is T03ConvergenceStatus.HONEST_NONCONVERGENCE
        and not nonconvergence_preserved
    ):
        restrictions.append("t03_nonconvergence_not_preserved")
    if ForbiddenT03Shortcut.FORCED_SINGLE_WINNER_UNDER_AMBIGUITY.value in forbidden_shortcuts:
        restrictions.append("t03_forced_single_winner_shortcut_detected")
    return T03GateDecision(
        convergence_consumer_ready=convergence_consumer_ready,
        frontier_consumer_ready=frontier_consumer_ready,
        nonconvergence_preserved=nonconvergence_preserved,
        forbidden_shortcuts=forbidden_shortcuts,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "t03 produced bounded hypothesis competition and silent convergence frontier over t01/t02 structures"
        ),
    )


def _build_scope_marker() -> T03ScopeMarker:
    return T03ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        t03_first_slice_only=True,
        t04_implemented=False,
        o01_implemented=False,
        o02_implemented=False,
        o03_implemented=False,
        full_silent_thought_line_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded t03 slice only; t04/o01/o02/o03 and full silent-thought line remain out of scope"
        ),
    )
